# Verificar instalación de ngrok
Write-Host "`n========================================" -ForegroundColor Cyan
Write-Host "VERIFICACION DE NGROK" -ForegroundColor Cyan
Write-Host "========================================`n" -ForegroundColor Cyan

$ngrokPath = "C:\ngrok\ngrok.exe"

if (Test-Path $ngrokPath) {
    Write-Host "[OK] ngrok.exe encontrado en: $ngrokPath" -ForegroundColor Green

    try {
        $version = & $ngrokPath version 2>&1
        Write-Host "[OK] Version: $version" -ForegroundColor Green

        Write-Host "`n========================================" -ForegroundColor Cyan
        Write-Host "NGROK ESTA LISTO PARA USAR" -ForegroundColor Green
        Write-Host "========================================`n" -ForegroundColor Cyan

        Write-Host "PROXIMOS PASOS:`n" -ForegroundColor Yellow
        Write-Host "1. Configura tu authtoken (si aun no lo has hecho):" -ForegroundColor White
        Write-Host "   C:\ngrok\ngrok.exe config add-authtoken TU_AUTHTOKEN`n" -ForegroundColor Gray

        Write-Host "2. Obtén tu authtoken en:" -ForegroundColor White
        Write-Host "   https://dashboard.ngrok.com/get-started/your-authtoken`n" -ForegroundColor Cyan

        Write-Host "3. Inicia Flask (en una terminal):" -ForegroundColor White
        Write-Host "   cd backend" -ForegroundColor Gray
        Write-Host "   python app.py`n" -ForegroundColor Gray

        Write-Host "4. Inicia ngrok (en OTRA terminal):" -ForegroundColor White
        Write-Host "   C:\ngrok\ngrok.exe http 5000`n" -ForegroundColor Gray

    } catch {
        Write-Host "[ERROR] No se pudo ejecutar ngrok: $_" -ForegroundColor Red
        Write-Host "`nWindows Defender puede estar bloqueandolo." -ForegroundColor Yellow
        Write-Host "Verifica que agregaste la excepcion para C:\ngrok" -ForegroundColor Yellow
    }
} else {
    Write-Host "[ERROR] ngrok.exe NO encontrado en: $ngrokPath" -ForegroundColor Red
    Write-Host "`nEjecuta: .\descargar_ngrok.ps1" -ForegroundColor Yellow
}

Write-Host "`n========================================`n" -ForegroundColor Cyan
