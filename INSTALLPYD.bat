@echo off
setlocal EnableDelayedExpansion

echo ============================================================
echo   Diagnostics Test Tool - Dependency Installer
echo ============================================================
echo.

:: ---------------------------------------------------------------
:: Check for Python
:: ---------------------------------------------------------------
echo [1/4] Checking for Python...
python --version >nul 2>&1
if errorlevel 1 (
    echo.
    echo  ERROR: Python was not found on this computer.
    echo  Please install Python 3.8 or newer from https://www.python.org/downloads/
    echo  Make sure to check "Add Python to PATH" during installation.
    echo.
    pause
    exit /b 1
)
for /f "tokens=*" %%v in ('python --version 2^>^&1') do set PYVER=%%v
echo  Found: %PYVER%
echo.

:: ---------------------------------------------------------------
:: Upgrade pip
:: ---------------------------------------------------------------
echo [2/4] Upgrading pip...
python -m pip install --upgrade pip --quiet
if errorlevel 1 (
    echo  WARNING: pip upgrade failed - continuing anyway...
) else (
    echo  pip is up to date.
)
echo.

:: ---------------------------------------------------------------
:: Install dependencies
:: ---------------------------------------------------------------
echo [3/4] Installing required packages...
echo.

echo  Installing customtkinter ...
python -m pip install customtkinter --quiet
if errorlevel 1 ( echo  FAILED: customtkinter ) else ( echo  OK: customtkinter )

echo  Installing Pillow (PIL) ...
python -m pip install Pillow --quiet
if errorlevel 1 ( echo  FAILED: Pillow ) else ( echo  OK: Pillow )

echo  Installing opencv-python (camera support) ...
python -m pip install opencv-python --quiet
if errorlevel 1 ( echo  FAILED: opencv-python ) else ( echo  OK: opencv-python )

echo  Installing pyaudio (microphone support) ...
python -m pip install pyaudio --quiet
if errorlevel 1 (
    echo  FAILED: pyaudio via pip - trying pipwin fallback...
    python -m pip install pipwin --quiet
    python -m pipwin install pyaudio --quiet
    if errorlevel 1 (
        echo  WARNING: pyaudio install failed. Microphone test may not work.
        echo  Manual fix: download the .whl from https://www.lfd.uci.edu/~gohlke/pythonlibs/#pyaudio
        echo  and run: pip install ^<downloaded_file^>.whl
    ) else (
        echo  OK: pyaudio (via pipwin)
    )
) else (
    echo  OK: pyaudio
)

echo  Installing numpy (audio/camera helper) ...
python -m pip install numpy --quiet
if errorlevel 1 ( echo  FAILED: numpy ) else ( echo  OK: numpy )

echo  Installing screen-brightness-control (brightness test) ...
python -m pip install screen-brightness-control --quiet
if errorlevel 1 ( echo  FAILED: screen-brightness-control ) else ( echo  OK: screen-brightness-control )

echo  Installing psutil (system info) ...
python -m pip install psutil --quiet
if errorlevel 1 ( echo  FAILED: psutil ) else ( echo  OK: psutil )

echo  Installing pywin32 (Windows API helpers) ...
python -m pip install pywin32 --quiet
if errorlevel 1 ( echo  FAILED: pywin32 ) else ( echo  OK: pywin32 )

echo  Installing pynput (touchpad/keyboard input) ...
python -m pip install pynput --quiet
if errorlevel 1 ( echo  FAILED: pynput ) else ( echo  OK: pynput )

echo.

:: ---------------------------------------------------------------
:: Verify core imports
:: ---------------------------------------------------------------
echo [4/4] Verifying core imports...
echo.

python -c "import customtkinter" >nul 2>&1
if errorlevel 1 ( echo  [FAIL] customtkinter ) else ( echo  [PASS] customtkinter )

python -c "import tkinter" >nul 2>&1
if errorlevel 1 ( echo  [FAIL] tkinter ) else ( echo  [PASS] tkinter )

python -c "from PIL import Image" >nul 2>&1
if errorlevel 1 ( echo  [FAIL] Pillow / PIL ) else ( echo  [PASS] Pillow / PIL )

python -c "import cv2" >nul 2>&1
if errorlevel 1 ( echo  [FAIL] opencv-python (cv2) ) else ( echo  [PASS] opencv-python (cv2) )

python -c "import numpy" >nul 2>&1
if errorlevel 1 ( echo  [FAIL] numpy ) else ( echo  [PASS] numpy )

python -c "import psutil" >nul 2>&1
if errorlevel 1 ( echo  [FAIL] psutil ) else ( echo  [PASS] psutil )

python -c "import winsound" >nul 2>&1
if errorlevel 1 ( echo  [FAIL] winsound ^(built-in - should always pass^) ) else ( echo  [PASS] winsound )

python -c "import ctypes" >nul 2>&1
if errorlevel 1 ( echo  [FAIL] ctypes ^(built-in^) ) else ( echo  [PASS] ctypes )

echo.
echo ============================================================
echo   Installation complete!
echo   If any packages show [FAIL] above, try running this
echo   script as Administrator (right-click -> Run as admin).
echo ============================================================
echo.
pause