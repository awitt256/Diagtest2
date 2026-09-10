@echo off

:: --- Elevate this batch file to admin first ---
fsutil dirty query %systemdrive% >nul 2>&1
if errorlevel 1 (
    powershell -NoProfile -WindowStyle Hidden -Command "Start-Process -FilePath '%~f0' -Verb RunAs"
    exit /b
)

setlocal

:: Get the full path to AUDIO8.PS1
set "scriptpath=%~dp0AUDIO8.PS1"

:: Run AUDIO8.PS1 as admin (we are already elevated now)
powershell.exe -ExecutionPolicy Bypass -File "%scriptpath%"

exit /b 0