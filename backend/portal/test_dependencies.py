import json
import uuid
from unittest.mock import patch
from django.test import TestCase, override_settings
from . import test_idp
from .catalog import CATALOG_BY_ID
from .models import Application, Attachment, Delivery, Document
from .dependencies import ExchangeError


@override_settings(DOCUMENT_SIMULATION_ENABLED=True, DEPENDENCIES_URL='https://receiver.example.invalid', DEPENDENCIES_KEY='test-integration-key-with-more-than-32', DEPENDENCIES_SOURCE='test-portal')
class DependenciesTests(TestCase):
    setUp = test_idp.IDPIntegrationTests.setUp

    def prepare(self):
        self.user.can_simulate_documents = True
        self.user.save()
        app = Application.objects.create(owner=self.user, procedure='funcionamiento', status='submitted', is_demo=True)
        app.folio = 'DEMO-' + app.id.hex.upper()
        app.save()
        for kind in CATALOG_BY_ID['funcionamiento']['requirements']:
            doc = Document(owner=self.user, kind=kind, original_name='ficticio.png', size=100, is_simulated=True, analysis_status='accepted')
            doc.file.save('ficticio.png', test_idp.sample_upload(), save=True)
            Attachment.objects.create(application=app, document=doc)
        self.app = app
        self.path = f'/api/applications/{app.id}/dependencies/'
        self.remote_id = uuid.uuid5(uuid.NAMESPACE_URL, 'test-portal:' + str(app.id))
        return app

    def result(self, state='in_review'):
        return {'id': str(self.remote_id), 'folio': self.app.folio, 'is_demo': True, 'status': state,
                'areas': [{'area': a, 'name': a, 'status': 'approved' if state == 'approved' else 'pending', 'notes': ''} for a in ['proteccion_civil', 'obras_publicas', 'ecologia']]}

    def post(self, **data):
        return self.client.post(self.path, json.dumps(data or {'confirm_demo_files': True}), content_type='application/json')

    def test_resumable_send_and_sync(self):
        self.prepare()
        def receiver(path, method='GET', data=None):
            return {'received': True} if 'documentos/' in path else self.result()
        with patch('portal.dependencies.remote', side_effect=receiver) as remote:
            for index in range(9):
                response = self.post()
                self.assertEqual(response.status_code, 200, response.content)
                self.assertEqual(response.json()['application']['delivery']['sent_files'], index + 1)
            response = self.post()
            self.assertEqual(response.json()['application']['delivery']['status'], 'received')
            self.assertEqual(response.json()['application']['status'], 'in_review')
        self.assertEqual(Delivery.objects.count(), 1)
        with patch('portal.dependencies.remote', return_value=self.result('approved')):
            response = self.post(action='sync')
        self.assertEqual(response.json()['application']['status'], 'approved')

    def test_timeout_keeps_files_and_retries_same_document(self):
        self.prepare()
        with patch('portal.dependencies.remote', side_effect=[self.result(), ExchangeError('Conexión interrumpida')]):
            self.assertEqual(self.post().status_code, 503)
        delivery = Delivery.objects.get(application=self.app)
        self.assertEqual(delivery.next_file, 0)
        self.assertIsNone(delivery.lease_until)
        self.assertEqual(Document.objects.count(), 9)
        with patch('portal.dependencies.remote', side_effect=[self.result(), {'received': True}]):
            self.assertEqual(self.post().status_code, 200)
        delivery.refresh_from_db()
        self.assertEqual(delivery.next_file, 1)

    def test_owner_simulation_and_confirmation_required(self):
        self.prepare()
        with patch('portal.dependencies.remote') as remote:
            self.assertEqual(self.post(confirm_demo_files=False).status_code, 400)
            with override_settings(DOCUMENT_SIMULATION_ENABLED=False):
                self.assertEqual(self.post().status_code, 403)
            Document.objects.update(is_simulated=False)
            self.assertEqual(self.post().status_code, 503)
            self.client.logout()
            self.assertEqual(self.post().status_code, 401)
            remote.assert_not_called()

    def test_wrong_response_cannot_approve_application(self):
        self.prepare()
        response = {**self.result('approved'), 'id': str(uuid.uuid4())}
        with patch('portal.dependencies.remote', return_value=response):
            self.assertEqual(self.post(action='sync').status_code, 503)
        self.app.refresh_from_db()
        self.assertEqual(self.app.status, 'submitted')
