# Portal de dependencias · demostración web

Aplicación Django independiente del portal ciudadano, con su propia base de datos y usuarios. Se publica como un servicio Docker en Render; sirve tanto la interfaz de revisores como la API. No necesita otro frontend en Vercel, bot ni credenciales de OpenAI.

## Alcance de la demostración

- Licencia de funcionamiento, nueve documentos y tres áreas: Protección Civil, Obras Públicas y Ecología.
- El ciudadano registra la solicitud y luego pulsa **Enviar a dependencias**, confirmando que los archivos son ficticios. No se transfieren automáticamente los documentos de cuentas normales.
- Solo se admiten expedientes con todos los documentos marcados como simulados. La marca de simulación no elimina datos personales del contenido: usar archivos ficticios.
- El envío conserva el folio, usa identificadores reproducibles y transfiere una copia de cada archivo. Puede reanudarse desde el último archivo confirmado; una repetición no duplica el expediente.
- Cada área ve sus documentos y los generales. La resolución guarda revisor, fecha y observaciones. Rechazar requiere motivo. Una resolución emitida es definitiva en esta demo.
- El ciudadano pulsa **Actualizar estado** para recuperar las decisiones. Tres aprobaciones producen aprobación simulada; cualquier rechazo produce rechazo. No hay webhook ni actualización automática en esta versión.
- Los archivos privados se guardan en PostgreSQL como binarios: se mantienen entre despliegues sin disco persistente. Es una simplificación para una demo pequeña (máximo 10 MB por archivo), no una arquitectura para miles de expedientes; para ese volumen se debe migrar a almacenamiento de objetos privado.

## 1. Publicar el código

Subir al repositorio los cambios de `backend`, `frontend` y `dependencias`, incluyendo las migraciones `0003`, `0004` del portal y `receiver/migrations/0001_initial.py`. No incluir archivos `.env`, documentos personales ni bases SQLite.

El despliegue del backend ciudadano debe ejecutar `python manage.py migrate --noinput` antes de servir la versión nueva. Redeplegar también el frontend Vercel.

## 2. Crear una base de datos independiente

Crear otra base PostgreSQL para dependencias. No reutilizar el mismo DATABASE_URL del portal ciudadano: ambas aplicaciones tienen usuarios y migraciones diferentes.

Puede ser PostgreSQL de Render o un proyecto Supabase separado. Usar la conexión accesible desde Render; con Supabase puede usarse su Session pooler. Guardar el connection string completo en DATABASE_URL del nuevo servicio, nunca en Git.

## 3. Crear el servicio Render

Opción Blueprint: crear un Blueprint desde el repositorio y seleccionar `dependencias/render.yaml`. Declara un servicio **Starter de pago**; revisar el costo mostrado antes de crear. La base de datos se configura aparte, no la crea el Blueprint.

Opción manual: New → Web Service → repositorio existente:

| Campo | Valor |
|---|---|
| Name | `hackatec-dependencias` (o un nombre disponible) |
| Language | Docker |
| Root Directory | dejar vacío |
| Dockerfile Path | `./dependencias/Dockerfile` |
| Docker Build Context Directory | `./dependencias` |
| Docker Command | dejar vacío; utiliza el CMD del Dockerfile |
| Health Check Path | `/health/` |
| Pre-Deploy Command | `python manage.py migrate --noinput` |

Esta receta usa un plan con pre-deploy y Shell para crear revisores. No cambiar simplemente a Free sin preparar una alternativa para migraciones y creación de usuarios.

Variables del nuevo servicio (reemplazar el dominio por el asignado realmente):

```dotenv
DJANGO_DEBUG=false
DJANGO_SECRET_KEY=<clave aleatoria exclusiva de Django>
DJANGO_ALLOWED_HOSTS=<dominio-real>.onrender.com
CSRF_TRUSTED_ORIGINS=https://<dominio-real>.onrender.com
DATABASE_URL=<connection string de la NUEVA base PostgreSQL>
INTEGRATION_SOURCE=portal-render-demo
INTEGRATION_KEY=<secreto aleatorio compartido de al menos 32 caracteres>
```

Generar secretos distintos con `python -c "import secrets; print(secrets.token_urlsafe(48))"`. Compartir únicamente la clave de integración entre los dos backends; no ponerla en Vercel ni enviarla al navegador. No usar la clave de OpenAI ni la del bot.

La URL se asigna en Render; el nombre sugerido no garantiza un dominio disponible. Confirmar `/health/` devuelve `{"status":"ok"}`.

## 4. Crear revisores

En la Shell del nuevo servicio (`/app`):

