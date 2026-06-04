@echo off
REM Setup Auto Git Upload using schtasks (simplified, no password prompt)
REM Run as Administrator

title Setup Auto Git Upload Task
color 0A

echo.
echo ========================================
echo   Setting up Auto Git Upload Task
echo   (Every 5 minutes)
echo ========================================
echo.

REM Check if running as admin
net session >nul 2>&1
if %errorlevel% neq 0 (
    echo ERROR: This batch file requires Administrator privileges.
    echo Please right-click and select "Run as administrator"
    echo.
    pause
    exit /b 1
)

cd /d "%~dp0"

REM Get the full path to the script
set SCRIPT_PATH=%cd%\AutoGitUpload.ps1

REM Check if AutoGitUpload.ps1 exists
if not exist "%SCRIPT_PATH%" (
    echo ERROR: AutoGitUpload.ps1 not found in "%~dp0"
    echo Please make sure AutoGitUpload.ps1 is in the same folder
    echo.
    pause
    exit /b 1
)

echo Removing old task if it exists...
schtasks /delete /tn "AutoGitUpload-Every5Minutes" /f >nul 2>&1

echo Creating new scheduled task...
echo.

REM Create the task using schtasks (simplified - no password prompt)
schtasks /create ^
    /tn "AutoGitUpload-Every5Minutes" ^
    /tr "powershell.exe -NoProfile -ExecutionPolicy Bypass -File \"%SCRIPT_PATH%\" -Action timecheck" ^
    /sc minute ^
    /mo 5 ^
    /f

if %errorlevel% equ 0 (
    echo.
    echo ========================================
    echo   SUCCESS!
    echo ========================================
    echo.
    echo Task created: AutoGitUpload-Every5Minutes
    echo Frequency: Every 5 minutes
    echo.
    echo What it does:
    echo   - Uploads NEW files immediately 24/7
    echo   - Uploads modified files during 3:30-4:30 PM
    echo   - Skips unchanged files outside time window
    echo.
    echo You can manage this task in:
    echo   Control Panel ^> System and Security ^> Task Scheduler
    echo.
    echo Or from PowerShell:
    echo   Get-ScheduledTask -TaskName "AutoGitUpload-Every5Minutes"
    echo.
) else (
    echo.
    echo ERROR: Failed to create scheduled task
    echo Error code: %errorlevel%
    echo Please try running this batch file as Administrator
    echo.
)

echo.
pause
