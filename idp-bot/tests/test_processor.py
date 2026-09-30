"""Fixtures sintéticas; estos tests no miden precisión en documentos oficiales."""
import io
import os
import unittest
from unittest.mock import patch
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont
from pypdf import PdfWriter
from pypdf.generic import DictionaryObject, NameObject, DecodedStreamObject
from fastapi.testclient import TestClient
from processor import analyze, evaluate, extract_pages, DocumentError
from main import app, gate

SAMPLES = {
 'ine': 'INSTITUTO NACIONAL ELECTORAL\nCREDENCIAL PARA VOTAR\nNOMBRE\nPERSONA PRUEBA FICTICIA\nDOMICILIO\nCALLE EJEMPLO 123\nCURP\nPEPF900101HGRRRC09\nCLAVE DE ELECTOR\nFICTICIO123456\nSECCION 1234\nVIGENCIA 2024 - 2034',
 'cfe': 'COMISION FEDERAL DE ELECTRICIDAD\nCFE\nNOMBRE DEL CLIENTE: PERSONA FICTICIA\nDIRECCION DEL SERVICIO\nCALLE EJEMPLO 123\nCOLONIA DEMOSTRACION\nACAPULCO GUERRERO 39000\nNUMERO DE SERVICIO 123456789012\nTOTAL A PAGAR 150\nPERIODO FACTURADO ENERO FEBRERO 2026\nTARIFA 1',
 'curp': 'REGISTRO NACIONAL DE POBLACION\nCLAVE UNICA DE REGISTRO DE POBLACION\nCURP CERTIFICADA\nCURP\nPEPF900101HGRRRC09\nNOMBRE(S): PERSONA\nPRIMER APELLIDO: PRUEBA\nSEGUNDO APELLIDO: FICTICIA\nFECHA DE NACIMIENTO: 01/01/1990',
}

def pdf_bytes(text):
    writer = PdfWriter()
    page = writer.add_blank_page(width=800, height=1000)
    font = DictionaryObject({NameObject('/Type'): NameObject('/Font'), NameObject('/Subtype'): NameObject('/Type1'), NameObject('/BaseFont'): NameObject('/Helvetica')})
    page[NameObject('/Resources')] = DictionaryObject({NameObject('/Font'): DictionaryObject({NameObject('/F1'): writer._add_object(font)})})
    instructions = ['BT /F1 16 Tf 24 TL 35 950 Td']
    for line in text.splitlines():
        escaped = line.replace('\\', '\\\\').replace('(', '\\(').replace(')', '\\)')
        instructions.append(f'({escaped}) Tj T*')
    instructions.append('ET')
    stream = DecodedStreamObject()
    stream.set_data('\n'.join(instructions).encode('ascii'))
    page[NameObject('/Contents')] = writer._add_object(stream)
    out = io.BytesIO(); writer.write(out)
    return out.getvalue()

def sample_image(text):
    candidates = [Path('C:/Windows/Fonts/arial.ttf'), Path('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf')]
    font = next((ImageFont.truetype(str(p), 30) for p in candidates if p.exists()), ImageFont.load_default(size=30))
    image = Image.new('RGB', (1500, 1100), 'white')
    ImageDraw.Draw(image).multiline_text((40, 40), text, font=font, fill='black', spacing=17)
    return image

