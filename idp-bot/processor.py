import io
import re
import threading
import unicodedata
import warnings
from datetime import date
from pathlib import Path
from PIL import Image, ImageOps
from pypdf import PdfReader
import pypdfium2 as pdfium

MAX_BYTES = 10 * 1024 * 1024
MAX_PAGES = 10
MAX_PIXELS = 25_000_000
CURP_PATTERN = r'\b[A-Z][AEIOUX][A-Z]{2}\d{6}[HM][A-Z]{5}[A-Z\d]\d\b'
_engine = None
_engine_lock = threading.Lock()

class DocumentError(Exception):
    def __init__(self, message, code='invalid_file', status=422):
        super().__init__(message)
        self.code, self.status = code, status

def normalized(text):
    text = unicodedata.normalize('NFKD', text)
    return re.sub(r'[^A-Z0-9\s:./#-]', ' ', ''.join(c for c in text if not unicodedata.combining(c)).upper())

def get_engine():
    global _engine
    if _engine is None:
        with _engine_lock:
            if _engine is None:
                from rapidocr_onnxruntime import RapidOCR
                _engine = RapidOCR(intra_op_num_threads=2, inter_op_num_threads=1)
    return _engine

def ocr_image(image):
    import numpy as np
    image = ImageOps.exif_transpose(image).convert('RGB')
    image.thumbnail((2400, 2400))
    result, _ = get_engine()(np.asarray(image)[:, :, ::-1].copy())
    return '\n'.join(str(row[1]) for row in (result or []) if float(row[2]) >= 0.5)

def extract_pages(data, filename, force_ocr=False):
    if not data or len(data) > MAX_BYTES:
        raise DocumentError('Carga un archivo no vacío de hasta 10 MB.', 'invalid_size', 413)
    suffix = Path(filename).suffix.lower()
    if suffix == '.pdf':
        if not data.startswith(b'%PDF-'):
            raise DocumentError('El archivo no corresponde a un PDF.')
        try:
            reader = PdfReader(io.BytesIO(data))
            if reader.is_encrypted:
                raise DocumentError('El PDF no debe tener contraseña.')
            if not 1 <= len(reader.pages) <= MAX_PAGES:
                raise DocumentError(f'El PDF debe tener entre 1 y {MAX_PAGES} páginas.')
            results = []
            with pdfium.PdfDocument(data) as rendered:
                for i, page in enumerate(reader.pages):
                    text = page.extract_text() or ''
                    if not force_ocr and sum(c.isalnum() for c in text) >= 40:
                        results.append((text, 'pdf_text'))
                    else:
                        pdf_page = rendered[i]
                        try:
                            width, height = pdf_page.get_size()
                            bitmap = pdf_page.render(scale=min(2.5, 2400 / max(width, height)))
                            try:
                                results.append((ocr_image(bitmap.to_pil().copy()), 'ocr'))
                            finally:
                                bitmap.close()
                        finally:
                            pdf_page.close()
            return results
        except DocumentError:
            raise
        except Exception as exc:
            raise DocumentError('No se pudo leer el PDF. Revisa el archivo.') from exc
    if suffix not in ['.png', '.jpg', '.jpeg']:
        raise DocumentError('Solo se admiten PDF, JPG y PNG.')
    try:
        with warnings.catch_warnings():
            warnings.simplefilter('error', Image.DecompressionBombWarning)
            with Image.open(io.BytesIO(data)) as image:
                if image.format not in ['PNG', 'JPEG'] or image.width * image.height > MAX_PIXELS:
                    raise DocumentError('Imagen no admitida o demasiado grande (máximo 25 megapíxeles).')
                image.load()
                return [(ocr_image(image), 'ocr')]
    except DocumentError:
        raise
    except Exception as exc:
        raise DocumentError('No se pudo leer la imagen. Carga otra fotografía.') from exc

