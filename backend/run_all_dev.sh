#!/bin/bash
# Script para ejecutar TODOS los servicios (modo desarrollo)
# ADVERTENCIA: Esto inicia multiples procesos en paralelo

echo "========================================"
echo "BJJ MINGO - Modo Desarrollo (Todo en Uno)"
echo "========================================"
echo ""

# Activar entorno virtual
if [ -d "venv" ]; then
    source venv/bin/activate
fi

# Verificar Redis
if ! redis-cli ping >/dev/null 2>&1; then
    echo "[ERROR] Redis no esta corriendo!"
    echo "Inicia Redis primero: docker run -d --name redis-bjj -p 6379:6379 redis"
    exit 1
fi

echo "[OK] Redis verificado"
echo ""
echo "Iniciando servicios en segundo plano..."
echo ""

# Iniciar Celery Worker en background
echo "[1/3] Iniciando Celery Worker..."
celery -A app.celery_app worker --loglevel=info > celery_worker.log 2>&1 &
WORKER_PID=$!
sleep 2

# Iniciar Celery Beat en background
echo "[2/3] Iniciando Celery Beat..."
celery -A app.celery_app beat --loglevel=info > celery_beat.log 2>&1 &
BEAT_PID=$!
sleep 2

# Función para cleanup al salir
cleanup() {
    echo ""
    echo "Deteniendo servicios..."
    kill $WORKER_PID 2>/dev/null
    kill $BEAT_PID 2>/dev/null
    echo "Servicios detenidos"
    exit 0
}

trap cleanup INT TERM

# Iniciar Flask en foreground
echo "[3/3] Iniciando Flask App..."
echo ""
echo "========================================"
echo "Sistema completo iniciado!"
echo "========================================"
echo ""
echo "Procesos en background:"
echo "  - Celery Worker (PID: $WORKER_PID) - Log: celery_worker.log"
echo "  - Celery Beat (PID: $BEAT_PID) - Log: celery_beat.log"
echo "  - Flask App (foreground)"
echo ""
echo "Para detener: Presiona Ctrl+C"
echo "========================================"
echo ""

python run.py

# Cleanup al terminar Flask
cleanup
