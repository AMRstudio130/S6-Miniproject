@echo off
REM Start Django development server on all network interfaces
REM This makes the app accessible from other devices on the network

echo.
echo ========================================
echo  DR AI Vision - Network Access Setup
echo ========================================
echo.
echo Your machine IP: 192.168.20.2
echo.
echo Starting server on 0.0.0.0:8000 (all interfaces)
echo Other devices can access at:
echo   http://192.168.20.2:8000
echo.
echo ========================================
echo.

cd /d "%~dp0"
python manage.py runserver 0.0.0.0:8000

pause
