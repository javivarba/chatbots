#!/bin/bash
# Script para iniciar Celery Beat (Scheduler) en Linux/Mac
# Ejecutar desde el directorio backend/

echo "========================================"
echo "Iniciando Celery Beat para BJJ Mingo"
echo "========================================"
echo ""

# Activar entorno virtual si existe
if [ -d "venv" ]; then
    echo "Activando entorno virtual..."
    source venv/bin/activate
fi

echo "Iniciando Celery Beat (Scheduler)..."
echo ""
echo "NOTA: Mantener esta terminal abierta mientras el sistema esté en uso"
echo "      Esta tarea ejecuta recordatorios cada hora"
echo "      Presionar Ctrl+C para detener"
echo ""

celery -A app.celery_app beat --loglevel=info
