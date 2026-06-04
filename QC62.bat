@echo off
cls
echo   ^|   \  ^|_ _^|  /   \  / __^| ^| \^| ^|  / _ \  / __^| ^|_   _^| ^|_ _^|  / __^|  / __^|    o O O^|_   _^| ^| __^|  / __^| ^|_   _^|
echo   ^| ^|) ^|  ^| ^|   ^| - ^| ^| (_ ^| ^| .` ^| ^| (_) ^| \__ \   ^| ^|    ^| ^|  ^| (^__   \__ \   o       ^| ^|   ^| _^|   \__ \   ^| ^|   
echo   ^|___/  ^|___^|  ^|_^|_^|  \___^| ^|_\^|_^|  \___/  ^|___/  _^|_^|_  ^|___^|  \___^|  ^|___/  TS__^[O^] _^|_^|_  ^|___^|  ^|___/  _^|_^|_  
echo _^|"""""_^|"""""_^|"""""_^|"""""_^|"""""_^|"""""_^|"""""_^|"""""_^|"""""_^|"""""_^|"""""_^|"""""^|{======_^|"""""_^|"""""_^|"""""_^|"""""^|
echo "`-0-0-'"`-0-0-'"`-0-0-'"`-0-0-'"`-0-0-'"`-0-0-'"`-0-0-'"`-0-0-'"`-0-0-'"`-0-0-'"`-0-0-'.\o--000'"`-0-0-'"`-0-0-'"`-0-0-'"`-0-0-' 
echo.
echo                 DIAGNOSTICS TEST TOOL V.62 - BUILT BY ANTHONY WITT 2025
timeout /t 3 >nul

:Menu
echo =================================================================================
echo                   DIAGNOSTICS TEST TOOL V.62- BUILT BY ANTHONY WITT
echo ================================================================================
echo [ SYSTEM / HARDWARE ]
echo     1.  System Info          2.  Bitlocker Check      3.  Hotkeys Test
echo     4.  Device Manager       5.  Battery Test         6.  Speaker Test
echo     7.  Mic Test             8.  Camera Test          9.  Windows Activation
echo    10.  Keyboard Test       11.  Notepad              12. Windows Update
echo    13.  Windows Test        14.  Show Serial/SKU      15.  Change Audio Output
echo.
echo [ SYSTEM DIAGNOSTICS & HEALTH ]
echo    16.  System File Checker  17.  SMART Drive Health   18.  Memory Diagnostic
echo    19.  Disk Cleanup
echo.
echo [ ADVANCED HARDWARE TESTING ]
echo    20.  Stress Test Suite    21.  Performance Tests   22.  USB Port Test
echo    23.  SSD TEST
echo.
echo [ NETWORK ]
echo    24.  Network Settings    25.  Wi‑Fi Info
echo.
echo [ SETTINGS / SECURITY ]
echo    26.  Camera Settings     27.  Activation Settings
echo    28.  Sound Settings      29.  Account Menu
echo    30.  Date/Time Settings  31.  Language/Region
echo    32.  Defender            33.  Check Windows Key
echo    34.  Windows Version     35.  Computrace Check
echo.
echo [ DEPLOYMENT / TESTS ]
echo    36.  Sysprep Options     37.  Software Framework
echo.
echo [ UTILITIES ]
echo    38.  Task Manager        39.  Event Viewer        40.  Clear Temp Files
echo.
echo [ POWER ]
echo    41.  Restart            42.  Shutdown            43.  Exit
echo.
set /p choice=Select an option (1-43): 
echo.

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
if "%choice%"=="10" goto KBtest
if "%choice%"=="11" goto Notepad
if "%choice%"=="12" goto WindowsUpdate
if "%choice%"=="13" goto Test
if "%choice%"=="14" (
    powershell -Command "Write-Host 'Serial Number:'; (Get-CimInstance Win32_BIOS).SerialNumber; Write-Host ''; Write-Host 'System SKU Number:'; (Get-CimInstance Win32_ComputerSystem).SystemSKUNumber"
    pause
    goto Menu
)
if "%choice%"=="15" (
    call "%~dp0AUDIOR.BAT"
    goto Menu
)
if "%choice%"=="16" goto SystemFileChecker
if "%choice%"=="17" goto SMARTDriveHealth
if "%choice%"=="18" goto MemoryDiagnostic
if "%choice%"=="19" goto DiskCleanup
if "%choice%"=="20" goto StressTestSuite
if "%choice%"=="21" goto PerformanceTests
if "%choice%"=="22" (
    start USBTreeView.exe
    goto Menu
)
if "%choice%"=="23" goto ssd
if "%choice%"=="24" goto NetworkSettings
if "%choice%"=="25" (
    netsh wlan show interfaces
    pause
    goto Menu
)
if "%choice%"=="26" goto CameraSettings
if "%choice%"=="27" goto ActivationSettings
if "%choice%"=="28" goto SoundSettings
if "%choice%"=="29" goto AccountMenu
if "%choice%"=="30" goto DateTimeSettings
if "%choice%"=="31" goto LanguageRegion
if "%choice%"=="32" goto Defender
if "%choice%"=="33" goto WinKey
if "%choice%"=="34" goto WindowsVersion
if "%choice%"=="35" goto Computrace
if "%choice%"=="36" goto Sysprep
if "%choice%"=="37" goto SF
if "%choice%"=="38" (start taskmgr & goto Menu)
if "%choice%"=="39" (start eventvwr.msc & goto Menu)
if "%choice%"=="40" (echo Cleaning Temp... & del /s /q %temp%\*.* >nul 2>&1 & del /s /q C:\Windows\Prefetch\*.* >nul 2>&1 & echo Done! & pause & goto Menu)
if "%choice%"=="41" goto Restart
if "%choice%"=="42" goto Shutdown
if "%choice%"=="43" goto End
goto Menu

:: --------- EXISTING FUNCTIONS (unchanged) ---------
:sysinfo
echo Checking System Info
call sysinfo3.bat
goto Menu

:bitlocker
echo Checking Bitlocker
call bitlockercheck1.bat
goto Menu

:Hotkeys
echo Hotkeys Test
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

:Activation
echo Checking Activation
CALL ACT.BAT
goto Menu

:KBtest
echo ====================================
echo           KEYBOARD TEST
echo ====================================
echo 1. KB Test
echo 2. Doubletyping Check
echo 3. Notepad
echo 4. Exit to Main Menu
echo.
set /p kbchoice=Select an option (1-4): 

if "%kbchoice%"=="1" (start kb.exe & goto KBtest)
if "%kbchoice%"=="2" (start kbtest.exe & goto KBtest)
if "%kbchoice%"=="3" (start notepad & goto KBtest)
if "%kbchoice%"=="4" goto Menu

echo Invalid choice. Please try again.
pause
goto KBtest
:Test
echo Starting Windows Test
start launch-tool.bat
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
if "%accchoice%"=="3" (start account.bat & goto Menu)
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
echo Updating Windows Defender and running a quick scan...
call wd
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

:Computrace
call "%~dp0Computrace.bat"
goto Menu

:Sysprep
echo ================================
echo            SYSPREP
echo ================================
echo 1. Sysprep Restart
echo 2. Sysprep Shutdown
echo 3. Return to main menu
echo.
set /p sysprepchoice=Enter your choice (1-3): 

if "%sysprepchoice%"=="1" (
    echo Running Sysprep with Restart...
    if exist "%SystemRoot%\System32\Sysprep\sysprep.exe" (
        start "" "%SystemRoot%\System32\Sysprep\sysprep.exe" /reboot
    ) else (
        echo Sysprep.exe not found! Please check your Windows installation.
    )
    pause
    goto Sysprep
)

if "%sysprepchoice%"=="2" (
    echo Running Sysprep with Shutdown...
    if exist "%SystemRoot%\System32\Sysprep\sysprep.exe" (
        start "" "%SystemRoot%\System32\Sysprep\sysprep.exe" /shutdown
    ) else (
        echo Sysprep.exe not found! Please check your Windows installation.
    )
    pause
    goto Sysprep
)

if "%sysprepchoice%"=="3" goto Menu


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
echo Starting CrystalDiskInfo
start CrystalDiskInfo
goto Menu

:RunFurMark
echo Running FurMark...
start Furmark
goto Menu

:RunHeaven
echo Running Heaven Benchmark...
start Heaven 
goto Menu

:Runocct
echo Running OCCT Stress Test...
start occt.exe
goto Menu

:Restart
set /p confirm="Are you sure you want to restart? (Y/N): "
if /i "%confirm%"=="Y" start shutdown /r /t 0
if /i "%confirm%"=="N" goto Menu

:Shutdown
set /p confirm="Are you sure you want to shutdown? (Y/N): "
if /i "%confirm%"=="Y" start shutdown /s /t 0
if /i "%confirm%"=="N" goto Menu

:End
exit

:SystemFileChecker
echo Running System File Checker (SFC)...
sfc /scannow
echo.
pause
goto Menu

:SMARTDriveHealth
echo Running SMART Drive Health Check...
echo.
echo Checking drive health status...
powershell -Command "Get-CimInstance Win32_DiskDrive | Select-Object Model,SerialNumber,Size,Status | Format-Table -AutoSize"
echo.
echo For more detailed SMART data, use CrystalDiskInfo or similar tools.
echo.
pause
goto Menu

:MemoryDiagnostic
echo =================================================================================
echo                        MEMORY DIAGNOSTIC TOOL
echo =================================================================================
echo.
echo Choose your memory test option:
echo.
echo 1. Schedule memory test on next restart (Recommended)
echo 2. View last memory test results
echo 3. Quick memory info check
echo 4. Return to main menu
echo.
set /p memchoice=Enter your choice (1-4): 

if "%memchoice%"=="1" (
    echo.
    echo Scheduling Windows Memory Diagnostic to run on next restart...
    mdsched.exe
    echo.
    echo Memory diagnostic has been scheduled.
    echo Your computer will restart and run the memory test.
    echo Results will be available after restart in Event Viewer.
    pause
    goto Menu
)

if "%memchoice%"=="2" (
    echo.
    echo Checking for previous memory diagnostic results...
    echo Opening Event Viewer to show memory diagnostic results...
    start eventvwr.msc /c:"Microsoft-Windows-MemoryDiagnostics-Results/Operational"
    pause
    goto Menu
)

if "%memchoice%"=="3" (
    echo.
    echo Current Memory Information:
    echo.
    powershell -Command "Get-CimInstance Win32_PhysicalMemory | Select-Object Capacity,Speed,Manufacturer,PartNumber | Format-Table -AutoSize"
    echo.
    echo Total Physical Memory:
    powershell -Command "(Get-CimInstance Win32_ComputerSystem).TotalPhysicalMemory"
    echo.
    echo Available Memory:
    powershell -Command "Get-CimInstance Win32_OperatingSystem | Select-Object TotalVisibleMemorySize,FreePhysicalMemory | Format-Table -AutoSize"
    echo.
    pause
    goto Menu
)

if "%memchoice%"=="4" goto Menu

echo Invalid choice. Please try again.
pause
goto MemoryDiagnostic

:StressTestSuite
echo =================================================================================
echo                           STRESS TEST SUITE
echo =================================================================================
echo.
echo WARNING: Stress tests will push your hardware to maximum performance.
echo Ensure adequate cooling and monitor temperatures during testing.
echo.
echo Available Stress Tests:
echo.
echo 1. CPU Stress Test (Built-in)
echo 2. GPU Stress Test (FurMark)
echo 3. Memory Stress Test (Schedule restart test)
echo 4. Combined System Stress Test
echo 5. Temperature Monitor
echo 6. System Performance Info
echo 7. Stress Test OCCT
echo 8. Return to main menu
echo.
set /p stresschoice=Enter your choice (1-8): 

if "%stresschoice%"=="1" (
    echo.
    echo Starting CPU Stress Test...
    echo This will use all CPU cores at 100%% for 60 seconds.
    echo Press Ctrl+C to stop early if needed.
    echo.
    pause
    echo Running CPU stress test...
    powershell -Command "Get-WmiObject -Class Win32_Processor | ForEach-Object { 1..($_.NumberOfCores) | ForEach-Object { Start-Job -ScriptBlock { while($true){1+1} } } }; Start-Sleep 60; Get-Job | Remove-Job -Force"
    echo CPU stress test completed.
    pause
    goto StressTestSuite
)

if "%stresschoice%"=="2" (
    echo.
    echo Launching FurMark GPU Stress Test...
    if exist "Furmark.exe" (
        start Furmark.exe
    ) else (
        echo FurMark not found. Please ensure Furmark.exe is in the same directory.
        echo You can download FurMark from: https://geeks3d.com/furmark/
    )
    pause
    goto StressTestSuite
)

if "%stresschoice%"=="3" (
    echo.
    echo Scheduling comprehensive memory test on next restart...
    mdsched.exe
    echo Memory diagnostic scheduled for next restart.
    pause
    goto StressTestSuite
)

if "%stresschoice%"=="4" (
    echo.
    echo Starting Combined System Stress Test...
    echo This will stress CPU, memory, and disk simultaneously.
    echo Duration: 2 minutes
    echo.
    pause
    
    echo Starting multi-component stress test...
    REM CPU stress
    powershell -Command "1..4 | ForEach-Object { Start-Job -ScriptBlock { while($true){[math]::sqrt((Get-Random))} } }"
    
    REM Memory allocation stress
    powershell -Command "Start-Job -ScriptBlock { $a = @(); while($true){ $a += ,('x' * 1MB); if($a.Count -gt 100){ $a = @() } } }"
    
    REM Disk I/O stress
    powershell -Command "Start-Job -ScriptBlock { while($true){ Get-ChildItem C:\ -Recurse -ErrorAction SilentlyContinue | Out-Null } }"
    
    echo Running combined stress test for 120 seconds...
    timeout /t 120 >nul
    
    REM Clean up background jobs
    powershell -Command "Get-Job | Remove-Job -Force"
    
    echo Combined stress test completed.
    pause
    goto StressTestSuite
)

if "%stresschoice%"=="5" (
    echo.
    echo Current System Temperatures and Performance:
    echo.
    echo CPU Information:
    powershell -Command "Get-CimInstance Win32_Processor | Select-Object Name,LoadPercentage,CurrentClockSpeed | Format-Table -AutoSize"
    echo.
    echo Memory Usage:
    powershell -Command "Get-CimInstance Win32_OperatingSystem | Select-Object TotalVisibleMemorySize,FreePhysicalMemory | Format-Table -AutoSize"
    echo.
    echo Disk Usage:
    powershell -Command "Get-CimInstance Win32_LogicalDisk | Select-Object DeviceID,Size,FreeSpace | Format-Table -AutoSize"
    echo.
    echo Note: For detailed temperature monitoring, use HWiNFO64 or similar tools.
    pause
    goto StressTestSuite
)

if "%stresschoice%"=="6" (
    echo.
    echo System Performance Information:
    echo.
    echo Processor:
    powershell -Command "Get-CimInstance Win32_Processor | Select-Object Name,NumberOfCores,NumberOfLogicalProcessors,MaxClockSpeed | Format-Table -AutoSize"
    echo.
    echo Memory:
    powershell -Command "Get-CimInstance Win32_PhysicalMemory | Select-Object Capacity,Speed,Manufacturer | Format-Table -AutoSize"
    echo.
    echo Graphics:
    powershell -Command "Get-CimInstance Win32_VideoController | Select-Object Name,AdapterRAM | Format-Table -AutoSize"
    echo.
    echo Storage:
    powershell -Command "Get-CimInstance Win32_DiskDrive | Select-Object Model,Size,InterfaceType | Format-Table -AutoSize"
    echo.
    pause
    goto StressTestSuite
)

if "%stresschoice%"=="7" (
    GOTO Runocct
    goto StressTestSuite
)

if "%stresschoice%"=="8" goto Menu

:PerformanceTests
echo =================================================================================
echo                           PERFORMANCE TESTS MENU
echo =================================================================================
echo 1. Burn-In Test
echo 2. Run FurMark
echo 3. Return to main menu
echo.
set /p perfchoice=Select an option (1-3): 

if "%perfchoice%"=="1" goto Burnin
if "%perfchoice%"=="2" goto RunFurMark
if "%perfchoice%"=="3" goto Menu

echo Invalid choice. Please try again.
pause
goto PerformanceTests

:DiskCleanup
echo Running Disk Cleanup...
start %SystemRoot%\system32\cleanmgr.exe
pause
goto Menu

:WindowsUpdate
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

echo Installing security updates and drivers automatically...
powershell -NoProfile -ExecutionPolicy Bypass -Command "Install-PackageProvider -Name NuGet -Force -Scope CurrentUser; if (-not (Get-Module -ListAvailable -Name PSWindowsUpdate)) { Install-Module -Name PSWindowsUpdate -Force -Scope CurrentUser }; Import-Module PSWindowsUpdate; Install-WindowsUpdate -MicrosoftUpdate -AcceptAll -IgnoreReboot -NotCategory 'Upgrades' | Out-Host"

echo.
echo Checking for major updates (e.g., feature updates like Windows 11 25H2)...
powershell -NoProfile -ExecutionPolicy Bypass -Command "Import-Module PSWindowsUpdate; $updates = Get-WindowsUpdate -MicrosoftUpdate -Category 'Upgrades'; if ($updates) { Write-Host 'Available major updates:'; $updates | Format-Table -Property Title, KB, Size; Write-Host 'Do you want to install these major updates? (Y/N): '; $choice = Read-Host; if ($choice -eq 'Y') { Install-WindowsUpdate -MicrosoftUpdate -AcceptAll -IgnoreReboot -Category 'Upgrades' | Out-Host } else { Write-Host 'Major updates skipped.' } } else { Write-Host 'No major updates available.' }"

echo.
echo Windows Update process complete.
echo If drivers were available, they have been installed.
echo.
set /p restartchoice=Do you want to restart now? (Y/N): 
if /i "%restartchoice%"=="Y" start shutdown /r /t 0
if /i "%restartchoice%"=="N" goto Menu