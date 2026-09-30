# Frontend en Vercel

1. Importar el repositorio de GitHub en Vercel (Add New > Project).
2. Root Directory: frontend. Framework Preset: Vite.
3. Install Command: npm ci. Build Command: npm run build. Output Directory: dist.
4. Configurar el rewrite /api/:path* hacia la URL real de Django en vercel.json.
   Conservar /api/ en el destino. No apuntar al bot.
5. Desplegar y copiar el origen HTTPS de producción asignado por Vercel.
6. En Render, añadir ese origen exacto a CSRF_TRUSTED_ORIGINS (sin barra final).
   Mantener DJANGO_ALLOWED_HOSTS con el dominio del backend, sin https://.
7. Guardar los cambios de Render y comprobar desde Vercel /api/health/ y
   /api/auth/session/. Luego probar login, carga y descarga de un documento de
   prueba y una solicitud. Con EMAIL_DEMO_MODE=true, los códigos están en los
   logs del backend en Render y no se envían por correo.

La aplicación llama a /api/ en el mismo origen. Vercel funciona como proxy;
no se agregan claves de OpenAI, Supabase ni IDP al frontend. Las respuestas de
API no deben almacenarse en caché. El proxy de vite.config.js es solo local.
Los despliegues Preview tienen otros dominios: no autorizar indiscriminadamente
todos los subdominios de vercel.app en CSRF_TRUSTED_ORIGINS.

Un despliegue estático correcto no confirma el flujo completo: verificar cookies,
CSRF, tamaño de cargas y tiempos del análisis contra Render antes de la demo.
