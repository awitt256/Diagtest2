@echo off
:: Wrapper seguro para ejecutar Windows Test Tool
:: Este archivo simplemente llama al script de PowerShell firmado
cd /d "%~dp0"
powershell.exe -NoProfile -ExecutionPolicy Bypass -File "script\launch-tool.ps1" %*
