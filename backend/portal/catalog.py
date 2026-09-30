DOCUMENT_TYPES = {'ine': 'INE', 'cfe': 'Comprobante CFE', 'curp': 'Constancia de CURP'}
# Reglas de demostración configurables; no son requisitos oficiales de Acapulco.
CATALOG = [
    {'id': 'predial', 'name': 'Pago de Predial', 'category': 'Patrimonio', 'description': 'Inicia tu solicitud de atención para consulta y pago del impuesto predial.', 'requirements': ['ine', 'cfe'], 'reference_label': 'Cuenta o clave predial', 'reference_required': True},
    {'id': 'funcionamiento', 'name': 'Licencia de funcionamiento', 'category': 'Actividad económica', 'description': 'Prepara el expediente para la solicitud de licencia de tu negocio.', 'requirements': ['ine', 'cfe', 'curp'], 'reference_label': 'Nombre del establecimiento', 'reference_required': False},
    {'id': 'construccion', 'name': 'Permiso de construcción', 'category': 'Desarrollo urbano', 'description': 'Reúne tus documentos e inicia una solicitud de permiso de construcción.', 'requirements': ['ine', 'cfe'], 'reference_label': 'Referencia del predio', 'reference_required': False},
]
CATALOG_BY_ID = {item['id']: item for item in CATALOG}
