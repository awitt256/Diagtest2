@echo off
@echo off
cls
echo Checking BitLocker status for drive C:...

:: Get conversion status
for /f "tokens=3" %%a in ('manage-bde -status C: ^| find "Conversion Status"') do set status=%%a

:: Display current status
echo Current Conversion Status: %status%

:: Check if not Fully Decrypted
if /I not "%status%"=="Fully" (
    echo BitLocker is not fully decrypted. Running dbl1.bat...
    call dbl1.bat
) else (
    echo BitLocker is already fully decrypted.
)

echo.
echo Final BitLocker Status:
manage-bde -status C:

pause
