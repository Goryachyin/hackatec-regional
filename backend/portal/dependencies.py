"""Intercambio explícito de expedientes de demostración; un archivo por petición."""
import base64
import json
import uuid
from datetime import timedelta
from urllib.error import HTTPError, URLError
from urllib.parse import urlparse
from urllib.request import HTTPRedirectHandler, Request, build_opener
from django.conf import settings
from django.db.models import Q
from django.utils import timezone
from .models import Delivery

AREAS = {'proteccion_civil', 'obras_publicas', 'ecologia'}


class ExchangeError(Exception):
    pass


class NoRedirect(HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None


def configured():
    url = urlparse(settings.DEPENDENCIES_URL)
    return bool(url.scheme == 'https' and url.hostname and not url.username and not url.password
                and not url.query and not url.fragment and len(settings.DEPENDENCIES_KEY) >= 32
                and 1 <= len(settings.DEPENDENCIES_SOURCE) <= 80)


def remote(path, method='GET', data=None):
    if not configured():
        raise ExchangeError('Falta configurar la conexión HTTPS con el portal de dependencias.')
    request = Request(settings.DEPENDENCIES_URL + '/api/expedientes/' + path,
                      data=json.dumps(data).encode() if data is not None else None, method=method,
                      headers={'Content-Type': 'application/json', 'X-Integration-Key': settings.DEPENDENCIES_KEY,
                               'X-Source': settings.DEPENDENCIES_SOURCE})
    try:
        with build_opener(NoRedirect()).open(request, timeout=25) as response:
            raw = response.read(128 * 1024 + 1)
        if len(raw) > 128 * 1024:
            raise ValueError()
        result = json.loads(raw)
        if not isinstance(result, dict):
            raise ValueError()
        return result
    except HTTPError as exc:
        message = 'Credencial de integración rechazada. Revisa la configuración de ambos servidores.' if exc.code in (401, 403) else 'El portal de dependencias no aceptó el intercambio. Puedes reintentar.'
        raise ExchangeError(message) from exc
    except (URLError, TimeoutError, OSError, ValueError) as exc:
        raise ExchangeError('No se pudo completar la comunicación. El expediente sigue guardado; vuelve a intentar.') from exc


def validate_result(data, delivery, app):
    if data.get('id') != str(delivery.remote_id) or data.get('folio') != app.folio or data.get('is_demo') is not True:
        raise ExchangeError('La respuesta no corresponde al expediente enviado.')
    areas = data.get('areas')
    if not isinstance(areas, list) or len(areas) != 3 or any(not isinstance(a, dict) for a in areas):
        raise ExchangeError('La respuesta de las dependencias no es válida.')
    if {a.get('area') for a in areas} != AREAS:
        raise ExchangeError('La respuesta de las dependencias no es válida.')
    for area in areas:
        if area.get('status') not in ('pending', 'approved', 'rejected') or not isinstance(area.get('notes'), str) or len(area['notes']) > 2000:
            raise ExchangeError('La resolución recibida no es válida.')
    status = data.get('status')
    expected = 'rejected' if any(a['status'] == 'rejected' for a in areas) else 'approved' if all(a['status'] == 'approved' for a in areas) else 'in_review'
    if status not in ('receiving', expected):
        raise ExchangeError('El estado recibido no coincide con las resoluciones.')
    return data


def delivery_data(app):
    try:
        delivery = app.delivery
    except Delivery.DoesNotExist:
        return {'status': 'not_sent', 'configured': configured()}
    return {'status': delivery.status, 'configured': configured(), 'sent_files': delivery.next_file,
            'error': delivery.error, 'result': delivery.result,
            'synced_at': delivery.synced_at.isoformat() if delivery.synced_at else None}


def exchange_step(app, sync=False):
    if not configured():
        raise ExchangeError('Configura primero la conexión con el portal de dependencias.')
    docs = [a.document for a in app.attachments.select_related('document').order_by('document__kind')]
    if app.status == 'draft' or not app.is_demo or app.procedure != 'funcionamiento' or not docs or not all(d.is_simulated for d in docs):
        raise ExchangeError('Esta integración admite únicamente licencias enviadas con todos sus documentos simulados.')
    source = settings.DEPENDENCIES_SOURCE
    delivery, _ = Delivery.objects.get_or_create(application=app, defaults={
        'remote_id': uuid.uuid5(uuid.NAMESPACE_URL, source + ':' + str(app.id)), 'source': source,
        'target_url': settings.DEPENDENCIES_URL})
    if delivery.source != source or delivery.target_url != settings.DEPENDENCIES_URL:
        raise ExchangeError('La conexión cambió desde el primer envío. Conserva el destino y origen del expediente.')
    now = timezone.now()
    claimed = Delivery.objects.filter(pk=delivery.pk).filter(Q(lease_until__isnull=True) | Q(lease_until__lt=now)).update(lease_until=now + timedelta(seconds=90))
    if not claimed:
        raise ExchangeError('Ya hay un intercambio en curso. Espera unos segundos.')
    try:
        delivery.refresh_from_db()
        path = str(delivery.remote_id) + '/'
        def document_id(doc):
            return str(uuid.uuid5(delivery.remote_id, str(doc.id)))
        if sync or delivery.status == 'received':
            result = validate_result(remote(path), delivery, app)
            if result['status'] == 'receiving':
                raise ExchangeError('Aún falta terminar la transferencia del expediente.')
            delivery.status = 'received'
        else:
            manifest = [{'id': document_id(doc), 'kind': doc.kind} for doc in docs]
            validate_result(remote(path, 'POST', {'folio': app.folio, 'is_demo': True, 'procedure': app.procedure, 'documents': manifest}), delivery, app)
            if delivery.next_file < len(docs):
                doc = docs[delivery.next_file]
                with doc.file.open('rb') as file:
                    content = file.read(10 * 1024 * 1024 + 1)
                if len(content) > 10 * 1024 * 1024:
                    raise ExchangeError('Un archivo supera el límite de la demostración.')
                receipt = remote(path + 'documentos/' + document_id(doc) + '/', 'POST', {
                    'name': doc.original_name, 'content': base64.b64encode(content).decode('ascii')})
                if receipt.get('received') is not True:
                    raise ExchangeError('El portal no confirmó la recepción del archivo.')
                delivery.next_file += 1
                delivery.status = 'sending'
                result = delivery.result
            else:
                result = validate_result(remote(path + 'confirmar/', 'POST', {}), delivery, app)
                if result['status'] == 'receiving':
                    raise ExchangeError('El portal aún no confirmó el expediente completo.')
                delivery.status = 'received'
        delivery.result, delivery.error = result, ''
        delivery.synced_at = timezone.now()
        delivery.save(update_fields=['next_file', 'status', 'result', 'error', 'synced_at'])
        if result.get('status') in ('approved', 'rejected', 'in_review'):
            app.status = result['status']
            app.save(update_fields=['status'])
    except ExchangeError as exc:
        Delivery.objects.filter(pk=delivery.pk).update(error=str(exc))
        raise
    except OSError as exc:
        message = 'No fue posible leer uno de los archivos guardados. Reintenta el envío.'
        Delivery.objects.filter(pk=delivery.pk).update(error=message)
        raise ExchangeError(message) from exc
    finally:
        Delivery.objects.filter(pk=delivery.pk).update(lease_until=None)
