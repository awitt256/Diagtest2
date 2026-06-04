@echo off
cls
echo   ^|   \  ^|_ _^|  /   \  / __^| ^| \^| ^|  / _ \  / __^| ^|_   _^| ^|_ _^|  / __^|  / __^|    o O O^|_   _^| ^| __^|  / __^| ^|_   _^|
echo   ^| ^|) ^|  ^| ^|   ^| - ^| ^| (_ ^| ^| .` ^| ^| (_) ^| \__ \   ^| ^|    ^| ^|  ^| (^__   \__ \   o       ^| ^|   ^| _^|   \__ \   ^| ^|   
echo   ^|___/  ^|___^|  ^|_^|_^|  \___^| ^|_\^|_^|  \___/  ^|___/  _^|_^|_  ^|___^|  \___^|  ^|___/  TS__^[O^] _^|_^|_  ^|___^|  ^|___/  _^|_^|_  
echo _^|"""""_^|"""""_^|"""""_^|"""""_^|"""""_^|"""""_^|"""""_^|"""""_^|"""""_^|"""""_^|"""""^|{======_^|"""""_^|"""""_^|"""""_^|"""""^|
echo "`-0-0-'"`-0-0-'"`-0-0-'"`-0-0-'"`-0-0-'"`-0-0-'"`-0-0-'"`-0-0-'"`-0-0-'"`-0-0-'"`-0-0-'.\o--000'"`-0-0-'"`-0-0-'"`-0-0-'"`-0-0-' 
echo.
echo                 DIAGNOSTICS TEST TOOL V.53  - BUILT BY ANTHONY WITT 2025
timeout /t 4 >nul
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
echo   7.  Mic Test              8.  Camera Test            9.  Windows Activation
echo  10.  Keyboard Test        11.  Notepad               12.  Missing Drivers
echo  13.  Windows Test         14. Show Serial/SKU
echo.
echo [ SYSTEM DIAGNOSTICS & HEALTH ]
echo  15. System File Checker
echo  16. SMART Drive Health
echo  17. Memory Diagnostic
echo.
echo [ ADVANCED HARDWARE TESTING ]
echo  18. Stress Test Suite      19. USB Port Test
echo  20. Touchscreen Test       21. Webcam Quality Test
echo.
echo [ NETWORK ]
echo  22. Network Settings       23. Wi-Fi Info
echo.
echo [ SETTINGS / SECURITY ]
echo  24. Camera Settings       25. Activation Settings    26. Sound Settings
echo  27. Account Settings      28. Date/Time Settings     29. Language/Region
echo  30. Windows Defender      31. Windows Update         32. Check Windows Key
echo  33. Windows Version
echo.
echo [ DEPLOYMENT / TESTS ]
echo  34. Sysprep Options       35. Software Framework     36. Burn-In Test
echo  37. SSD Test
echo.
echo [ PERFORMANCE ]
echo  38. Run FurMark           39. Run Heaven Benchmark
echo.
echo [ UTILITIES ]
echo  40. Task Manager          41. Event Viewer           42. Clear Temp Files
echo.
echo [ POWER ]
echo  43. Restart               44. Shutdown               45. Exit
echo =================================================================================
set /p choice=Select an option (1-45): 

:: --------- MAIN MENU LOGIC ---------
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
if "%choice%"=="14" (wmic bios get SerialNumber & wmic computersystem get SystemSKUNumber & pause & goto Menu)
if "%choice%"=="15" goto SystemFileChecker
if "%choice%"=="16" goto SMARTDriveHealth
if "%choice%"=="17" goto MemoryDiagnostic
if "%choice%"=="18" goto StressTestSuite
if "%choice%"=="19" goto USBPortTest
if "%choice%"=="20" goto TouchscreenTest
if "%choice%"=="21" goto WebcamQualityTest
if "%choice%"=="22" goto NetworkSettings
if "%choice%"=="23" (netsh wlan show interfaces & pause & goto Menu)
if "%choice%"=="24" goto CameraSettings
if "%choice%"=="25" goto ActivationSettings
if "%choice%"=="26" goto SoundSettings
if "%choice%"=="27" goto AccountSettings
if "%choice%"=="28" goto DateTimeSettings
if "%choice%"=="29" goto LanguageRegion
if "%choice%"=="30" goto Defender
if "%choice%"=="31" goto WindowsUpdate
if "%choice%"=="32" goto WinKey
if "%choice%"=="33" goto WindowsVersion
if "%choice%"=="34" goto Sysprep
if "%choice%"=="35" goto SF
if "%choice%"=="36" goto Burnin
if "%choice%"=="37" goto SSD
if "%choice%"=="38" goto RunFurMark
if "%choice%"=="39" goto RunHeaven
if "%choice%"=="40" (start taskmgr & goto Menu)
if "%choice%"=="41" (start eventvwr.msc & goto Menu)
if "%choice%"=="42" (echo Cleaning Temp... & del /s /q %temp%\*.* >nul 2>&1 & del /s /q C:\Windows\Prefetch\*.* >nul 2>&1 & echo Done! & pause & goto Menu)
if "%choice%"=="43" goto Restart
if "%choice%"=="44" goto Shutdown
if "%choice%"=="45" goto End

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
pause
goto Menu

:Speaker
echo Playing speaker test sound...
start "" "st.mp3"
pause
goto Menu

:Mic
echo Starting microphone test...
start "" "soundcheck"
pause
goto Menu

:Camera
echo Opening Camera...
start microsoft.windows.camera:
pause
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

:AccountSettings
echo Opening Windows Account Settings...
start ms-settings:yourinfo
goto Menu

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

:WindowsUpdate
cls
echo =================================================================================
echo                  WINDOWS UPDATE & OPTIONAL DRIVER INSTALLER
echo =================================================================================
echo Checking for Windows Updates and optional drivers...
echo.

:: Install PSWindowsUpdate module if needed, then check and install all updates (including drivers)
powershell -command "if (-not (Get-Module -ListAvailable -Name PSWindowsUpdate)) { Install-Module -Name PSWindowsUpdate -Force -Scope CurrentUser }; Import-Module PSWindowsUpdate; Get-WindowsUpdate -MicrosoftUpdate -AcceptAll | Out-Host; Install-WindowsUpdate -MicrosoftUpdate -AcceptAll -AutoReboot | Out-Host"

echo.
echo Windows Update and optional driver installation complete.
echo If drivers were available, they have been installed.
echo.
pause
goto Menu

:WinKey
echo Checking Windows Key
pause
goto Menu

:WindowsVersion
echo Windows Version
pause
goto Menu

:Sysprep
echo Sysprep Options
pause
goto Menu

:SF
echo Software Framework
pause
goto Menu

:Burnin
echo Burn-In Test
pause
goto Menu

:SSD
echo SSD Test
pause
goto Menu

:RunFurMark
echo Running FurMark...
start Furmark
pause
goto Menu

:RunHeaven
echo Running Heaven Benchmark...
start Heaven
pause
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