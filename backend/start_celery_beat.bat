@echo off
REM Script para iniciar Celery Beat (Scheduler) en Windows
REM Ejecutar desde el directorio backend/

echo ========================================
echo Iniciando Celery Beat para BJJ Mingo
echo ========================================
echo.

REM Activar entorno virtual si existe
if exist venv\Scripts\activate.bat (
    echo Activando entorno virtual...
    call venv\Scripts\activate.bat
)

echo Iniciando Celery Beat (Scheduler)...
echo.
echo NOTA: Mantener esta ventana abierta mientras el sistema esté en uso
echo       Esta tarea ejecuta recordatorios cada hora
echo       Presionar Ctrl+C para detener
echo.

celery -A app.celery_app beat --loglevel=info

pause
