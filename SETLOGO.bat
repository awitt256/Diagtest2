@echo off
:: ============================================================
::  HP BIOS Boot Logo Setter
::  Sets dtt_bios.jpg (on Desktop) as the HP firmware boot logo
:: ============================================================

:: --- Auto-elevate to Administrator ---
net session >nul 2>&1
if %errorlevel% neq 0 (
    echo Requesting Administrator privileges...
    powershell -Command "Start-Process '%~f0' -Verb RunAs"
    exit /b
)

echo.
echo  ==========================================
echo   HP BIOS Boot Logo - DTT
echo  ==========================================
echo.
echo  Setting boot logo from Desktop...
echo.

:: Run the CMSL command pointing to the Desktop file
powershell -ExecutionPolicy Bypass -Command ^
    "Set-HPFirmwareBootLogo -File '%USERPROFILE%\Desktop\dtt_bios.jpg'"

if %errorlevel% equ 0 (
    echo.
    echo  [SUCCESS] Boot logo set successfully!
    echo  Restart your PC to see the new logo.
) else (
    echo.
    echo  [ERROR] Something went wrong.
    echo  Make sure HP Client Management Script Library is installed.
    echo  Download: https://www.hp.com/go/clientmanagement
)

echo.
pause