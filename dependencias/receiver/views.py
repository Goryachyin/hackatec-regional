import base64
import binascii
import hashlib
import io
import json
import secrets
import uuid
from datetime import timedelta
from functools import wraps
from pathlib import Path
from PIL import Image
from pypdf import PdfReader
from django.conf import settings
from django.contrib.auth import authenticate, login
from django.contrib.auth.decorators import login_required
from django.db import connection, transaction
from django.http import HttpResponse, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
from django.views.decorators.cache import never_cache
from .models import AREAS, KINDS, REQUIREMENTS, Decision, Dossier, File, Reviewer, LoginAttempt


def health(request):
    try:
        with connection.cursor() as cursor:
            cursor.execute('SELECT 1')
    except Exception:
        return JsonResponse({'status': 'unavailable'}, status=503)
    return JsonResponse({'status': 'ok'})


def integration(methods):
    def decorate(fn):
        @csrf_exempt
        @never_cache
        @wraps(fn)
        def wrapped(request, *args, **kwargs):
            if request.method not in methods:
                return JsonResponse({'message': 'Método no permitido.'}, status=405)
            key = request.headers.get('X-Integration-Key', '')
            if not secrets.compare_digest(key.encode(), settings.INTEGRATION_KEY.encode()) or request.headers.get('X-Source') != settings.INTEGRATION_SOURCE:
                return JsonResponse({'message': 'Acceso no autorizado.'}, status=401)
            try:
                return fn(request, *args, **kwargs)
            except (ValueError, TypeError, KeyError, UnicodeDecodeError, binascii.Error):
                return JsonResponse({'message': 'Datos de integración no válidos.'}, status=400)
        return wrapped
    return decorate


def payload(request):
    data = json.loads(request.body)
    if not isinstance(data, dict):
        raise ValueError()
    return data


def snapshot(dossier):
    decisions = {d.area: d for d in dossier.decisions.all()}
    outcome = 'rejected' if any(d.outcome == 'rejected' for d in decisions.values()) else 'approved' if len(decisions) == 3 else 'in_review' if dossier.ready else 'receiving'
    return {'id': str(dossier.id), 'folio': dossier.folio, 'is_demo': True, 'status': outcome,
            'areas': [{'area': area, 'name': name, 'status': decisions[area].outcome if area in decisions else 'pending',
                       'notes': decisions[area].notes if area in decisions else '',
                       'decided_at': decisions[area].decided_at.isoformat() if area in decisions else None} for area, name in AREAS.items()]}


@integration(['POST', 'GET'])
def exchange(request, pk):
    if request.method == 'GET':
        return JsonResponse(snapshot(get_object_or_404(Dossier, pk=pk, source=settings.INTEGRATION_SOURCE)))
    data = payload(request)
    if data.get('is_demo') is not True or data.get('procedure') != 'funcionamiento':
        raise ValueError()
    folio = data.get('folio')
    manifest = data.get('documents')
    if not isinstance(folio, str) or not folio.startswith('DEMO-') or len(folio) > 40 or not isinstance(manifest, list) or len(manifest) != len(KINDS):
        raise ValueError()
    clean = []
    for doc in manifest:
        clean.append({'id': str(uuid.UUID(doc['id'])), 'kind': doc['kind']})
    if {doc['kind'] for doc in clean} != KINDS or len({doc['id'] for doc in clean}) != len(clean):
        raise ValueError()
    clean.sort(key=lambda d: d['kind'])
    dossier, created = Dossier.objects.get_or_create(pk=pk, defaults={'source': settings.INTEGRATION_SOURCE, 'folio': folio, 'manifest': clean})
    if dossier.source != settings.INTEGRATION_SOURCE or dossier.folio != folio or dossier.manifest != clean:
        return JsonResponse({'message': 'El identificador corresponde a otro expediente.'}, status=409)
    return JsonResponse(snapshot(dossier), status=201 if created else 200)


def check_file(raw, name):
    stream = io.BytesIO(raw)
    if not 0 < len(raw) <= 10 * 1024 * 1024:
        raise ValueError()
    try:
        if Path(name).suffix.lower() == '.pdf':
            if not raw.startswith(b'%PDF-'):
                raise ValueError()
            reader = PdfReader(stream)
            if reader.is_encrypted or not 1 <= len(reader.pages) <= 10:
                raise ValueError()
            return 'application/pdf'
        with Image.open(stream) as picture:
            if picture.format not in ('PNG', 'JPEG') or picture.width * picture.height > 25000000:
                raise ValueError()
            picture.verify()
            return Image.MIME[picture.format]
    except Exception as exc:
        raise ValueError() from exc


