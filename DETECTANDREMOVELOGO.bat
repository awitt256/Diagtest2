@echo off
:: Check if already running as admin
net session >nul 2>&1
if %errorlevel% == 0 goto :run

:: Re-launch as admin
echo Requesting Administrator privileges...
powershell -Command "Start-Process cmd -ArgumentList '/c \"%~f0\"' -Verb RunAs"
exit /b

:run
:: Run the PowerShell script from the same directory as this bat file
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0detectlogo1.ps1"
pause