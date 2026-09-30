import hashlib
import json
import logging
import re
import secrets
from datetime import timedelta
from functools import wraps
from pathlib import Path

from PIL import Image
from pypdf import PdfReader
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.hashers import check_password, make_password
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError
from django.core.mail import send_mail
from django.core.validators import validate_email
from django.db import IntegrityError, transaction
from django.db.models import F
from django.http import FileResponse, JsonResponse
from django.middleware.csrf import get_token
from django.utils import timezone

from .catalog import CATALOG, CATALOG_BY_ID, DOCUMENT_TYPES
from .models import Application, Attachment, AuthAttempt, Document, User, Verification
from .idp import IDPError, inspect_document


class ApiError(Exception):
    def __init__(self, message, status=400):
        self.message, self.status = message, status


def endpoint(methods, private=True):
    def decorate(fn):
        @wraps(fn)
        def wrapped(request, *args, **kwargs):
            if request.method not in methods:
                return JsonResponse({'message': 'Método no permitido.'}, status=405)
            if private and (not request.user.is_authenticated or not request.user.email_verified):
                return JsonResponse({'message': 'Inicia sesión para continuar.'}, status=401)
            try:
                return fn(request, *args, **kwargs)
            except ApiError as error:
                return JsonResponse({'message': error.message}, status=error.status)
            except IDPError as error:
                return JsonResponse({'message': str(error)}, status=error.status)
            except (json.JSONDecodeError, UnicodeDecodeError):
                return JsonResponse({'message': 'La petición no es válida.'}, status=400)
        return wrapped
    return decorate


def body(request):
    value = json.loads(request.body or '{}')
    if not isinstance(value, dict):
        raise ApiError('La petición debe ser un objeto.')
    return value


def field(data, name):
    value = data.get(name, '')
    if not isinstance(value, str):
        raise ApiError('Revisa los campos de la solicitud.')
    return value.strip()


def throttle(request, action, limit=20):
    key = hashlib.sha256(f'{action}:{request.META.get("REMOTE_ADDR", "unknown")}'.encode()).hexdigest()
    now = timezone.now()
    with transaction.atomic():
        row, _ = AuthAttempt.objects.select_for_update().get_or_create(key=key, defaults={'window_start': now})
        if row.window_start < now - timedelta(minutes=15):
            row.window_start, row.count = now, 0
        if row.count >= limit:
            raise ApiError('Demasiados intentos. Inténtalo en 15 minutos.', 429)
        row.count += 1
        row.save()


def issue_code(user):
    now = timezone.now()
    previous = Verification.objects.filter(user=user).first()
    if previous and previous.sent_at > now - timedelta(seconds=60):
        raise ApiError('Espera un minuto antes de solicitar otro código.', 429)
    code = f'{secrets.randbelow(1000000):06d}'
    with transaction.atomic():
        Verification.objects.update_or_create(user=user, defaults={'code_hash': make_password(code), 'expires_at': now + timedelta(minutes=10), 'sent_at': now, 'attempts': 0})
        try:
            send_mail('Verifica tu correo · Portal ciudadano', f'Tu código de verificación es: {code}\nVence en 10 minutos. Si no solicitaste esta cuenta, ignora este correo.', None, [user.email], fail_silently=False)
        except Exception:
            logging.getLogger(__name__).warning('Falló el envío del correo de verificación.')
            raise ApiError('No pudimos enviar el código. Intenta reenviarlo más tarde.', 503)


def user_data(user):
    return {'email': user.email, 'curp': user.curp}


def document_data(doc):
    return {'id': str(doc.id), 'kind': doc.kind, 'name': doc.original_name, 'size': doc.size, 'in_vault': doc.in_vault, 'created_at': doc.created_at.isoformat(), 'url': f'/api/documents/{doc.id}/download/', 'analysis_status': doc.analysis_status, 'analysis': doc.analysis_result, 'analyzed_at': doc.analyzed_at.isoformat() if doc.analyzed_at else None}


def application_data(app):
    return {'id': str(app.id), 'procedure': app.procedure, 'name': CATALOG_BY_ID[app.procedure]['name'], 'status': app.status, 'reference': app.reference, 'folio': app.folio, 'created_at': app.created_at.isoformat(), 'submitted_at': app.submitted_at.isoformat() if app.submitted_at else None, 'documents': [document_data(a.document) for a in app.attachments.select_related('document').all()]}


@endpoint(['GET'], private=False)
def session(request):
    return JsonResponse({'csrf': get_token(request), 'user': user_data(request.user) if request.user.is_authenticated and request.user.email_verified else None})