```sh
python manage.py create_reviewer proteccion proteccion_civil
python manage.py create_reviewer obras obras_publicas
python manage.py create_reviewer ecologia ecologia
```

Cada comando solicita una contraseña de al menos 12 caracteres sin mostrarla. No hay contraseñas predeterminadas. Entrar en `https://<dominio-real>.onrender.com/login/` con la cuenta del área. Para un operador que revise las tres áreas se puede crear un superusuario con `python manage.py createsuperuser`; no es necesario para el flujo habitual.

## 5. Conectar Django ciudadano

En las variables del servicio **hackatec-backend**:

```dotenv
DOCUMENT_SIMULATION_ENABLED=true
DEPENDENCIES_URL=https://<dominio-real>.onrender.com
DEPENDENCIES_KEY=<mismo valor que INTEGRATION_KEY>
DEPENDENCIES_SOURCE=portal-render-demo
```

Guardar y redeplegar. En su Shell, autorizar una cuenta ciudadana existente:

```sh
python manage.py document_simulation CORREO_DE_LA_CUENTA --enable
```

No se cambia la configuración del bot. El frontend existente conserva su proxy a Django. La clave nunca se entrega al frontend.

## 6. Ensayo en dos navegadores/computadoras

1. En el portal ciudadano Vercel, iniciar sesión con la cuenta de demostración y cargar archivos ficticios.
2. Registrar Licencia de funcionamiento con sus nueve documentos simulados. Se genera un folio DEMO.
3. Abrir la solicitud, confirmar archivos ficticios y pulsar **Enviar a dependencias**. Esperar hasta que el expediente esté recibido. Si se interrumpe, **Continuar envío**.
4. En el portal nuevo, iniciar sesión como Protección Civil; actualizar la bandeja, abrir el folio, descargar un documento y aprobar.
5. En el portal ciudadano, **Actualizar estado**: debe aparecer únicamente esa área aprobada.
6. Repetir con Obras Públicas y Ecología. Tres aprobaciones completan el resultado.
7. Para probar rechazo, crear una segunda solicitud; rechazar desde un área con observaciones. Consultar el estado en el portal ciudadano.

Las solicitudes anteriores con documentos de validación real o mezcla de tipos no pueden transferirse con este modo. Crear otra solicitud con archivos ficticios; no modificar expedientes ya enviados.

## Contrato y fallos

Todas las llamadas servidor-servidor utilizan HTTPS, `X-Integration-Key` y `X-Source`. Cada instalación receptora acepta el origen configurado. Para una demo local separada con otra identidad se requiere otra instancia receptora; esta versión configura una sola pareja de instalaciones.

| Método y ruta | Función |
|---|---|
| `POST /api/expedientes/{uuid}/` | Registrar folio, marca demo, trámite y manifiesto de documentos |
| `POST /api/expedientes/{uuid}/documentos/{doc_uuid}/` | Enviar JSON con `name` y `content` base64 (archivo completo) |
| `POST /api/expedientes/{uuid}/confirmar/` | Habilitar revisión solo cuando están los nueve documentos |
| `GET /api/expedientes/{uuid}/` | Recuperar estado general y estados/observaciones por área |

El identificador remoto se deriva del origen + UUID local. Los identificadores de copias documentales se derivan del expediente + UUID del documento, de modo que el mismo documento pueda utilizarse en diferentes solicitudes sin colisiones. Un folio no es una credencial.

401/403: revisar que clave y origen coincidan. 409: expediente/documento incompatible o resolución ya emitida. Una transferencia incompleta no aparece en la bandeja. Un fallo de red no borra la solicitud del ciudadano; el avance queda en `Delivery`.

No hay worker de reintentos automático ni notificaciones en segundo plano. Cambiar la URL/origen de una entrega iniciada está bloqueado para evitar duplicarla en otro destino. Para esta demo, crear una nueva solicitud si se cambia de instalación.

## Verificación local aislada

Con dependencias Python instaladas, usar SQLite de prueba y claves ficticias de prueba; no apuntar las pruebas a la base de producción:

```powershell
$env:DJANGO_DEBUG='true'
$env:DATABASE_URL=''
$env:DJANGO_ALLOWED_HOSTS='localhost,127.0.0.1,testserver'
$env:INTEGRATION_KEY='test-only-integration-key-32-characters'
python dependencias/manage.py test receiver --noinput
python backend/manage.py test portal --noinput
npm --prefix frontend run build
```

Referencias: [Docker en Render](https://render.com/docs/docker), [Blueprints](https://render.com/docs/blueprint-spec).
