@echo off
:: Windows Activation Checker and Activator
:: Run as Administrator

:: Check for administrator privileges
net session >nul 2>&1
if %errorlevel% neq 0 (
    echo Requesting administrative privileges...
    powershell -Command "Start-Process '%~f0' -Verb runAs"
    exit /b
)

echo ================================================================
echo              Windows Activation Status Checker
echo ================================================================
echo.

:: Check current activation status
echo Checking Windows activation status...
echo.

:: Use slmgr to check activation status
echo Current Windows License Information:
echo ----------------------------------
slmgr /dli

echo.
echo ================================================================
echo              Activation Status Analysis
echo ================================================================
echo.

:: Use PowerShell to get more detailed activation info
powershell -NoProfile -ExecutionPolicy Bypass -Command "& {try {$activation = Get-CimInstance -ClassName SoftwareLicensingProduct | Where-Object { $_.PartialProductKey -and $_.Name -like 'Windows*' }; if ($activation) {Write-Host 'Windows Edition:' $activation.Name -ForegroundColor Cyan; Write-Host 'License Status:' $activation.LicenseStatus -ForegroundColor Cyan; Write-Host 'Partial Product Key:' $activation.PartialProductKey -ForegroundColor Cyan; Write-Host ''; switch ($activation.LicenseStatus) {0 { Write-Host 'STATUS: Unlicensed' -ForegroundColor Red; $needsActivation = $true }; 1 { Write-Host 'STATUS: Licensed (Activated)' -ForegroundColor Green; $needsActivation = $false }; 2 { Write-Host 'STATUS: Out-of-Box Grace Period' -ForegroundColor Yellow; $needsActivation = $true }; 3 { Write-Host 'STATUS: Out-of-Tolerance Grace Period' -ForegroundColor Yellow; $needsActivation = $true }; 4 { Write-Host 'STATUS: Non-Genuine Grace Period' -ForegroundColor Red; $needsActivation = $true }; 5 { Write-Host 'STATUS: Notification' -ForegroundColor Yellow; $needsActivation = $true }; 6 { Write-Host 'STATUS: Extended Grace Period' -ForegroundColor Yellow; $needsActivation = $true }; default { Write-Host 'STATUS: Unknown (' $activation.LicenseStatus ')' -ForegroundColor Red; $needsActivation = $true }; }; Write-Host ''; if ($needsActivation) {Write-Host 'Windows requires activation!' -ForegroundColor Red; exit 1;} else {Write-Host 'Windows is already activated!' -ForegroundColor Green; exit 0;};} else {Write-Host 'Could not retrieve Windows license information' -ForegroundColor Red; exit 1;};} catch {Write-Host 'Error checking activation status:' $_.Exception.Message -ForegroundColor Red; exit 1;}}"

:: Check the result of the PowerShell script
if %errorlevel% equ 0 (
    echo.
    echo Windows is already properly activated. No action needed.
    goto :end
)

echo.
echo ================================================================
echo              Attempting Windows Activation
echo ================================================================
echo.

echo Windows needs to be activated. Attempting automatic activation...
echo.

:: Try online activation first
echo Step 1: Attempting online activation...
slmgr /ato

:: Wait a moment for activation to process
timeout /t 10 /nobreak >nul

echo.
echo Step 2: Refreshing license information...
slmgr /ipk

echo.
echo Step 3: Checking activation status again...
echo.

:: Check activation status again
powershell -NoProfile -ExecutionPolicy Bypass -Command "& {try {$activation = Get-CimInstance -ClassName SoftwareLicensingProduct | Where-Object { $_.PartialProductKey -and $_.Name -like 'Windows*' }; if ($activation -and $activation.LicenseStatus -eq 1) {Write-Host 'SUCCESS: Windows has been activated!' -ForegroundColor Green; exit 0;} else {Write-Host 'Activation attempt completed, but Windows may still need activation.' -ForegroundColor Yellow; Write-Host 'Current License Status:' $activation.LicenseStatus -ForegroundColor Yellow; exit 1;};} catch {Write-Host 'Error checking activation status after attempt:' $_.Exception.Message -ForegroundColor Red; exit 1;}}"

if %errorlevel% equ 0 (
    echo.
    echo ================================================================
    echo                   Activation Successful!
    echo ================================================================
    goto :end
)

echo.
echo ================================================================
echo                Additional Activation Options
echo ================================================================
echo.
echo Automatic activation was not successful. You may need to:
echo.
echo 1. Enter a valid product key manually:
echo    - Open Settings ^> Update ^& Security ^> Activation
echo    - Click "Change product key"
echo    - Enter your valid Windows product key
echo.
echo 
set /p manual="Would you like to open Windows Activation settings? (Y/N): "
if /i "%manual%"=="Y" (
    echo Opening Windows Activation settings...
    start ms-settings:activation
)

:end
echo.
echo ================================================================
echo                    Process Complete
echo ================================================================
echo.
echo Final license status check:   
slmgr /xpr

echo.
pause