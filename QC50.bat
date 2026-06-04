

:Menu
cls
echo ====================================
echo           SYSTEM TOOL MENU
echo ====================================
echo 1.  System Info
echo 2.  Bitlocker Check
echo 3.  Hotkeys Test
echo 4.  Device Manager
echo 5.  Battery Test
echo 6.  Speaker Test
echo 7.  Mic Test
echo 8.  Camera Test
echo 9.  Windows Activation
echo 10. KB Test
echo 11. Notepad
echo 12. Missing Drivers
echo 13. Run Windows Test
echo 14. Sysprep
echo 15. Restart
echo 16. Shutdown
echo 17. Software Framework Driver
echo 18. Burn In Test
echo 19. Settings Menu
echo 20. SSD Test
echo 21. Performance Tests
echo 22. Exit
echo ====================================
set /p choice=Enter your choice (1-22): 

if "%choice%"=="1"  goto sysinfo
if "%choice%"=="2"  goto bitlocker
if "%choice%"=="3"  goto Hotkeys
if "%choice%"=="4"  goto DevMgr
if "%choice%"=="5"  goto Battery
if "%choice%"=="6"  goto Speaker
if "%choice%"=="7"  goto Mic
if "%choice%"=="8"  goto Camera
if "%choice%"=="9"  goto Activation
if "%choice%"=="10" goto KB
if "%choice%"=="11" goto Notepad
if "%choice%"=="12" goto Drivers
if "%choice%"=="13" goto Test
if "%choice%"=="14" goto Sysprep
if "%choice%"=="15" goto Restart
if "%choice%"=="16" goto Shutdown
if "%choice%"=="17" goto SF
if "%choice%"=="18" goto Burnin
if "%choice%"=="19" goto SettingsMenu
if "%choice%"=="20" goto SSD
if "%choice%"=="21" goto Performancetests
if "%choice%"=="22" goto End
goto Menu

:sysinfo
echo Checking System Info
call sysinfo3.bat
goto Menu

:Bitlocker
call bitlockercheck1.bat
goto Menu

:Hotkeys
echo Installing Hotkeys
call hk1
goto Menu

:DevMgr
echo Opening Device Manager...
start devmgmt.msc
goto Menu

:Battery
echo Running battery test...
start bat
timeout /t 7 >nul
taskkill /f /im batterycat.exe >nul 2>&1
goto Menu

:Speaker
echo Playing speaker test sound...
start "" "st.mp3"
timeout /t 25 >nul
taskkill /f /im microsoft.media.player.exe >nul 2>&1
taskkill /f /im wmplayer.exe >nul 2>&1
goto Menu

:Mic
echo Starting microphone test...
start "" "soundcheck"
timeout /t 10 >nul
taskkill /f /im SOUNDCHECK.exe >nul 2>&1
goto Menu

:Camera
echo Opening Camera...
start microsoft.windows.camera:
timeout /t 10 >nul
taskkill /f /im WindowsCamera.exe >nul 2>&1
goto Menu

:Drivers
echo Installing Drivers
call "drivers"
pause
goto Menu

:Test
echo Starting Windows Test
start ctl.bat
pause
goto Menu

:Activation
echo Checking Activation
CALL ACT.BAT
goto Menu

:KB
echo Starting Keyboard Test
start kb
goto Menu

:Burnin
echo Installing Burn in Test
call burnin
goto Menu

:Notepad
echo Starting Notepad...
start notepad
goto Menu

:Restart
echo Restarting...
start shutdown /r /t 0
pause

:Shutdown
echo Shutting Down...
start shutdown /s /t 0
pause
goto menu

:SF
echo  Installing Software Framework Driver
call SF
goto menu

:settingsMenu
cls
echo ====================================
echo          SETTINGS MENU
echo ====================================
echo 1. Network
echo 2. Camera
echo 3. Activation
echo 4. Sound
echo 5. Account
echo 6. Date and Time
echo 7. Language and Region
echo 8. Windows Defender
echo 9. Windows Update
echo 10. Check Windows Key
echo 11. Go Back to Previous Menu
echo.
set /p setchoice=Enter your choice: 

if "%setchoice%"=="1" start ms-settings:network && goto settingsMenu
if "%setchoice%"=="2" start ms-settings:camera && goto settingsMenu
if "%setchoice%"=="3" start ms-settings:activation && goto settingsMenu
if "%setchoice%"=="4" start ms-settings:sound && goto settingsMenu
if "%setchoice%"=="5" goto accountSettings
if "%setchoice%"=="6" start ms-settings:dateandtime && goto settingsMenu
if "%setchoice%"=="7" start ms-settings:regionlanguage && goto settingsMenu
if "%setchoice%"=="8" start windowsdefender://threat && goto settingsMenu
if "%setchoice%"=="9" start ms-settings:windowsupdate-action && goto settingsMenu
if "%setchoice%"=="10" goto WinKey
if "%setchoice%"=="11" goto Menu

echo Invalid choice. Please try again.
pause
goto settingsMenu

@echo off
:Sysprep
cls
echo ================================
echo            SYSPREP
echo ================================
echo 1. Sysprep Restart
echo 2. Sysprep Shutdown
echo 3. Main Menu
echo.

set /p choice=Select an option: 

if "%choice%"=="1" goto SYSPREP_RESTART
if "%choice%"=="2" goto SYSPREP_SHUTDOWN
if "%choice%"=="3" goto Menu
if "%choice%"=="4" goto dbl
pause
goto menu

:accountSettings
cls
echo ====================================
echo        ACCOUNT SETTINGS
echo ====================================
echo 1. Manage Other Users
echo 2. Delete User Account
echo 3. Create Local Account
echo 4. Go Back to Settings Menu
echo.
set /p accchoice=Enter your choice: 

if "%accchoice%"=="1" (start ms-settings:otherusers && goto accountSettings)
if "%accchoice%"=="2" (start deleteaccount.bat && goto accountSettings)
if "%accchoice%"=="3" start account
if "%accchoice%"=="4" goto MENU


echo Invalid choice. Please try again.
pause
goto accountSettings
:SYSPREP_RESTART
cls
echo Running: Sysprep OOBE No Generalize with Restart...
%SystemRoot%\System32\Sysprep\Sysprep.exe /oobe /reboot
goto end

:SYSPREP_SHUTDOWN
cls
echo Running: Sysprep OOBE No Generalize with Shutdown...
%SystemRoot%\System32\Sysprep\Sysprep.exe /oobe /shutdown
goto end

:WinKey
echo.
echo Getting Windows Key
call WK
pause
goto Menu

:ssd
echo.
echo Launching SeaTools...
start seatools
goto menu

:PerformanceTests
cls
echo ====================================
echo         PERFORMANCE TESTS MENU
echo ====================================
echo 1. Run FurMark
echo 2. Run Heaven Benchmark
echo 3. Back to Main Menu
echo ====================================
set /p choice=Enter your choice (1-3): 

if "%choice%"=="1" goto RunFurMark
if "%choice%"=="2" goto RunHeaven
if "%choice%"=="3" goto Menu
goto PerformanceTests

:RunFurMark
echo Launching FurMark...
start Furmark
timeout /t 5
goto PerformanceTests

:RunHeaven
echo Launching Heaven Benchmark...
start Heaven
timeout /t 5
goto PerformanceTests