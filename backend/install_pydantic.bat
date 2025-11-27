@echo off
REM Script de instalación rápida de Pydantic
REM Ejecutar desde backend/

echo ============================================================
echo INSTALACION DE PYDANTIC - BJJ ACADEMY BOT
echo ============================================================
echo.

echo [1/3] Instalando Pydantic con soporte para emails...
pip install pydantic[email]==2.5.0

if %ERRORLEVEL% NEQ 0 (
    echo.
    echo ERROR: No se pudo instalar Pydantic
    pause
    exit /b 1
)

echo.
echo [2/3] Verificando instalacion...
python -c "import pydantic; print(f'Pydantic {pydantic.__version__} instalado correctamente')"

if %ERRORLEVEL% NEQ 0 (
    echo.
    echo ERROR: Pydantic no se importa correctamente
    pause
    exit /b 1
)

echo.
echo [3/3] Ejecutando tests de validacion...
python test_pydantic_validation.py

echo.
echo ============================================================
echo INSTALACION COMPLETADA
echo ============================================================
echo.
echo Proximos pasos:
echo 1. Revisar PYDANTIC_IMPLEMENTATION_GUIDE.md
echo 2. Migrar endpoints restantes en dashboard_routes.py
echo 3. Probar con servidor: python run.py
echo.

pause
