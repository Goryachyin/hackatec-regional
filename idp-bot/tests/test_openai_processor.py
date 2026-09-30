import io
import json
import unittest
from unittest.mock import patch
import httpx
from PIL import Image
from fastapi.testclient import TestClient
from main import app
from openai_processor import Extraction, Fields, analyze, evaluate_extraction, prepare_input
from processor import DocumentError
from test_processor import pdf_bytes


def extraction(kind='curp', **changes):
    fields = dict.fromkeys(Fields.model_fields)
    fields.update(nombre_completo='PERSONA PRUEBA FICTICIA', nombres='PERSONA',
                  primer_apellido='PRUEBA', segundo_apellido='FICTICIA',
                  curp='PEPF900101HGRRRC09', fecha_nacimiento='1990-01-01',
                  direccion='CALLE EJEMPLO 123', vigencia='2034')
    fields.update(changes)
    return Extraction(document_type=kind, multiple_documents=False, readable=True, fields=Fields(**fields))


class OpenAITests(unittest.TestCase):
    def call(self, body=None, status=200):
        body = body if body is not None else {'status': 'completed', 'output': [
            {'type': 'message', 'content': [{'type': 'output_text', 'text': extraction().model_dump_json()}]}]}
        response = httpx.Response(status, json=body, request=httpx.Request('POST', 'https://api.openai.com/v1/responses'))
        with patch.dict('os.environ', {'OPENAI_API_KEY': 'test-only'}), patch('openai_processor.httpx.Client') as client:
            client.return_value.__enter__.return_value.post.return_value = response
            result = analyze(pdf_bytes('SYNTHETIC'), 'private-name.pdf', 'curp')
            payload = client.return_value.__enter__.return_value.post.call_args.kwargs['json']
        return result, payload

    def test_pdf_transport_and_exact_fields(self):
        result, payload = self.call()
        self.assertEqual(result['extracted_data']['nombre_completo'], 'PERSONA PRUEBA FICTICIA')
        self.assertEqual(result['extracted_data']['primer_apellido'], 'PRUEBA')
        self.assertEqual(result['extracted_data']['fecha_nacimiento'], '1990-01-01')
        self.assertEqual(result['status'], 'accepted')
        self.assertFalse(payload['store'])
        self.assertTrue(payload['text']['format']['strict'])
        content = payload['input'][1]['content'][0]
        self.assertEqual(content['type'], 'input_file')
        self.assertEqual(content['filename'], 'document.pdf')
        self.assertTrue(content['file_data'].startswith('data:application/pdf;base64,'))

    def test_image_input(self):
        output = io.BytesIO(); Image.new('RGB', (20, 20)).save(output, 'JPEG')
        content, pages = prepare_input(output.getvalue(), 'a.jpg')
        self.assertEqual(content['type'], 'input_image')
        self.assertEqual(content['detail'], 'high')
        self.assertEqual(pages, 1)

    def test_new_types_require_visible_fields(self):
        extra = dict(titulo_documento='DOCUMENTO DE PRUEBA', emisor='EMISOR FICTICIO',
                     titular='PERSONA FICTICIA', concepto='CONCEPTO DE PRUEBA', folio='001',
                     fecha_emision='2020-01-01', vigencia_hasta='2099-01-01',
                     clave_catastral='00001234', residuos='Papel y cartón')
        for kind in ['propiedad', 'pc_pago', 'pc_uso_suelo', 'op_solicitud', 'op_predial', 'eco_recoleccion', 'eco_solicitud', 'clave_catastral']:
            with self.subTest(kind=kind):
                result = evaluate_extraction(extraction(kind, **extra), kind, 1)
                self.assertEqual(result['status'], 'accepted')
                self.assertFalse(result['official_validation'])
                self.assertEqual(evaluate_extraction(extraction(kind), kind, 1)['status'], 'needs_review')
        self.assertEqual(evaluate_extraction(extraction('op_predial', **extra), 'pc_pago', 1)['status'], 'rejected')
        self.assertEqual(evaluate_extraction(extraction('op_predial', **extra), 'clave_catastral', 1)['status'], 'accepted')
        extra['vigencia_hasta'] = '2000-01-01'
        self.assertEqual(evaluate_extraction(extraction('pc_uso_suelo', **extra), 'pc_uso_suelo', 1)['status'], 'needs_review')

    def test_missing_optional_fields_not_invented(self):
        result = evaluate_extraction(extraction(primer_apellido=None, fecha_nacimiento=None), 'curp', 1)
        self.assertIsNone(result['extracted_data']['primer_apellido'])
        self.assertIsNone(result['extracted_data']['fecha_nacimiento'])

    def test_decisions(self):
        cases = [(extraction('cfe'), 'curp', 'rejected'),
                 (extraction(curp='INVALID'), 'curp', 'needs_review'),
                 (extraction(nombre_completo=None), 'curp', 'needs_review'),
                 (extraction('ine', vigencia='2000'), 'ine', 'needs_review'),
                 (extraction(fecha_nacimiento='1990-02-31'), 'curp', 'needs_review'),
                 (extraction('unknown'), 'curp', 'needs_review'),
                 (extraction('cfe'), 'cfe', 'accepted')]
        for obj, expected, status in cases:
            with self.subTest(expected=expected, status=status):
                self.assertEqual(evaluate_extraction(obj, expected, 1)['status'], status)
        for attr in ('multiple_documents', 'readable'):
            obj = extraction(); setattr(obj, attr, attr == 'multiple_documents')
            self.assertEqual(evaluate_extraction(obj, 'curp', 1)['status'], 'needs_review')

    def test_provider_failures(self):
        for status in (401, 429, 500):
            with self.subTest(status=status), self.assertRaises(DocumentError) as ctx:
                self.call(status=status)
            self.assertEqual(ctx.exception.status, 503)
        for body in ({'status': 'incomplete'}, {'status': 'completed', 'output': []},
                     {'status': 'completed', 'output': [{'type': 'message', 'content': [{'type': 'output_text', 'text': '{}'}]}]}):
            with self.assertRaises(DocumentError) as ctx:
                self.call(body)
            self.assertEqual(ctx.exception.code, 'provider_invalid_response')

    def test_timeout(self):
        with patch.dict('os.environ', {'OPENAI_API_KEY': 'test'}), patch('openai_processor.httpx.Client') as client:
            client.return_value.__enter__.return_value.post.side_effect = httpx.ReadTimeout('timeout')
            with self.assertRaises(DocumentError) as ctx:
                analyze(pdf_bytes('TEST'), 'a.pdf', 'curp')
            self.assertEqual(ctx.exception.code, 'provider_timeout')

    def test_quota_is_not_temporary_rate_limit(self):
        for code in ('insufficient_quota', 'credit_balance_exhausted', 'project_spend_limit_exceeded'):
            with self.subTest(code=code), self.assertRaises(DocumentError) as ctx:
                self.call({'error': {'code': code}}, status=429)
            self.assertEqual(ctx.exception.code, 'provider_quota')
        with self.assertRaises(DocumentError) as ctx:
            self.call({'error': {'code': 'rate_limit_exceeded'}}, status=429)
        self.assertEqual(ctx.exception.code, 'provider_rate_limit')

    def test_refusal(self):
        with self.assertRaises(DocumentError) as ctx:
            self.call({'status': 'completed', 'output': [{'type': 'message', 'content': [{'type': 'refusal', 'refusal': 'No'}]}]})
        self.assertEqual(ctx.exception.code, 'provider_refusal')

    def test_missing_key_and_bad_file_do_not_call_provider(self):
        with patch.dict('os.environ', {'OPENAI_API_KEY': ''}), patch('openai_processor.httpx.Client') as client:
            for data in (b'bad', pdf_bytes('TEST')):
                with self.assertRaises(DocumentError):
                    analyze(data, 'a.pdf', 'curp')
            client.assert_not_called()

    def test_route_selects_openai(self):
        expected = evaluate_extraction(extraction(), 'curp', 1)
        with patch.dict('os.environ', {'IDP_PROVIDER': 'openai', 'OPENAI_API_KEY': 'test', 'IDP_API_KEY': 'test-internal'}), patch('openai_processor.analyze', return_value=expected) as mock:
            response = TestClient(app).post('/process-document/', headers={'X-IDP-Key': 'test-internal'}, data={'doc_type': 'curp'}, files={'file': ('a.pdf', pdf_bytes('TEST'))})
            self.assertEqual(response.json(), expected)
            mock.assert_called_once()

    def test_health_missing_key(self):
        with patch.dict('os.environ', {'IDP_PROVIDER': 'openai', 'OPENAI_API_KEY': ''}):
            self.assertEqual(TestClient(app).get('/health/').status_code, 503)
