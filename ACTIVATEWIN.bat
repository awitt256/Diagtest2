@echo off
setlocal

set "PSSCRIPT=%~dp0ACTIATEWIN.ps1"
if not exist "%PSSCRIPT%" (
    echo ERROR: "%PSSCRIPT%" not found.
    pause
    exit /b 1
)

set "OUTPUTFILE=%TEMP%\ACTIVATEWIN-output-%RANDOM%.txt"
set "WRAPPERPS=%TEMP%\ACTIVATEWIN-wrapper-%RANDOM%.ps1"

:: Check for administrator privileges
net session >nul 2>&1
if %errorlevel% neq 0 (
    echo Requesting administrator privileges...
    > "%WRAPPERPS%" echo ^& '%PSSCRIPT%' ^| Out-File -FilePath '%OUTPUTFILE%' -Encoding UTF8
    powershell.exe -NoProfile -ExecutionPolicy Bypass -Command "Start-Process powershell.exe -ArgumentList '-NoProfile','-ExecutionPolicy','Bypass','-File','%WRAPPERPS%' -Verb RunAs -Wait"

    if exist "%OUTPUTFILE%" (
        type "%OUTPUTFILE%"
        del /f /q "%OUTPUTFILE%" >nul 2>&1
    ) else (
        echo ERROR: No output was captured from the elevated PowerShell process.
    )

    del /f /q "%WRAPPERPS%" >nul 2>&1
    pause
    exit /b
)

powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%PSSCRIPT%"
set "EXITCODE=%ERRORLEVEL%"
pause
exit /b %EXITCODE%
