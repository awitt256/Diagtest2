
@echo off
REM Run PowerShell script as Administrator
 
echo Starting USB Format and Copy Script...
timeout /t 2
 
powershell -NoProfile -ExecutionPolicy Bypass -Command "Start-Process powershell -ArgumentList '-NoProfile -ExecutionPolicy Bypass -File \"%~dp0Format-And-Copy-USB.ps1\"' -Verb RunAs -Wait"
 
echo Script completed. You can close this window.
pause