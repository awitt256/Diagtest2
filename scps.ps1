# Ensure the script is running with administrative privileges
$isAdmin = ([Security.Principal.WindowsPrincipal][Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)
if (-not $isAdmin) {
    Write-Warning "This script must be run as an Administrator to modify system power configurations."
    Exit
}

Write-Host "============================================================" -ForegroundColor Cyan
Write-Host "        GETAC DIAGNOSTIC: DISABLE SMART CARD POWER SAVING    " -ForegroundColor Cyan
Write-Host "============================================================" -ForegroundColor Cyan

# Step 1: Disable USB Selective Suspend in Windows Power Settings
Write-Host "[*] Disabling USB Selective Suspend globally..." -ForegroundColor Yellow
# 2a0337f6-dd84-474c-a981-eba10d440d5b is the GUID for USB Settings
# 4867297d-12ee-4710-818a-406c4e0ea716 is the GUID for USB Selective Suspend
powercfg /setacvalueindex SCHEME_CURRENT 2a0337f6-dd84-474c-a981-eba10d440d5b 4867297d-12ee-4710-818a-406c4e0ea716 0
powercfg /setdcvalueindex SCHEME_CURRENT 2a0337f6-dd84-474c-a981-eba10d440d5b 4867297d-12ee-4710-818a-406c4e0ea716 0
# Apply the changes immediately
powercfg /setactive SCHEME_CURRENT
Write-Host "[+] USB Selective Suspend disabled." -ForegroundColor Green

# Step 2: Target the Smart Card Reader Class Driver Settings
Write-Host "`n[*] Modifying Smart Card Driver Power Management Flags..." -ForegroundColor Yellow
$SmartCardClassPath = "HKLM:\SYSTEM\CurrentControlSet\Control\Class\{50DD5230-BA8A-11D1-BF5D-0000F805F530}"

if (Test-Path $SmartCardClassPath) {
    # Get all subkeys (individual hardware device configurations under this class)
    $SubKeys = Get-ChildItem -Path $SmartCardClassPath | Where-Object { $_.PSChildName -match "^\d{4}$" }

    if ($SubKeys) {
        foreach ($Key in $SubKeys) {
            $DevicePath = $Key.PSPath
            Write-Host "  -> Tuning device instance properties at: $($Key.PSChildName)" -ForegroundColor Cyan
            
            # Force the idle power state values to 0 (Disabled)
            # This mimics unchecking 'Allow the computer to turn off this device to save power'
            Set-ItemProperty -Path $DevicePath -Name "IdleInWorkingState" -Value 0 -ErrorAction SilentlyContinue
            Set-ItemProperty -Path $DevicePath -Name "WdfPowerDeviceWakeToWdfPowerDeviceInvalid" -Value 1 -ErrorAction SilentlyContinue
        }
        Write-Host "[+] Registry modifications applied to Smart Card Class entries." -ForegroundColor Green
    } else {
        Write-Host "[-] Class GUID found, but no active device instances enumerated yet." -ForegroundColor Gray
    }
} else {
    Write-Host "[!] Warning: Smart Card Class GUID path not found in registry." -ForegroundColor System.ConsoleColor::DarkYellow
}

# Step 3: Restart the Smart Card service and force a hardware bus poll
Write-Host "`n[*] Restarting core services and forcing hardware bus poll..." -ForegroundColor Yellow
Stop-Service -Name "SCardSvr" -Force -ErrorAction SilentlyContinue
Start-Service -Name "SCardSvr"
pnputil /scan-devices | Out-Null

Write-Host "`n[DONE] Power saving overrides deployed. Check Device Manager to see if the reader appears." -ForegroundColor Green
Write-Host "============================================================" -ForegroundColor Cyan