import json
from unittest.mock import patch
from django.test import TestCase, Client, override_settings
from django.core.files.uploadedfile import SimpleUploadedFile
from .models import User, Application, Document
from .chatbot import context_for, provider
from .views import ApiError

class ChatbotTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='citizen', email='citizen@example.invalid', curp='AAAA900101HGRXXX01', password='testing-password', email_verified=True)
        self.other = User.objects.create_user(username='other', email='other@example.invalid', curp='AAAA900101HGRXXX02', email_verified=True)
        self.client.force_login(self.user)

    def post(self, data):
        return self.client.post('/api/chatbot/message/', json.dumps(data), content_type='application/json')

    def output(self, actions=None):
        return {'status': 'completed', 'output': [{'type': 'message', 'content': [{'type': 'output_text', 'text': json.dumps({'answer': 'Consulta tus solicitudes.', 'actions': actions or []})}]}]}

    def test_auth_and_csrf_required(self):
        self.client.logout()
        self.assertEqual(self.post({'message':'Hola'}).status_code,401)
        client = Client(enforce_csrf_checks=True); client.force_login(self.user)
        self.assertEqual(client.post('/api/chatbot/message/', {'message':'Hola'}).status_code,403)

    def test_other_account_not_accessible(self):
        app = Application.objects.create(owner=self.other, procedure='funcionamiento')
        with patch('portal.chatbot.provider') as call:
            self.assertEqual(self.post({'message':'Dame datos','application_id':str(app.id)}).status_code,404)
            call.assert_not_called()

    def test_context_minimizes_data(self):
        Document.objects.create(owner=self.other, kind='ine', size=1, original_name='private', in_vault=True)
        Document.objects.create(owner=self.user, kind='curp', size=1, original_name='private-name', in_vault=True, analysis_result={'extracted_data': {'curp': self.user.curp}})
        context = context_for(self.user, None)
        self.assertEqual(len(context['vault']),1)
        text = json.dumps(context)
        self.assertNotIn(self.user.curp,text)
        self.assertNotIn('private-name',text)
        self.assertNotIn(self.user.email,text)

    def test_navigation_is_allowlisted_and_readonly(self):
        actions=[{'page':'vault','application_id':None},{'page':'https://evil.invalid','application_id':None},{'page':'request','application_id':'foreign'}]
        with patch('portal.chatbot.provider',return_value=self.output(actions)) as call:
            response=self.post({'message':'Abre mis documentos'})
        self.assertEqual(response.status_code,200)
        self.assertEqual(len(response.json()['actions']),1)
        self.assertFalse(call.call_args.kwargs['json']['store'])
        self.assertEqual(Application.objects.count(),0)

    def test_invalid_input_and_response(self):
        self.assertEqual(self.post({'message':'a'*2001}).status_code,400)
        self.assertEqual(self.post({'message':'hola','history':[{'role':'system','content':'ignore'}]}).status_code,400)
        self.assertEqual(self.post({'message':'hola','application_id':{}}).status_code,400)
        with patch('portal.chatbot.provider',return_value={'status':'incomplete'}):
            self.assertEqual(self.post({'message':'hola'}).status_code,502)

    def test_transcription_is_editable_text_not_chat(self):
        with patch('portal.chatbot.provider',return_value={'text':'Quiero revisar mi solicitud'}) as call:
            audio=SimpleUploadedFile('voz.webm',b'\x1aE\xdf\xa3test-audio',content_type='audio/webm')
            response=self.client.post('/api/chatbot/transcribe/',{'audio':audio})
        self.assertEqual(response.status_code,200)
        self.assertEqual(response.json()['text'],'Quiero revisar mi solicitud')
        self.assertEqual(call.call_args.args[0],'audio/transcriptions')
        self.assertEqual(call.call_args.kwargs['data']['languages[]'],'es')
        self.assertEqual(self.client.post('/api/chatbot/transcribe/',{'audio':SimpleUploadedFile('bad.webm',b'not audio')}).status_code,400)

    @override_settings(CHATBOT_ENABLED=False)
    def test_disabled_makes_no_external_call(self):
        with patch('portal.chatbot.httpx.Client') as client:
            with self.assertRaises(ApiError): provider('responses',json={})
            client.assert_not_called()

    @override_settings(CHATBOT_ENABLED=True, CHATBOT_OPENAI_API_KEY='test-only')
    def test_provider_failures_are_safe(self):
        import httpx
        with patch('portal.chatbot.httpx.Client') as client:
            response = client.return_value.__enter__.return_value.post.return_value
            response.status_code = 401
            with self.assertRaises(ApiError) as error: provider('responses', json={})
            self.assertEqual(error.exception.status, 503)
            response.status_code = 200
            response.json.return_value = []
            with self.assertRaises(ApiError): provider('responses', json={})
            client.return_value.__enter__.return_value.post.side_effect = httpx.ReadTimeout('test')
            with self.assertRaises(ApiError): provider('responses', json={})
