@echo off
setlocal

:: Elevate to admin if not already
net session >nul 2>&1
if %errorlevel% neq 0 (
    echo This script requires administrator rights.
    echo Relaunching with admin privileges...
    powershell -Command "Start-Process '%~f0' -Verb RunAs"
    exit /b
)

set "LOGFILE=D:\DELL UNIT SPECS.txt"

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
powershell -NoProfile -Command "Get-CimInstance Win32_VideoController | Where-Object { $_.Name -and $_.Name -notmatch 'Intel|Microsoft Basic Display|Basic Display' } | ForEach-Object { $name = $_.Name; $vram = [math]::Round($_.AdapterRAM / 1GB, 2); Write-Host $name 'with' $vram 'GB VRAM' }"

:: RAM
echo.
echo [System Memory]
powershell -NoProfile -Command "[math]::Ceiling((Get-CimInstance Win32_ComputerSystem).TotalPhysicalMemory / 1GB).ToString() + ' GB RAM'"

:: DISK
echo.
echo [Disk Drives]
powershell -NoProfile -Command "$disk0 = Get-PhysicalDisk | Sort-Object DeviceId | Where-Object { $_.DeviceId -eq 0 } | Select-Object -First 1; if (-not $disk0) { $disk0 = Get-PhysicalDisk | Sort-Object DeviceId | Select-Object -First 1 }; if ($disk0) { $size = [math]::Round($disk0.Size / 1GB, 2); $type = if ($disk0.MediaType) { $disk0.MediaType } else { 'Unknown' }; Write-Host 'Disk' $disk0.DeviceId '(' $type '):' $size 'GB' }"

echo.
set /p "ISSUES_NOTES=Any Issues w/ Computer: "
if not defined ISSUES_NOTES set "ISSUES_NOTES=None"

echo.
echo [Saving Dell Unit Specs Log]
powershell -NoProfile -ExecutionPolicy Bypass -Command ^
 "$logFile = '%LOGFILE%';" ^
 "function Format-Size($bytes) {" ^
 "    $gb = $bytes / 1GB;" ^
 "    if ($gb -ge 900 -and $gb -lt 1000) { return '1TB' }" ^
 "    if ($bytes -ge 1TB) { return ('{0:N0}TB' -f ($bytes / 1TB)) }" ^
 "    return ('{0:N0}GB' -f [math]::Round($gb, 0))" ^
 "};" ^
 "$system = Get-CimInstance Win32_ComputerSystem;" ^
 "$serial = ((Get-CimInstance Win32_BIOS).SerialNumber).Trim();" ^
 "$model = ($system.Model).Trim();" ^
 "$systemSku = (($system.SystemSKUNumber) -as [string]).Trim();" ^
 "$cpu = ((Get-CimInstance Win32_Processor | Select-Object -First 1 -ExpandProperty Name) -as [string]).Trim();" ^
 "$notes = (($env:ISSUES_NOTES) -as [string]).Trim();" ^
 "$ram = ('{0:N0} GB' -f [math]::Ceiling($system.TotalPhysicalMemory / 1GB));" ^
 "$gpu = (Get-CimInstance Win32_VideoController | Where-Object { $_.Name -and $_.Name -notmatch 'Intel|Microsoft Basic Display|Basic Display' } | ForEach-Object { $name = $_.Name.Trim(); $vram = if ($_.AdapterRAM) { [math]::Round($_.AdapterRAM / 1GB, 0) } else { $null }; if ($vram) { $name + ' with ' + $vram + ' GB VRAM' } else { $name } } | Where-Object { $_ } | Sort-Object -Unique) -join ' | ';" ^
 "$disk0 = Get-PhysicalDisk | Sort-Object DeviceId | Where-Object { $_.DeviceId -eq 0 } | Select-Object -First 1;" ^
 "if (-not $disk0) { $disk0 = Get-PhysicalDisk | Sort-Object DeviceId | Select-Object -First 1 };" ^
 "$ssd = if ($disk0) { Format-Size $disk0.Size } else { 'Unknown' };" ^
 "if ([string]::IsNullOrWhiteSpace($ssd)) { $ssd = 'Unknown' };" ^
 "if ([string]::IsNullOrWhiteSpace($gpu)) { $gpu = 'Unknown' };" ^
 "if ([string]::IsNullOrWhiteSpace($systemSku)) { $systemSku = 'Unknown' };" ^
 "if ([string]::IsNullOrWhiteSpace($cpu)) { $cpu = 'Unknown' };" ^
 "if ([string]::IsNullOrWhiteSpace($notes)) { $notes = 'None' };" ^
 "$existingCount = 0;" ^
 "if (Test-Path $logFile) {" ^
 "    $existingCount = @(Select-String -Path $logFile -Pattern '^Unit #' -SimpleMatch:$false).Count" ^
 "};" ^
 "$nextNumber = $existingCount + 1;" ^
 "$lines = @(" ^
 "    ('Unit #' + $nextNumber)," ^
 "    ('Serial: ' + $serial)," ^
 "    ('Model: ' + $model)," ^
 "    ('System SKU: ' + $systemSku)," ^
 "    ('CPU: ' + $cpu)," ^
 "    ('GPU: ' + $gpu)," ^
 "    ('System Memory: ' + $ram)," ^
 "    ('Disk Drive: ' + $ssd)," ^
 "    ('Notes: ' + $notes)," ^
 "    ''" ^
 ");" ^
 "Add-Content -Path $logFile -Value $lines;" ^
 "Write-Host ('Saved entry #' + $nextNumber + ' to ' + $logFile)"

echo.
echo ==========================================
echo Press any key to exit...
pause >nul
