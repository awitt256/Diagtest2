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
REM OOBE Sysprep Script with Account Cleanup using CimInstance
REM WARNING: This script will remove user accounts and restart the computer

echo ================================================
echo OOBE Sysprep Script with Account Cleanup
echo Running as Administrator - AUTO-ELEVATED
echo WARNING: This will remove user accounts and restart
echo ================================================
echo.

echo.
echo Step 1: Removing user accounts (excluding built-in accounts)...
echo ================================================

REM Get list of user accounts using CimInstance and delete non-system accounts
powershell -Command "Get-CimInstance -ClassName Win32_UserAccount -Filter \"LocalAccount=True AND Name!='Administrator' AND Name!='Guest' AND Name!='DefaultAccount' AND Name!='WDAGUtilityAccount'\" | ForEach-Object { Write-Output $_.Name }" > "%TEMP%\userlist.txt"

for /f "usebackq delims=" %%i in ("%TEMP%\userlist.txt") do (
    echo Removing user account: %%i
    net user "%%i" /delete >nul 2>&1
    if !errorLevel! == 0 (
        echo   - Successfully removed: %%i
    ) else (
        echo   - Failed to remove: %%i
    )
)

echo.
echo Step 2: Cleaning up user profiles...
echo ================================================

REM Remove user profile directories (be careful with this)
for /d %%i in (C:\Users\*) do (
    set "folder=%%~ni"
    setlocal enabledelayedexpansion
    if not "!folder!"=="Administrator" if not "!folder!"=="Default" if not "!folder!"=="Public" if not "!folder!"=="All Users" if not "!folder!"=="Default User" (
        echo Removing profile folder: !folder!
        rd /s /q "%%i" >nul 2>&1
        if !errorLevel! == 0 (
            echo   - Successfully removed profile: !folder!
        ) else (
            echo   - Failed to remove profile: !folder! (may be in use)
        )
    )
    endlocal
)

echo.
echo Step 3: Preparing for Sysprep...
echo ================================================

REM Stop Windows Update service using CimInstance
echo Stopping Windows Update service...
powershell -Command "Stop-Service -Name wuauserv -Force -ErrorAction SilentlyContinue"

REM Get system information using CimInstance
echo Gathering system information...
powershell -Command "Get-CimInstance -ClassName Win32_OperatingSystem | Select-Object Caption, Version, BuildNumber | Format-List"

REM Clear temporary files
echo Cleaning temporary files...
del /q /s %TEMP%\*.* >nul 2>&1
del /q /s C:\Windows\Temp\*.* >nul 2>&1

echo.
echo Step 4: Running Sysprep OOBE...
echo ================================================
echo This will generalize the system and restart into OOBE
echo The computer will restart automatically after sysprep completes
echo.

REM Create sysprep answer file for unattended operation
echo Creating sysprep answer file...
echo ^<?xml version="1.0" encoding="utf-8"?^> > "%TEMP%\sysprep_unattend.xml"
echo ^<unattend xmlns="urn:schemas-microsoft-com:unattend"^> >> "%TEMP%\sysprep_unattend.xml"
echo     ^<settings pass="generalize"^> >> "%TEMP%\sysprep_unattend.xml"
echo         ^<component name="Microsoft-Windows-Security-SPP" processorArchitecture="amd64" publicKeyToken="31bf3856ad364e35" language="neutral" versionScope="nonSxS" xmlns:wcm="http://schemas.microsoft.com/WMIConfig/2002/State"^> >> "%TEMP%\sysprep_unattend.xml"
echo             ^<SkipRearm^>1^</SkipRearm^> >> "%TEMP%\sysprep_unattend.xml"
echo         ^</component^> >> "%TEMP%\sysprep_unattend.xml"
echo     ^</settings^> >> "%TEMP%\sysprep_unattend.xml"
echo ^</unattend^> >> "%TEMP%\sysprep_unattend.xml"

REM Run sysprep with OOBE, generalize, restart, and unattend file
echo Starting sysprep process...
echo Command: %WINDIR%\System32\Sysprep\sysprep.exe /oobe /generalize /restart /unattend:"%TEMP%\sysprep_unattend.xml"
echo.

%WINDIR%\System32\Sysprep\sysprep.exe /oobe /generalize /restart /unattend:"%TEMP%\sysprep_unattend.xml"

REM If we reach here, sysprep failed
echo.
echo ERROR: Sysprep failed to complete successfully
echo Check the sysprep log files at: %WINDIR%\System32\Sysprep\Panther\
echo.
pause

REM Cleanup temporary files
del /q "%TEMP%\userlist.txt" >nul 2>&1
if exist "%TEMP%\sysprep_unattend.xml" del "%TEMP%\sysprep_unattend.xml"

exit /b %errorLevel%