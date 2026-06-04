@echo off
title Diagnostics Test Tool v5.1 - Anthony Witt 2025
cls

:Menu
cls
echo =================================================================================
echo                   DIAGNOSTICS TEST TOOL v5.1 - BUILT BY ANTHONY WITT
echo =================================================================================
echo [ SYSTEM / HARDWARE ]
echo   1.  System Info           2.  Bitlocker Check        3.  Hotkeys Test
echo   4.  Device Manager        5.  Battery Test           6.  Speaker Test
echo   7.  Mic Test              8.  Camera Test            9.  Windows Activation
echo  10.  Keyboard Test        11.  Notepad               12.  Missing Drivers
echo  13.  Windows Test         33. Show CPU Info          34. Show RAM Info
echo  35. Show GPU Info         36. Show Disk Info         37. Show Serial/SKU
echo.
echo [ NETWORK ]
echo  14. Network Settings      38. Show IP Config         39. Ping Test
echo  40. Wi-Fi Info
echo.
echo [ SETTINGS / SECURITY ]
echo  15. Camera Settings       16. Activation Settings    17. Sound Settings
echo  18. Account Settings      19. Date/Time Settings     20. Language/Region
echo  21. Windows Defender      22. Windows Update         23. Check Windows Key
echo  41. Windows Version
echo.
echo [ DEPLOYMENT / TESTS ]
echo  24. Sysprep Options       25. Software Framework     26. Burn-In Test
echo  27. SSD Test
echo.
echo [ PERFORMANCE ]
echo  28. Run FurMark           29. Run Heaven Benchmark
echo.
echo [ UTILITIES ]
echo  42. Task Manager          43. Event Viewer           44. Services
echo  45. Clear Temp Files
echo.
echo [ POWER ]
echo  30. Restart               31. Shutdown               32. Exit
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
if "%choice%"=="14" goto NetworkSettings
if "%choice%"=="15" goto CameraSettings
if "%choice%"=="16" goto ActivationSettings
if "%choice%"=="17" goto SoundSettings
if "%choice%"=="18" goto AccountSettings
if "%choice%"=="19" goto DateTimeSettings
if "%choice%"=="20" goto LanguageRegion
if "%choice%"=="21" goto Defender
if "%choice%"=="22" goto WindowsUpdate
if "%choice%"=="23" goto WinKey
if "%choice%"=="24" goto Sysprep
if "%choice%"=="25" goto SF
if "%choice%"=="26" goto Burnin
if "%choice%"=="27" goto SSD
if "%choice%"=="28" goto RunFurMark
if "%choice%"=="29" goto RunHeaven
if "%choice%"=="30" goto Restart
if "%choice%"=="31" goto Shutdown
if "%choice%"=="32" goto End

:: --------- NEW FEATURES ---------
if "%choice%"=="33" (wmic cpu get name,NumberOfCores,NumberOfLogicalProcessors,MaxClockSpeed & pause & goto Menu)
if "%choice%"=="34" (wmic memorychip get capacity & echo --- Total in GB --- & powershell -command "(Get-CimInstance Win32_PhysicalMemory | Measure-Object -Property Capacity -Sum).Sum /1GB" & pause & goto Menu)
if "%choice%"=="35" (wmic path win32_VideoController get name,AdapterRAM & pause & goto Menu)
if "%choice%"=="36" (wmic diskdrive get model,size & pause & goto Menu)
if "%choice%"=="37" (wmic bios get SerialNumber & wmic computersystem get SystemSKUNumber & pause & goto Menu)
if "%choice%"=="38" (ipconfig /all | more & pause & goto Menu)
if "%choice%"=="39" (ping 8.8.8.8 & pause & goto Menu)
if "%choice%"=="40" (netsh wlan show interfaces & pause & goto Menu)
if "%choice%"=="41" (ver & systeminfo | findstr /B /C:"OS Name" /C:"OS Version" & pause & goto Menu)
if "%choice%"=="42" (start taskmgr & goto Menu)
if "%choice%"=="43" (start eventvwr.msc & goto Menu)
if "%choice%"=="44" (start services.msc & goto Menu)
if "%choice%"=="45" (echo Cleaning Temp... & del /s /q %temp%\*.* >nul 2>&1 & del /s /q C:\Windows\Prefetch\*.* >nul 2>&1 & echo Done! & pause & goto Menu)

goto Menu

:sysinfo
echo Checking System Info
:: call sysinfo3.bat
pause
goto Menu

:bitlocker
echo Checking Bitlocker
:: call bitlockercheck1.bat
pause
goto Menu

:Hotkeys
echo Hotkeys Test
:: call hk1
pause
goto Menu

:DevMgr
echo Opening Device Manager...
start devmgmt.msc
pause
goto Menu

:Battery
echo Running battery test...
:: start bat
pause
goto Menu

:Speaker
echo Playing speaker test sound...
:: start "" "st.mp3"
pause
goto Menu

:Mic
echo Starting microphone test...
:: start "" "soundcheck"
pause
goto Menu

:Camera
echo Opening Camera...
:: start microsoft.windows.camera:
pause
goto Menu

:Activation
echo Checking Activation
:: CALL ACT.BAT
pause
goto Menu

:KB
echo Starting Keyboard Test
:: start kb
pause
goto Menu

:Notepad
echo Starting Notepad...
start notepad
pause
goto Menu

:Drivers
echo Installing Drivers
:: call "drivers"
pause
goto Menu

:Test
echo Starting Windows Test
:: start ctl.bat
pause
goto Menu

:NetworkSettings
echo Network Settings
pause
goto Menu

:CameraSettings
echo Camera Settings
pause
goto Menu

:ActivationSettings
echo Activation Settings
pause
goto Menu

:SoundSettings
echo Sound Settings
pause
goto Menu

:AccountSettings
echo Account Settings
pause
goto Menu

:DateTimeSettings
echo Date/Time Settings
pause
goto Menu

:LanguageRegion
echo Language/Region Settings
pause
goto Menu

:Defender
echo Windows Defender
pause
goto Menu

:WindowsUpdate
echo Windows Update
pause
goto Menu

:WinKey
echo Checking Windows Key
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
:: start Furmark
pause
goto Menu

:RunHeaven
echo Running Heaven Benchmark...
:: start Heaven
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