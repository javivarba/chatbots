Write-Host "`n=== VERIFICACIÓN DE ESTRUCTURA DEL PROYECTO ===" -ForegroundColor Cyan

$baseDir = "C:\Users\javiv\OneDrive\Desktop\Proyectos\bjj-chatbot\bjj-academy-bot"
$requiredFiles = @{
    "Backend Core" = @(
        "backend\app\__init__.py",
        "backend\app\config.py",
        "backend\run.py",
        "backend\.env"
    )
    "Models" = @(
        "backend\app\models\__init__.py",
        "backend\app\models\academy.py",
        "backend\app\models\lead.py",
        "backend\app\models\conversation.py"
    )
    "Services" = @(
        "backend\app\services\__init__.py",
        "backend\app\services\message_processor.py",
        "backend\app\services\ai_service.py"
    )
    "Webhooks" = @(
        "backend\app\api\webhooks\__init__.py",
        "backend\app\api\webhooks\whatsapp_webhook.py"
    )
    "Database" = @(
        "backend\bjj_academy.db",
        "backend\migrations\"
    )
    "Testing" = @(
        "backend\simulate_whatsapp.py",
        "backend\check_db.py",
        "backend\test_complete_system.py"
    )
}

$totalFiles = 0
$foundFiles = 0

foreach($category in $requiredFiles.Keys) {
    Write-Host "`n$category" -ForegroundColor Yellow
    foreach($file in $requiredFiles[$category]) {
        $fullPath = Join-Path $baseDir $file
        $totalFiles++
        if(Test-Path $fullPath) {
            Write-Host "  ✅ $file" -ForegroundColor Green
            $foundFiles++
        } else {
            Write-Host "  ❌ $file" -ForegroundColor Red
        }
    }
}

Write-Host "`n=== RESUMEN ===" -ForegroundColor Cyan
Write-Host "Archivos encontrados: $foundFiles/$totalFiles" -ForegroundColor $(if($foundFiles -eq $totalFiles){"Green"}else{"Yellow"})
$percentage = [math]::Round(($foundFiles/$totalFiles)*100)
Write-Host "Completitud: $percentage%" -ForegroundColor $(if($percentage -ge 90){"Green"}elseif($percentage -ge 70){"Yellow"}else{"Red"})
