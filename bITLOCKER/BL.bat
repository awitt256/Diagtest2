@echo off
:: Check for admin rights
net session >nul 2>&1
if %errorLevel% neq 0 (
    echo This script must be run as administrator.
    echo Attempting to relaunch with admin privileges...
    powershell -Command "Start-Process '%~f0' -Verb runAs"
    exit /b
)

echo ==========================================
echo     BitLocker Status for All Drives
echo ==========================================
echo.

manage-bde -status

echo.
echo ==========================================
echo Press any key to exit...
pause >nul
