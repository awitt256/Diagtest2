 @echo off
cls
:MainMenu
echo ============================
echo        PnP Utility
echo ============================
echo 1. Driver Pull
echo 2. Driver Push
echo 3. Exit
echo.

set /p Choice=Select an option (1-3): 

if "%Choice%"=="1" goto DriverPull
if "%Choice%"=="2" goto DriverPush
if "%Choice%"=="3" goto End
echo.
echo Invalid choice. Please choose 1, 2, or 3.
echo.
goto MainMenu

:DriverPull
echo Running Driver Pull (DP1)...
call DP1.bat
pause
goto End

:DriverPush
echo Running Driver Push (DRIVEPUSH)...
call DRIVERPUSH.bat
pause
goto End

:End
echo.
echo Done.
exit /b
