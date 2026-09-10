
@echo off
setlocal enabledelayedexpansion

echo Getting Serial Number...
wmic bios get serialnumber
set /p snmatch=Does SN match? (Y/N): 
if /i "%snmatch%" NEQ "Y" (
    echo SN did not match. Exiting...
    exit /b
)

echo Getting SKU...
wmic computersystem get SystemSKUNumber
set /p skumatch=Does SKU match? (Y/N): 
if /i "%skumatch%" NEQ "Y" (
    echo SKU did not match. Exiting...
    exit /b
)

echo Running Start Enroll...
START ENROLL
timeout 15
start 13
TIMEOUT 17
start 69
TIMEOUT 17
start devmgmt
pause
start bat
timeout 7
start soundcheck 
timeout 15
start microsoft.windows.camera:
timeout 8
start slui
timeout 5
start kb
PAUSE
start notepad
PAUSE
START DEVMGMT
@echo off
setlocal

:: Step 1: Ask about missing drivers
set /p drivers=Missing Drivers? (Y/N): 
if /I "%drivers%"=="Y" (
    call drivers
    PAUSE
)

:: Step 2: Ask about sysprep (no /generalize, use /oobe /reboot)
set /p sysprep=Do you want to sysprep? (Y/N): 
if /I "%sysprep%"=="Y" (
    %SystemRoot%\System32\Sysprep\Sysprep.exe /oobe /reboot
    goto end
)

:: Step 3: Ask about restart
set /p restart=Do you want to restart? (Y/N): 
if /I "%restart%"=="Y" (
    shutdown /r /t 0
    goto end
)

:: Step 4: Ask about shutdown
set /p shut=Do you want to shut down? (Y/N): 
if /I "%shut%"=="Y" (
    shutdown /s /t 0
    goto end
)

:: Final: Exit script
:end
exit