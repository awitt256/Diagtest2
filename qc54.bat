@echo off
cls
echo   ^|   \  ^|_ _^|  /   \  / __^| ^| \^| ^|  / _ \  / __^| ^|_   _^| ^|_ _^|  / __^|  / __^|    o O O^|_   _^| ^| __^|  / __^| ^|_   _^|
echo   ^| ^|) ^|  ^| ^|   ^| - ^| ^| (_ ^| ^| .` ^| ^| (_) ^| \__ \   ^| ^|    ^| ^|  ^| (^__   \__ \   o       ^| ^|   ^| _^|   \__ \   ^| ^|   
echo   ^|___/  ^|___^|  ^|_^|_^|  \___^| ^|_\^|_^|  \___/  ^|___/  _^|_^|_  ^|___^|  \___^|  ^|___/  TS__^[O^] _^|_^|_  ^|___^|  ^|___/  _^|_^|_  
echo _^|"""""_^|"""""_^|"""""_^|"""""_^|"""""_^|"""""_^|"""""_^|"""""_^|"""""_^|"""""_^|"""""_^|"""""^|{======_^|"""""_^|"""""_^|"""""_^|"""""^|
echo "`-0-0-'"`-0-0-'"`-0-0-'"`-0-0-'"`-0-0-'"`-0-0-'"`-0-0-'"`-0-0-'"`-0-0-'"`-0-0-'"`-0-0-'.\o--000'"`-0-0-'"`-0-0-'"`-0-0-'"`-0-0-' 
echo.
echo                 DIAGNOSTICS TEST TOOL V.50  - BUILT BY ANTHONY WITT 2025
timeout /t 3 >nul
@echo off
cls
:Menu
cls
echo =================================================================================
echo                   DIAGNOSTICS TEST TOOL v .53 - BUILT BY ANTHONY WITT
echo ================================================================================
echo [ SYSTEM / HARDWARE ]
echo   1.  System Info           2.  Bitlocker Check        3.  Hotkeys Test
echo   4.  Device Manager        5.  Battery Test           6.  Speaker Test
echo   7.  Mic Test              8.  Camera Test            9.  USB Checker
echo  10.  Windows Activation   11.  Keyboard Test         12.  Notepad
echo  13.  Missing Drivers      14.  Windows Test          15. Show Serial/SKU
echo.
echo [ SYSTEM DIAGNOSTICS ^& HEALTH ]
echo  16. System File Checker
echo  17. SMART Drive Health
echo  18. Memory Diagnostic
echo  19. Disk Cleanup	
echo.
echo [ ADVANCED HARDWARE TESTING ]
echo  20. Stress Test Suite      21. USB Port Test
echo  22. Touchscreen Test       23. Webcam Quality Test
echo.
echo [ NETWORK ]
echo  24. Network Settings       25. Wi-Fi Info
echo.
echo [ SETTINGS / SECURITY ]
echo  26. Camera Settings       27. Activation Settings    28. Sound Settings
echo  29. Account Settings      30. Date/Time Settings     31. Language/Region
echo  32. Windows Defender      33. Windows Update         34. Check Windows Key
echo  35. Windows Version
echo.
echo [ DEPLOYMENT / TESTS ]
echo  36. Sysprep Options       37. Software Framework     38. Burn-In Test
echo  39. SSD Test
echo.
echo [ PERFORMANCE ]
echo  40. Run FurMark           41. Run Heaven Benchmark
echo.
echo [ UTILITIES ]
echo  42. Task Manager          43. Event Viewer           44. Clear Temp Files
echo.
echo [ POWER ]
echo  45. Restart               46. Shutdown               47. Exit
echo =================================================================================
set /p choice=Select an option (1-47): 

:: --------- MAIN MENU LOGIC ---------
if "%choice%"=="1"  goto sysinfo
if "%choice%"=="2"  goto bitlocker
if "%choice%"=="3"  goto Hotkeys
if "%choice%"=="4"  goto DevMgr
if "%choice%"=="5"  goto Battery
if "%choice%"=="6"  goto Speaker
if "%choice%"=="7"  goto Mic
if "%choice%"=="8"  goto Camera
if "%choice%"=="9"  (start USBTreeView.exe & goto Menu)
if "%choice%"=="10" goto Activation
if "%choice%"=="11" goto KB
if "%choice%"=="12" goto Notepad
if "%choice%"=="13" goto Drivers
if "%choice%"=="14" goto Test
if "%choice%"=="15" (wmic bios get SerialNumber & wmic computersystem get SystemSKUNumber & pause & goto Menu)
if "%choice%"=="16" goto SystemFileChecker
if "%choice%"=="17" goto SMARTDriveHealth
if "%choice%"=="18" goto MemoryDiagnostic
if "%choice%"=="19" goto DiskCleanup
if "%choice%"=="20" goto StressTestSuite
if "%choice%"=="21" goto USBPortTest
if "%choice%"=="22" goto TouchscreenTest
if "%choice%"=="23" goto WebcamQualityTest
if "%choice%"=="24" goto NetworkSettings
if "%choice%"=="25" (netsh wlan show interfaces & pause & goto Menu)
if "%choice%"=="26" goto CameraSettings
if "%choice%"=="27" goto ActivationSettings
if "%choice%"=="28" goto SoundSettings
if "%choice%"=="29" goto AccountMenu
if "%choice%"=="30" goto DateTimeSettings
if "%choice%"=="31" goto LanguageRegion
if "%choice%"=="32" goto Defender
if "%choice%"=="33" goto WindowsUpdate
if "%choice%"=="34" goto WinKey
if "%choice%"=="35" goto WindowsVersion
if "%choice%"=="36" goto Sysprep
if "%choice%"=="37" goto SF
if "%choice%"=="38" goto Burnin
if "%choice%"=="39" goto ssd
if "%choice%"=="40" goto RunFurMark
if "%choice%"=="41" goto RunHeaven
if "%choice%"=="42" (start taskmgr & goto Menu)
if "%choice%"=="43" (start eventvwr.msc & goto Menu)
if "%choice%"=="44" (echo Cleaning Temp... & del /s /q %temp%\*.* >nul 2>&1 & del /s /q C:\Windows\Prefetch\*.* >nul 2>&1 & echo Done! & pause & goto Menu)
if "%choice%"=="45" goto Restart
if "%choice%"=="46" goto Shutdown
if "%choice%"=="47" goto End

goto Menu

:: --------- EXISTING FUNCTIONS (unchanged) ---------
:sysinfo
echo Checking System Info
call sysinfo3.bat
pause
goto Menu

:bitlocker
echo Checking Bitlocker
call bitlockercheck1.bat
pause
goto Menu

:Hotkeys
echo Hotkeys Test
call hk1
pause
goto Menu

:DevMgr
echo Opening Device Manager...
start devmgmt.msc
pause
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

:Activation
echo Checking Activation
CALL ACT.BAT
pause
goto Menu

:KB
echo Starting Keyboard Test
start kb
pause
goto Menu

:Notepad
echo Starting Notepad...
start notepad
pause
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

:NetworkSettings
echo Opening Windows Network Settings...
start ms-settings:network
goto Menu

:CameraSettings
echo Opening Windows Camera Settings...
start ms-settings:privacy-webcam
goto Menu

:ActivationSettings
echo Opening Windows Activation Settings...
start ms-settings:activation
goto Menu

:SoundSettings
echo Opening Windows Sound Settings...
start ms-settings:sound
goto Menu

:AccountMenu
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

if "%accchoice%"=="1" (start ms-settings:otherusers & goto AccountMenu)
if "%accchoice%"=="2" (start deleteaccount.bat & goto AccountMenu)
if "%accchoice%"=="3" (start account & goto Menu)
if "%accchoice%"=="4" goto Menu

:DateTimeSettings
echo Opening Windows Date/Time Settings...
start ms-settings:dateandtime
goto Menu

:LanguageRegion
echo Opening Windows Language & Region Settings...
start ms-settings:regionlanguage
goto Menu

:Defender
echo Opening Windows Security (Defender)...
start windowsdefender:
goto Menu

:WinKey
echo Checking Windows Key
START WK
pause
goto Menu

:WindowsVersion
echo Windows Version
START Winver
pause
goto Menu

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

:SF
echo Software Framework
START SF
pause
goto Menu

:Burnin
echo Burn-In Test
START Burnin
pause
goto Menu

:ssd
echo.
echo Launching SeaTools...
start Seatools
goto Menu

:RunFurMark
echo Running FurMark...
start Furmark
goto Menu

:RunHeaven
echo Running Heaven Benchmark...
start Heaven 
goto Menu

:Restart
echo Restarting...
start shutdown /r /t 0
pause

:Shutdown
echo Shutting Down...
start shutdown /s /t 0
pause

:End
exit

:SystemFileChecker
echo Running System File Checker (SFC)...
sfc /scannow
echo.
pause
goto Menu

:DiskCleanup
echo Running Disk Cleanup...
start cleanmgr
pause
goto Menu

:WindowsUpdate
cls
echo =================================================================================
echo                  WINDOWS UPDATE DRIVER INSTALLER
echo =================================================================================
echo Checking for Windows Updates and optional drivers...
echo.

REM Relaunch as admin if needed
net session >nul 2>&1
if %errorlevel% neq 0 (
    powershell -Command "Start-Process '%~f0' -Verb RunAs"
    exit /b
)

powershell -NoProfile -ExecutionPolicy Bypass -Command "Install-PackageProvider -Name NuGet -Force -Scope CurrentUser; if (-not (Get-Module -ListAvailable -Name PSWindowsUpdate)) { Install-Module -Name PSWindowsUpdate -Force -Scope CurrentUser }; Import-Module PSWindowsUpdate; Get-WindowsUpdate -MicrosoftUpdate -AcceptAll | Out-Host; Install-WindowsUpdate -MicrosoftUpdate -AcceptAll -IgnoreReboot | Out-Host"

echo.
echo Windows Update and optional driver installation complete.
echo If drivers were available, they have been installed.
echo.
pause
goto Menu