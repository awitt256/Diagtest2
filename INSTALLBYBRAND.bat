@echo off
setlocal
title Run InstallByBrand (Admin)

REM =========================================
REM Resolve script path:
REM  1) Preferred Desktop folder
REM  2) Fallback: same folder as this BAT
REM =========================================
set "PREFERRED=C:\Users\Anthony\Desktop\win test 2.5.17\InstallByBrand.ps1"
if exist "%PREFERRED%" (
    set "SCRIPT=%PREFERRED%"
) else (
    set "SCRIPT=%~dp0InstallByBrand.ps1"
)

if not exist "%SCRIPT%" (
    echo [ERROR] Could not find InstallByBrand.ps1 at:
    echo   "%PREFERRED%"
    echo   "%~dp0InstallByBrand.ps1"
    echo.
    pause
    exit /b 1
)

REM =========================================
REM Pick PowerShell host: prefer PowerShell 7 (pwsh), else Windows PowerShell
REM =========================================
set "PS7=%ProgramFiles%\PowerShell\7\pwsh.exe"
set "PS5=%SystemRoot%\System32\WindowsPowerShell\v1.0\powershell.exe"

if exist "%PS7%" (
    set "PS=%PS7%"
) else (
    set "PS=%PS5%"
)

REM =========================================
REM Check if we are already admin (net session works only when elevated)
REM =========================================
net session >nul 2>&1
if %errorlevel%==0 (
    echo [INFO] Already elevated. Running the script directly...
    "%PS%" -NoLogo -NoProfile -ExecutionPolicy Bypass -NoExit -File "%SCRIPT%"
    goto :eof
)

REM =========================================
REM Not admin: Elevate via UAC and keep the elevated window open (-NoExit)
REM IMPORTANT: The quoting inside -Command uses single quotes for PS strings
REM and lets CMD expand variables before PowerShell starts.
REM =========================================
echo [INFO] Elevating (you will see a UAC prompt)...
"%PS5%" -NoLogo -NoProfile -Command "Start-Process -FilePath '%PS%' -ArgumentList @('-NoLogo','-NoProfile','-ExecutionPolicy','Bypass','-NoExit','-File','%SCRIPT%') -WorkingDirectory '%~dp0' -Verb RunAs -Wait"

echo.
echo [INFO] If nothing appears, check the elevated PowerShell window.
pause
exit /b 0