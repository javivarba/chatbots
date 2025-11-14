#!/bin/bash
# Script maestro para iniciar todos los componentes del sistema
# Ejecutar desde el directorio backend/

echo "========================================"
echo "INICIANDO SISTEMA COMPLETO BJJ MINGO"
echo "========================================"
echo ""

# Verificar si Redis esta corriendo
echo "[1/4] Verificando Redis..."
if redis-cli ping >/dev/null 2>&1; then
    echo "[OK] Redis esta corriendo"
else
    echo "[!] Redis no esta corriendo."
    echo ""
    echo "Opciones para iniciar Redis:"
    echo "  a) Con Docker: docker run -d --name redis-bjj -p 6379:6379 redis"
    echo "  b) Linux: sudo systemctl start redis"
    echo "  c) Mac: brew services start redis"
    echo ""
    echo "Por favor, inicia Redis primero y luego vuelve a ejecutar este script."
    exit 1
fi

# Activar entorno virtual
echo ""
echo "[2/4] Activando entorno virtual..."
if [ -d "venv" ]; then
    source venv/bin/activate
    echo "[OK] Entorno virtual activado"
else
    echo "[!] No se encontro entorno virtual en venv/"
fi

# Verificar instalacion de dependencias
echo ""
echo "[3/4] Verificando dependencias..."
if python -c "import celery; import redis" >/dev/null 2>&1; then
    echo "[OK] Dependencias instaladas"
else
    echo "[!] Faltan dependencias. Instalando..."
    pip install -r requirements.txt
fi

echo ""
echo "[4/4] Sistema listo para iniciar"
echo ""
echo "========================================"
echo "INSTRUCCIONES"
echo "========================================"
echo ""
echo "Necesitas abrir 3 terminales separadas:"
echo ""
echo "TERMINAL 1 - Flask App:"
echo "   cd backend"
echo "   python run.py"
echo ""
echo "TERMINAL 2 - Celery Worker:"
echo "   cd backend"
echo "   ./start_celery_worker.sh"
echo ""
echo "TERMINAL 3 - Celery Beat:"
echo "   cd backend"
echo "   ./start_celery_beat.sh"
echo ""
echo "========================================"
echo ""
echo "Presiona Enter para ver comandos de inicio rapido..."
read

echo ""
echo "INICIO RAPIDO - Copia y pega estos comandos:"
echo ""
echo "=== TERMINAL 1 ==="
echo "cd backend && python run.py"
echo ""
echo "=== TERMINAL 2 ==="
echo "cd backend && ./start_celery_worker.sh"
echo ""
echo "=== TERMINAL 3 ==="
echo "cd backend && ./start_celery_beat.sh"
echo ""
