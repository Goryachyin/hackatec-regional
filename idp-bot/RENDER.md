# Primer despliegue del bot en Render

Se incluye una imagen para OpenAI sin RapidOCR/ONNX. El Docker Compose local sigue
usando el dockerfile original. Render construye Dockerfile.render; no ejecuta Compose.

## Publicación

1. Subir el proyecto a un repositorio Git privado conectado a Render. No subir .env,
   documentos personales, private_media, SQLite ni credenciales.
2. En Render seleccionar New > Blueprint y conectar el repositorio. Usar render.yaml
   de la raíz. La plantilla crea únicamente el bot como Web Service en el plan Free.
3. Introducir OPENAI_API_KEY en Render. IDP_API_KEY se genera automáticamente:
   copiarla desde Environment al .env del backend, sin publicarla en frontend/chat.
4. Desplegar y esperar Live. Consultar https://TU-SERVICIO.onrender.com/health/.
   Debe devolver status=ok y engine=openai. No verifica saldo ni disponibilidad de OpenAI.

Alternativa manual: New > Web Service, repositorio, runtime Docker, Root Directory
vacío, Dockerfile Path=idp-bot/Dockerfile.render, Docker Build Context=idp-bot,
Health Check Path=/health/. Dejar Docker Command vacío. Configurar IDP_ENV=production,
IDP_PROVIDER=openai, OPENAI_MODEL=gpt-4.1, OPENAI_API_KEY y una IDP_API_KEY aleatoria
de al menos 32 caracteres. El contenedor escucha en 0.0.0.0 y usa PORT de Render.

## Conectar Django local

Modificar backend/.env:

```dotenv
IDP_BOT_URL=https://TU-SERVICIO.onrender.com
IDP_API_KEY=LA_MISMA_CLAVE_INTERNA_DE_RENDER
IDP_TIMEOUT=120
```

Reiniciar Django. Primero probar /health/ y luego un archivo sintético desde el
portal. Una solicitud de procesamiento sin X-IDP-Key debe devolver 401.
No usar documentos reales para comprobar conectividad. No modificar OPENAI_API_KEY
en Django: esa clave pertenece únicamente al bot.

## Límites de esta primera etapa

- El plan gratuito puede suspenderse por inactividad; no garantiza respuesta
  inmediata para una demostración. Elegir instancia pagada si se necesita siempre activa.
- Un documento simultáneo por proceso; los adicionales reciben 503 busy. No es
  todavía una configuración para miles de solicitudes.
- El bot no necesita disco persistente: procesa archivos temporalmente y devuelve JSON.
- No se requiere GPU, PostgreSQL ni Supabase para desplegar este servicio.
- El endpoint es público porque Django todavía está local. Cuando ambos estén en
  Render, conviene pasar a Private Service y usar la dirección interna.
- La imagen cloud admite únicamente IDP_PROVIDER=openai. El arranque falla si faltan
  secretos o se utiliza la clave interna de desarrollo.

Fuentes: https://render.com/docs/docker y https://render.com/docs/web-services
