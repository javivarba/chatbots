@echo off
REM Script maestro para iniciar todos los componentes del sistema
REM Ejecutar desde el directorio backend/

echo ========================================
echo INICIANDO SISTEMA COMPLETO BJJ MINGO
echo ========================================
echo.

REM Verificar si Redis esta corriendo
echo [1/4] Verificando Redis...
redis-cli ping >nul 2>&1
if %errorlevel% neq 0 (
    echo [!] Redis no esta corriendo.
    echo.
    echo Opciones para iniciar Redis:
    echo   a) Con Docker: docker run -d --name redis-bjj -p 6379:6379 redis
    echo   b) Manualmente: Abrir redis-server.exe si esta instalado
    echo.
    echo Por favor, inicia Redis primero y luego vuelve a ejecutar este script.
    pause
    exit /b 1
) else (
    echo [OK] Redis esta corriendo
)

REM Activar entorno virtual
echo.
echo [2/4] Activando entorno virtual...
if exist venv\Scripts\activate.bat (
    call venv\Scripts\activate.bat
    echo [OK] Entorno virtual activado
) else (
    echo [!] No se encontro entorno virtual en venv\
)

REM Verificar instalacion de dependencias
echo.
echo [3/4] Verificando dependencias...
python -c "import celery; import redis" >nul 2>&1
if %errorlevel% neq 0 (
    echo [!] Faltan dependencias. Instalando...
    pip install -r requirements.txt
) else (
    echo [OK] Dependencias instaladas
)

echo.
echo [4/4] Sistema listo para iniciar
echo.
echo ========================================
echo INSTRUCCIONES
echo ========================================
echo.
echo Necesitas abrir 3 terminales separadas:
echo.
echo TERMINAL 1 - Flask App:
echo    cd backend
echo    python run.py
echo.
echo TERMINAL 2 - Celery Worker:
echo    cd backend
echo    start_celery_worker.bat
echo.
echo TERMINAL 3 - Celery Beat:
echo    cd backend
echo    start_celery_beat.bat
echo.
echo ========================================
echo.
echo Presiona cualquier tecla para ver comandos de inicio rapido...
pause >nul

echo.
echo INICIO RAPIDO - Copia y pega estos comandos:
echo.
echo === TERMINAL 1 ===
echo cd backend ^&^& python run.py
echo.
echo === TERMINAL 2 ===
echo cd backend ^&^& start_celery_worker.bat
echo.
echo === TERMINAL 3 ===
echo cd backend ^&^& start_celery_beat.bat
echo.
pause