@endpoint(['POST'], private=False)
def register(request):
    throttle(request, 'register', 10)
    data = body(request)
    curp, email, password = field(data, 'curp').upper(), field(data, 'email').lower(), field(data, 'password')
    if not re.fullmatch(r'[A-Z][AEIOUX][A-Z]{2}\d{6}[HMX][A-Z]{5}[A-Z0-9]\d', curp):
        raise ApiError('Revisa el formato de la CURP: debe contener 18 caracteres.')
    try:
        validate_email(email)
        validate_password(password, User(username=email, email=email, curp=curp))
    except ValidationError as error:
        raise ApiError(' '.join(error.messages))
    if len(email) > 150:
        raise ApiError('El correo es demasiado largo.')
    try:
        with transaction.atomic():
            user = User.objects.create_user(username=email, email=email, curp=curp, password=password, is_active=False)
    except IntegrityError:
        raise ApiError('No se pudo crear la cuenta con esos datos. Si ya te registraste, verifica tu correo o inicia sesión.', 409)
    issue_code(user)
    return JsonResponse({'message': 'Revisa tu correo para completar el registro.'}, status=201)


@endpoint(['POST'], private=False)
def resend(request):
    throttle(request, 'resend', 10)
    user = User.objects.filter(email=field(body(request), 'email').lower(), email_verified=False).first()
    if user:
        issue_code(user)
    return JsonResponse({'message': 'Si existe una cuenta pendiente, se enviará un código.'})


@endpoint(['POST'], private=False)
def verify(request):
    throttle(request, 'verify', 30)
    data = body(request)
    error = None
    with transaction.atomic():
        row = Verification.objects.select_for_update().select_related('user').filter(user__email=field(data, 'email').lower()).first()
        if not row or row.expires_at <= timezone.now() or row.attempts >= 5:
            error = 'Código vencido o no disponible. Solicita uno nuevo.'
        elif not check_password(field(data, 'code'), row.code_hash):
            Verification.objects.filter(pk=row.pk).update(attempts=F('attempts') + 1)
            error = 'Código incorrecto. Revisa el correo e inténtalo de nuevo.'
        else:
            user = row.user
            user.email_verified, user.is_active = True, True
            user.save(update_fields=['email_verified', 'is_active'])
            row.delete()
    if error:
        raise ApiError(error)
    login(request, user, backend='django.contrib.auth.backends.ModelBackend')
    return JsonResponse({'user': user_data(user), 'csrf': get_token(request)})


@endpoint(['POST'], private=False)
def sign_in(request):
    throttle(request, 'login', 20)
    data = body(request)
    user = authenticate(request, username=field(data, 'email').lower(), password=field(data, 'password'))
    if not user or not user.email_verified:
        raise ApiError('No pudimos iniciar sesión. Revisa tus datos y verifica tu correo.', 401)
    login(request, user)
    return JsonResponse({'user': user_data(user), 'csrf': get_token(request)})


@endpoint(['POST'])
def sign_out(request):
    logout(request)
    return JsonResponse({'message': 'Sesión cerrada.', 'csrf': get_token(request)})


@endpoint(['GET'])
def catalog(request):
    return JsonResponse({'procedures': CATALOG, 'document_types': DOCUMENT_TYPES, 'requirements_mode': 'demo'})


def inspect_file(upload):
    if not upload or upload.size == 0 or upload.size > 10 * 1024 * 1024:
        raise ApiError('Selecciona un archivo de hasta 10 MB, que no esté vacío.')
    suffix = Path(upload.name).suffix.lower()
    try:
        if suffix == '.pdf':
            if not upload.read(5).startswith(b'%PDF-'):
                raise ValueError()
            upload.seek(0)
            reader = PdfReader(upload)
            if reader.is_encrypted or not 1 <= len(reader.pages) <= 10:
                raise ValueError()
            mime = 'application/pdf'
        elif suffix in ['.png', '.jpg', '.jpeg']:
            with Image.open(upload) as picture:
                if picture.format not in ['PNG', 'JPEG'] or picture.width * picture.height > 25000000:
                    raise ValueError()
                picture.verify()
                mime = Image.MIME[picture.format]
        else:
            raise ValueError()
    except Exception:
        raise ApiError('El archivo no es un PDF, JPG o PNG legible. Los PDF deben tener hasta 10 páginas y no llevar contraseña.')
    upload.seek(0)
    return mime


