"""IDP local: revisión preliminar, no autenticación oficial."""
import hmac
import os
import threading
from contextlib import asynccontextmanager
from typing import Literal
from fastapi import FastAPI, File, Form, UploadFile
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from processor import DocumentError, MAX_BYTES, analyze, get_engine

gate = threading.Lock()

@asynccontextmanager
async def lifespan(app):
    if os.getenv('IDP_PROVIDER', 'local') == 'local':
        get_engine()
    elif os.getenv('IDP_PROVIDER') != 'openai':
        raise RuntimeError('IDP_PROVIDER debe ser local u openai')
    yield

app = FastAPI(title='IDP local · INE, CFE y CURP', version='2.0.0', lifespan=lifespan)

@app.middleware('http')
async def protect_upload(request, call_next):
    if request.url.path == '/process-document/' and request.method == 'POST':
        if not hmac.compare_digest(os.getenv('IDP_API_KEY', 'local-development-key'), request.headers.get('x-idp-key', '')):
            return JSONResponse({'code': 'unauthorized', 'message': 'Acceso al bot no autorizado.'}, status_code=401)
        try:
            length = int(request.headers.get('content-length', '-1'))
        except ValueError:
            length = -1
        if length < 0:
            return JSONResponse({'code': 'length_required', 'message': 'Content-Length requerido.'}, status_code=411)
        if length > MAX_BYTES + 1024 * 1024:
            return JSONResponse({'code': 'too_large', 'message': 'El archivo supera 10 MB.'}, status_code=413)
    return await call_next(request)

@app.exception_handler(RequestValidationError)
async def invalid_request(request, exc):
    return JSONResponse({'code': 'invalid_request', 'message': 'Envía file y doc_type: ine, cfe o curp.'}, status_code=422)

@app.get('/health/')
def health():
    provider = os.getenv('IDP_PROVIDER', 'local')
    ready = provider == 'local' or bool(os.getenv('OPENAI_API_KEY', '').strip())
    return JSONResponse({'status': 'ok' if ready else 'not_configured',
                         'engine': 'openai' if provider == 'openai' else 'rapidocr-onnx-cpu',
                         'schema_version': 1}, status_code=200 if ready else 503)

@app.post('/process-document/')
def process_document(doc_type: Literal['ine', 'cfe', 'curp'] = Form(...), file: UploadFile = File(...)):
    # Un trabajo por proceso. La ruta síncrona utiliza el threadpool de FastAPI.
    if not gate.acquire(blocking=False):
        return JSONResponse({'code': 'busy', 'message': 'El bot está ocupado. Intenta nuevamente en unos segundos.'}, status_code=503, headers={'Retry-After': '3'})
    try:
        if os.getenv('IDP_PROVIDER', 'local') == 'openai':
            from openai_processor import analyze as analyze_openai
            return analyze_openai(file.file.read(MAX_BYTES + 1), file.filename or '', doc_type)
        return analyze(file.file.read(MAX_BYTES + 1), file.filename or '', doc_type)
    except DocumentError as exc:
        return JSONResponse({'code': exc.code, 'message': str(exc)}, status_code=exc.status)
    except Exception:
        return JSONResponse({'code': 'processing_error', 'message': 'No pudimos procesar el archivo. Intenta otra captura.'}, status_code=500)
    finally:
        file.file.close()
        gate.release()
