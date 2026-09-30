# Despliegue del backend Django

## Preparación de Supabase

1. Crear el proyecto PostgreSQL y copiar la cadena de conexión desde **Connect**. Se usará como `DATABASE_URL`; Django fuerza SSL cuando `DJANGO_DEBUG=false`.
2. En Storage, crear un bucket privado, por ejemplo `private-documents`.
3. En la configuración S3 de Supabase, obtener el endpoint, la región y las credenciales S3. No usar la contraseña de PostgreSQL, la clave `anon` ni `service_role` como credenciales S3.

Los archivos se guardan mediante el backend S3 de `django-storages`. Las descargas siguen pasando por Django, que verifica sesión y propietario antes de leer el objeto; no se exponen URLs públicas del bucket.

## Servicio Render

Opción automatizada: New > Blueprint, conectar el repositorio y seleccionar
`backend/render.yaml` como Blueprint Path. Es una plantilla independiente del bot;
declara una instancia Starter de pago para disponer de Pre-Deploy Command y SMTP.
Revisar el costo mostrado por Render antes de crear el servicio. No se ha publicado
ningún servicio ni contratado ningún plan desde el proyecto.

Crear un Web Service separado con:

| Campo | Valor |
| --- | --- |
| Name | `hackatec-backend` |
| Branch | `main` |
| Runtime | Docker |
| Root Directory | vacío |
| Dockerfile Path | `backend/Dockerfile` |
| Docker Build Context | `backend` |
| Docker Command | vacío |
| Region | la misma del bot |
| Health Check Path | `/api/health/` |

El contenedor escucha en `PORT` de Render y ejecuta Gunicorn. El health check responde `200` solo si Django puede ejecutar una consulta a la base de datos.

## Variables de entorno

Configurar en Render, nunca en el frontend ni en archivos versionados:

| Variable | Valor |
| --- | --- |
| `DJANGO_DEBUG` | `false` |
| `DJANGO_SECRET_KEY` | clave aleatoria nueva y privada |
| `DJANGO_ALLOWED_HOSTS` | host del backend, por ejemplo `hackatec-backend.onrender.com` |
| `CSRF_TRUSTED_ORIGINS` | origen HTTPS del frontend |
| `DATABASE_URL` | cadena PostgreSQL de Supabase |
| `SUPABASE_STORAGE_ENDPOINT` | endpoint S3 de Supabase, normalmente termina en `/storage/v1/s3` |
| `SUPABASE_STORAGE_REGION` | región indicada por Supabase |
| `SUPABASE_STORAGE_BUCKET` | nombre del bucket privado |
| `SUPABASE_STORAGE_ACCESS_KEY_ID` | access key S3 de Supabase |
| `SUPABASE_STORAGE_SECRET_ACCESS_KEY` | secret S3 de Supabase |
| `IDP_BOT_URL` | URL HTTPS del servicio `hackatec-idp-bot` |
| `IDP_API_KEY` | la misma clave aleatoria de al menos 32 caracteres configurada en el bot |
| `IDP_TIMEOUT` | `120` |
| `EMAIL_BACKEND` | `django.core.mail.backends.smtp.EmailBackend` |
| `EMAIL_HOST` | host SMTP del proveedor de correo |
| `EMAIL_PORT` | puerto SMTP del proveedor |
| `EMAIL_HOST_USER` | usuario SMTP, si el proveedor lo requiere |
| `EMAIL_HOST_PASSWORD` | contraseña SMTP, si el proveedor la requiere |
| `EMAIL_USE_TLS` | `true` según el proveedor |
| `DEFAULT_FROM_EMAIL` | remitente verificado del dominio |

La aplicación rechaza el arranque de producción si faltan PostgreSQL, bucket/credenciales de Storage, una clave de bot robusta o la configuración básica de correo SMTP. Render termina TLS en el proxy; Django confía en `X-Forwarded-Proto`, redirige HTTP a HTTPS y marca las cookies de sesión y CSRF como seguras.

## Migraciones y comprobación

En un plan que admita **Pre-Deploy Command**, configurar `python manage.py migrate --noinput`. En planes sin ese comando, ejecutar la misma migración una sola vez desde un entorno controlado con el mismo commit y las variables de producción del servicio; no ejecutar migraciones concurrentemente desde cada worker al arrancar.

Después del despliegue, comprobar `https://<backend>/api/health/`. Antes de usar datos reales, validar registro y correo, login, carga/descarga autenticada en el Baúl, análisis del bot y envío de solicitudes.

PostgreSQL inicia vacío: `migrate` crea tablas, no copia usuarios ni archivos de
SQLite. No borrar la base ni los documentos locales. Para un traslado de datos
existentes se requiere una migración de datos y archivos por separado.

Para Supabase, utilizar la cadena del Session Pooler si Render no dispone de
conectividad IPv6 hacia el endpoint directo. Codificar caracteres especiales de
la contraseña en la URL. Mantener las tablas de Django fuera del acceso público
de la Data API (deshabilitar Data API si no se utiliza) y el bucket como privado.

El frontend actual conserva cookies del mismo origen. Al desplegarlo en Vercel,
configurar un rewrite `/api/:path*` hacia `https://BACKEND/api/:path*`, sin caché
de respuestas privadas, y añadir el origen del frontend a CSRF_TRUSTED_ORIGINS.
La configuración de Vercel queda pendiente; no cambiar a fetch entre dominios
sin configurar también CORS y cookies.

## Comprobación local de la imagen

Desde la raíz del proyecto:

```powershell
docker build -f backend/Dockerfile -t hackatec-backend ./backend
```

Para ejecutarla se deben proporcionar variables de producción mediante un archivo
privado con `docker run --env-file ... -p 10000:10000 hackatec-backend`. Ese arranque
no ejecuta migraciones: Render lo hace en Pre-Deploy. No incluir secretos en la
línea de comandos, en Dockerfile ni en archivos .env.example.

## Secretos previamente expuestos

Si una clave del bot o una contraseña de Supabase llegó a Git, rotarla en el proveedor y actualizar todas las variables dependientes. Retirar el valor del archivo actual no lo elimina del historial de Git. Mantener `.env`, SQLite, `.venv` y `private_media` fuera del repositorio.
