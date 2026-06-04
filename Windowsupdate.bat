:WindowsUpdate
echo =================================================================================
echo                  WINDOWS UPDATE DRIVER INSTALLER
echo =================================================================================
echo Checking for Windows Updates and optional drivers...
echo.

REM Relaunch as admin if needed
net session >nul 2>&1
if %errorlevel% neq 0 (
    powershell -Command "Start-Process '%~f0' -Verb RunAs"
    exit /b
)

powershell -NoProfile -ExecutionPolicy Bypass -Command "Install-PackageProvider -Name NuGet -Force -Scope CurrentUser; if (-not (Get-Module -ListAvailable -Name PSWindowsUpdate)) { Install-Module -Name PSWindowsUpdate -Force -Scope CurrentUser }; Import-Module PSWindowsUpdate; Get-WindowsUpdate -MicrosoftUpdate -AcceptAll | Out-Host; Install-WindowsUpdate -MicrosoftUpdate -AcceptAll -IgnoreReboot | Out-Host"

echo.
echo Windows Update and optional driver installation complete.
echo If drivers were available, they have been installed.
echo.
:RestartPrompt
set /p restartchoice=Do you want to restart now? (Y/N): 
if /i "%restartchoice%"=="Y" start shutdown /r /t 0
if /i "%restartchoice%"=="N" exit
echo Invalid choice. Please enter Y or N.
goto RestartPrompt