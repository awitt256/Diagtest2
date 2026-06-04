@echo off
setlocal enabledelayedexpansion
:: System Information Display Script - CimInstance Version
title System Information

cls
echo ================================================================
echo         SYSTEM INFO REPORT BUILT BY ANTHONY WITT 2025
echo ================================================================
echo.
echo Generated: %date% %time%
echo.

echo ================================================================
echo                     SYSTEM IDENTIFICATION
echo ================================================================

echo [System]
powershell -NoProfile -Command "Get-CimInstance Win32_ComputerSystem | ForEach-Object { Write-Host 'Manufacturer : ' $_.Manufacturer; Write-Host 'Model        : ' $_.Model; Write-Host 'System SKU   : ' $_.SystemSKUNumber }"

echo.
echo [BIOS]
powershell -NoProfile -Command "Get-CimInstance Win32_BIOS | ForEach-Object { Write-Host 'Serial Number: ' $_.SerialNumber }"

echo.
echo ================================================================
echo                        STORAGE INFORMATION
echo ================================================================

echo Logical Drive Information:
powershell -command "try { Get-CimInstance -ClassName Win32_LogicalDisk | Where-Object {$_.DriveType -eq 3} | ForEach-Object { $totalGB = [math]::Round($_.Size/1GB,1); $freeGB = [math]::Round($_.FreeSpace/1GB,1); $usedGB = [math]::Round(($_.Size - $_.FreeSpace)/1GB,1); Write-Host '  Drive '$_.Caption' Total: '$totalGB' GB, Free: '$freeGB' GB, Used: '$usedGB' GB' } } catch { Write-Host '  Error retrieving drive information' }"

echo.
echo Physical Disk Information:
powershell -command "try { Get-CimInstance -ClassName Win32_DiskDrive | ForEach-Object { $sizeGB = [math]::Round($_.Size/1GB,0); Write-Host '  '$_.Model' - '$sizeGB' GB' } } catch { Write-Host '  Error retrieving disk information' }"

echo.
echo ================================================================
echo                        MEMORY INFORMATION
echo ================================================================

echo Total System Memory:
powershell -command "try { $cs = Get-CimInstance -ClassName Win32_ComputerSystem; $ramGB = [math]::Round($cs.TotalPhysicalMemory/1GB,1); Write-Host '  Total RAM: '$ramGB' GB' } catch { Write-Host '  Not Available' }"

echo.
echo Memory Modules:
powershell -command "try { Get-CimInstance -ClassName Win32_PhysicalMemory | ForEach-Object { $capGB = [math]::Round($_.Capacity/1GB,0); $speed = if($_.Speed) { $_.Speed.ToString() + ' MHz' } else { 'Unknown Speed' }; $mfg = if($_.Manufacturer) { $_.Manufacturer.Trim() } else { 'Unknown' }; Write-Host '  Module: '$capGB' GB, '$speed', '$mfg } } catch { Write-Host '  Error retrieving memory information' }"

echo.
echo ================================================================
echo                        GRAPHICS INFORMATION
echo ================================================================

echo Graphics Cards:
powershell -command "try { Get-CimInstance -ClassName Win32_VideoController | ForEach-Object { if($_.AdapterRAM -and $_.AdapterRAM -gt 0) { $vramGB = [math]::Round($_.AdapterRAM/1GB,1); if($vramGB -lt 1) { $vramMB = [math]::Round($_.AdapterRAM/1MB,0); Write-Host '  '$_.Name' - '$vramMB' MB' } else { Write-Host '  '$_.Name' - '$vramGB' GB' } } else { Write-Host '  '$_.Name' - VRAM: Not Available' } } } catch { Write-Host '  Error retrieving graphics information' }"

echo.
echo ================================================================
echo                         WIFI INFORMATION
echo ================================================================

