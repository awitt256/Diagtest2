@echo off
setlocal ENABLEDELAYEDEXPANSION
title PG25 Setup Installer

set "BASE_DIR=%~dp0"
set "ENV_DIR=%BASE_DIR%.venv_pg25"
set "PY_SCRIPT=%BASE_DIR%PG25.PY"

echo ============================================
echo   PG25 Dependency Installer (Local Folder)
echo ============================================
echo.

where py >nul 2>nul
if %ERRORLEVEL%==0 (
    set "PY_CMD=py -3"
) else (
    where python >nul 2>nul
    if %ERRORLEVEL%==0 (
        set "PY_CMD=python"
    ) else (
        echo [ERROR] Python not found.
        echo Install Python 3.10+ then run this again.
        pause
        exit /b 1
    )
)

if not exist "%ENV_DIR%\Scripts\python.exe" (
    echo [1/5] Creating virtual environment in:
    echo       %ENV_DIR%
    %PY_CMD% -m venv "%ENV_DIR%"
    if errorlevel 1 (
        echo [ERROR] Failed to create virtual environment.
        pause
        exit /b 1
    )
) else (
    echo [1/5] Virtual environment already exists.
)

echo [2/5] Activating environment...
call "%ENV_DIR%\Scripts\activate.bat"
if errorlevel 1 (
    echo [ERROR] Could not activate virtual environment.
    pause
    exit /b 1
)

echo [3/5] Upgrading pip/setuptools/wheel...
python -m pip install --upgrade pip setuptools wheel
if errorlevel 1 (
    echo [ERROR] Failed upgrading pip tools.
    pause
    exit /b 1
)

echo [4/5] Installing required packages...
python -m pip install customtkinter pillow opencv-python pygame sounddevice numpy scipy
if errorlevel 1 (
    echo [ERROR] Failed installing one or more packages.
    echo Try rerunning this script as Administrator.
    pause
    exit /b 1
)

echo [5/5] Setup complete.
echo.
if exist "%PY_SCRIPT%" (
    choice /C YN /M "Launch PG25.PY now?"
    if errorlevel 2 goto :done
    echo Launching PG25.PY...
    python "%PY_SCRIPT%"
) else (
    echo [WARN] Could not find PG25.PY at:
    echo        %PY_SCRIPT%
)

:done
echo.
echo Ready. Your dependencies are isolated in:
echo %ENV_DIR%
pause
endlocal
