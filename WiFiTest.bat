@echo off
:: Check for admin rights
net session >nul 2>&1
if %errorLevel% neq 0 (
    echo Requesting administrator rights...
    powershell -Command "Start-Process '%~f0' -Verb RunAs"
    exit /b
)

:: Now running as admin
title WiFi Test Tool

echo ========================================
echo WiFi Test Tool - Launcher
echo ========================================
echo.
echo Enabling Location Services...
echo.

:: Enable Location Services using multiple methods
echo Method 1: Registry - System Location Access...
reg add "HKLM\SOFTWARE\Microsoft\Windows\CurrentVersion\CapabilityAccessManager\ConsentStore\location" /v Value /t REG_SZ /d Allow /f >nul 2>&1

echo Method 2: Registry - User Location Access...
reg add "HKCU\SOFTWARE\Microsoft\Windows\CurrentVersion\CapabilityAccessManager\ConsentStore\location" /v Value /t REG_SZ /d Allow /f >nul 2>&1

echo Method 3: Registry - Location Policy...
reg add "HKLM\SOFTWARE\Policies\Microsoft\Windows\LocationAndSensors" /v DisableLocation /t REG_DWORD /d 0 /f >nul 2>&1

echo Method 4: PowerShell Location Service...
powershell -Command "try { $locSvc = Get-Service -Name 'lfsvc' -ErrorAction SilentlyContinue; if ($locSvc) { Start-Service -Name 'lfsvc' -ErrorAction SilentlyContinue } } catch {}" >nul 2>&1

echo Method 5: Registry - Let Apps Access Location...
reg add "HKLM\SOFTWARE\Microsoft\Windows\CurrentVersion\CapabilityAccessManager\ConsentStore\location\NonPackaged" /v Value /t REG_SZ /d Allow /f >nul 2>&1

echo.
echo Location Services enabled successfully.
echo.
echo Starting WiFi Test Tool...
echo.

:: Change to script directory
cd /d "%~dp0"

:: Try multiple Python locations
where python >nul 2>&1
if %errorLevel% equ 0 (
    python WiFiTest.py
    goto :end
)

:: Try common Python locations
if exist "%LOCALAPPDATA%\Programs\Python\Python*\python.exe" (
    for /d %%i in ("%LOCALAPPDATA%\Programs\Python\Python*") do (
        "%%i\python.exe" WiFiTest.py
        goto :end
    )
)

if exist "C:\Python*\python.exe" (
    for /d %%i in ("C:\Python*") do (
        "%%i\python.exe" WiFiTest.py
        goto :end
    )
)

if exist "%USERPROFILE%\AppData\Local\Programs\Python\Python*\python.exe" (
    for /d %%i in ("%USERPROFILE%\AppData\Local\Programs\Python\Python*") do (
        "%%i\python.exe" WiFiTest.py
        goto :end
    )
)

:: Try py launcher
where py >nul 2>&1
if %errorLevel% equ 0 (
    py WiFiTest.py
    goto :end
)

:: Try python3
where python3 >nul 2>&1
if %errorLevel% equ 0 (
    python3 WiFiTest.py
    goto :end
)

echo.
echo ERROR: Python not found!
echo.
echo Please install Python from https://www.python.org/downloads/
echo Or use the Windows Store: winget install Python.Python.3.11
echo.
pause

:end
if %errorLevel% neq 0 (
    echo.
    echo Error running WiFi Test Tool.
    pause
)
