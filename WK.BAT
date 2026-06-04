@echo off
cls
echo =======================================
echo     WINDOWS PRODUCT KEY RETRIEVAL
echo =======================================
echo.

echo Checking for Windows Product Key...
powershell -NoProfile -ExecutionPolicy Bypass -Command "(Get-CimInstance -ClassName SoftwareLicensingService).OA3xOriginalProductKey"
echo.

echo Script completed.
echo.
pause