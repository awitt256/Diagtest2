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
start microsoft.windows.camera:
timeout 8
star
start slui
timeout 5
start kb
PAUSE
start notepad
PAUSE
START DEVMGMT
@echo off
set /p choice=Missing Drivers? (Y/N): 
if /i "%choice%"=="N" (
    shutdown /r /t 0
) else (
    drivers
)
@echo off
set /p answer=Sysprep Computer? (Y/N): 
if /i "%answer%"=="Y" (
    %WINDIR%\system32\sysprep\sysprep.exe
) else (
set /p answer=Shutdown Computer? (Y/N): 
if /i "%answer%"=="Y" (
    Shutdown /s /t 0
) else (
    exit
