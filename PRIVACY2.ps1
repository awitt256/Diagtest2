Write-Host "============================================================" -ForegroundColor Cyan
Write-Host "        DIAGNOSTIC: PRIVACY SCREEN HARDWARE DETECTION       " -ForegroundColor Cyan
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host "[*] Analyzing system hardware bus and active OEM drivers..." -ForegroundColor Yellow

# Pull the System Manufacturer to narrow down our target checks
$SysInfo = Get-CimInstance -ClassName Win32_ComputerSystem
$Vendor = $SysInfo.Manufacturer

Write-Host "Detected Vendor: $Vendor" -ForegroundColor LightBlue

$PrivacyScreenFound = $false
$DetectedFeatureName = ""

# Query ALL PnP Devices once to search through them efficiently
$PnPDevices = Get-CimInstance -ClassName Win32_PnPEntity

if ($Vendor -like "*HP*" -or $Vendor -like "*Hewlett-Packard*") {
    Write-Host "[*] Scanning for HP Sure View signatures..." -ForegroundColor Yellow
    
    # HP handles Sure View via App Helpers, specific display extensions, or specialized ACPI hooks
    $Check = $PnPDevices | Where-Object { 
        $_.Name -like "*Sure View*" -or 
        $_.Description -like "*SureView*" -or
        $_.HardwareID -like "*HPNB001*" # Common HP privacy/display filter ACPI hardware ID
    }
    
    if ($Check) {
        $PrivacyScreenFound = $true
        $DetectedFeatureName = "HP Sure View Technology"
    }

}
elseif ($Vendor -like "*Lenovo*") {
    Write-Host "[*] Scanning for Lenovo Privacy Guard / ePrivacy signatures..." -ForegroundColor Yellow
    
    # Lenovo integrates ePrivacy/Privacy Guard flags into Lenovo PM, View, or specialized display drivers
    $Check = $PnPDevices | Where-Object { 
        $_.Name -like "*Privacy Guard*" -or 
        $_.Name -like "*ePrivacy*" -or
        $_.Description -like "*PrivacyGuard*"
    }
    
    if ($Check) {
        $PrivacyScreenFound = $true
        $DetectedFeatureName = "Lenovo Privacy Guard (ePrivacy Panel)"
    }

}
elseif ($Vendor -like "*Dell*") {
    Write-Host "[*] Scanning for Dell SafeScreen signatures..." -ForegroundColor Yellow
    
    # Dell uses the marketing name SafeScreen for its built-in hardware privacy filters
    $Check = $PnPDevices | Where-Object { 
        $_.Name -like "*SafeScreen*" -or 
        $_.Description -like "*Safe Screen*"
    }
    
    if ($Check) {
        $PrivacyScreenFound = $true
        $DetectedFeatureName = "Dell SafeScreen Technology"
    }
}

# --- GLOBAL FALLBACK ---
# If the vendor mapping misses it (e.g. customized image), search the whole bus for the raw strings
if (-not $PrivacyScreenFound) {
    $FallbackCheck = $PnPDevices | Where-Object { $_.Name -like "*Privacy Screen*" -or $_.Name -like "*Sure View*" -or $_.Name -like "*Privacy Guard*" -or $_.Name -like "*SafeScreen*" }
    if ($FallbackCheck) {
        $PrivacyScreenFound = $true
        $DetectedFeatureName = $FallbackCheck.Name
    }
}

# --- OUTPUT VERDICT ---
if ($PrivacyScreenFound) {
    Write-Host "`n==================== DETECTED ====================" -ForegroundColor Green
    Write-Host "[+] PRIVACY SCREEN CAPABLE: TRUE" -ForegroundColor Green
    Write-Host "[+] Feature Identified:    $DetectedFeatureName" -ForegroundColor Green
    Write-Host "==================================================" -ForegroundColor Green
}
else {
    Write-Host "`n==================== NOT DETECTED ====================" -ForegroundColor Red
    Write-Host "[-] PRIVACY SCREEN CAPABLE: FALSE (or Disabled in BIOS)" -ForegroundColor Red
    Write-Host "--> Note: Standard generic LCD panel detected." -ForegroundColor Yellow
    Write-Host "--> Verify that the component isn't disabled under the Security/Display tab in BIOS." -ForegroundColor Yellow
    Write-Host "======================================================" -ForegroundColor Red
}