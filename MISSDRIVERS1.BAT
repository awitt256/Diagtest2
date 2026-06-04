@echo off
setlocal enabledelayedexpansion

echo Checking for missing drivers in Device Manager...
echo.

REM Use PowerShell to get devices with ConfigManagerErrorCode != 0 (missing drivers)
powershell -Command "Get-PnpDevice | Where-Object { $_.ConfigManagerErrorCode -ne 0 } | Select-Object Name, Status, ConfigManagerErrorCode | Format-Table -AutoSize"

echo.
set /p choice="Were missing drivers found? (Y/N): "
if /i "%choice%"=="Y" (
if exist "WindowsUpdate.bat" (
echo Running WindowsUpdate.bat...
call WindowsUpdate.bat
) else (
echo WindowsUpdate.bat not found.
)
) else (
goto menu
)

:menu
echo Returning to menu...
REM Add your menu code here or call the main script's menu
pause
exit /b