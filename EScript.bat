@echo off
:: Check for administrative privileges
net session >nul 2>&1
if %errorlevel% neq 0 (
    echo Requesting administrative privileges...
    powershell -Command "Start-Process '%~f0' -Verb RunAs"
    exit /b
)

:: Run the PowerShell script
echo Running EnrollTest.ps1 as Administrator...
powershell -ExecutionPolicy Bypass -NoProfile -File "EnrollTest.ps1"
pause