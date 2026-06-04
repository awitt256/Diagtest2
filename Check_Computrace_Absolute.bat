@echo off
REM Run PowerShell script to check for Computrace/Absolute Persistence module

REM Set script and log file paths
set SCRIPT="%~dp0# Check for Computrace or Absolute Persi.ps1"
set LOGFILE="%~dp0Computrace_Absolute_Check_Log.txt"

REM Run PowerShell script and pass log file location
powershell.exe -NoProfile -ExecutionPolicy Bypass -File %SCRIPT%

REM Display log file contents
if exist %LOGFILE% (
    echo.
    echo Results:
    type %LOGFILE%
) else (
    echo Log file not found.
)

pause