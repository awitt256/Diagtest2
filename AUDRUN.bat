
@echo off
:: Batch script to run AUDIO3.PS1 as administrator
set "ps1path=%~dp0AUDIO3.ps1"

:: Check if running as admin
openfiles >nul 2>&1
if %errorlevel% neq 0 (
    echo Requesting administrative privileges...
    powershell -Command "Start-Process cmd -ArgumentList '/c, %~f0' -Verb RunAs"
    exit /b
)

:: Run the PowerShell script as admin
powershell -NoProfile -ExecutionPolicy Bypass -File "%ps1path%"
pause
