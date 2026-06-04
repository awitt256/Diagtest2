
@echo off
setlocal EnableDelayedExpansion

:: =============================================================================
:: EXE‑READY MODE — ALWAYS RUN FROM THIS SCRIPT'S DIRECTORY
:: =============================================================================
cd /d "%~dp0"

:: =============================================================================
:: ANSI COLOR SUPPORT (Safe Mode — No Registry Change)
:: =============================================================================

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

:: =============================================================================
:: SEARCH INDEX (Description = number label)
:: =============================================================================

set "S1=System Info=1 sysinfo"
set "S2=Bitlocker Check=2 bitlocker"
set "S3=Hotkeys Test=3 Hotkeys"
set "S4=Device Manager=4 DevMgr"
set "S5=Battery Test=5 Battery"
set "S6=Speaker Test=6 Speaker"
set "S7=Mic Test=7 Mic"
set "S8=Camera Test=8 Camera"
set "S9=Windows Activation=9 Activation"
set "S10=Keyboard Test=10 KBtest"
set "S11=Notepad=11 Notepad"
set "S12=Windows Update=12 WindowsUpdate"
set "S13=Windows Test=13 Test"
set "S14=Serial/SKU=14 SerialSKU"
set "S15=Audio Output=15 AudioSwitch"
set "S16=SFC Scan=16 SystemFileChecker"
set "S17=SMART Health=17 SMARTDriveHealth"
set "S18=Memory Diagnostic=18 MemoryDiagnostic"
set "S19=Disk Cleanup=19 DiskCleanup"
set "S20=Stress Test Suite=20 StressTestSuite"
set "S21=Performance Tests=21 PerformanceTests"
set "S22=USB Port Test=22 USBPortTest"
set "S23=SSD Test=23 ssd"
set "S24=Network Settings=24 NetworkSettings"
set "S25=WiFi Info=25 WifiInfo"
set "S26=Camera Settings=26 CameraSettings"
set "S27=Activation Settings=27 ActivationSettings"
set "S28=Sound Settings=28 SoundSettings"
set "S29=Account Menu=29 AccountMenu"
set "S30=Date/Time Settings=30 DateTimeSettings"
set "S31=Language/Region=31 LanguageRegion"
set "S32=Defender=32 Defender"
set "S33=Windows Key Check=33 WinKey"
set "S34=Windows Version=34 WindowsVersion"
set "S35=Computrace Check=35 Computrace"
set "S36=Sysprep Options=36 Sysprep"
set "S38=Task Manager=38 Task"
set "S39=Event Viewer=39 Event"
set "S40=Clear Temp Files=40 ClearTemp"
set "S41=Restart=41 Restart"
set "S42=Shutdown=42 Shutdown"
set "S43=Exit Program=43 End"

:: =============================================================================
:: MAIN MENU (Now Includes Bottom Search)
:: =============================================================================

:Menu
cls
set "query="

:MenuLoop
cls
echo %C_CYAN%=====================================================================================%C_RESET%
echo %C_GREEN%                     DIAGNOSTICS TEST TOOL V.66%C_RESET%
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

echo %C_YELLOW%[ UTILITIES / POWER ]%C_RESET%
echo   36. Sysprep Options       38. Task Manager          39. Event Viewer
echo   40. Clear Temp Files      41. Restart               42. Shutdown
echo   43. Exit
echo.

echo %C_CYAN%---------------------------------------------%C_RESET%
echo Search (Type text to search)
echo Current search: %C_GREEN%!query!%C_RESET%
echo.

set matchCount=0

if not "!query!"=="" (
    echo Matches:
    echo.
    for /l %%I in (1,1,43) do (
    for /f "tokens=1,* delims==" %%A in ("!S%%I!") do (
        set "DESC=%%A"
        set "REST=%%B"

        echo !DESC! | findstr /I "!query!" >nul
        if not errorlevel 1 (
            echo %C_GREEN%[%%I] !DESC!%C_RESET%
            set /a matchCount+=1
        )
    )
)
    if !matchCount!==0 echo %C_RED%No matches found.%C_RESET%
    echo.
)

set /p input=Select # or type search: 
set "input=%input:"=%"

if /i "%input%"=="x" (
    set "query="
    goto MenuLoop
)

echo "%input%" | findstr /R "^[0-9][0-9]*$" >nul
if not errorlevel 1 goto %input%

set "query=%input%"
goto MenuLoop

:: =============================================================================
:: FUNCTION HANDLERS (EXE‑READY)
:: =============================================================================

:sysinfo
cls
call "%~dp0Tools\sysinfo3.bat"
pause
goto Menu

:bitlocker
cls
call "%~dp0Tools\bitlockercheck1.bat"
pause
goto Menu

:Hotkeys
cls
call "%~dp0Tools\hk1.bat"
goto Menu

