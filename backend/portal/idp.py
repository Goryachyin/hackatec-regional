"""Cliente interno: nunca enviar el archivo directamente del navegador al bot."""
import json
import re
import uuid
from urllib.request import Request, urlopen
from urllib.error import HTTPError, URLError
from django.conf import settings


class IDPError(Exception):
    def __init__(self, message, status=503):
        super().__init__(message)
        self.status = status


def inspect_document(file, filename, kind):
    if kind not in ('ine', 'cfe', 'curp'):
        raise IDPError('Este tipo documental no está soportado por el bot.', 422)
    if not settings.IDP_API_KEY:
        raise IDPError('Falta configurar el acceso al servicio IDP.')
    file.seek(0)
    contents = file.read(10 * 1024 * 1024 + 1)
    file.seek(0)
    if len(contents) > 10 * 1024 * 1024:
        raise IDPError('El documento supera 10 MB.', 413)
    boundary = uuid.uuid4().hex
    # Nombre fijo: evita inyección de encabezados a través del nombre del usuario.
    suffix = filename.rsplit('.', 1)[-1].lower()
    safe_name = 'document.' + (suffix if suffix in ('pdf', 'png', 'jpg', 'jpeg') else 'bin')
    payload = (f'--{boundary}\r\nContent-Disposition: form-data; name="doc_type"\r\n\r\n{kind}\r\n'
               f'--{boundary}\r\nContent-Disposition: form-data; name="file"; filename="{safe_name}"\r\n'
               'Content-Type: application/octet-stream\r\n\r\n').encode() + contents + f'\r\n--{boundary}--\r\n'.encode()
    request = Request(settings.IDP_BOT_URL + '/process-document/', data=payload, headers={
        'Content-Type': f'multipart/form-data; boundary={boundary}', 'X-IDP-Key': settings.IDP_API_KEY}, method='POST')
    try:
        with urlopen(request, timeout=settings.IDP_TIMEOUT) as response:
            result = json.loads(response.read(1024 * 1024))
    except HTTPError as exc:
        if exc.code == 503:
            try:
                code = json.loads(exc.read(8192)).get('code')
            except (ValueError, AttributeError):
                code = None
            messages = {
                'provider_quota': 'El análisis está suspendido por saldo o cuota de API. Contacta al administrador.',
                'provider_auth': 'El servicio de análisis tiene un problema de credenciales. Contacta al administrador.',
                'provider_access': 'El servicio de análisis no tiene acceso al modelo configurado. Contacta al administrador.',
                'provider_rate_limit': 'El análisis alcanzó un límite temporal. Espera antes de reintentar.',
                'provider_timeout': 'El análisis agotó el tiempo de espera. Intenta de nuevo.',
            }
            raise IDPError(messages.get(code, 'El servicio de análisis no está disponible. Inténtalo más tarde.')) from exc
        if exc.code in (400, 413, 422):
            try:
                detail = json.loads(exc.read(8192)).get('message', 'Revisa el archivo cargado.')
            except (ValueError, AttributeError):
                detail = 'Revisa el archivo cargado.'
            raise IDPError(detail, 422) from exc
        raise IDPError('El bot no está disponible u ocupado. Tu documento no se guardó; vuelve a intentarlo.') from exc
    except (URLError, TimeoutError, OSError) as exc:
        raise IDPError('No pudimos conectar con el bot o terminó el tiempo de espera. Inténtalo de nuevo.') from exc
    except (ValueError, UnicodeDecodeError) as exc:
        raise IDPError('El bot devolvió una respuesta no válida.', 502) from exc
    if (not isinstance(result, dict) or result.get('schema_version') != 1
            or result.get('expected_type') != kind
            or result.get('document_type') not in ('ine', 'cfe', 'curp', 'unknown')
            or result.get('status') not in ('accepted', 'rejected', 'needs_review')
            or not isinstance(result.get('extracted_data'), dict)
            or not isinstance(result.get('message'), str)
            or not isinstance(result.get('checks'), list)
            or result.get('official_validation') is not False):
        raise IDPError('El resultado del bot no cumple el contrato esperado.', 502)
    if result['status'] == 'accepted':
        required = {'ine': ['nombre', 'curp', 'vigencia'], 'cfe': ['direccion'], 'curp': ['curp', 'nombre']}[kind]
        fields = result['extracted_data']
        if (result['document_type'] != kind or not all(isinstance(fields.get(k), str) and fields[k].strip() for k in required)
                or not result['checks'] or not all(isinstance(c, dict) and c.get('passed') is True for c in result['checks'])):
            raise IDPError('El bot no aportó evidencia suficiente para aceptar el archivo.', 502)
    return result
