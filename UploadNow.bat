@echo off
REM Upload all changed files to GitHub right now

title Upload Changed Files to GitHub
color 0A

echo.
echo ========================================
echo   Uploading All Changed Files
echo ========================================
echo.

cd /d "%~dp0"

REM Check if git is available
git --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ERROR: Git is not installed or not in PATH
    echo Please install Git for Windows
    echo.
    pause
    exit /b 1
)

REM Check if we're in a git repository
git rev-parse --git-dir >nul 2>&1
if %errorlevel% neq 0 (
    echo ERROR: Not in a git repository
    echo.
    pause
    exit /b 1
)

echo Checking for changed files...
git status --short

echo.
echo Adding all changes...
git add -A

echo Committing changes...
git commit -m "Manual upload: %date% %time%"

if %errorlevel% neq 0 (
    echo.
    echo No changes to commit
    echo.
    pause
    exit /b 0
)

echo.
echo Pushing to GitHub...
git push -u origin master

if %errorlevel% equ 0 (
    echo.
    echo ========================================
    echo   SUCCESS - Files uploaded!
    echo ========================================
    echo.
) else (
    echo.
    echo ERROR: Failed to push to GitHub
    echo Please check your internet connection
    echo.
)

echo.
pause