:DevMgr
cls
start "" devmgmt.msc
goto Menu

:Battery
cls
start "" "%~dp0Apps\bat"
timeout /t 7 >nul
taskkill /f /im batterycat.exe >nul 2>&1
goto Menu

:Speaker
cls
start "" "%~dp0Media\st.mp3"
timeout /t 25 >nul
taskkill /f /im wmplayer.exe >nul 2>&1
goto Menu

:Mic
cls
start "" "%~dp0Apps\soundcheck.exe"
timeout /t 10 >nul
taskkill /f /im soundcheck.exe >nul 2>&1
goto Menu

:Camera
cls
start microsoft.windows.camera:
timeout /t 10 >nul
taskkill /f /im WindowsCamera.exe >nul 2>&1
goto Menu

:Activation
cls
call "%~dp0Tools\ACT.bat"
goto Menu

:SerialSKU
cls
powershell -Command "Write-Host 'Serial Number:'; (Get-CimInstance Win32_BIOS).SerialNumber; Write-Host ''; Write-Host 'System SKU:'; (Get-CimInstance Win32_ComputerSystem).SystemSKUNumber"
pause
goto Menu

:AudioSwitch
cls
call "%~dp0Tools\AUDIOrun.bat"
goto Menu

:USBPortTest
cls
start "" "%~dp0Apps\USBTreeView.exe"
goto Menu

:ssd
cls
start "" "%~dp0Apps\CrystalDiskInfo.exe"
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
call "%~dp0Tools\wd.bat"
goto Menu

:WinKey
cls
start "" "%~dp0Apps\WK.exe"
pause
goto Menu

:WindowsVersion
cls
start "" Winver
pause
goto Menu

:Computrace
cls
call "%~dp0Tools\Computrace.bat"
goto Menu

:ClearTemp
cls
echo %C_GREEN%Clearing temporary files...%C_RESET%
del /s /q "%temp%\*.*" >nul 2>&1
del /s /q "C:\Windows\Prefetch\*.*" >nul 2>&1
echo %C_GREEN%Done!%C_RESET%
pause
goto Menu

:SystemFileChecker
cls
sfc /scannow
pause
goto Menu

:SMARTDriveHealth
cls
powershell -Command "Get-CimInstance Win32_DiskDrive | Select-Object Model,SerialNumber,Size,Status | Format-Table -AutoSize"
pause
goto Menu

:MemoryDiagnostic
cls
echo 1. Schedule memory test
echo 2. View last results
echo 3. Quick memory info
echo 4. Back
set /p memchoice=Option: 
if "%memchoice%"=="1" mdsched.exe & goto Menu
if "%memchoice%"=="2" start eventvwr.msc /c:"Microsoft-Windows-MemoryDiagnostics-Results/Operational" & goto Menu
if "%memchoice%"=="3" powershell -Command "Get-CimInstance Win32_PhysicalMemory | Format-Table -AutoSize" & pause
goto Menu

:StressTestSuite
cls
echo 1. CPU Stress
echo 2. FurMark GPU
echo 3. Memory Stress
echo 4. Combined Stress
echo 5. Temperature Monitor
echo 6. Sys Performance
echo 7. OCCT Stress
echo 8. Back
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
powershell -Command "1..4 | % { Start-Job { while($true){1+1} } }; Start-Sleep 60; Get-Job | Remove-Job -Force"
pause
goto StressTestSuite

:RunFurMark
start "" "%~dp0Apps\FurMark.exe"
goto Menu

:Runocct
start "" "%~dp0Apps\occt.exe"
goto StressTestSuite

:Burnin
start "" "%~dp0Apps\Burnin.exe"
pause
goto Menu

:RunPerformanceTest
call "%~dp0Tools\Install-PerfTest-WithWinget.bat"
goto Menu

:CombinedStress
cls
powershell -Command "1..4 | % { Start-Job { while($true){[math]::sqrt((Get-Random))} } }"
timeout /t 120 >nul
powershell -Command "Get-Job | Remove-Job -Force"
pause
goto StressTestSuite

:TempMonitor
cls
powershell -Command "Get-CimInstance Win32_Processor | ft Name,LoadPercentage,CurrentClockSpeed -Auto"
pause
goto StressTestSuite

:PerfInfo
cls
powershell -Command "Get-CimInstance Win32_Processor | ft Name,NumberOfCores,NumberOfLogicalProcessors -Auto"
pause
goto StressTestSuite

:Restart
cls
set /p c=Restart? (Y/N): 
if /I "%c%"=="Y" shutdown /r /t 0
goto Menu

:Shutdown
cls
set /p c=Shutdown? (Y/N): 
if /I "%c%"=="Y" shutdown /s /t 0
goto Menu

:End
exit