@integration(['POST'])
def upload(request, pk, doc_id):
    data = payload(request)
    name = data.get('name')
    if not isinstance(name, str) or not 1 <= len(name) <= 255:
        raise ValueError()
    name = Path(name).name
    raw = base64.b64decode(data['content'], validate=True)
    mime = check_file(raw, name)
    digest = hashlib.sha256(raw).hexdigest()
    with transaction.atomic():
        dossier = get_object_or_404(Dossier.objects.select_for_update(), pk=pk, source=settings.INTEGRATION_SOURCE)
        expected = next((d for d in dossier.manifest if d['id'] == str(doc_id)), None)
        if not expected:
            raise ValueError()
        existing = File.objects.filter(pk=doc_id).first()
        if existing:
            if existing.dossier_id != pk or existing.digest != digest or existing.name != name:
                return JsonResponse({'message': 'El documento ya existe con otro contenido.'}, status=409)
            return JsonResponse({'received': True})
        if dossier.ready:
            return JsonResponse({'message': 'El expediente está cerrado para cargas.'}, status=409)
        File.objects.create(id=doc_id, dossier=dossier, kind=expected['kind'], name=name, mime=mime, digest=digest, content=raw)
    return JsonResponse({'received': True}, status=201)


@integration(['POST'])
def confirm(request, pk):
    with transaction.atomic():
        dossier = get_object_or_404(Dossier.objects.select_for_update(), pk=pk, source=settings.INTEGRATION_SOURCE)
        if set(dossier.files.values_list('kind', flat=True)) != KINDS:
            return JsonResponse({'message': 'Faltan documentos.'}, status=409)
        dossier.ready = True
        dossier.save(update_fields=['ready'])
        return JsonResponse(snapshot(dossier))


@never_cache
def sign_in(request):
    error = ''
    if request.method == 'POST':
        username = request.POST.get('username', '')[:150]
        key = hashlib.sha256(username.casefold().encode()).hexdigest()
        with transaction.atomic():
            attempt, _ = LoginAttempt.objects.select_for_update().get_or_create(key=key, defaults={'started_at': timezone.now()})
            if attempt.started_at < timezone.now() - timedelta(minutes=10):
                attempt.count, attempt.started_at = 0, timezone.now()
            if attempt.count >= 10:
                return render(request, 'receiver/login.html', {'error': 'Demasiados intentos. Espera diez minutos.'}, status=429)
            attempt.count += 1
            attempt.save()
        user = authenticate(request, username=username, password=request.POST.get('password', ''))
        if user and (user.is_superuser or Reviewer.objects.filter(user=user).exists()):
            login(request, user)
            LoginAttempt.objects.filter(key=key).delete()
            return redirect('/')
        error = 'Revisa tu usuario y contraseña.'
    return render(request, 'receiver/login.html', {'error': error})


def allowed_areas(user):
    return set(AREAS) if user.is_superuser else set(Reviewer.objects.filter(user=user).values_list('area', flat=True))


@login_required
@never_cache
def inbox(request):
    if not allowed_areas(request.user):
        return HttpResponse(status=403)
    dossiers = Dossier.objects.filter(ready=True).order_by('-created_at')[:100]
    return render(request, 'receiver/inbox.html', {'dossiers': dossiers})


@login_required
@never_cache
def detail(request, pk):
    areas = allowed_areas(request.user)
    if not areas:
        return HttpResponse(status=403)
    dossier = get_object_or_404(Dossier, pk=pk, ready=True)
    data = snapshot(dossier)
    for area in data['areas']:
        area['can_decide'] = area['area'] in areas and area['status'] == 'pending'
    kinds = set.union(*(REQUIREMENTS[a] for a in areas))
    return render(request, 'receiver/detail.html', {'dossier': dossier, 'data': data, 'files': dossier.files.filter(kind__in=kinds).defer('content')})


@login_required
@never_cache
def download(request, pk):
    file = get_object_or_404(File, pk=pk, dossier__ready=True)
    if not any(file.kind in REQUIREMENTS[a] for a in allowed_areas(request.user)):
        return HttpResponse(status=403)
    from django.utils.http import content_disposition_header
    response = HttpResponse(bytes(file.content), content_type=file.mime)
    response['Content-Disposition'] = content_disposition_header(True, file.name)
    response['Cache-Control'] = 'private, no-store'
    return response


@login_required
@require_POST
def resolve(request, pk, area):
    if area not in allowed_areas(request.user):
        return HttpResponse(status=403)
    outcome, notes = request.POST.get('outcome'), request.POST.get('notes', '').strip()
    if outcome not in ('approved', 'rejected') or len(notes) > 2000 or (outcome == 'rejected' and not notes):
        return HttpResponse('Para rechazar, escribe un motivo. Máximo 2000 caracteres.', status=400)
    with transaction.atomic():
        dossier = get_object_or_404(Dossier.objects.select_for_update(), pk=pk, ready=True)
        if Decision.objects.filter(dossier=dossier, area=area).exists():
            return HttpResponse('Esta área ya emitió su resolución.', status=409)
        Decision.objects.create(dossier=dossier, area=area, outcome=outcome, notes=notes, reviewer=request.user)
    return redirect(f'/expedientes/{pk}/')
