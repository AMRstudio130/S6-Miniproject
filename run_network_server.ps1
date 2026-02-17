# Start Django development server on all network interfaces
# This makes the app accessible from other devices on the network

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  DR AI Vision - Network Access Setup" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "Your machine IP: 192.168.20.2" -ForegroundColor Yellow
Write-Host ""
Write-Host "Starting server on 0.0.0.0:8000 (all interfaces)" -ForegroundColor Green
Write-Host "Other devices can access at:" -ForegroundColor Green
Write-Host "  http://192.168.20.2:8000" -ForegroundColor Cyan
Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Change to project directory
Set-Location $PSScriptRoot

# Start the server
python manage.py runserver 0.0.0.0:8000

Read-Host "Press Enter to exit"
