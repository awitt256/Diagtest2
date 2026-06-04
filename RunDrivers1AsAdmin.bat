@echo off
REM Run DRIVERS1.ps1 as Administrator
set "SCRIPT=C:\Users\Anthony\Documents\WINDOWS TEST 2.2\DRIVERS1.ps1"

REM Detect PowerShell Core or Windows PowerShell
where pwsh >nul 2>&1
if %errorlevel%==0 (
    set "PWSH=pwsh"
) else (
    set "PWSH=powershell"
)

REM Relaunch batch as admin if not already
openfiles >nul 2>&1 || (
    echo Requesting administrator privileges...
    powershell -Command "Start-Process '%~f0' -Verb RunAs"
    exit /b
)

REM Run the script elevated
%PWSH% -NoProfile -ExecutionPolicy Bypass -File "%SCRIPT%"
