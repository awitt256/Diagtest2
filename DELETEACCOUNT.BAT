@echo off
setlocal enabledelayedexpansion

REM Auto-elevate to Administrator if not already running as admin
REM Check if running as administrator
net session >nul 2>&1
if %errorLevel% == 0 goto :admin

REM If not admin, re-launch as administrator
echo Requesting Administrator privileges...
powershell -Command "Start-Process '%~f0' -Verb RunAs"
exit /b

:admin
echo ================================================
echo HP User Account Deletion Script
echo Running as Administrator - AUTO-ELEVATED
echo ================================================
echo.

REM Set target account name
set "target_account=hp"

echo Checking for user account: %target_account%
echo ================================================

REM Check if the HP account exists
powershell -Command "Get-CimInstance -ClassName Win32_UserAccount -Filter \"LocalAccount=True AND Name='%target_account%'\"" > "%TEMP%\hp_check.txt"

REM Check if file has content (account exists)
for %%A in ("%TEMP%\hp_check.txt") do set size=%%~zA
if %size% EQU 0 (
    echo.
    echo [INFO] User account '%target_account%' does not exist on this system.
    echo No action needed.
    echo.
    pause
    goto :exit_script
)

REM Display account details
echo Account found! Getting details...
echo.
powershell -Command "Get-CimInstance -ClassName Win32_UserAccount -Filter \"LocalAccount=True AND Name='%target_account%'\" | Select-Object Name, Disabled, Description, SID | Format-List"

echo.
echo ================================================
echo READY TO DELETE ACCOUNT: %target_account%
echo ================================================

REM Final confirmation
echo [WARNING] This will permanently delete the user account: %target_account%
echo This will also remove the user's profile and all associated data!
echo This action cannot be undone!
echo.
set /p final_confirm="Type DELETE to confirm removal of '%target_account%': "

if not "!final_confirm!"=="DELETE" (
    echo.
    echo Deletion cancelled - account was NOT removed
    echo.
    goto :exit_script
)

echo.
echo ================================================
echo DELETING USER ACCOUNT: %target_account%
echo ================================================

REM Delete the user account
echo Removing user account: %target_account%...
net user %target_account% /delete

if %errorlevel% EQU 0 (
    echo [SUCCESS] User account '%target_account%' has been successfully deleted.
    
    REM Also remove the user profile if it exists
    echo.
    echo Checking for user profile...
    powershell -Command "Get-CimInstance -ClassName Win32_UserProfile | Where-Object {$_.LocalPath -like '*\%target_account%'} | ForEach-Object { Write-Host 'Found profile:' $_.LocalPath; $_.Delete(); Write-Host 'Profile deleted.' }" 2>nul
    
    if %errorlevel% EQU 0 (
        echo User profile cleanup completed.
    ) else (
        echo Note: No user profile found or profile cleanup not needed.
    )
) else (
    echo [ERROR] Failed to delete user account '%target_account%'
    echo Error code: %errorlevel%
)

echo.
echo ================================================
echo OPERATION COMPLETED
echo ================================================

:exit_script
echo.
echo Press any key to exit...
pause >nul
exit /b

REM Clean up temporary files
del "%TEMP%\hp_check.txt" 2>nul