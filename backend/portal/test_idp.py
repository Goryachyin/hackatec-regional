import io
import json
import os
import tempfile
import unittest
from copy import deepcopy
from unittest.mock import patch
from urllib.error import URLError

from PIL import Image
from django.test import TestCase, override_settings
from django.core.files.uploadedfile import SimpleUploadedFile
from .models import User, Document, Application, Attachment
from .idp import IDPError, inspect_document


def sample_upload():
    out = io.BytesIO(); Image.new('RGB', (100, 100), 'white').save(out, 'PNG')
    return SimpleUploadedFile('synthetic.png', out.getvalue(), content_type='image/png')


def accepted(kind='ine'):
    from .catalog import IDP_REQUIRED
    return {'schema_version': 1, 'expected_type': kind, 'document_type': kind, 'status': 'accepted',
            'code': 'precheck_passed', 'message': 'Revisión preliminar completa.', 'official_validation': False,
            'extracted_data': {'nombre': 'PERSONA FICTICIA', 'curp': 'PEPF900101HGRRRC09', 'vigencia': '2034'} if kind == 'ine' else {key: 'DATO FICTICIO' for key in IDP_REQUIRED[kind]},
            'checks': [{'field': 'type', 'passed': True}]}


class IDPIntegrationTests(TestCase):
    def setUp(self):
        self.media = tempfile.TemporaryDirectory()
        self.settings_override = override_settings(
            MEDIA_ROOT=self.media.name,
            STORAGES={
                'default': {'BACKEND': 'django.core.files.storage.FileSystemStorage'},
                'staticfiles': {'BACKEND': 'django.contrib.staticfiles.storage.StaticFilesStorage'},
            },
        )
        self.settings_override.enable()
        self.addCleanup(self.settings_override.disable)
        self.addCleanup(self.media.cleanup)
        self.user = User.objects.create_user(username='test@example.invalid', email='test@example.invalid', curp='PEPF900101HGRRRC09', password='test-pass-123', email_verified=True)
        self.client.force_login(self.user)

    def test_health_is_public_and_checks_database(self):
        self.client.logout()
        response = self.client.get('/api/health/')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {'status': 'ok'})

    def create_document(self, kind='ine', app=None):
        with patch('portal.views.inspect_document', return_value=accepted(kind)):
            data = {'file': sample_upload(), 'kind': kind}
            if app: data['application_id'] = str(app.id)
            response = self.client.post('/api/documents/', data)
            self.assertEqual(response.status_code, 201, response.content)
            return Document.objects.get(id=response.json()['document']['id'])

    def test_vault_upload_saves_analysis(self):
        doc = self.create_document()
        self.assertTrue(doc.in_vault)
        self.assertEqual(doc.analysis_status, 'accepted')
        self.assertIsNotNone(doc.analyzed_at)

    def test_history_contains_only_submitted_applications(self):
        from django.utils import timezone
        Application.objects.create(owner=self.user, procedure='predial')
        sent = Application.objects.create(owner=self.user, procedure='predial', status='submitted',
                                          submitted_at=timezone.now(), folio='TEST-SENT')
        response = self.client.get('/api/applications/')
        self.assertEqual([row['id'] for row in response.json()['applications']], [str(sent.id)])

    def test_license_requires_general_and_department_documents(self):
        from .catalog import CATALOG_BY_ID, IDP_TYPES
        rule = CATALOG_BY_ID['funcionamiento']
        self.assertEqual([len(group['requirements']) for group in rule['requirement_groups']], [3, 2, 2, 2])
        self.assertEqual(rule['requirement_groups'][0]['requirements'], ['ine', 'curp', 'cfe'])
        app = Application.objects.create(owner=self.user, procedure='funcionamiento')
        with patch('portal.views.inspect_document') as bot:
            bot.side_effect = lambda upload, filename, kind: accepted(kind)
            for index, kind in enumerate(rule['requirements']):
                response = self.client.post('/api/documents/', {'kind': kind, 'file': sample_upload(), 'application_id': str(app.id)})
                self.assertEqual(response.status_code, 201, response.content)
                self.assertEqual(response.json()['document']['analysis_status'], 'accepted' if kind in IDP_TYPES else 'received')
                self.assertFalse(response.json()['document']['analysis']['official_validation'])
                if index < 8:
                    self.assertEqual(self.client.post(f'/api/applications/{app.id}/submit/').status_code, 400)
            self.assertEqual([call.args[2] for call in bot.call_args_list], rule['requirements'])
        self.assertEqual(Document.objects.filter(in_vault=True).count(), 0)
        response = self.client.post(f'/api/applications/{app.id}/submit/')
        self.assertEqual(response.status_code, 201, response.content)
        self.assertEqual(Document.objects.filter(in_vault=True).count(), 9)

    def test_update_preserves_submitted_version(self):
        doc = self.create_document()
        app = Application.objects.create(owner=self.user, procedure='predial', status='submitted')
        Attachment.objects.create(application=app, document=doc)
        original_path = doc.file.path
        with patch('portal.views.inspect_document', return_value=accepted()):
            response = self.client.post(f'/api/documents/{doc.id}/', {'file': sample_upload()})
        self.assertEqual(response.status_code, 200)
        doc.refresh_from_db()
        self.assertFalse(doc.in_vault)
        self.assertTrue(os.path.exists(original_path))
        self.assertEqual(app.attachments.get().document_id, doc.id)
        self.assertNotEqual(response.json()['document']['id'], str(doc.id))
        self.assertEqual(Document.objects.filter(in_vault=True).count(), 1)

    def test_rejected_update_preserves_original(self):
        doc = self.create_document()
        rejected = accepted(); rejected['status'] = 'needs_review'
        with patch('portal.views.inspect_document', return_value=rejected):
            response = self.client.post(f'/api/documents/{doc.id}/', {'file': sample_upload()})
        self.assertEqual(response.status_code, 422)
        doc.refresh_from_db()
        self.assertTrue(doc.in_vault)
        self.assertEqual(Document.objects.count(), 1)

    def test_delete_unlinked_removes_file(self):
        doc = self.create_document()
        path = doc.file.path
        with self.captureOnCommitCallbacks(execute=True):
            response = self.client.delete(f'/api/documents/{doc.id}/')
        self.assertEqual(response.status_code, 200)
        self.assertFalse(Document.objects.filter(id=doc.id).exists())
        self.assertFalse(os.path.exists(path))

    def test_delete_linked_preserves_attachment(self):
        doc = self.create_document()
        app = Application.objects.create(owner=self.user, procedure='predial')
        Attachment.objects.create(application=app, document=doc)
        response = self.client.delete(f'/api/documents/{doc.id}/')
        self.assertEqual(response.status_code, 200)
        doc.refresh_from_db()
        self.assertFalse(doc.in_vault)
        self.assertTrue(app.attachments.filter(document=doc).exists())

    def test_document_mutations_require_owner(self):
        doc = self.create_document()
        other = User.objects.create_user(username='other', email='other@example.invalid', curp='OTHER', email_verified=True)
        self.client.force_login(other)
        self.assertEqual(self.client.delete(f'/api/documents/{doc.id}/').status_code, 404)
        with patch('portal.views.inspect_document') as inspect:
            self.assertEqual(self.client.post(f'/api/documents/{doc.id}/', {'file': sample_upload()}).status_code, 404)
            inspect.assert_not_called()

    def test_draft_upload_promoted_only_when_submitted(self):
        app = Application.objects.create(owner=self.user, procedure='predial', reference='TEST-123')
        docs = [self.create_document(kind, app) for kind in ['ine', 'cfe']]
        self.assertEqual(self.client.get('/api/documents/').json()['documents'], [])
        response = self.client.post(f'/api/applications/{app.id}/submit/')
        self.assertEqual(response.status_code, 201, response.content)
        for doc in docs:
            doc.refresh_from_db(); self.assertTrue(doc.in_vault); self.assertIsNone(doc.temporary_for)
        again = self.client.post(f'/api/applications/{app.id}/submit/')
        self.assertEqual(again.json()['application']['folio'], response.json()['application']['folio'])

    def test_rejected_not_stored(self):
        result = accepted(); result.update(status='rejected', document_type='cfe', message='Tipo incorrecto')
        with patch('portal.views.inspect_document', return_value=result):
            response = self.client.post('/api/documents/', {'file': sample_upload(), 'kind': 'ine'})
        self.assertEqual(response.status_code, 422)
        self.assertEqual(Document.objects.count(), 0)

    def test_outage_does_not_store_document(self):
        with patch('portal.views.inspect_document', side_effect=IDPError('Servicio no disponible')):
            response = self.client.post('/api/documents/', {'file': sample_upload(), 'kind': 'ine'})
        self.assertEqual(response.status_code, 503)
        self.assertEqual(Document.objects.count(), 0)

    def test_unanalyzed_document_cannot_be_submitted(self):
        app = Application.objects.create(owner=self.user, procedure='predial', reference='TEST')
        for kind in ['ine', 'cfe']:
            doc = self.create_document(kind, app)
            doc.analysis_status = 'not_analyzed'; doc.save()
        response = self.client.post(f'/api/applications/{app.id}/submit/')
        self.assertEqual(response.status_code, 400)
        self.assertEqual(Document.objects.filter(in_vault=True).count(), 0)

    def test_reanalysis_updates_existing_document(self):
        doc = self.create_document()
        with patch('portal.views.inspect_document', return_value={**accepted(), 'status': 'needs_review'}):
            response = self.client.post(f'/api/documents/{doc.id}/analyze/')
        self.assertEqual(response.status_code, 200)
        doc.refresh_from_db(); self.assertEqual(doc.analysis_status, 'needs_review')

    def test_other_user_cannot_analyze_or_download(self):
        doc = self.create_document()
        other = User.objects.create_user(username='other', email='other@example.invalid', curp='XXXX900101HGRRRC09', email_verified=True)
        self.client.force_login(other)
        self.assertEqual(self.client.post(f'/api/documents/{doc.id}/analyze/').status_code, 404)
        self.assertEqual(self.client.get(f'/api/documents/{doc.id}/download/').status_code, 404)

    def test_cancel_removes_temporary_not_vault(self):
        vault = self.create_document()
        app = Application.objects.create(owner=self.user, procedure='predial')
        Attachment.objects.create(application=app, document=vault)
        temporary = self.create_document('cfe', app)
        storage, name = temporary.file.storage, temporary.file.name
        with self.captureOnCommitCallbacks(execute=True):
            response = self.client.delete(f'/api/applications/{app.id}/')
        self.assertEqual(response.status_code, 200)
        self.assertFalse(storage.exists(name))
        self.assertTrue(Document.objects.filter(pk=vault.pk).exists())

    def test_client_checks_contract(self):
        result = accepted(); result['extracted_data'] = {}
        with patch('portal.idp.urlopen') as call:
            call.return_value.__enter__.return_value.read.return_value = json.dumps(result).encode()
            with self.assertRaises(IDPError): inspect_document(sample_upload(), 'test.png', 'ine')

    def test_client_handles_unavailable(self):
        with patch('portal.idp.urlopen', side_effect=URLError('offline')):
            with self.assertRaises(IDPError): inspect_document(sample_upload(), 'test.png', 'ine')

    @unittest.skipUnless(os.getenv('RUN_LIVE_IDP') == '1', 'Requiere IDP local en puerto 8001')
    def test_live_http_upload_to_vault(self):
        # PDF sintético generado por los tests del bot; no contiene datos reales.
        import sys
        from pathlib import Path
        tests_dir = Path(__file__).resolve().parents[2] / 'idp-bot' / 'tests'
        # Generación PDF mínima, sin importar dependencias del bot en Django.
        from pypdf import PdfWriter
        from pypdf.generic import DictionaryObject, NameObject, DecodedStreamObject
        writer = PdfWriter(); page = writer.add_blank_page(600, 800)
        font = DictionaryObject({NameObject('/Type'): NameObject('/Font'), NameObject('/Subtype'): NameObject('/Type1'), NameObject('/BaseFont'): NameObject('/Helvetica')})
        page[NameObject('/Resources')] = DictionaryObject({NameObject('/Font'): DictionaryObject({NameObject('/F1'): writer._add_object(font)})})
        stream = DecodedStreamObject(); stream.set_data(b'BT /F1 16 Tf 25 TL 30 750 Td (CFE) Tj T* (COMISION FEDERAL DE ELECTRICIDAD) Tj T* (TOTAL A PAGAR 123) Tj T* (DIRECCION DEL SERVICIO) Tj T* (CALLE FICTICIA 123) Tj T* (NUMERO DE SERVICIO 123456) Tj ET')
        page[NameObject('/Contents')] = writer._add_object(stream)
        output = io.BytesIO(); writer.write(output)
        response = self.client.post('/api/documents/', {'kind': 'cfe', 'file': SimpleUploadedFile('synthetic.pdf', output.getvalue(), content_type='application/pdf')})
        self.assertEqual(response.status_code, 201, response.content)
        self.assertEqual(response.json()['document']['analysis']['document_type'], 'cfe')