def detect_type(text):
    value = normalized(text)
    # OCR puede unir palabras: REGISTRONACIONALDEPOBLACION sigue siendo
    # una señal de encabezado. No corregimos ni inventamos datos del ciudadano.
    has = lambda pattern: bool(re.search(pattern.replace(r'\s+', r'\s*'), value))
    signals = {
        'ine': [has(r'INSTITUTO\s+NACIONAL\s+ELECTORAL'), has(r'CREDENCIAL\s+PARA\s+VOTAR'), has(r'CLAVE\s+DE\s+ELECTOR'), has(r'\bSECCION\b')],
        'cfe': [has(r'COMISION\s+FEDERAL\s+DE\s+ELECTRICIDAD|\bCFE\b'), has(r'NUMERO\s+DE\s+SERVICIO|NO[. ]*DE\s+SERVICIO|\bRPU\b'), has(r'TOTAL\s+A\s+PAGAR'), has(r'PERIODO\s+FACTURADO|\bKWH\b|\bTARIFA\b')],
        'curp': [has(r'REGISTRO\s+NACIONAL\s+DE\s+POBLACION|\bRENAPO\b'), has(r'CLAVE\s+UNICA\s+DE\s+REGISTRO\s+DE\s+POBLACION'), has(r'CURP\s+CERTIFICADA|CONSTANCIA.*CURP'), has(r'SOY\s+MEXICO|SECRETARIA\s+DE\s+GOBERNACION')],
    }
    candidates = [kind for kind, matches in signals.items() if sum(matches) >= 2 and any(matches[:2])]
    return candidates[0] if len(candidates) == 1 else 'unknown'

def after_label(text, patterns, multiple=False):
    lines = [re.sub(r'\s+', ' ', line).strip() for line in normalized(text).splitlines() if line.strip()]
    stop = r'^(CURP|DOMICILIO|DIRECCION|CLAVE|SECCION|VIGENCIA|FECHA|SEXO|NUMERO|NO\.? DE|RPU|TOTAL|PERIODO|TARIFA|REGISTRO|FOLIO|ENTIDAD|PRIMER APELLIDO|SEGUNDO APELLIDO)'
    stop = stop.replace(' ', r'\s*')
    for i, line in enumerate(lines):
        for pattern in patterns:
            flexible_pattern = pattern.replace(' ', r'\s*')
            match = re.match(flexible_pattern + r'(?=\s|:|$|\d)\s*:?\s*(.*)$', line)
            if not match:
                continue
            values = [match.group(1).strip()] if match.group(1).strip() else []
            for following in lines[i + 1:i + 4]:
                if re.match(stop, following) or (values and not multiple):
                    break
                values.append(following)
                if not multiple:
                    break
            return ' '.join(values) or None
    return None

def extract_curp_name(text):
    lines = [re.sub(r'\s+', ' ', line).strip() for line in normalized(text).splitlines() if line.strip()]
    label = r'NOMBRE(?:\s*S|\s*COMPLETO|\s*DEL\s*REGISTRADO)?'
    # No usar párrafos legales/encabezados como sustituto de un nombre faltante.
    forbidden = r'CURP|REGISTRO|POBLACION|SECRETARIA|GOBIERNO|GOBERNACION|CERTIFICAD|IDENTIDAD|DOCUMENTO|NACIMIENTO|APELLIDO|FOLIO|PRESENTE|TRAMITE|RENAPO|MEXICO|CLAVE|SEXO|ENTIDAD|FECHA'
    def plausible(value):
        compact = re.sub(r'\s+', '', value)
        return (3 <= len(compact) <= 100 and re.fullmatch(r'[A-Z ]+', value) is not None
                and not re.search(forbidden, compact))
    for i, line in enumerate(lines):
        match = re.match(r'^' + label + r'\s*:\s*(.+)$', line)
        if match and plausible(match.group(1)):
            return match.group(1)
        match = re.match(r'^' + label + r'\s+(.+)$', line)
        if match and plausible(match.group(1)) and match.group(1) != 'S':
            return match.group(1)
        if not re.fullmatch(label + r'\s*:?\s*', line):
            continue
        following = lines[i + 1] if i + 1 < len(lines) else ''
        preceding = lines[i - 1] if i > 0 else ''
        candidates = [value for value in [following, preceding] if plausible(value)]
        # Dos vecinos plausibles constituyen un caso ambiguo: no adivinar.
        if len(set(candidates)) == 1:
            return candidates[0]
    return None


