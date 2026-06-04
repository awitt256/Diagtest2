# ================================================
# DEVICE CAPABILITY CHECK WITH ERROR LOGGING
# ================================================

Clear-Host

# Log file on desktop
$LogFile = "$env:USERPROFILE\Desktop\ErrorLog.txt"

# Create/empty the log file
"" | Out-File -FilePath $LogFile -Encoding utf8

Write-Host "=== DEVICE CAPABILITY REPORT ===" -ForegroundColor Cyan
Write-Host "Generated: $(Get-Date)"
Write-Host ""

function LogError {
    param (
        [string]$msg
    )
    Add-Content -Path $LogFile -Value "[$(Get-Date)] $msg"
}

function SafeCheck {
    param (
        [string]$Name,
        [scriptblock]$Code
    )

    try {
        $value = & $Code

        if ($value) {
            Write-Host "$Name: YES" -ForegroundColor Green
        }
        else {
            Write-Host "$Name: NO" -ForegroundColor Red
        }
    }
    catch {
        Write-Host "$Name: ERROR (logged)" -ForegroundColor Yellow
        LogError "$Name failed - $($_.Exception.Message)"
    }
}

# ============================================================
SafeCheck "WLAN" {
    (Get-CimInstance Win32_NetworkAdapter | 
        Where-Object { $_.Name -match "Wireless|Wi-Fi|WLAN" -and $_.PhysicalAdapter }) -ne $null
}

SafeCheck "WWAN" {
    (Get-CimInstance Win32_NetworkAdapter | 
        Where-Object { $_.Name -match "WWAN|Mobile|Cellular|LTE|Broadband" -and $_.PhysicalAdapter }) -ne $null
}

SafeCheck "NFC" {
    (Get-PnpDevice | 
        Where-Object { $_.FriendlyName -match "NFC|Near Field" }) -ne $null
}

SafeCheck "SmartCard" {
    (Get-PnpDevice | 
        Where-Object { $_.Class -match "SmartCard" -or $_.FriendlyName -match "Smart Card" }) -ne $null
}

SafeCheck "Fingerprint" {
    (Get-PnpDevice | 
        Where-Object { $_.FriendlyName -match "Fingerprint|Biometric|FP Sensor" }) -ne $null
}

SafeCheck "Keyboard Backlight" {
    $kb = Get-PnpDevice | Where-Object { $_.FriendlyName -match "Keyboard" }
    ($kb | Where-Object { $_.FriendlyName -match "Backlight|Light|Illumi" }) -ne $null
}

SafeCheck "Touchscreen" {
    (Get-PnpDevice | 
        Where-Object { $_.FriendlyName -match "Touch Screen|Touchscreen|HID-compliant touch" }) -ne $null
}

SafeCheck "Privacy Screen" {
    (Get-PnpDevice | 
        Where-Object { $_.FriendlyName -match "Privacy|ePrivacy|SureView|Sure View|SafeScreen" }) -ne $null
}

Write-Host ""
Write-Host "=== DONE ===" -ForegroundColor Cyan
Write-Host "If any errors occurred, they were logged to:"
Write-Host $LogFile -ForegroundColor Yellow
Write-Host ""

Read-Host "Press ENTER to exit..."