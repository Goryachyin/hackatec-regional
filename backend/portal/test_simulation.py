import json
from unittest.mock import patch
from django.test import TestCase, override_settings
from django.core.files.uploadedfile import SimpleUploadedFile
from . import test_idp
from .test_idp import sample_upload, accepted
from .models import Application, Attachment, Document
from .catalog import CATALOG_BY_ID


@override_settings(DOCUMENT_SIMULATION_ENABLED=True)
class SimulationTests(TestCase):
    setUp = test_idp.IDPIntegrationTests.setUp
    def authorize(self):
        self.user.can_simulate_documents = True
        self.user.save(update_fields=['can_simulate_documents'])

    def upload_simulated(self):
        self.authorize()
        with patch('portal.views.inspect_document') as bot:
            response = self.client.post('/api/documents/', {'kind': 'ine', 'file': sample_upload()})
            self.assertEqual(response.status_code, 201)
            bot.assert_not_called()
        doc = response.json()['document']
        self.assertTrue(doc['is_simulated'])
        self.assertEqual(doc['analysis']['performed_by'], str(self.user.pk))
        self.assertNotIn('extracted_data', doc['analysis'])
        return doc

    def test_simulated_upload_update_reanalysis(self):
        doc = self.upload_simulated()
        with patch('portal.views.inspect_document') as bot:
            response = self.client.post('/api/documents/%s/' % doc['id'], {'file': sample_upload()})
            self.assertEqual(response.status_code, 200)
            new_doc = response.json()['document']
            response = self.client.post('/api/documents/%s/analyze/' % new_doc['id'])
            self.assertTrue(response.json()['document']['is_simulated'])
            bot.assert_not_called()

    def test_unprivileged_cannot_request_bypass(self):
        with patch('portal.views.inspect_document', return_value=accepted()) as bot:
            response = self.client.post('/api/documents/', {'kind': 'ine', 'file': sample_upload(), 'is_simulated': 'true'})
            self.assertEqual(response.status_code, 201)
            self.assertFalse(response.json()['document']['is_simulated'])
            bot.assert_called_once()

    @override_settings(DOCUMENT_SIMULATION_ENABLED=False)
    def test_switch_required_even_for_authorized_account(self):
        self.authorize()
        with patch('portal.views.inspect_document', return_value=accepted()) as bot:
            response = self.client.post('/api/documents/', {'kind': 'ine', 'file': sample_upload()})
            self.assertFalse(response.json()['document']['is_simulated'])
            bot.assert_called_once()

    def test_simulation_still_checks_file(self):
        self.authorize()
        with patch('portal.views.inspect_document') as bot:
            response = self.client.post('/api/documents/', {'kind': 'ine', 'file': SimpleUploadedFile('bad.pdf', b'not pdf')})
            self.assertEqual(response.status_code, 400)
            bot.assert_not_called()

    def test_disabled_simulation_cannot_attach_or_submit(self):
        self.upload_simulated()
        app = Application.objects.create(owner=self.user, procedure='construccion')
        for kind in CATALOG_BY_ID['construccion']['requirements']:
            doc = Document.objects.create(owner=self.user, kind=kind, original_name='demo.png', size=1, in_vault=True, is_simulated=True, analysis_status='accepted')
            Attachment.objects.create(application=app, document=doc)
        with override_settings(DOCUMENT_SIMULATION_ENABLED=False):
            response = self.client.post('/api/applications/', json.dumps({'procedure': 'construccion'}), content_type='application/json')
            self.assertEqual(response.json()['application']['documents'], [])
            response = self.client.patch('/api/applications/%s/' % app.id, json.dumps({'reference': '', 'document_id': str(doc.id)}), content_type='application/json')
            self.assertEqual(response.status_code, 400)
            self.assertEqual(self.client.post('/api/applications/%s/submit/' % app.id).status_code, 400)
        self.user.can_simulate_documents = False
        self.user.save(update_fields=['can_simulate_documents'])
        self.assertEqual(self.client.post('/api/applications/%s/submit/' % app.id).status_code, 400)
        self.authorize()
        response = self.client.post('/api/applications/%s/submit/' % app.id)
        self.assertEqual(response.status_code, 201)
        self.assertTrue(response.json()['application']['is_demo'])
        self.assertTrue(response.json()['application']['folio'].startswith('DEMO-'))
        folio = response.json()['application']['folio']
        self.assertLessEqual(len(folio), Application._meta.get_field('folio').max_length)
        self.assertTrue(folio.endswith(app.id.hex.upper()))
        self.assertEqual(self.client.post('/api/documents/%s/analyze/' % doc.id).status_code, 409)
