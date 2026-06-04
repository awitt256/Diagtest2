@echo off
setlocal

:: Get the full path to AUDIO7.PS1 (adjust path if needed)
set "scriptpath=%~dp0AUDIO7.PS1"

:: Check if PowerShell is available
where powershell.exe >nul 2>&1
if errorlevel 1 (
    echo PowerShell not found on this system.
    pause
    exit /b 1
)

:: Run AUDIO7.PS1 as Administrator, and keep the PowerShell window open
powershell.exe -Command "Start-Process PowerShell -ArgumentList '-ExecutionPolicy Bypass -File \"%scriptpath%\"' -Verb RunAs"

exit /b 0