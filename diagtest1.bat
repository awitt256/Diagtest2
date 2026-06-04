@echo off
cls
echo   ^|   \  ^|_ _^|  /   \  / __^| ^| \^| ^|  / _ \  / __^| ^|_   _^| ^|_ _^|  / __^|  / __^|    o O O^|_   _^| ^| __^|  / __^| ^|_   _^|
echo   ^| ^|) ^|  ^| ^|   ^| - ^| ^| (_ ^| ^| .` ^| ^| (_) ^| \__ \   ^| ^|    ^| ^|  ^| (^__   \__ \   o       ^| ^|   ^| _^|   \__ \   ^| ^|   
echo   ^|___/  ^|___^|  ^|_^|_^|  \___^| ^|_\^|_^|  \___/  ^|___/  _^|_^|_  ^|___^|  \___^|  ^|___/  TS__^[O^] _^|_^|_  ^|___^|  ^|___/  _^|_^|_  
echo _^|"""""_^|"""""_^|"""""_^|"""""_^|"""""_^|"""""_^|"""""_^|"""""_^|"""""_^|"""""_^|"""""^|{======_^|"""""_^|"""""_^|"""""_^|"""""^|
echo "`-0-0-'"`-0-0-'"`-0-0-'"`-0-0-'"`-0-0-'"`-0-0-'"`-0-0-'"`-0-0-'"`-0-0-'"`-0-0-'"`-0-0-'.\o--000'"`-0-0-'"`-0-0-'"`-0-0-'"`-0-0-' 
echo.
echo                 DIAGNOSTICS TEST TOOL V.60  - BUILT BY ANTHONY WITT 2025
timeout /t 3 >nul

:Menu
cls
echo ====================================
echo      ENHANCED SYSTEM TOOL MENU
echo ====================================
echo HARDWARE TESTS:
echo 1.  System Info           15. RAM Test
echo 2.  Bitlocker Check       16. CPU Stress Test
echo 3.  Device Manager        17. Temperature Monitor
echo 4.  Battery Test          18. Burn In Test
echo 5.  Missing Drivers       19. SSD Test
echo 6.  Performance Tests     20. HDD Health Check
echo.
echo CONNECTIVITY TESTS:
echo 7.  Speaker Test          21. Network Diagnostics
echo 8.  Microphone Test       22. WiFi Speed Test
echo 9.  Camera Test           23. Internet Connectivity
echo 10. Hotkeys Test          24. Port Scanner
echo 11. Keyboard Test
echo.
echo SYSTEM MAINTENANCE:
echo 12. Windows Activation    25. Disk Cleanup
echo 13. Run Windows Test      26. Registry Cleanup
echo 14. Event Viewer          27. Temp Files Clean
echo                          28. System File Check
echo                          29. Update System
echo.
echo UTILITIES:
echo 30. Settings Menu         33. Create System Report
echo 31. Sysprep              34. Export System Info
echo 32. Notepad              35. Quick Health Scan
echo.
echo POWER OPTIONS:
echo 36. Restart               37. Shutdown
echo.
echo 38. Exit
echo ====================================
set /p choice=Enter your choice (1-38): 

if "%choice%"=="1"  goto sysinfo
if "%choice%"=="2"  goto bitlocker
if "%choice%"=="3"  goto DevMgr
if "%choice%"=="4"  goto Battery
if "%choice%"=="5"  goto Drivers
if "%choice%"=="6"  goto Performancetests
if "%choice%"=="7"  goto Speaker
if "%choice%"=="8"  goto Mic
if "%choice%"=="9"  goto Camera
if "%choice%"=="10" goto Hotkeys
if "%choice%"=="11" goto KB
if "%choice%"=="12" goto Activation
if "%choice%"=="13" goto Test
if "%choice%"=="14" goto EventViewer
if "%choice%"=="15" goto RAMTest
if "%choice%"=="16" goto CPUStress
if "%choice%"=="17" goto TempMonitor
if "%choice%"=="18" goto Burnin
if "%choice%"=="19" goto SSD
if "%choice%"=="20" goto HDDHealth
if "%choice%"=="21" goto NetworkDiag
if "%choice%"=="22" goto WiFiSpeed
if "%choice%"=="23" goto InternetTest
if "%choice%"=="24" goto PortScan
if "%choice%"=="25" goto DiskClean
if "%choice%"=="26" goto RegClean
if "%choice%"=="27" goto TempClean
if "%choice%"=="28" goto SFC
if "%choice%"=="29" goto UpdateSystem
if "%choice%"=="30" goto SettingsMenu
if "%choice%"=="31" goto Sysprep
if "%choice%"=="32" goto Notepad
if "%choice%"=="33" goto SystemReport
if "%choice%"=="34" goto ExportInfo
if "%choice%"=="35" goto QuickScan
if "%choice%"=="36" goto Restart
if "%choice%"=="37" goto Shutdown
if "%choice%"=="38" goto End
goto Menu

:sysinfo
echo Checking System Info
call sysinfo3.bat
goto Menu

:Bitlocker
call bitlockercheck1.bat
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

:Drivers
echo Installing Drivers
call "drivers"
pause
goto Menu

:Performancetests
cls
echo ====================================
echo         PERFORMANCE TESTS MENU
echo ====================================
echo 1. Run FurMark (GPU Stress)
echo 2. Run Heaven Benchmark
echo 3. CPU-Z (System Info)
echo 4. GPU-Z (Graphics Info)
echo 5. Back to Main Menu
echo ====================================
set /p choice=Enter your choice (1-5): 

if "%choice%"=="1" goto RunFurMark
if "%choice%"=="2" goto RunHeaven
if "%choice%"=="3" goto RunCPUZ
if "%choice%"=="4" goto RunGPUZ
if "%choice%"=="5" goto Menu
goto Performancetests

:RunFurMark
echo Launching FurMark...
start Furmark
timeout /t 5
goto Performancetests

:RunHeaven
echo Launching Heaven Benchmark...
start Heaven
timeout /t 5
goto Performancetests

:RunCPUZ
echo Launching CPU-Z...
start cpuz.exe
goto Performancetests

:RunGPUZ
echo Launching GPU-Z...
start gpuz.exe
goto Performancetests

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

:Hotkeys
echo Installing Hotkeys
call hk1
goto Menu

:KB
echo Starting Keyboard Test
start kb
goto Menu

:Activation
echo Checking Activation
CALL ACT.BAT
goto Menu

:Test
echo Starting Windows Test
start ctl.bat
pause
goto Menu

:EventViewer
echo Opening Event Viewer...
start eventvwr.msc
goto Menu

:RAMTest
echo Starting Windows Memory Diagnostic...
start mdsched.exe
echo System will restart to run memory test.
pause
goto Menu

:CPUStress
echo Running CPU Stress Test...
powershell -Command "for($i=1;$i -le (Get-WmiObject -Class Win32_ComputerSystem).NumberOfLogicalProcessors;$i++){Start-Job -ScriptBlock{$result = 1; foreach ($number in 1..2147483647){$result = $result * $number}}}; Write-Host 'CPU Stress test running... Press any key to stop'; Read-Host; Get-Job | Remove-Job -Force"
goto Menu

:TempMonitor
echo Checking system temperatures...
powershell -Command "Get-WmiObject -Namespace root/OpenHardwareMonitor -Class Sensor | Where-Object {$_.SensorType -eq 'Temperature'} | Format-Table Name, Value -AutoSize"
echo If no data shown, install HWMonitor or similar tool
pause
goto Menu

:Burnin
echo Installing Burn in Test
call burnin
goto Menu

:SSD
echo Launching SeaTools...
start seatools
goto Menu

:HDDHealth
echo Checking HDD/SSD Health...
echo Running CHKDSK scan...
echo.
chkdsk C: /f /r /x
echo.
echo Running SMART status check...
wmic diskdrive get status
pause
goto Menu

:NetworkDiag
echo Running Network Diagnostics...
echo.
echo Testing network adapter configuration...
ipconfig /all > "%TEMP%\network_info.txt"
echo.
echo Running network troubleshooter...
msdt.exe -id NetworkDiagnosticsNetworkAdapter
echo.
echo Network info saved to: %TEMP%\network_info.txt
pause
goto Menu

:WiFiSpeed
echo Testing WiFi Speed...
echo Opening built-in network speed test...
start ms-settings:network-status
echo.
echo Alternative: Running ping tests...
ping -t google.com
goto Menu

:InternetTest
echo Testing Internet Connectivity...
echo.
ping -n 4 8.8.8.8
echo.
ping -n 4 google.com
echo.
nslookup google.com
pause
goto Menu

:PortScan
echo Checking open ports...
netstat -an | find "LISTENING"
echo.
echo Active network connections:
netstat -b
pause
goto Menu

:DiskClean
echo Running Disk Cleanup...
cleanmgr /sagerun:1
goto Menu

:RegClean
echo Starting Registry Cleanup...
echo WARNING: Registry cleanup can be risky!
echo Opening Registry Editor for manual inspection...
start regedit
echo.
echo For automated cleanup, consider using CCleaner or similar tools
pause
goto Menu

:TempClean
echo Cleaning temporary files...
del /q /s "%TEMP%\*.*" 2>nul
del /q /s "C:\Windows\Temp\*.*" 2>nul
del /q /s "%USERPROFILE%\AppData\Local\Temp\*.*" 2>nul
echo.
echo Temporary files cleaned!
pause
goto Menu

:SFC
echo Running System File Checker...
sfc /scannow
echo.
echo Running DISM health check...
DISM /Online /Cleanup-Image /CheckHealth
echo.
DISM /Online /Cleanup-Image /ScanHealth
echo.
DISM /Online /Cleanup-Image /RestoreHealth
pause
goto Menu

:UpdateSystem
echo Checking for Windows Updates...
start ms-settings:windowsupdate-action
echo.
echo Running Windows Update t