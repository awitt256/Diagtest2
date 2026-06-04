@echo off
setlocal

echo --------------------------------------------------
echo Install Python 3.12 and required Python packages
echo --------------------------------------------------

echo Installing Python 3.12 via winget (may prompt for approval)...
winget install --id Python.Python.3.12 -e --accept-package-agreements --accept-source-agreements || (
    echo Winget install failed or Python may already be installed. Continuing...
)

echo Locating Python executable (trying py -3.12, then python)...
set "PYEXE="
for /f "usebackq delims=" %%p in (`py -3.12 -c "import sys; print(sys.executable)" 2^>nul`) do set "PYEXE=%%p"
if not defined PYEXE (
    for /f "usebackq delims=" %%p in (`python -c "import sys; print(sys.executable)" 2^>nul`) do set "PYEXE=%%p"
)

if not defined PYEXE (
    echo ERROR: Could not find a Python executable. Please ensure Python 3.12 was installed and is on PATH.
    pause
    exit /b 1
)

echo Using Python: %PYEXE%

echo Upgrading pip, setuptools, wheel...
"%PYEXE%" -m pip install --upgrade pip setuptools wheel

echo Installing required Python packages...
"%PYEXE%" -m pip install --upgrade customtkinter Pillow sounddevice numpy scipy opencv-python pygame wmi pywin32

echo Installation finished.
pause
endlocal
