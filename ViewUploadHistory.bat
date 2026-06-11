@echo off
REM Show all files that were changed and uploaded

title Upload History - Changed Files
color 0A

echo.
echo ========================================
echo   Recently Changed Files (Last 10 commits)
echo ========================================
echo.

cd /d "%~dp0"

REM Check if git is available
git --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ERROR: Git is not installed
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

echo.
git log --oneline -10

echo.
echo.
echo ========================================
echo   Detailed Changes (Last 3 commits)
echo ========================================
echo.

git log --name-status -3

echo.
echo.
echo ========================================
echo   Current Status
echo ========================================
echo.

git status

echo.
pause
