@echo off

:: Check if running as admin
>nul 2>&1 "%SYSTEMROOT%\system32\cacls.exe" "%SYSTEMROOT%\system32\config\system"
if %errorlevel% NEQ 0 (
    echo Elevating to Administrator...
    powershell -NoProfile -ExecutionPolicy Bypass -Command "Start-Process -File '%~f0' -Verb RunAs"
    exit /b
)

:: Run the PowerShell script as admin from same folder
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0PerformanceTest.ps1"

echo.
echo Script complete. Press any key to exit...
pause >nul
``