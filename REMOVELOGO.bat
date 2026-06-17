@echo off
:: Run detectandremovecustomlogo.ps1 as Administrator

:: Check if already running as admin
net session >nul 2>&1
if %errorlevel% == 0 goto :run

:: Re-launch this BAT elevated via PowerShell
echo Requesting Administrator privileges...
powershell -Command "Start-Process -FilePath 'cmd.exe' -ArgumentList '/c \"%~f0\"' -Verb RunAs"
exit /b

:run
:: Run the PowerShell script from the same folder as this BAT file
powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%~dp0detectandremovecustomlogo.ps1" -LauncherPath "%~f0"