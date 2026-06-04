@echo off
:: Check for admin rights
net session >nul 2>&1
if %errorLevel% neq 0 (
    echo Requesting administrator privileges...
    powershell -Command "Start-Process '%~f0' -Verb RunAs"
    exit /b
)

:: Set colors and title
title Running WinDef.ps1
color 0B

echo ========================================
echo Running WinDef.ps1 Script
echo ========================================
echo.

:: CHANGE THIS to your actual WinDef.ps1 location
set "WINDEF_PATH=WINDEF.PS1

:: Check if file exists
if exist "%WINDEF_PATH%" (
    echo Found WinDef.ps1
    echo Running script...
    echo.
    
    :: Run the PowerShell script
    powershell.exe -ExecutionPolicy Bypass -File "%WINDEF_PATH%"
    
    echo.
    echo Script completed!
) else (
    echo ERROR: Cannot find WinDef.ps1 at: %WINDEF_PATH%
    echo.
    echo Current directory: %CD%
)

echo.
pause