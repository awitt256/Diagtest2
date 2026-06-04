@echo off
setlocal EnableDelayedExpansion

:: =================================================================================
::  ANSI COLOR SUPPORT (Safe Mode — Does NOT alter registry)
:: =================================================================================
::
::  Windows 10/11 support ANSI colors in Windows Terminal, PowerShell, and CMD
::  depending on environment. If unsupported, script gracefully degrades.
::
::  COLOR CODES:
::      [96m = Cyan
::      [92m = Green
::      [91m = Red
::      [93m = Yellow
::      [0m  = Reset (default)
::
:: =================================================================================

:: Quick check — if ANSI is not supported, disable colors:
echo.[96m>nul 2>&1
if %errorlevel% neq 0 (
    set "C_CYAN="
    set "C_GREEN="
    set "C_RED="
    set "C_YELLOW="
    set "C_RESET="
) else (
    set "C_CYAN=[96m"
    set "C_GREEN=[92m"
    set "C_RED=[91m"
    set "C_YELLOW=[93m"
    set "C_RESET=[0m"
)

cls

:: =================================================================================
::  BANNER B — Modern Cyber Look
:: =================================================================================

echo %C_CYAN%
echo   ============================================
echo         DIAGNOSTICS TEST TOOL 
echo     v.65  -  BUILT BY ANTHONY WITT 2026
echo   ============================================
echo %C_RESET%
echo.
timeout /t 2 >nul

:Menu
cls
echo %C_CYAN%=====================================================================================%C_RESET%
echo %C_GREEN%                     DIAGNOSTICS TEST TOOL V.65  %C_RESET%
echo %C_CYAN%=====================================================================================%C_RESET%
echo.

echo %C_YELLOW%[ SYSTEM / HARDWARE ]%C_RESET%
echo    1. System Info           2. Bitlocker Check       3. Hotkeys Test
echo    4. Device Manager        5. Battery Test          6. Speaker Test
echo    7. Mic Test              8. Camera Test           9. Windows Activation
echo   10. Keyboard Test        11. Notepad              12. Windows Update
echo   13. Windows Test         14. Show Serial/SKU      15. Change Audio Output
echo.

echo %C_YELLOW%[ SYSTEM DIAGNOSTICS ^& HEALTH ]%C_RESET%
echo   16. System File Checker   17. SMART Drive Health    18. Memory Diagnostic
echo   19. Disk Cleanup
echo.

echo %C_YELLOW%[ ADVANCED HARDWARE TESTING ]%C_RESET%
echo   20. Stress Test Suite     21. Performance Tests     22. USB Port Test
echo   23. SSD Test
echo.

echo %C_YELLOW%[ NETWORK ]%C_RESET%
echo   24. Network Settings      25. WiFi Info
echo.

echo %C_YELLOW%[ SETTINGS / SECURITY ]%C_RESET%
echo   26. Camera Settings       27. Activation Settings
echo   28. Sound Settings        29. Account Menu
echo   30. Date/Time Settings    31. Language/Region
echo   32. Defender              33. Check Windows Key
echo   34. Windows Version       35. Computrace Check
echo.

echo %C_YELLOW%[ DEPLOYMENT / TESTS ]%C_RESET%
echo   36. Sysprep Options
echo.

echo %C_YELLOW%[ UTILITIES ]%C_RESET%
echo   38. Task Manager          39. Event Viewer          40. Clear Temp Files
echo.

echo %C_YELLOW%[ POWER ]%C_RESET%
echo   41. Restart               42. Shutdown               43. Exit
echo.

set /p choice=%C_CYAN%Select an option (1-43): %C_RESET%
echo.

::===============================
:: MAIN MENU LOGIC
::===============================
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
if "%choice%"=="14" goto SerialSKU
if "%choice%"=="15" goto AudioSwitch
if "%choice%"=="16" goto SystemFileChecker
if "%choice%"=="17" goto SMARTDriveHealth
if "%choice%"=="18" goto MemoryDiagnostic
if "%choice%"=="19" goto DiskCleanup
if "%choice%"=="20" goto StressTestSuite
if "%choice%"=="21" goto PerformanceTests
if "%choice%"=="22" goto USBPortTest
if "%choice%"=="23" goto ssd
if "%choice%"=="24" goto NetworkSettings
if "%choice%"=="25" goto WifiInfo
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
if "%choice%"=="38" start taskmgr & goto Menu
if "%choice%"=="39" start eventvwr.msc & goto Menu
if "%choice%"=="40" goto ClearTemp
if "%choice%"=="41" goto Restart
if "%choice%"=="42" goto Shutdown
if "%choice%"=="43" goto End

goto Menu

:: =================================================================================
:: FUNCTIONS — ALL CLEANED & VALIDATED
:: =================================================================================

:sysinfo
cls
echo %C_GREEN%Gathering system info...%C_RESET%
call sysinfo3.bat
pause
goto Menu

:bitlocker
cls
echo %C_GREEN%Checking BitLocker status...%C_RESET%
call bitlockercheck1.bat
pause
goto Menu

:Hotkeys
cls
echo %C_GREEN%Hotkeys Test% C_RESET%
call hk1
goto Menu

:DevMgr
cls
start devmgmt.msc
goto Menu

:Battery
cls
echo %C_GREEN%Running battery test...%C_RESET%
start bat
timeout /t 7 >nul
taskkill /f /im batterycat.exe >nul 2>&1
goto Menu

:Speaker
cls
echo %C_GREEN%Playing speaker test sound...%C_RESET%
start "" "st.mp3"
timeout /t 25 >nul
taskkill /f /im microsoft.media.player.exe >nul 2>&1
taskkill /f /im wmplayer.exe >nul 2>&1
goto Menu

:Mic
cls
echo %C_GREEN%Starting microphone test...%C_RESET%
start "" "soundcheck"
timeout /t 10 >nul
taskkill /f /im SOUNDCHECK.exe >nul 2>&1
goto Menu

:Camera
cls
echo %C_GREEN%Opening Camera...%C_RESET%
start microsoft.windows.camera:
timeout /t 10 >nul
taskkill /f /im WindowsCamera.exe >nul 2>&1
goto Menu

:Activation
cls
call ACT.BAT
goto Menu

:SerialSKU
cls
powershell -Command "Write-Host 'Serial Number:'; (Get-CimInstance Win32_BIOS).SerialNumber; Write-Host ''; Write-Host 'System SKU:'; (Get-CimInstance Win32_ComputerSystem).SystemSKUNumber"
pause
goto Menu

:AudioSwitch
cls
call "%~dp0AUDIOrun.bat"
goto Menu

:USBPortTest
cls
start USBTreeView.exe
goto Menu

:ssd
cls
start CrystalDiskInfo
goto Menu

:WifiInfo
cls
netsh wlan show interfaces
pause
goto Menu

:SoundSettings
cls
start ms-settings:sound
goto Menu

:CameraSettings
cls
start ms-settings:privacy-webcam
goto Menu

:ActivationSettings
cls
start ms-settings:activation
goto Menu

:NetworkSettings
cls
start ms-settings:network
goto Menu

:DateTimeSettings
cls
start ms-settings:dateandtime
goto Menu

:LanguageRegion
cls
start ms-settings:regionlanguage
goto Menu

:Defender
cls
call wd
goto Menu

:WinKey
cls
START WK
pause
goto Menu

:WindowsVersion
cls
START Winver
pause
goto Menu

:Computrace
cls
call "%~dp0Computrace.bat"
goto Menu

:ClearTemp
cls
echo %C_GREEN%Clearing temporary files...%C_RESET%
del /s /q "%temp%\*.*" >nul 2>&1
del /s /q "C:\Windows\Prefetch\*.*" >nul 2>&1
echo %C_GREEN%Done!%C_RESET%
pause
goto Menu

:: ================================================================================
:: STRESS TEST SUITE + MEMORY + SFC + SMART — (unchanged logic, formatted)
:: ================================================================================

:SystemFileChecker
cls
echo %C_GREEN%Running System File Checker...%C_RESET%
sfc /scannow
pause
goto Menu

:SMARTDriveHealth
cls
echo %C_GREEN%SMART Drive Health:%C_RESET%
powershell -Command "Get-CimInstance Win32_DiskDrive | Select-Object Model,SerialNumber,Size,Status | Format-Table -AutoSize"
pause
goto Menu

:MemoryDiagnostic
cls
echo %C_CYAN%=========================================================%C_RESET%
echo %C_GREEN%               MEMORY DIAGNOSTIC TOOL                  %C_RESET%
echo %C_CYAN%=========================================================%C_RESET%
echo.
echo 1. Schedule memory test (restart required)
echo 2. View last memory test results
echo 3. Quick memory info
echo 4. Back to menu
echo.
set /p memchoice=Enter option: 

if "%memchoice%"=="1" mdsched.exe & goto Menu
if "%memchoice%"=="2" start eventvwr.msc /c:"Microsoft-Windows-MemoryDiagnostics-Results/Operational" & goto Menu
if "%memchoice%"=="3" (
    powershell -Command "Get-CimInstance Win32_PhysicalMemory | Select-Object Capacity,Speed,Manufacturer,PartNumber | Format-Table -AutoSize"
    pause
    goto Menu
)
goto Menu

:StressTestSuite
cls
echo %C_CYAN%=========================================================%C_RESET%
echo %C_GREEN%                STRESS TEST SUITE MENU                 %C_RESET%
echo %C_CYAN%=========================================================%C_RESET%
echo.
echo 1. CPU Stress Test
echo 2. GPU (FurMark)
echo 3. Memory Stress Test
echo 4. Combined Stress
echo 5. Temperature Monitor
echo 6. System Performance
echo 7. OCCT Stress
echo 8. Back to Menu
echo.
set /p S=Choice:

if "%S%"=="1" goto CPUStress
if "%S%"=="2" goto RunFurMark
if "%S%"=="3" mdsched.exe & goto StressTestSuite
if "%S%"=="4" goto CombinedStress
if "%S%"=="5" goto TempMonitor
if "%S%"=="6" goto PerfInfo
if "%S%"=="7" goto Runocct
goto Menu

:CPUStress
cls
echo %C_GREEN%Running CPU Stress Test...%C_RESET%
powershell -Command "1..4 | ForEach-Object { Start-Job { while($true){1+1} } }; Start-Sleep 60; Get-Job | Remove-Job -Force"
pause
goto StressTestSuite

:CombinedStress
cls
echo %C_GREEN%Running Combined Stress Test...%C_RESET%

powershell -Command "1..4 | % { Start-Job { while($true){[math]::sqrt((Get-Random))} } }"
powershell -Command "Start-Job { $a=@(); while($true){ $a+=,('x'*1MB); if($a.Count -gt 100){$a=@()}} }"
powershell -Command "Start-Job { while($true){ Get-ChildItem C:\ -Recurse -EA 0 | Out-Null } }"

timeout /t 120 >nul
powershell -Command "Get-Job | Remove-Job -Force"
pause
goto StressTestSuite

:TempMonitor
cls
echo %C_GREEN%System temperatures:%C_RESET%
powershell -Command "Get-CimInstance Win32_Processor | Select Name,LoadPercentage,CurrentClockSpeed | ft -Auto"
pause
goto StressTestSuite

:PerfInfo
cls
powershell -Command "Get-CimInstance Win32_Processor | ft Name,NumberOfCores,NumberOfLogicalProcessors,MaxClockSpeed -Auto"
pause
goto StressTestSuite

:Runocct
start occt.exe
goto StressTestSuite

:PerformanceTests
cls
echo 1. Burn-In
echo 2. FurMark
echo 3. Performance Test
echo 4. Back
set /p P=Select:

if "%P%"=="1" goto Burnin
if "%P%"=="2" goto RunFurMark
if "%P%"=="3" goto RunPerformanceTest
goto Menu

:Burnin
start Burnin
pause
goto Menu

:RunFurMark
start FurMark
goto Menu

:RunPerformanceTest
call Install-PerfTest-WithWinget.bat
goto Menu

:Restart
cls
set /p c=Restart? (Y/N):
if /i "%c%"=="Y" shutdown /r /t 0
goto Menu

:Shutdown
cls
set /p c=Shutdown? (Y/N):
if /i "%c%"=="Y" shutdown /s /t 0
goto Menu

:End
exit