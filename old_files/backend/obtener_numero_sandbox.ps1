# Script para obtener y actualizar el número del Sandbox de Twilio
Write-Host "`n========================================" -ForegroundColor Cyan
Write-Host "ACTUALIZAR NUMERO DE TWILIO SANDBOX" -ForegroundColor Cyan
Write-Host "========================================`n" -ForegroundColor Cyan

Write-Host "Ya que pudiste interactuar con el chat, el Sandbox esta configurado." -ForegroundColor Green
Write-Host "Solo necesitamos actualizar el numero en el archivo .env`n" -ForegroundColor Yellow

Write-Host "PASO 1: Obtener el numero del Sandbox" -ForegroundColor Cyan
Write-Host "---------------------------------------`n" -ForegroundColor Cyan

Write-Host "Abre tu navegador y ve a:" -ForegroundColor White
Write-Host "https://console.twilio.com/us1/develop/sms/settings/whatsapp-sandbox`n" -ForegroundColor Cyan

Write-Host "En esa pagina, busca 'Sandbox Phone Number' o 'Your Sandbox Number'" -ForegroundColor White
Write-Host "Ejemplos: +1 415 523 8886, +1 202 759 9459, etc.`n" -ForegroundColor Gray

$sandboxNumber = Read-Host "Pega aqui el numero del Sandbox (incluye el +)"

if (-not $sandboxNumber) {
    Write-Host "`n[X] No proporcionaste un numero." -ForegroundColor Red
    exit 1
}

# Limpiar el número
$sandboxNumber = $sandboxNumber.Trim().Replace(" ", "").Replace("-", "")
if (-not $sandboxNumber.StartsWith("+")) {
    $sandboxNumber = "+" + $sandboxNumber
}

Write-Host "`n[OK] Numero limpio: $sandboxNumber" -ForegroundColor Green
Write-Host "Formato para .env: whatsapp:$sandboxNumber`n" -ForegroundColor Cyan

# Actualizar .env
$envPath = Join-Path $PSScriptRoot ".env"

if (-not (Test-Path $envPath)) {
    Write-Host "[X] No se encontro el archivo .env en: $envPath" -ForegroundColor Red
    exit 1
}

Write-Host "Actualizando archivo .env..." -ForegroundColor Yellow

try {
    $content = Get-Content $envPath -Raw
    $newValue = "TWILIO_WHATSAPP_NUMBER=whatsapp:$sandboxNumber"

    if ($content -match "TWILIO_WHATSAPP_NUMBER=.*") {
        $oldValue = $Matches[0]
        $content = $content -replace "TWILIO_WHATSAPP_NUMBER=.*", $newValue

        Set-Content -Path $envPath -Value $content -NoNewline

        Write-Host "[OK] Archivo .env actualizado!" -ForegroundColor Green
        Write-Host "`nAnterior: $oldValue" -ForegroundColor Gray
        Write-Host "Nuevo:    $newValue" -ForegroundColor Green
    } else {
        Write-Host "[!] No se encontro TWILIO_WHATSAPP_NUMBER en .env" -ForegroundColor Yellow
        Write-Host "Agregando al final del archivo..." -ForegroundColor Yellow

        Add-Content -Path $envPath -Value "`n$newValue"
        Write-Host "[OK] Linea agregada!" -ForegroundColor Green
    }

    Write-Host "`n========================================" -ForegroundColor Cyan
    Write-Host "CONFIGURACION COMPLETADA" -ForegroundColor Green
    Write-Host "========================================`n" -ForegroundColor Cyan

    Write-Host "PROXIMO PASO:" -ForegroundColor Yellow
    Write-Host "Ejecuta el test nuevamente para confirmar:" -ForegroundColor White
    Write-Host "  python test_full_flow.py`n" -ForegroundColor Gray

    Write-Host "O prueba enviando un mensaje real de WhatsApp:" -ForegroundColor White
    Write-Host "  Desde +50670150369 al numero del Sandbox" -ForegroundColor Gray
    Write-Host "  Mensaje: 'Quiero agendar una clase de prueba'`n" -ForegroundColor Gray

} catch {
    Write-Host "[X] Error actualizando .env: $_" -ForegroundColor Red
    exit 1
}

Write-Host "========================================`n" -ForegroundColor Cyan
