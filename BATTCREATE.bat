@echo off
echo ============================================
echo  Battery Status - EXE Builder
echo ============================================
echo.

echo [1/3] Installing PyInstaller...
python -m pip install pyinstaller
if errorlevel 1 (
    echo.
    echo ERROR: pip failed. Make sure Python is installed and in your PATH.
    pause
    exit /b 1
)

echo.
echo [2/3] Building BatteryStatus.exe...
python -m PyInstaller --onefile --windowed --name BatteryStatus "C:\Users\Anthony\Desktop\WinTest3.0\BAT.py"
if errorlevel 1 (
    echo.
    echo ERROR: Build failed. See above for details.
    pause
    exit /b 1
)

echo.
echo [3/3] Done!
echo.
echo Your EXE is ready at:
echo   C:\Users\Anthony\Desktop\WinTest3.0\dist\BatteryStatus.exe
echo.
pause