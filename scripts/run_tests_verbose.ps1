# Script para ejecutar pruebas con checkmarks
Write-Host "`n🚀 Ejecutando pruebas de exportación Excel..." -ForegroundColor Cyan
Write-Host "============================================`n" -ForegroundColor Cyan

# Activar entorno virtual
$venvPath = ".\jjenv\Scripts\Activate.ps1"
if (Test-Path $venvPath) {
    & $venvPath
    Write-Host "✅ Entorno virtual activado`n" -ForegroundColor Green
}

# Ejecutar pruebas
python manage.py test projects.tests_excel_simple --settings=core.settings_test -v 2

Write-Host "`n============================================" -ForegroundColor Cyan
Write-Host "✨ Ejecución completada" -ForegroundColor Green
