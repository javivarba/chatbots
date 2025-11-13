# Script para descargar e instalar ngrok versión actual
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host "DESCARGANDO NGROK VERSION ACTUAL" -ForegroundColor Cyan
Write-Host "============================================================`n" -ForegroundColor Cyan

# Crear carpeta
$ngrokDir = "C:\ngrok"
if (-not (Test-Path $ngrokDir)) {
    New-Item -ItemType Directory -Path $ngrokDir -Force | Out-Null
    Write-Host "[OK] Carpeta creada: $ngrokDir" -ForegroundColor Green
} else {
    Write-Host "[OK] Carpeta ya existe: $ngrokDir" -ForegroundColor Green
}

# Descargar ngrok
Write-Host "`nDescargando ngrok (ultima version)..." -ForegroundColor Yellow
$zipPath = "$ngrokDir\ngrok.zip"
$url = "https://bin.equinox.io/c/bNyj1mQVY4c/ngrok-v3-stable-windows-amd64.zip"

try {
    Invoke-WebRequest -Uri $url -OutFile $zipPath -UseBasicParsing
    Write-Host "[OK] Descarga completada" -ForegroundColor Green
} catch {
    Write-Host "[ERROR] No se pudo descargar ngrok: $_" -ForegroundColor Red
    Write-Host "`nPor favor descarga manualmente desde:" -ForegroundColor Yellow
    Write-Host "https://ngrok.com/download" -ForegroundColor Cyan
    exit 1
}

# Extraer archivo
Write-Host "`nExtrayendo archivo..." -ForegroundColor Yellow
try {
    Expand-Archive -Path $zipPath -DestinationPath $ngrokDir -Force
    Write-Host "[OK] Archivo extraido" -ForegroundColor Green

    # Eliminar zip
    Remove-Item $zipPath -Force
    Write-Host "[OK] Archivo zip eliminado" -ForegroundColor Green
} catch {
    Write-Host "[ERROR] No se pudo extraer: $_" -ForegroundColor Red
    exit 1
}

# Verificar instalación
Write-Host "`nVerificando instalacion..." -ForegroundColor Yellow
$ngrokExe = "$ngrokDir\ngrok.exe"
if (Test-Path $ngrokExe) {
    $version = & $ngrokExe version 2>&1
    Write-Host "[OK] ngrok instalado correctamente" -ForegroundColor Green
    Write-Host "    Version: $version" -ForegroundColor Cyan
} else {
    Write-Host "[ERROR] No se encontro ngrok.exe" -ForegroundColor Red
    exit 1
}

Write-Host "`n============================================================" -ForegroundColor Cyan
Write-Host "INSTALACION COMPLETADA" -ForegroundColor Green
Write-Host "============================================================`n" -ForegroundColor Cyan

Write-Host "Ubicacion: $ngrokExe" -ForegroundColor Cyan
Write-Host "`nPROXIMOS PASOS:" -ForegroundColor Yellow
Write-Host "1. Configura tu authtoken:" -ForegroundColor White
Write-Host "   C:\ngrok\ngrok.exe config add-authtoken TU_AUTHTOKEN`n" -ForegroundColor Gray
Write-Host "2. Obtén tu authtoken en:" -ForegroundColor White
Write-Host "   https://dashboard.ngrok.com/get-started/your-authtoken`n" -ForegroundColor Cyan
Write-Host "3. Inicia ngrok:" -ForegroundColor White
Write-Host "   C:\ngrok\ngrok.exe http 5000`n" -ForegroundColor Gray

Write-Host "============================================================`n" -ForegroundColor Cyan
