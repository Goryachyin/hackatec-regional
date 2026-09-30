# Bot IDP: OpenAI y motor local

El proveedor OpenAI clasifica INE, CFE y constancias CURP usando Responses API,
PDF como input_file e imágenes como input_image, con JSON Schema estricto.
Mantiene el contrato v1 con Django. No es una verificación de autenticidad.

## Arranque desde la raíz del proyecto (PowerShell)

1. Copiar `idp-bot/.env.example` a `idp-bot/.env` si todavía no existe.
2. Editar `.env` y colocar una clave de API en OPENAI_API_KEY. Nunca pegarla en
   el chat ni en el frontend. Se requiere facturación de API independiente.
3. Ejecutar:

```powershell
docker compose --env-file .\idp-bot\.env -f .\idp-bot\docker-compose.yml up -d --build --wait
Invoke-RestMethod http://127.0.0.1:8001/health/
```

Health debe indicar engine=openai. Solo verifica configuración local, no saldo,
acceso al modelo ni conectividad con OpenAI. Sin clave devuelve 503.
El modelo inicial es gpt-4.1, configurable con OPENAI_MODEL; cualquier sustituto
debe admitir imágenes, PDF y Structured Outputs.
Para usar OCR local configurar IDP_PROVIDER=local y recrear el contenedor.
Fuera de Docker se deben exportar estas variables al proceso; no se carga .env
automáticamente. Django conserva IDP_TIMEOUT=120 y la misma IDP_API_KEY.

## Comportamiento

- Clasificación independiente del tipo solicitado; diferencias se rechazan.
- Nombre completo separado de nombres/apellidos; campos ambiguos quedan null.
- `nombre` es alias de `nombre_completo` para el contrato existente.
- Se comprueban campos mínimos, formato CURP, fechas y vigencia INE. Apellidos
  y fecha no visibles son opcionales, nunca se deducen de la CURP.
- No hay caída silenciosa a OCR local, ni reintentos automáticos facturables.
- Límite 10 MB, 10 páginas, 25 MP; un análisis simultáneo por proceso.
- PDF enviado directamente en base64; imágenes reserializadas sin EXIF.
- Se envía el documento a OpenAI, con store=false; esto no garantiza retención
  cero por parte del proveedor. No se crean archivos persistentes vía Files API
  ni vector stores. No registrar cuerpos de peticiones ni datos extraídos.

## Verificación

```powershell
cd idp-bot
.\.venv\Scripts\python.exe -m unittest discover -s tests
```

Los tests del proveedor usan respuestas simuladas: verifican transporte,
clasificación, campos exactos y errores; no demuestran precisión real.
Para evaluar calidad, usar muestras autorizadas y comparar cada campo con una
transcripción manual, incluyendo archivos borrosos, tipos incorrectos y PDFs
escaneados. Volver a analizar los documentos guardados desde la interfaz.

Fuentes: https://developers.openai.com/api/docs/guides/file-inputs
y https://developers.openai.com/api/docs/guides/structured-outputs


## Tipos adicionales (revisión preliminar)

OpenAI reconoce también pc_pago, pc_uso_suelo, op_solicitud, op_predial,
eco_recoleccion, eco_solicitud, propiedad y clave_catastral. El motor OCR local
continúa limitado a INE, CFE y CURP y rechaza otros tipos explícitamente.

Los campos mínimos son reglas del prototipo, no requisitos legales verificados.
Una constancia de uso de suelo sin vencimiento explícito requiere revisión;
no se inventa su vigencia. Una factura no acredita ser la última disponible ni
un recibo confirma el movimiento bancario. Los formatos reales deben evaluarse
con muestras autorizadas antes de afirmar precisión.

Django envía ahora todos estos tipos al bot. Archivos guardados previamente como
received deben volver a analizarse; no se convierten a accepted automáticamente.
La pantalla de Predial mantiene Continuar sin acción; clave_catastral está
soportada por el bot y el Baúl, sin activar el envío del formulario de Predial.

Tras actualizar: reconstruir el contenedor, reiniciar Django y recargar el portal.
