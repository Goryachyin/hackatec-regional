import base64
import io
import json
import uuid
from PIL import Image
from django.contrib.auth import get_user_model
from django.test import Client, TestCase
from .models import AREAS, KINDS, Decision, Dossier, File, Reviewer
from django.conf import settings


class ExchangeTests(TestCase):
    def setUp(self):
        self.pk = uuid.uuid4()
        self.path = f'/api/expedientes/{self.pk}/'
        self.headers = {'HTTP_X_INTEGRATION_KEY': settings.INTEGRATION_KEY, 'HTTP_X_SOURCE': settings.INTEGRATION_SOURCE}
        self.manifest = [{'id': str(uuid.uuid4()), 'kind': kind} for kind in sorted(KINDS)]
        self.data = {'folio': 'DEMO-' + self.pk.hex.upper(), 'is_demo': True, 'procedure': 'funcionamiento', 'documents': self.manifest}
        out = io.BytesIO()
        Image.new('RGB', (10, 10), 'white').save(out, 'PNG')
        self.file = {'name': 'ficticio.png', 'content': base64.b64encode(out.getvalue()).decode()}

    def post(self, path, data):
        return self.client.post(path, json.dumps(data), content_type='application/json', **self.headers)

    def fill(self):
        self.assertEqual(self.post(self.path, self.data).status_code, 201)
        for doc in self.manifest:
            self.assertEqual(self.post(self.path + f"documentos/{doc['id']}/", self.file).status_code, 201)
        self.assertEqual(self.post(self.path + 'confirmar/', {}).status_code, 200)

    def test_authentication_and_non_demo_rejected(self):
        self.assertEqual(self.client.get(self.path).status_code, 401)
        self.assertEqual(self.post(self.path, {**self.data, 'is_demo': False}).status_code, 400)
        self.headers['HTTP_X_SOURCE'] = 'another-source'
        self.assertEqual(self.post(self.path, self.data).status_code, 401)

    def test_retry_incomplete_confirmation_and_payload_validation(self):
        self.assertEqual(self.post(self.path, self.data).status_code, 201)
        self.assertEqual(self.post(self.path, self.data).status_code, 200)
        self.assertEqual(Dossier.objects.count(), 1)
        self.assertEqual(self.post(self.path + 'confirmar/', {}).status_code, 409)
        doc_path = self.path + f"documentos/{self.manifest[0]['id']}/"
        self.assertEqual(self.post(doc_path, {'name': 'bad.pdf', 'content': base64.b64encode(b'bad').decode()}).status_code, 400)
        self.assertEqual(self.post(doc_path, self.file).status_code, 201)
        self.assertEqual(self.post(doc_path, self.file).status_code, 200)
        self.assertEqual(File.objects.count(), 1)
        self.assertEqual(self.post(doc_path, {**self.file, 'name': 'otro.png'}).status_code, 409)

    def test_area_permissions_decisions_and_citizen_status(self):
        self.fill()
        for index, area in enumerate(AREAS):
            user = get_user_model().objects.create_user(username=area, password='long-test-pass-123')
            Reviewer.objects.create(user=user, area=area)
            self.client.force_login(user)
            self.assertEqual(self.client.get('/').status_code, 200)
            self.assertEqual(self.client.get(f'/expedientes/{self.pk}/').status_code, 200)
            if index == 0:
                foreign = File.objects.get(kind='eco_solicitud')
                self.assertEqual(self.client.get(f'/documentos/{foreign.id}/').status_code, 403)
                self.assertEqual(self.client.post(f'/expedientes/{self.pk}/resolver/ecologia/', {'outcome': 'approved'}).status_code, 403)
                self.assertEqual(self.client.post(f'/expedientes/{self.pk}/resolver/{area}/', {'outcome': 'rejected'}).status_code, 400)
            path = f'/expedientes/{self.pk}/resolver/{area}/'
            self.assertEqual(self.client.post(path, {'outcome': 'approved', 'notes': 'Prueba completada'}).status_code, 302)
            self.assertEqual(self.client.post(path, {'outcome': 'rejected', 'notes': 'Cambiar'}).status_code, 409)
        result = self.client.get(self.path, **self.headers).json()
        self.assertEqual(result['status'], 'approved')
        self.assertEqual(Decision.objects.count(), 3)
        csrf_client = Client(enforce_csrf_checks=True)
        csrf_client.force_login(user)
        self.assertEqual(csrf_client.post(path, {'outcome': 'approved'}).status_code, 403)
        self.client.logout()
        self.assertEqual(self.client.get(f'/documentos/{foreign.id}/').status_code, 302)

    def test_rejection_and_login(self):
        self.fill()
        user = get_user_model().objects.create_user(username='reviewer', password='long-test-pass-123')
        Reviewer.objects.create(user=user, area='ecologia')
        self.assertEqual(self.client.post('/login/', {'username': user.username, 'password': 'long-test-pass-123'}).status_code, 302)
        self.client.post(f'/expedientes/{self.pk}/resolver/ecologia/', {'outcome': 'rejected', 'notes': 'Falta información de residuos.'})
        result = self.client.get(self.path, **self.headers).json()
        self.assertEqual(result['status'], 'rejected')
        self.assertEqual(result['areas'][2]['notes'], 'Falta información de residuos.')
