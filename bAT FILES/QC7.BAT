@echo off
PowerShell.exe -NoProfile -ExecutionPolicy Bypass -File "SN.ps1"
pause
start enroll
timeout 15
start 13
TIMEOUT 17
start 69
TIMEOUT 17
start devmgmt
pause
start bat
timeout 7
@echo off
:: Run the speaker test file
start /wait "" "ST"

:: Ask the user if the speakers worked
set /p speakerResponse=Did the speakers work? (Y/N): 

if /I "%speakerResponse%"=="Y" (
    echo Launching SoundCheck...
    start "" "SoundCheck"
) else if /I "%speakerResponse%"=="N" (
    echo Please check your speakers.
)
PAUSE
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