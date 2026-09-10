@echo off
:: Batch file to run iwl.exe as administrator

:: Check if script is already running as admin
net session >nul 2>&1
if %errorlevel% neq 0 (
    echo Requesting administrator privileges...
    powershell -Command "Start-Process '%~f0' -Verb RunAs"
    exit /b
)

:: Run iwl.exe from same folder as this script
echo Launching iwl.exe as administrator...
start "" "%~dp0iwl.exe"

exit /b
