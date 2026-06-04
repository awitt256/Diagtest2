@echo off
:: Elevate to admin if not already
net session >nul 2>&1
if %errorlevel% neq 0 (
    echo This script requires administrator rights.
    echo Relaunching with admin privileges...
    powershell -Command "Start-Process '%~f0' -Verb RunAs"
    exit /b
)

cls
echo ==========================================
echo         FULL SYSTEM INFORMATION
echo ==========================================

:: SYSTEM MANUFACTURER, MODEL, SKU
echo.
echo [System]
powershell -NoProfile -Command "Get-CimInstance Win32_ComputerSystem | ForEach-Object { Write-Host 'Manufacturer : ' $_.Manufacturer; Write-Host 'Model        : ' $_.Model; Write-Host 'System SKU   : ' $_.SystemSKUNumber }"

:: SERIAL NUMBER
echo.
echo [Serial Number]
powershell -NoProfile -Command "(Get-CimInstance Win32_BIOS).SerialNumber"

:: CPU
echo.
echo [CPU]
powershell -NoProfile -Command "(Get-CimInstance Win32_Processor).Name"

:: GPU
echo.
echo [GPU Name + Memory]
powershell -NoProfile -Command "Get-CimInstance Win32_VideoController | ForEach-Object { $name = $_.Name; $vram = [math]::Round($_.AdapterRAM / 1GB, 2); Write-Host $name 'with' $vram 'GB VRAM' }"

:: RAM
echo.
echo [System Memory]
powershell -NoProfile -Command "[math]::Round((Get-CimInstance Win32_ComputerSystem).TotalPhysicalMemory / 1GB, 2).ToString() + ' GB RAM'"

:: DISK
echo.
echo [Disk Drives]
powershell -NoProfile -Command "Get-PhysicalDisk | ForEach-Object { $size = [math]::Round($_.Size / 1GB, 2); $type = if ($_.MediaType) { $_.MediaType } else { 'Unknown' }; Write-Host 'Disk' $_.DeviceId '(' $type '):' $size 'GB' }"

echo.
echo ==========================================
echo Press any key to exit...
pause >nul
