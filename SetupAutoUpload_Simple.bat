@echo off
REM Setup Auto Git Upload - Runs Monday-Friday 8 AM - 4:30 PM every 5 minutes
REM Run as Administrator

title Setup Auto Git Upload Task
color 0A

echo.
echo ========================================
echo   Setting up Auto Git Upload Task
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

REM Create a temporary PowerShell script file
set TEMP_PS=%TEMP%\setup_task.ps1

(
    echo $action = New-ScheduledTaskAction -Execute 'powershell.exe' -Argument '-NoProfile -ExecutionPolicy Bypass -File "%SCRIPT_PATH%" -Action timecheck'
    echo $trigger = New-ScheduledTaskTrigger -Weekly -DaysOfWeek Monday,Tuesday,Wednesday,Thursday,Friday -At 08:00:00 -RepetitionInterval ^(New-TimeSpan -Minutes 5^) -RepetitionDuration ^(New-TimeSpan -Hours 8 -Minutes 30^)
    echo $principal = New-ScheduledTaskPrincipal -UserId "$env:USERDOMAIN\$env:USERNAME" -LogonType Interactive -RunLevel Highest
    echo $settings = New-ScheduledTaskSettingsSet -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries -StartWhenAvailable -RunOnlyIfNetworkAvailable
    echo Register-ScheduledTask -TaskName 'AutoGitUpload-Every5Minutes' -Action $action -Trigger $trigger -Principal $principal -Settings $settings -Force ^| Out-Null
    echo Write-Host 'Task created successfully!' -ForegroundColor Green
) > "%TEMP_PS%"

REM Run the PowerShell script
powershell -NoProfile -ExecutionPolicy Bypass -File "%TEMP_PS%"

if %errorlevel% equ 0 (
    echo.
    echo ========================================
    echo   SUCCESS!
    echo ========================================
    echo.
    echo Task created: AutoGitUpload-Every5Minutes
    echo.
    echo Schedule:
    echo   - Days: Monday-Friday ONLY
    echo   - Start: 8:00 AM
    echo   - Stop: 4:30 PM
    echo   - Frequency: Every 5 minutes
    echo.
    echo What it does:
    echo   - Uploads NEW files when detected
    echo   - Uploads MODIFIED files when detected
    echo   - Does NOT run on weekends or outside business hours
    echo.
    echo You can manage this task in:
    echo   Control Panel ^> System and Security ^> Task Scheduler
    echo.
) else (
    echo.
    echo ERROR: Failed to create scheduled task
    echo Error code: %errorlevel%
    echo.
)

REM Clean up temp file
del /f /q "%TEMP_PS%" >nul 2>&1

echo.
pause