@endpoint(['GET', 'POST'])
def documents(request):
    if request.method == 'GET':
        return JsonResponse({'documents': [document_data(d) for d in Document.objects.filter(owner=request.user, in_vault=True).order_by('-created_at')]})
    kind = request.POST.get('kind')
    if kind not in DOCUMENT_TYPES:
        raise ApiError('Selecciona un tipo de documento.')
    upload = request.FILES.get('file')
    mime = inspect_file(upload)
    app_id = request.POST.get('application_id')
    if app_id:
        try:
            candidate = Application.objects.get(id=app_id, owner=request.user, status='draft')
        except (Application.DoesNotExist, ValidationError):
            raise ApiError('No se encontró un borrador editable.', 404)
        if kind not in CATALOG_BY_ID[candidate.procedure]['requirements']:
            raise ApiError('Este documento no corresponde al trámite.')
    # El OCR ocurre antes de abrir la transacción: no mantener bloqueos durante inferencia.
    analysis = inspect_document(upload, upload.name, kind)
    if analysis['status'] != 'accepted':
        # Diagnóstico sin nombres, identificadores ni texto del documento.
        logging.getLogger('django.request').warning(
            'IDP: status=%s code=%s expected=%s detected=%s',
            analysis['status'], analysis.get('code'), kind, analysis.get('document_type'))
        return JsonResponse({'message': analysis['message'], 'analysis': analysis}, status=422)
    doc = None
    try:
        with transaction.atomic():
            app = None
            if app_id:
                try:
                    app = Application.objects.select_for_update().get(id=app_id, owner=request.user, status='draft')
                except (Application.DoesNotExist, ValidationError):
                    raise ApiError('No se encontró un borrador editable.', 404)
                if kind not in CATALOG_BY_ID[app.procedure]['requirements']:
                    raise ApiError('Este documento no corresponde a los requisitos del borrador.')
            if Document.objects.filter(owner=request.user).count() >= 100:
                raise ApiError('Alcanzaste el límite de 100 documentos del prototipo.', 409)
            doc = Document(owner=request.user, kind=kind, original_name=Path(upload.name).name[:255], size=upload.size, content_type=mime, in_vault=not bool(app), temporary_for=app, analysis_status='accepted', analysis_result=analysis, analyzed_at=timezone.now())
            doc.file.save(upload.name, upload, save=False)
            doc.save()
            if app:
                app.attachments.filter(document__kind=kind).delete()
                Attachment.objects.create(application=app, document=doc)
    except Exception:
        if doc and doc.file:
            doc.file.delete(save=False)
        raise
    return JsonResponse({'document': document_data(doc), 'message': analysis['message']}, status=201)


@endpoint(['POST', 'DELETE'])
def manage_document(request, doc_id):
    original = Document.objects.filter(id=doc_id, owner=request.user, in_vault=True).first()
    if not original:
        raise ApiError('Documento no encontrado en el Baúl.', 404)
    analysis = None
    if request.method == 'POST':
        upload = request.FILES.get('file')
        mime = inspect_file(upload)
        if original.kind not in DOCUMENT_TYPES:
            raise ApiError('Este tipo documental ya no admite actualizaciones.', 409)
        analysis = inspect_document(upload, upload.name, original.kind)
        if analysis['status'] != 'accepted':
            return JsonResponse({'message': analysis['message'], 'analysis': analysis}, status=422)
    replacement = None
    try:
        with transaction.atomic():
            original = Document.objects.select_for_update().filter(id=doc_id, owner=request.user, in_vault=True).first()
            if not original:
                raise ApiError('El documento ya fue actualizado o eliminado.', 409)
            linked = Attachment.objects.filter(document=original).exists()
            if analysis is not None:
                replacement = Document(owner=request.user, kind=original.kind,
                    original_name=Path(upload.name).name[:255], size=upload.size,
                    content_type=mime, in_vault=True, analysis_status='accepted',
                    analysis_result=analysis, analyzed_at=timezone.now())
                replacement.file.save(upload.name, upload, save=False)
                replacement.save()
            if linked:
                original.in_vault = False
                original.save(update_fields=['in_vault'])
            else:
                storage, name = original.file.storage, original.file.name
                original.delete()
                transaction.on_commit(lambda: storage.delete(name))
    except Exception:
        if replacement and replacement.file:
            replacement.file.delete(save=False)
        raise
    message = 'Documento actualizado en el Baúl.' if replacement else 'Documento eliminado del Baúl.'
    if linked:
        message += ' Los trámites vinculados conservan su versión anterior.'
    return JsonResponse({'message': message, 'document': document_data(replacement) if replacement else None})


@endpoint(['POST'])
def reanalyze(request, doc_id):
    doc = Document.objects.filter(id=doc_id, owner=request.user).first()
    if not doc:
        raise ApiError('Documento no encontrado.', 404)
    with doc.file.open('rb') as source:
        result = inspect_document(source, doc.original_name, doc.kind)
    doc.analysis_status = result['status']
    doc.analysis_result = result
    doc.analyzed_at = timezone.now()
    doc.save(update_fields=['analysis_status', 'analysis_result', 'analyzed_at'])
    return JsonResponse({'document': document_data(doc), 'message': result['message']})


