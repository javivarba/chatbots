#!/bin/bash
# Script para iniciar Celery Worker en Linux/Mac
# Ejecutar desde el directorio backend/

echo "========================================"
echo "Iniciando Celery Worker para BJJ Mingo"
echo "========================================"
echo ""

# Activar entorno virtual si existe
if [ -d "venv" ]; then
    echo "Activando entorno virtual..."
    source venv/bin/activate
fi

echo "Iniciando Celery Worker..."
echo ""
echo "NOTA: Mantener esta terminal abierta mientras el sistema esté en uso"
echo "      Presionar Ctrl+C para detener"
echo ""

celery -A app.celery_app worker --loglevel=info
