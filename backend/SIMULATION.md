# Simulación documental

Permite probar el Baúl y solicitudes sin llamar al bot ni consumir la API. No extrae datos ni acredita autenticidad. Usa archivos ficticios PDF/JPG/PNG; siguen aplicando límites de tamaño y formato.

Desde la raíz del proyecto, con el entorno virtual activo:

```powershell
python backend/manage.py migrate
python backend/manage.py document_simulation correo-de-la-cuenta@example.com --enable
```

La cuenta debe existir. El comando no crea usuarios, no evita la verificación de correo y no otorga permisos de administrador.

En backend/.env (local) o variables de entorno del backend en Render:

```dotenv
DOCUMENT_SIMULATION_ENABLED=true
```

Reinicia Django (o redespliega en Render) y recarga el portal. Ambas condiciones son necesarias: interruptor del servidor y permiso por cuenta. No agregues esta variable al frontend ni al bot.

Los archivos cargados, actualizados o reanalizados por esa cuenta llevan la etiqueta Revisión simulada. Se registra origen, usuario y fecha, sin datos extraídos ficticios. Las solicitudes que los incluyen se identifican como Demostración y generan folios DEMO. La revisión de documentos de solicitudes enviadas no se modifica; actualiza el documento para generar otra versión.

Para revocar el permiso:

```powershell
python backend/manage.py document_simulation correo-de-la-cuenta@example.com
```

Para apagarlo globalmente, configura DOCUMENT_SIMULATION_ENABLED=false y reinicia. Los documentos simulados quedan visibles pero no pueden adjuntarse ni satisfacer requisitos al enviar nuevas solicitudes. Reanalízalos con el bot o reemplázalos. Los expedientes de demostración enviados conservan su etiqueta histórica.

En Render ejecuta migrate y el comando de autorización en la Shell del servicio (desde /app usa python manage.py). El interruptor está desactivado por defecto. No se selecciona ni autoriza automáticamente ninguna cuenta.
