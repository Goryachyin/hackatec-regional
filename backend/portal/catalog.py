DOCUMENT_TYPES = {'ine': 'INE', 'cfe': 'Comprobante CFE', 'curp': 'Constancia de CURP'}

LICENSE_GROUPS = [
    {'name': 'Documentos generales', 'requirements': ['ine', 'curp', 'cfe']},
    {'name': 'Protección Civil', 'requirements': ['pc_pago', 'pc_uso_suelo']},
    {'name': 'Obras Públicas', 'requirements': ['op_solicitud', 'op_predial']},
    {'name': 'Ecología', 'requirements': ['eco_recoleccion', 'eco_solicitud']},
]
DOCUMENT_TYPES.update({
    'clave_catastral': 'Documento con clave catastral',
    'propiedad': 'Documento que acredite la propiedad',
    'pc_pago': 'Recibo de pago de derechos por verificación de Protección Civil',
    'pc_uso_suelo': 'Constancia de Uso de Suelo o Factibilidad vigente',
    'op_solicitud': 'Solicitud oficial con los datos catastrales del inmueble',
    'op_predial': 'Recibo de pago del impuesto Predial actualizado',
    'eco_recoleccion': 'Contrato de recolección de basura comercial o última factura de pago del servicio',
    'eco_solicitud': 'Solicitud ambiental especificando los residuos generados',
})
IDP_TYPES = set(DOCUMENT_TYPES)
IDP_REQUIRED = {'curp': ['curp', 'nombre'], 'ine': ['curp', 'nombre', 'vigencia'], 'cfe': ['direccion'], 'propiedad': ['titulo_documento', 'titular', 'direccion'], 'pc_pago': ['emisor', 'concepto', 'folio', 'fecha_emision'], 'pc_uso_suelo': ['titulo_documento', 'emisor', 'direccion'], 'op_solicitud': ['titulo_documento', 'titular', 'clave_catastral'], 'op_predial': ['emisor', 'concepto', 'folio', 'fecha_emision'], 'eco_recoleccion': ['titulo_documento', 'emisor', 'concepto'], 'eco_solicitud': ['titulo_documento', 'titular', 'residuos'], 'clave_catastral': ['clave_catastral']}

# Reglas de demostración configurables; no son requisitos oficiales de Acapulco.
CATALOG = [
    {'id': 'predial', 'name': 'Pago de Predial', 'category': 'Patrimonio', 'description': 'Inicia tu solicitud de atención para consulta y pago del impuesto predial.', 'requirements': ['ine', 'cfe'], 'reference_label': 'Cuenta o clave predial', 'reference_required': True},
    {'id': 'funcionamiento', 'name': 'Licencia de funcionamiento', 'category': 'Actividad económica', 'description': 'Prepara el expediente para la solicitud de licencia de tu negocio.', 'requirements': [kind for group in LICENSE_GROUPS for kind in group['requirements']], 'requirement_groups': LICENSE_GROUPS, 'reference_label': 'Nombre del establecimiento', 'reference_required': False},
    {'id': 'construccion', 'name': 'Permiso de construcción', 'category': 'Desarrollo urbano', 'description': 'Reúne tus documentos e inicia una solicitud de permiso de construcción.', 'requirements': ['ine', 'propiedad', 'cfe', 'op_predial'], 'reference_label': 'Referencia del predio', 'reference_required': False},
]
CATALOG_BY_ID = {item['id']: item for item in CATALOG}
