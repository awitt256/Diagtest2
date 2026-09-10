@echo off
setlocal

:: Batch script to run audio.ps1 as administrator

set "ps1path=%~dp0audio.ps1"

:: Check for administrative privileges
openfiles >nul 2>&1
if %errorlevel% NEQ 0 (
    echo Requesting administrative privileges...
    powershell -Command "Start-Process '%SystemRoot%\System32\WindowsPowerShell\v1.0\powershell.exe' -ArgumentList '-NoProfile','-ExecutionPolicy','Bypass','-File','%ps1path%' -WindowStyle Normal -Verb RunAs"
    exit /b
)

:: Already running as admin
powershell -NoProfile -ExecutionPolicy Bypass -File "%ps1path%"

endlocal