def extract_fields(text, kind):
    value = normalized(text)
    curps = set(re.findall(CURP_PATTERN, value))
    curp = next(iter(curps)) if len(curps) == 1 else None
    if kind == 'ine':
        years = re.findall(r'\b(?:19|20|21)\d{2}\b', after_label(text, [r'VIGENCIA']) or '')
        return {'nombre': after_label(text, [r'NOMBRE'], multiple=True), 'curp': curp,
                'domicilio': after_label(text, [r'DOMICILIO'], multiple=True),
                'clave_elector': after_label(text, [r'CLAVE DE ELECTOR']), 'vigencia': years[-1] if years else None}
    if kind == 'curp':
        return {'curp': curp, 'nombre': extract_curp_name(text),
                'primer_apellido': after_label(text, [r'PRIMER APELLIDO']),
                'segundo_apellido': after_label(text, [r'SEGUNDO APELLIDO']),
                'fecha_nacimiento': after_label(text, [r'FECHA DE NACIMIENTO'])}
    address = after_label(text, [r'DIRECCION(?: DEL SERVICIO)?', r'DOMICILIO(?: DEL SERVICIO)?'], multiple=True)
    if not address:
        lines = [line.strip() for line in value.splitlines() if line.strip()]
        for i, line in enumerate(lines):
            if re.search(r'^(CALLE|AVENIDA|AV\.? |BLVD|BOULEVARD|PRIVADA|CERRADA|CARRETERA|CARR\.? )', line):
                parts = [line]
                for following in lines[i + 1:i + 3]:
                    if re.search(r'TOTAL|SERVICIO|RPU|PERIODO|TARIFA', following):
                        break
                    parts.append(following)
                address = ' '.join(parts)
                break
    return {'direccion': address, 'numero_servicio': after_label(text, [r'NUMERO DE SERVICIO', r'NO\.? DE SERVICIO', r'RPU']),
            'periodo': after_label(text, [r'PERIODO FACTURADO', r'PERIODO DE FACTURACION']),
            'nombre_cliente': after_label(text, [r'NOMBRE(?: DEL CLIENTE)?'])}

def evaluate(pages, expected):
    text = '\n'.join(page[0] for page in pages)
    kinds = {detect_type(page[0]) for page in pages} - {'unknown'}
    detected = next(iter(kinds)) if len(kinds) == 1 else detect_type(text) if not kinds else 'unknown'
    result = {'schema_version': 1, 'expected_type': expected, 'document_type': detected,
              'status': 'needs_review', 'code': 'unknown_document', 'message': 'No pudimos identificar con suficiente evidencia un único documento INE, CFE o CURP.',
              'extracted_data': {}, 'checks': [], 'pages': len(pages), 'sources': [p[1] for p in pages],
              'official_validation': False, 'warnings': ['Revisión preliminar de formato y campos; no acredita autenticidad.']}
    if len(text.strip()) < 15:
        result.update(code='unreadable', message='No pudimos leer suficiente texto. Toma otra fotografía con buena iluminación.')
        return result
    if detected == 'unknown':
        return result
    fields = extract_fields(text, detected)
    result['extracted_data'] = fields
    if detected != expected:
        result.update(status='rejected', code='type_mismatch', message=f'Se detectó {detected.upper()}, pero se solicita {expected.upper()}.')
        return result
    required = {'ine': ['nombre', 'curp', 'vigencia'], 'cfe': ['direccion'], 'curp': ['curp', 'nombre']}[detected]
    checks = [{'field': key, 'passed': bool(fields.get(key)), 'rule': 'required_field'} for key in required]
    if detected == 'ine' and fields.get('vigencia'):
        checks.append({'field': 'vigencia', 'passed': int(fields['vigencia']) >= date.today().year, 'rule': 'year_not_expired'})
    result['checks'] = checks
    if not all(check['passed'] for check in checks):
        failed = [c for c in checks if not c['passed']]
        message = 'No pudimos leer estos campos: ' + ', '.join(c['field'] for c in failed if c['rule'] == 'required_field') + '. Prueba otra imagen o el PDF original.'
        if any(c['rule'] == 'year_not_expired' for c in failed):
            message = 'La vigencia leída parece vencida. Revisa la fecha o carga una captura más clara.'
        result.update(code='fields_need_review', message=message)
    else:
        result.update(status='accepted', code='precheck_passed', message='Tipo y campos mínimos comprobados. No constituye validación oficial.')
    return result

def analyze(data, filename, expected):
    pages = extract_pages(data, filename)
    result = evaluate(pages, expected)
    if (Path(filename).suffix.lower() == '.pdf' and any(p[1] == 'pdf_text' for p in pages)
            and result['code'] in ['unknown_document', 'fields_need_review']):
        # Una capa textual incompleta o desordenada no debe ser la única lectura.
        # Nunca omitir una discrepancia de tipo ni una vigencia vencida reconocida.
        expired = any(c.get('rule') == 'year_not_expired' and not c['passed'] for c in result['checks'])
        if not expired:
            try:
                optical = evaluate(extract_pages(data, filename, force_ocr=True), expected)
                if optical['status'] == 'accepted' and result['document_type'] in ['unknown', optical['document_type']]:
                    optical['warnings'].append('Se utilizó OCR como segunda lectura del PDF.')
                    return optical
            except DocumentError:
                pass
    return result