echo Wi-Fi Adapters:
powershell -NoProfile -Command "try { $allAdapters = Get-NetAdapter -Physical -ErrorAction SilentlyContinue; $wifiAdapters = $allAdapters | Where-Object { $_.InterfaceDescription -match 'Wireless|Wi-Fi|802\.11|WLAN' -or $_.Name -match 'Wi-Fi|Wireless|WLAN' }; if (-not $wifiAdapters) { Write-Host '  No Wi-Fi card detected.' } else { foreach ($adapter in $wifiAdapters) { $profile = Get-NetConnectionProfile -InterfaceIndex $adapter.ifIndex -ErrorAction SilentlyContinue; $active = $adapter.Status -eq 'Up'; Write-Host ('  Adapter: ' + $adapter.Name); Write-Host ('  Description: ' + $adapter.InterfaceDescription); Write-Host ('  Adapter Status: ' + $adapter.Status); Write-Host ('  Active: ' + $(if ($active) { 'Yes' } else { 'No' })); if ($active -and $profile) { Write-Host '  Connected to network: Yes'; Write-Host ('  Network name: ' + $profile.Name); Write-Host ('  Network category: ' + $profile.NetworkCategory) } else { Write-Host '  Connected to network: No' }; Write-Host '' } }; Write-Host 'Ethernet Adapters:'; $ethernetAdapters = $allAdapters | Where-Object { $_.InterfaceDescription -notmatch 'Wireless|Wi-Fi|802\.11|WLAN|Bluetooth' -and $_.Name -notmatch 'Wi-Fi|Wireless|WLAN|Bluetooth' }; if (-not $ethernetAdapters) { Write-Host '  No Ethernet adapters detected.' } else { foreach ($adapter in $ethernetAdapters) { $profile = Get-NetConnectionProfile -InterfaceIndex $adapter.ifIndex -ErrorAction SilentlyContinue; $active = $adapter.Status -eq 'Up'; Write-Host ('  Adapter: ' + $adapter.Name); Write-Host ('  Description: ' + $adapter.InterfaceDescription); Write-Host ('  Adapter Status: ' + $adapter.Status); Write-Host ('  Active: ' + $(if ($active) { 'Yes' } else { 'No' })); if ($active -and $profile) { Write-Host '  Connected to network: Yes'; Write-Host ('  Network name: ' + $profile.Name); Write-Host ('  Network category: ' + $profile.NetworkCategory) } else { Write-Host '  Connected to network: No' }; Write-Host '' } } } catch { Write-Host '  Error retrieving network adapter information' }"
echo.
echo ================================================================
echo                      PROCESSOR INFORMATION
echo ================================================================

echo Processor:
powershell -command "try { $cpu = Get-CimInstance -ClassName Win32_Processor | Select-Object -First 1; Write-Host '  '$cpu.Name } catch { Write-Host '  Not Available' }"

echo.
echo Processor Details:
powershell -command "try { $cpu = Get-CimInstance -ClassName Win32_Processor | Select-Object -First 1; Write-Host '  Cores: '$cpu.NumberOfCores', Logical Processors: '$cpu.NumberOfLogicalProcessors', Max Speed: '$cpu.MaxClockSpeed' MHz' } catch { Write-Host '  Details not available' }"

echo.
echo ================================================================
echo                    OPERATING SYSTEM INFORMATION
echo ================================================================

echo Operating System:
powershell -command "try { $os = Get-CimInstance -ClassName Win32_OperatingSystem; Write-Host '  '$os.Caption } catch { Write-Host '  Not Available' }"

echo.
echo OS Details:
powershell -NoProfile -Command "try { $cv = Get-ItemProperty 'HKLM:\SOFTWARE\Microsoft\Windows NT\CurrentVersion'; $displayVersion = $cv.DisplayVersion; if (-not $displayVersion) { $displayVersion = $cv.ReleaseId }; if (-not $displayVersion) { $displayVersion = 'Unknown' }; $os = Get-CimInstance -ClassName Win32_OperatingSystem; Write-Host ('  Windows Release: ' + $displayVersion); Write-Host ('  Build: ' + $os.Version); Write-Host ('  Architecture: ' + $os.OSArchitecture) } catch { Write-Host '  Details not available' }"

echo.
echo System Name: %COMPUTERNAME%
echo Current User: %USERNAME%

echo.
echo ================================================================
echo                           SUMMARY
echo ================================================================
echo.

echo QUICK SYSTEM OVERVIEW:
echo =======================

powershell -command "try { $cs = Get-CimInstance -ClassName Win32_ComputerSystem; $bios = Get-CimInstance -ClassName Win32_BIOS; Write-Host 'Model: '$cs.Model; Write-Host 'Serial: '$bios.SerialNumber; $ramGB = [math]::Round($cs.TotalPhysicalMemory/1GB,0); Write-Host 'RAM: '$ramGB' GB' } catch { Write-Host 'Summary information not available' }"

echo Computer: %COMPUTERNAME%
echo User: %USERNAME%
echo Date: %date% %time%

echo.
echo ================================================================
echo.

pause