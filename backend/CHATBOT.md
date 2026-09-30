# Alebrije Guía

Asistente autenticado con resúmenes de la cuenta, orientación sobre el catálogo, botones de navegación permitidos y voz a texto. No modifica documentos ni solicitudes. El idp-bot permanece independiente.

## Activación

En el backend Django local (.env) o en Environment del backend Render:

```dotenv
CHATBOT_ENABLED=true
CHATBOT_OPENAI_API_KEY=<clave del proyecto OpenAI>
CHATBOT_MODEL=gpt-4.1-mini
CHATBOT_TRANSCRIBE_MODEL=gpt-transcribe
```

Instalar requisitos actualizados: `python -m pip install -r backend/requirements.txt`. Reiniciar Django/redeplegar Render y publicar el frontend actualizado en Vercel. No requiere migraciones. La clave del contenedor idp-bot no está disponible automáticamente en Django. No configurar secretos en frontend. No se invocó la API real durante las pruebas automatizadas.

## Uso

Tras iniciar sesión, pulsa el alebrije inferior derecho. Puedes escribir una pregunta o seleccionar una sugerencia. La solicitud abierta se utiliza como contexto; en otras páginas se incluyen hasta diez solicitudes recientes y el Baúl. El contexto no incluye archivos originales, nombres de archivo, correo, CURP ni campos extraídos; sí incluye folios, tipos, estados y observaciones de la cuenta. Las observaciones pueden contener texto personal: usa datos ficticios en demostraciones.

Pulsa micrófono, permite acceso, habla en español y detén la grabación. El audio se transcribe y aparece en la caja de texto para corregirlo. Solo Enviar lo convierte en consulta. El navegador limita la grabación a 60 segundos y el backend a 2 MB; no se comprueba duración en servidor. HTTPS (o localhost) y MediaRecorder son necesarios; sin ellos puede usarse texto.

Los botones del asistente navegan al portal; no envían trámites. Si hay una solicitud en preparación, se conserva el diálogo de confirmación de salida existente. Para consultar una solicitud antigua, ábrela primero en Mis solicitudes. Los estados proceden de la última sincronización guardada, sin refrescar dependencias automáticamente.

## Datos y límites

Historial en memoria del navegador, borrado al recargar/cerrar sesión o limpiar conversación. Se envían hasta 12 mensajes previos al modelo. No hay almacenamiento de chat en la base. Responses usa store=false; esto no representa una garantía general de retención cero por parte del proveedor. El audio no se guarda como documento; se procesa como carga temporal HTTP. Texto máximo 2000 caracteres; respuestas hasta 4000. Límite por cuenta/dirección: 30 consultas y 15 transcripciones por 15 minutos. Sin reintentos automáticos de OpenAI.

Endpoints POST con sesión y CSRF: `/api/chatbot/message/` (message, history opcional, application_id opcional) y `/api/chatbot/transcribe/` (multipart audio). Acciones validadas por backend, renderizadas como botones; no ejecución de HTML o enlaces arbitrarios. Respuestas de IA pueden contener errores; probar preguntas de requisitos, estados, simulación y datos inexistentes antes de la demostración.

Referencias oficiales: https://developers.openai.com/api/docs/guides/speech-to-text y https://developers.openai.com/api/docs/guides/structured-outputs . GPT-Transcribe utiliza languages[] en multipart para la indicación es; no utiliza el parámetro singular language de otros modelos.
