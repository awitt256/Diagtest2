@echo off
REM Setup Auto Git Upload - Runs SetupScheduledUpload.ps1 as Administrator

title Setup Auto Git Upload
color 0A

echo.
echo ========================================
echo   Setting up Auto Git Upload Task
echo ========================================
echo.

cd /d "%~dp0"

REM Run PowerShell script with admin privileges
powershell -Command "Start-Process powershell -ArgumentList '-NoProfile -ExecutionPolicy Bypass -File \""%~dp0SetupScheduledUpload.ps1\"\"' -Verb RunAs -Wait"

pause
