@echo off
REM HP Software Framework Driver Detection - Batch Launcher (Admin)
REM This script elevates itself and runs CHECK_HP_DRIVER.PS1 with full PowerShell authorization

setlocal enabledelayedexpansion

REM Check if running as Administrator
net session >nul 2>&1
if %errorlevel% neq 0 (
    echo Requesting Administrator privileges...
    REM Re-run the batch file as admin
    powershell -Command "Start-Process cmd -ArgumentList '/c \"%~f0\"' -Verb RunAs" -NoProfile -ExecutionPolicy Bypass
    exit /b
)

REM We are now running as Administrator
cls
echo.
echo ===============================================================
echo  HP SOFTWARE FRAMEWORK DRIVER DETECTION
echo  Running with Administrator Privileges
echo ===============================================================
echo.

REM Get the directory where this batch file is located
set "SCRIPT_DIR=%~dp0"
set "PS_SCRIPT=%SCRIPT_DIR%CHECK_HP_DRIVER.PS1"

REM Check if the PowerShell script exists
if not exist "%PS_SCRIPT%" (
    echo ERROR: CHECK_HP_DRIVER.PS1 not found in %SCRIPT_DIR%
    echo.
    pause
    exit /b 1
)

REM Run the PowerShell script with full authorization
echo Running PowerShell script...
echo.
powershell -NoProfile -ExecutionPolicy Bypass -File "%PS_SCRIPT%"

REM Capture the exit code
set "EXITCODE=%ERRORLEVEL%"

echo.
echo ===============================================================
if %EXITCODE% equ 0 (
    echo Script completed successfully.
) else (
    echo Script completed with exit code: %EXITCODE%
)
echo ===============================================================
echo.

REM Pause so the user can see the results
pause

exit /b %EXITCODE%
