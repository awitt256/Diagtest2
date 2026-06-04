@echo off
:: Check for admin rights
net session >nul 2>&1
if %errorLevel% neq 0 (
    echo This script must be run as administrator.
    echo Attempting to relaunch with admin privileges...
    powershell -Command "Start-Process '%~f0' -Verb runAs"
    exit /b
)

:: Display BitLocker status for all drives
echo ==========================================
echo     BitLocker Status for All Drives
echo ==========================================
echo.
manage-bde -status
echo.

:: Extract conversion status of C: drive
for /f "tokens=3*" %%a in ('manage-bde -status C: ^| find "Conversion Status"') do set status=%%a

echo ==========================================
echo Current Conversion Status: %status%
echo ==========================================

:: Check if not Fully Decrypted
if /I not "%status%"=="Fully" (
    echo BitLocker is not fully decrypted. Disabling BitLocker on C: ...
    PowerShell -NoProfile -ExecutionPolicy Bypass -Command "Start-Process PowerShell -ArgumentList '-NoProfile -ExecutionPolicy Bypass -Command \"Disable-BitLocker -MountPoint \"C:\"\"' -Verb RunAs"
) else (
    echo BitLocker is already fully decrypted.
)

echo.
echo Final BitLocker Status for C:
manage-bde -status C:

echo.
echo ==========================================
echo Press any key to exit...
pause >nul
