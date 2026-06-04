# NFC Reader Detection and Test Script
# Returns structured output for Python GUI consumption

Write-Output "=== NFC READER DETECTION TEST ==="
Write-Output ""

# Check if NFC Service is running
$nfcService = Get-Service -Name "NFCC" -ErrorAction SilentlyContinue
if ($nfcService) {
    Write-Output "NFC_SERVICE_NAME: NFCC"
    Write-Output "NFC_SERVICE_STATUS: $($nfcService.Status)"
} else {
    Write-Output "NFC_SERVICE_NAME: NFCC"
    Write-Output "NFC_SERVICE_STATUS: Not Found"
}

Write-Output ""
Write-Output "--- DETECTING NFC READERS ---"

$nfcDevices = @()
$nearFieldDevices = @()

try {
    # Method 1: Check for NFC devices in PnP
    $nfcPnp = Get-PnpDevice | Where-Object {
        $_.FriendlyName -match "NFC|Near Field|Proximity" -or
        $_.Class -match "NFC|Proximity"
    }
    
    if ($nfcPnp) {
        foreach ($device in $nfcPnp) {
            $nfcDevices += @{
                Name = $device.FriendlyName
                Status = $device.Status
                Class = $device.Class
                Present = ($device.Status -eq "OK")
            }
            Write-Output "NFC_DEVICE_FOUND: $($device.FriendlyName)"
            Write-Output "NFC_DEVICE_STATUS: $($device.Status)"
            Write-Output "NFC_DEVICE_CLASS: $($device.Class)"
            Write-Output "---"
        }
    }
    
    # Method 2: Check for Smart Card devices that might support NFC
    $smartCardDevices = Get-PnpDevice -Class "SmartCardReader" -ErrorAction SilentlyContinue
    if ($smartCardDevices) {
        foreach ($device in $smartCardDevices) {
            if ($device.FriendlyName -match "NFC|Contactless") {
                $nearFieldDevices += $device.FriendlyName
                Write-Output "NFC_CONTACTLESS_FOUND: $($device.FriendlyName)"
                Write-Output "NFC_CONTACTLESS_STATUS: $($device.Status)"
                Write-Output "---"
            }
        }
    }
    
    # Method 3: Check USB for NFC adapters
    $usbNfc = Get-PnpDevice | Where-Object {
        $_.InstanceId -match "^USB\\" -and
        ($_.FriendlyName -match "NFC|ACS ACR|Identive|SpringCard")
    }
    
    if ($usbNfc) {
        foreach ($device in $usbNfc) {
            $nfcDevices += @{
                Name = $device.FriendlyName
                Status = $device.Status
                Class = "USB"
                Present = ($device.Status -eq "OK")
            }
            Write-Output "NFC_USB_FOUND: $($device.FriendlyName)"
            Write-Output "NFC_USB_STATUS: $($device.Status)"
            Write-Output "---"
        }
    }
    
} catch {
    Write-Output "NFC_DETECTION_ERROR: $_"
}

if ($nfcDevices.Count -eq 0 -and $nearFieldDevices.Count -eq 0) {
    Write-Output "NFC_DEVICE_FOUND: NONE"
    Write-Output "NFC_DEVICE_STATUS: No NFC readers detected"
    Write-Output "---"
}

Write-Output ""
Write-Output "--- NFC CAPABILITY CHECK ---"

# Check if system supports NFC features
$nfcCapability = $false
try {
    # Check Windows NFC capabilities
    $nfcApi = Get-WindowsCapability -Online | Where-Object { $_.Name -match "NFC" }
    if ($nfcApi) {
        Write-Output "NFC_WINDOWS_CAPABILITY: Found"
        foreach ($cap in $nfcApi) {
            Write-Output "NFC_CAPABILITY_NAME: $($cap.Name)"
            Write-Output "NFC_CAPABILITY_STATE: $($cap.State)"
            if ($cap.State -eq "Installed") {
                $nfcCapability = $true
            }
        }
    } else {
        Write-Output "NFC_WINDOWS_CAPABILITY: Not Found"
    }
} catch {
    Write-Output "NFC_CAPABILITY_CHECK_ERROR: $_"
}

Write-Output ""
Write-Output "=== SUMMARY ==="
Write-Output "TOTAL_NFC_DEVICES: $($nfcDevices.Count)"
Write-Output "CONTACTLESS_READERS: $($nearFieldDevices.Count)"

$totalNfc = $nfcDevices.Count + $nearFieldDevices.Count
$workingNfc = ($nfcDevices | Where-Object { $_.Present }).Count + $nearFieldDevices.Count

Write-Output "WORKING_NFC_DEVICES: $workingNfc"
Write-Output "NFC_CAPABILITY_ENABLED: $nfcCapability"

if ($totalNfc -gt 0 -and $workingNfc -gt 0) {
    Write-Output "TEST_RESULT: PASS"
    Write-Output "TEST_MESSAGE: NFC reader detected and functional"
} elseif ($totalNfc -gt 0 -and $workingNfc -eq 0) {
    Write-Output "TEST_RESULT: FAIL"
    Write-Output "TEST_MESSAGE: NFC device found but not working properly"
} else {
    Write-Output "TEST_RESULT: FAIL"
    Write-Output "TEST_MESSAGE: No NFC readers detected"
}

if ($nfcDevices.Count -gt 0) {
    Write-Output ""
    Write-Output "NFC DEVICES DETECTED:"
    foreach ($device in $nfcDevices) {
        $status = if ($device.Present) { "[OK]" } else { "[ERR]" }
        Write-Output "  $status $($device.Name) ($($device.Class))"
    }
}

if ($nearFieldDevices.Count -gt 0) {
    Write-Output ""
    Write-Output "CONTACTLESS READERS:"
    foreach ($device in $nearFieldDevices) {
        Write-Output "  [OK] $device"
    }
}