@endpoint(['GET'])
def download(request, doc_id):
    doc = Document.objects.filter(id=doc_id, owner=request.user).first()
    if not doc:
        raise ApiError('Documento no encontrado.', 404)
    response = FileResponse(doc.file.open('rb'), as_attachment=True, filename=doc.original_name, content_type=doc.content_type)
    response['Cache-Control'] = 'no-store'
    return response


@endpoint(['GET', 'POST'])
def applications(request):
    if request.method == 'GET':
        return JsonResponse({'applications': [application_data(a) for a in Application.objects.filter(owner=request.user).order_by('-created_at')]})
    procedure = field(body(request), 'procedure')
    if procedure not in CATALOG_BY_ID:
        raise ApiError('Trámite no disponible.')
    with transaction.atomic():
        app = Application.objects.create(owner=request.user, procedure=procedure)
        for kind in CATALOG_BY_ID[procedure]['requirements']:
            doc = Document.objects.filter(owner=request.user, in_vault=True, kind=kind, analysis_status='accepted').order_by('-created_at').first()
            if doc:
                Attachment.objects.create(application=app, document=doc)
    return JsonResponse({'application': application_data(app)}, status=201)


@endpoint(['GET', 'PATCH', 'DELETE'])
def application_detail(request, app_id):
    with transaction.atomic():
        app = Application.objects.select_for_update().filter(id=app_id, owner=request.user).first()
        if not app:
            raise ApiError('Solicitud no encontrada.', 404)
        if request.method == 'GET':
            return JsonResponse({'application': application_data(app)})
        if app.status != 'draft':
            raise ApiError('La solicitud ya fue enviada.', 409)
        if request.method == 'DELETE':
            files = [(d.file.storage, d.file.name) for d in app.temporary_documents.filter(in_vault=False)]
            app.attachments.all().delete()
            app.delete()
            transaction.on_commit(lambda: [storage.delete(name) for storage, name in files])
            return JsonResponse({'message': 'Borrador cancelado; archivos temporales eliminados.'})
        data = body(request)
        reference = field(data, 'reference')
        if len(reference) > 100:
            raise ApiError('La referencia admite hasta 100 caracteres.')
        app.reference = reference
        app.save(update_fields=['reference'])
        if 'document_id' in data:
            try:
                doc = Document.objects.filter(id=data['document_id'], owner=request.user, in_vault=True).first()
            except ValidationError:
                doc = None
            if not doc or doc.kind not in CATALOG_BY_ID[app.procedure]['requirements']:
                raise ApiError('Documento del Baúl no disponible para este trámite.')
            app.attachments.filter(document__kind=doc.kind).delete()
            Attachment.objects.create(application=app, document=doc)
        return JsonResponse({'application': application_data(app)})


@endpoint(['POST'])
def submit(request, app_id):
    with transaction.atomic():
        app = Application.objects.select_for_update().filter(id=app_id, owner=request.user).first()
        if not app:
            raise ApiError('Solicitud no encontrada.', 404)
        if app.status != 'draft':
            return JsonResponse({'application': application_data(app)})
        rules = CATALOG_BY_ID[app.procedure]
        kinds = set(app.attachments.values_list('document__kind', flat=True))
        if not set(rules['requirements']).issubset(kinds):
            raise ApiError('Completa todos los documentos antes de enviar la solicitud.')
        if app.attachments.exclude(document__analysis_status='accepted').exists():
            raise ApiError('Analiza o reemplaza los documentos pendientes antes de enviar la solicitud.')
        if rules['reference_required'] and not app.reference:
            raise ApiError('Ingresa la cuenta o clave predial.')
        doc_ids = list(app.attachments.values_list('document_id', flat=True))
        # Promoción al Baúl y folio se confirman dentro de la misma transacción.
        Document.objects.filter(id__in=doc_ids, owner=request.user, temporary_for=app).update(in_vault=True, temporary_for=None)
        obsolete = list(app.temporary_documents.filter(in_vault=False))
        files = [(d.file.storage, d.file.name) for d in obsolete]
        app.temporary_documents.filter(in_vault=False).delete()
        transaction.on_commit(lambda: [storage.delete(name) for storage, name in files])
        app.status = 'submitted'
        app.folio = f'ACA-{timezone.now():%Y}-{app.id.hex.upper()}'
        app.submitted_at = timezone.now()
        app.save(update_fields=['status', 'folio', 'submitted_at'])
    return JsonResponse({'application': application_data(app)}, status=201)
