@echo off
REM Script para iniciar Celery Worker en Windows
REM Ejecutar desde el directorio backend/

echo ========================================
echo Iniciando Celery Worker para BJJ Mingo
echo ========================================
echo.

REM Activar entorno virtual si existe
if exist venv\Scripts\activate.bat (
    echo Activando entorno virtual...
    call venv\Scripts\activate.bat
)

echo Iniciando Celery Worker...
echo.
echo NOTA: Mantener esta ventana abierta mientras el sistema esté en uso
echo       Presionar Ctrl+C para detener
echo.

celery -A app.celery_app worker --loglevel=info --pool=solo

pause
