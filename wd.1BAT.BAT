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
echo.
:: Search for WinDef.ps1 in the same folder as this BAT
set "FOUND_WINDEF="
set "SCRIPT_DIR=%~dp0"

if exist "%SCRIPT_DIR%WINDEF.PS1" (
    set "FOUND_WINDEF=%SCRIPT_DIR%WINDEF.PS1"
    goto :found_defender
)

:: Search for WinDef.ps1 in multiple possible locations
for %%D in (d e f g h j k l) do (
    if exist "%%D:\WINDEF.PS1" (
        set "FOUND_WINDEF=%%D:\WINDEF.PS1"
        goto :found_defender
    )
)

if exist "C:\Users\Anthony\OneDrive - Close The Loop Inc\Documents\WINDEF.PS1" (
    set "FOUND_WINDEF=C:\Users\Anthony\OneDrive - Close The Loop Inc\Documents\WINDEF.PS1"
    goto :found_defender
)

if exist "C:\temp\WINDEF.PS1" (
    set "FOUND_WINDEF=C:\temp\WINDEF.PS1"
    goto :found_defender
)
if exist "c:\temp\WINDEF.PS1" (
    set "FOUND_WINDEF=c:\temp\WINDEF.PS1"
    goto :found_defender
)

:found_defender
if defined FOUND_WINDEF (
    echo Found WinDef.ps1 at: %FOUND_WINDEF%
    echo Running script...
    echo.
    powershell.exe -ExecutionPolicy Bypass -File "%FOUND_WINDEF%"
    echo.
    echo Script completed!
) else (
    echo ERROR: Could not find WinDef.ps1 in any known locations.
    echo.
    echo Checked script folder, drives: d,e,f,g,h,j,k,l and folders:
    echo   C:\Users\Anthony\OneDrive - Close The Loop Inc\Documents
    echo   C:\temp
    echo   c:\temp
    echo.
    echo Current directory: %CD%
)
pause