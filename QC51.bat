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
