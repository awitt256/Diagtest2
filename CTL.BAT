@echo off

:: Step 1: Run WINDOWS tST
start "" wt

:: Step 2: Pause so user can see or interact
pause

:: Step 3: Ask if user wants to run Sysprep
set /p choice=Do you want to Sysprep? (Y/N): 

:: Step 4: Handle response
if /I "%choice%"=="Y" (
    echo Running Sysprep...
    cd /d %windir%\System32\Sysprep
    sysprep.exe /oobe /shutdown /quiet
) else (
    echo Sysprep cancelled.
)

:: Optional: Pause at end to keep window open
pause
V