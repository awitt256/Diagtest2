@echo off
setlocal

REM Check if Node.js is installed
where node >nul 2>&1
if errorlevel 1 (
    echo Node.js is not installed or not in PATH.
    echo Please install Node.js from https://nodejs.org and try again.
    pause
    exit /b 1
)

REM Run the JS file in the same folder as this BAT
node "%~dp0KBTEST.js"

endlocal