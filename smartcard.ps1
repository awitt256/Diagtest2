# Ensure the script is running with administrative privileges
$isAdmin = ([Security.Principal.WindowsPrincipal][Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)

if (-not $isAdmin) {
    Write-Warning "This diagnostic utility must be run as an Administrator to force hardware rescans."
    Exit
}

Write-Host "============================================================" -ForegroundColor Cyan
Write-Host "        DIAGNOSTIC TEST: SMART CARD READER DETECTION        " -ForegroundColor Cyan
Write-Host "============================================================" -ForegroundColor Cyan

# 1. Force a PnP scan to refresh the device tree
Write-Host "[*] Triggering Windows Plug-and-Play hardware rescan..." -ForegroundColor Yellow
pnputil /scan-devices | Out-Null
Write-Host "[+] Hardware scan complete." -ForegroundColor Green

Write-Host "`n[*] Querying system hardware properties..." -ForegroundColor Yellow

# Windows Smart Card Reader official Setup Class GUID
$SmartCardClassGuid = "{50DD5230-BA8A-11D1-BF5D-0000F805F530}"

# Query the PnP Entity table directly for the official GUID
$Devices = Get-CimInstance -ClassName Win32_PnPEntity -Filter "ClassGuid = '$SmartCardClassGuid'"

# Fallback string match if the ClassGuid check didn't catch anything unusual
if (-not $Devices) {
    $Devices = Get-CimInstance -ClassName Win32_PnPEntity -Filter "Description LIKE '%Smart Card%'"
}

if ($Devices) {
    Write-Host "`n==================== TEST RESULT: PASS ====================" -ForegroundColor Green
    Write-Host "[+] Found $($Devices.Count) physical Smart Card Reader(s)!`n" -ForegroundColor Green

    $Index = 1
    foreach ($Dev in $Devices) {
        Write-Host "--- Reader #$Index ---" -ForegroundColor Cyan
        Write-Host "Device Name:   $($Dev.Name)"
        Write-Host "Description:   $($Dev.Description)"
        Write-Host "Status:        $($Dev.Status)"
        Write-Host "Device ID:     $($Dev.DeviceID)"
        Write-Host "--------------------------------------------"
        $Index++
    }
    Write-Host "============================================================" -ForegroundColor Green
} else {
    Write-Host "`n==================== TEST RESULT: FAIL ====================" -ForegroundColor Red
    Write-Host "[!] CRITICAL: No physical Smart Card Reader detected on this unit." -ForegroundColor Red
    Write-Host "    - Check if the hardware module is physically installed."
    Write-Host "    - Verify that 'Smart Card Slot' is enabled in the BIOS."
    Write-Host "============================================================" -ForegroundColor Red
}