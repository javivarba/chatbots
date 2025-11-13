@echo off
echo ============================================================
echo INSTALACION RAPIDA DE NGROK - BJJ MINGO
echo ============================================================
echo.

echo Instalando ngrok con winget...
echo.

winget install --id=ngrok.ngrok -e

echo.
echo ============================================================
echo INSTALACION COMPLETADA
echo ============================================================
echo.
echo Ahora debes:
echo 1. Cerrar y volver a abrir PowerShell/Terminal
echo 2. Ejecutar: ngrok version (para verificar)
echo 3. Crear cuenta en: https://dashboard.ngrok.com/signup
echo 4. Configurar authtoken (ver instrucciones)
echo.
echo ============================================================
pause
