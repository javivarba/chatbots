@echo off
REM Script para ejecutar TODOS los servicios en una sola ventana (modo desarrollo)
REM ADVERTENCIA: Esto inicia multiples procesos en paralelo

echo ========================================
echo BJJ MINGO - Modo Desarrollo (Todo en Uno)
echo ========================================
echo.

REM Activar entorno virtual
if exist venv\Scripts\activate.bat (
    call venv\Scripts\activate.bat
)

REM Verificar Redis
redis-cli ping >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] Redis no esta corriendo!
    echo Inicia Redis primero: docker run -d --name redis-bjj -p 6379:6379 redis
    pause
    exit /b 1
)

echo [OK] Redis verificado
echo.
echo Iniciando servicios en segundo plano...
echo.

REM Iniciar Celery Worker en background
echo [1/3] Iniciando Celery Worker...
start "Celery Worker" cmd /k "celery -A app.celery_app worker --loglevel=info --pool=solo"
timeout /t 2 >nul

REM Iniciar Celery Beat en background
echo [2/3] Iniciando Celery Beat...
start "Celery Beat" cmd /k "celery -A app.celery_app beat --loglevel=info"
timeout /t 2 >nul

REM Iniciar Flask en esta ventana
echo [3/3] Iniciando Flask App...
echo.
echo ========================================
echo Sistema completo iniciado!
echo ========================================
echo.
echo Ventanas abiertas:
echo   - Celery Worker (procesa tareas)
echo   - Celery Beat (scheduler)
echo   - Flask App (esta ventana)
echo.
echo Para detener: Cierra todas las ventanas o presiona Ctrl+C
echo ========================================
echo.

python run.py
