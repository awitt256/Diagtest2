 @echo off
:: Run DRIVERS2.ps1 as Administrator in PowerShell
cd /d "%~dp0"
powershell -NoProfile -ExecutionPolicy Bypass -Command "Start-Process powershell -ArgumentList '-NoProfile -ExecutionPolicy Bypass -File \"%~dp0DRIVERS3.ps1\"' -Verb RunAs"
exit
