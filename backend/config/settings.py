import os
from pathlib import Path
from dotenv import load_dotenv
import dj_database_url

BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(BASE_DIR / '.env')
DEBUG = os.getenv('DJANGO_DEBUG', 'true').lower() == 'true'
SECRET_KEY = os.getenv('DJANGO_SECRET_KEY', '')
if not SECRET_KEY:
    if not DEBUG:
        raise RuntimeError('Configura DJANGO_SECRET_KEY para producción.')
    SECRET_KEY = 'development-only-do-not-use-in-production-hackatec'
ALLOWED_HOSTS = [host.strip() for host in os.getenv('DJANGO_ALLOWED_HOSTS', 'localhost,127.0.0.1,testserver').split(',') if host.strip()]
INSTALLED_APPS = ['django.contrib.auth', 'django.contrib.contenttypes', 'django.contrib.sessions', 'portal']
MIDDLEWARE = ['django.middleware.security.SecurityMiddleware', 'django.contrib.sessions.middleware.SessionMiddleware', 'django.middleware.common.CommonMiddleware', 'django.middleware.csrf.CsrfViewMiddleware', 'django.contrib.auth.middleware.AuthenticationMiddleware', 'django.middleware.clickjacking.XFrameOptionsMiddleware']
ROOT_URLCONF = 'config.urls'
WSGI_APPLICATION = 'config.wsgi.application'
DATABASE_URL = os.getenv('DATABASE_URL', '').strip()
if DATABASE_URL:
    DATABASES = {'default': dj_database_url.parse(DATABASE_URL, conn_max_age=600, conn_health_checks=True, ssl_require=not DEBUG)}
    if not DEBUG and DATABASES['default']['ENGINE'] != 'django.db.backends.postgresql':
        raise RuntimeError('Producción requiere PostgreSQL.')
elif DEBUG:
    DATABASES = {'default': {'ENGINE': 'django.db.backends.sqlite3', 'NAME': BASE_DIR / 'db.sqlite3'}}
else:
    raise RuntimeError('Configura DATABASE_URL de PostgreSQL para producción.')
AUTH_USER_MODEL = 'portal.User'
AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator', 'OPTIONS': {'min_length': 10}},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]
LANGUAGE_CODE = 'es-mx'
TIME_ZONE = 'America/Mexico_City'
USE_TZ = True
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'
MEDIA_ROOT = Path(os.getenv('PRIVATE_MEDIA_ROOT', BASE_DIR / 'private_media'))
if not DEBUG:
    storage_settings = {
        'endpoint_url': os.getenv('SUPABASE_STORAGE_ENDPOINT', '').strip(),
        'bucket_name': os.getenv('SUPABASE_STORAGE_BUCKET', '').strip(),
        'access_key': os.getenv('SUPABASE_STORAGE_ACCESS_KEY_ID', '').strip(),
        'secret_key': os.getenv('SUPABASE_STORAGE_SECRET_ACCESS_KEY', '').strip(),
    }
    if not all(storage_settings.values()):
        raise RuntimeError('Configura el endpoint, bucket y credenciales S3 de Supabase Storage para producción.')
    STORAGES = {
        'default': {
            'BACKEND': 'storages.backends.s3.S3Storage',
            'OPTIONS': {
                **storage_settings,
                'region_name': os.getenv('SUPABASE_STORAGE_REGION', 'us-east-1'),
                'default_acl': None,
                'querystring_auth': True,
                'file_overwrite': False,
                'signature_version': 's3v4',
                'addressing_style': 'path',
                'object_parameters': {'CacheControl': 'private, no-store'},
            },
        },
        'staticfiles': {'BACKEND': 'django.contrib.staticfiles.storage.StaticFilesStorage'},
    }
DATA_UPLOAD_MAX_MEMORY_SIZE = 12 * 1024 * 1024
FILE_UPLOAD_MAX_MEMORY_SIZE = 2 * 1024 * 1024
CSRF_TRUSTED_ORIGINS = [origin.strip() for origin in os.getenv('CSRF_TRUSTED_ORIGINS', 'http://localhost:5173,http://127.0.0.1:5173').split(',') if origin.strip()]
SESSION_COOKIE_HTTPONLY = True
SESSION_COOKIE_SAMESITE = 'Lax'
SESSION_COOKIE_SECURE = not DEBUG
CSRF_COOKIE_SECURE = not DEBUG
SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')
SECURE_SSL_REDIRECT = not DEBUG
SECURE_HSTS_SECONDS = 31536000 if not DEBUG else 0
SECURE_CONTENT_TYPE_NOSNIFF = True
EMAIL_BACKEND = os.getenv('EMAIL_BACKEND', 'django.core.mail.backends.console.EmailBackend' if DEBUG else 'django.core.mail.backends.smtp.EmailBackend')
EMAIL_HOST = os.getenv('EMAIL_HOST', '')
EMAIL_PORT = int(os.getenv('EMAIL_PORT', '587'))
EMAIL_HOST_USER = os.getenv('EMAIL_HOST_USER', '')
EMAIL_HOST_PASSWORD = os.getenv('EMAIL_HOST_PASSWORD', '')
EMAIL_USE_TLS = os.getenv('EMAIL_USE_TLS', 'true').lower() == 'true'
EMAIL_TIMEOUT = 20
DEFAULT_FROM_EMAIL = os.getenv('DEFAULT_FROM_EMAIL', 'registro@localhost')
IDP_BOT_URL = os.getenv('IDP_BOT_URL', 'https://hackatec-idp-bot.onrender.com').rstrip('/')
IDP_API_KEY = os.getenv('IDP_API_KEY', 'local-development-key' if DEBUG else '')
IDP_TIMEOUT = int(os.getenv('IDP_TIMEOUT', '120'))

EMAIL_DEMO_MODE = os.getenv('EMAIL_DEMO_MODE', 'false').lower() == 'true'
if EMAIL_DEMO_MODE:
    EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'

if not DEBUG:
    if not IDP_BOT_URL.startswith(('https://', 'http://')):
        raise RuntimeError('IDP_BOT_URL debe ser una URL HTTP interna o HTTPS pública.')
    if len(IDP_API_KEY.strip()) < 32:
        raise RuntimeError('Configura IDP_API_KEY con al menos 32 caracteres aleatorios.')
    if EMAIL_BACKEND == 'django.core.mail.backends.console.EmailBackend' and not EMAIL_DEMO_MODE:
        raise RuntimeError('Configura un proveedor de correo para producción.')
    if EMAIL_BACKEND == 'django.core.mail.backends.smtp.EmailBackend' and (
        not EMAIL_HOST.strip() or not os.getenv('DEFAULT_FROM_EMAIL', '').strip()
    ):
        raise RuntimeError('Configura EMAIL_HOST y DEFAULT_FROM_EMAIL para producción.')