class ProcessorTests(unittest.TestCase):
    def test_native_pdf_all_types(self):
        for kind, text in SAMPLES.items():
            with self.subTest(kind=kind):
                result = analyze(pdf_bytes(text), 'test.pdf', kind)
                self.assertEqual(result['status'], 'accepted', result)
                self.assertEqual(result['sources'], ['pdf_text'])
                self.assertFalse(result['official_validation'])

    def test_detected_type_is_not_supplied_type(self):
        result = analyze(pdf_bytes(SAMPLES['cfe']), 'test.pdf', 'ine')
        self.assertEqual(result['document_type'], 'cfe')
        self.assertEqual(result['code'], 'type_mismatch')

    def test_ocr_joined_words(self):
        for kind, sample in SAMPLES.items():
            with self.subTest(kind=kind):
                # Reproducir el defecto observado con el motor OCR real.
                text = sample.replace(' ', '')
                result = evaluate([(text, 'ocr')], kind)
                self.assertEqual(result['status'], 'accepted', result)

    def test_unknown_is_not_accepted(self):
        result = evaluate([('DOCUMENTO DE PRUEBA SIN ENCABEZADOS CONOCIDOS', 'pdf_text')], 'ine')
        self.assertEqual(result['status'], 'needs_review')

    def test_curp_name_before_label(self):
        text = SAMPLES['curp'].replace('NOMBRE(S): PERSONA', 'PERSONA PRUEBA FICTICIA\nNombre')
        result = evaluate([(text, 'pdf_text')], 'curp')
        self.assertEqual(result['status'], 'accepted', result)
        self.assertEqual(result['extracted_data']['nombre'], 'PERSONA PRUEBA FICTICIA')

    def test_curp_name_variants(self):
        for label in ['Nombre:', 'Nombre(s):', 'Nombres:', 'Nombre completo:', 'NOMBREDELREGISTRADO:']:
            with self.subTest(label=label):
                text = SAMPLES['curp'].replace('NOMBRE(S): PERSONA', label + ' PERSONA FICTICIA')
                self.assertEqual(evaluate([(text, 'ocr')], 'curp')['extracted_data']['nombre'], 'PERSONA FICTICIA')

    def test_missing_name_cannot_use_legal_paragraph(self):
        text = SAMPLES['curp'].replace('NOMBRE(S): PERSONA', 'Nombre\nEL PRESENTE DOCUMENTO CERTIFICA EL REGISTRO')
        result = evaluate([(text, 'pdf_text')], 'curp')
        self.assertEqual(result['status'], 'needs_review')
        self.assertIsNone(result['extracted_data']['nombre'])

    def test_missing_name_triggers_optical_fallback(self):
        with patch('processor.extract_pages', side_effect=[[(SAMPLES['curp'].replace('NOMBRE(S): PERSONA', ''), 'pdf_text')], [(SAMPLES['curp'], 'ocr')]]) as extract:
            result = analyze(b'%PDF-test', 'test.pdf', 'curp')
        self.assertEqual(result['status'], 'accepted')
        self.assertTrue(extract.call_args.kwargs['force_ocr'])

    def test_mixed_documents_require_review(self):
        result = evaluate([(SAMPLES['cfe'], 'pdf_text'), (SAMPLES['ine'], 'pdf_text')], 'ine')
        self.assertEqual(result['document_type'], 'unknown')

    def test_missing_address(self):
        result = evaluate([('CFE\nTOTAL A PAGAR 20\nNUMERO DE SERVICIO 1234', 'ocr')], 'cfe')
        self.assertEqual(result['code'], 'fields_need_review')

    def test_expired_ine(self):
        result = evaluate([(SAMPLES['ine'].replace('2024 - 2034', '2010 - 2015'), 'ocr')], 'ine')
        self.assertEqual(result['status'], 'needs_review')

    def test_corrupted_image(self):
        with self.assertRaises(DocumentError): analyze(b'not an image', 'image.png', 'ine')

    def test_encrypted_pdf(self):
        writer = PdfWriter(); writer.add_blank_page(300, 300); writer.encrypt('secret')
        data = io.BytesIO(); writer.write(data)
        with self.assertRaises(DocumentError): analyze(data.getvalue(), 'file.pdf', 'ine')

    def test_page_limit(self):
        writer = PdfWriter()
        for _ in range(11): writer.add_blank_page(300, 300)
        data = io.BytesIO(); writer.write(data)
        with self.assertRaises(DocumentError): analyze(data.getvalue(), 'file.pdf', 'ine')

    def test_image_ocr_all_types(self):
        for kind, text in SAMPLES.items():
            with self.subTest(kind=kind):
                out = io.BytesIO(); sample_image(text).save(out, format='PNG')
                result = analyze(out.getvalue(), 'synthetic.png', kind)
                self.assertEqual(result['status'], 'accepted', result)

    def test_scanned_pdf_ocr(self):
        out = io.BytesIO(); sample_image(SAMPLES['cfe']).save(out, format='PDF')
        result = analyze(out.getvalue(), 'scan.pdf', 'cfe')
        self.assertEqual(result['status'], 'accepted', result)
        self.assertEqual(result['sources'], ['ocr'])

class APITests(unittest.TestCase):
    def setUp(self):
        self.client = TestClient(app)
        self.headers = {'X-IDP-Key': os.getenv('IDP_API_KEY', 'local-development-key')}

    def test_contract(self):
        response = self.client.post('/process-document/', headers=self.headers, data={'doc_type': 'curp'}, files={'file': ('sample.pdf', pdf_bytes(SAMPLES['curp']), 'application/pdf')})
        self.assertEqual(response.status_code, 200, response.text)
        self.assertEqual(response.json()['status'], 'accepted')
        self.assertNotIn('raw_ocr', response.json())

    def test_unauthorized(self):
        response = self.client.post('/process-document/', data={'doc_type': 'ine'}, files={'file': ('a.png', b'x')})
        self.assertEqual(response.status_code, 401)

    def test_unsupported_type(self):
        response = self.client.post('/process-document/', headers=self.headers, data={'doc_type': 'rfc'}, files={'file': ('a.png', b'x')})
        self.assertEqual(response.status_code, 422)
        self.assertIn('message', response.json())

    def test_busy(self):
        gate.acquire()
        try:
            response = self.client.post('/process-document/', headers=self.headers, data={'doc_type': 'ine'}, files={'file': ('a.png', b'x')})
            self.assertEqual(response.status_code, 503)
        finally: gate.release()

if __name__ == '__main__': unittest.main()
