"""Arranque del contenedor de Render usando el puerto asignado."""
import os
import uvicorn

if __name__ == '__main__':
    uvicorn.run('main:app', host='0.0.0.0', port=int(os.getenv('PORT', '10000')),
                workers=1, limit_concurrency=8, timeout_graceful_shutdown=100)
