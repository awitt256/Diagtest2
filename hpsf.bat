@echo off
REM Run fwd.ps1 as Administrator
REM This batch script elevates itself and runs fwd.ps1 with admin privileges

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
echo  Running fwd.ps1 with Administrator Privileges
echo ===============================================================
echo.

REM Get the directory where this batch file is located
set "SCRIPT_DIR=%~dp0"
set "PS_SCRIPT=%SCRIPT_DIR%fwd.ps1"

REM Check if fwd.ps1 exists
if not exist "%PS_SCRIPT%" (
    echo ERROR: fwd.ps1 not found in %SCRIPT_DIR%
    echo Expected path: %PS_SCRIPT%
    echo.
    pause
    exit /b 1
)

REM Run the PowerShell script with full authorization
echo Running: %PS_SCRIPT%
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
