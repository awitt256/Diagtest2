# USB Port Detection and Connectivity Test Script
# Returns structured output for Python GUI consumption

Write-Output "=== USB PORT DETECTION TEST ==="
Write-Output ""

# Get all USB controllers and devices
Write-Output "--- ENUMERATING USB PORTS AND DEVICES ---"

$usbDevices = @()
$usbControllers = @()
$usbHubs = @()
$failedDevices = @()
$workingDevices = @()

try {
    # Get USB Controllers
    $usbControllers = Get-PnpDevice -Class "USB" -ErrorAction SilentlyContinue | 
        Where-Object { 
            $_.FriendlyName -match "Host Controller|Root Hub" 
        }
    
    Write-Output "USB_CONTROLLERS_FOUND: $($usbControllers.Count)"
    foreach ($controller in $usbControllers) {
        Write-Output "CONTROLLER: $($controller.FriendlyName)"
        Write-Output "CONTROLLER_STATUS: $($controller.Status)"
    }
    Write-Output ""
    
    # Get USB Hubs
    $usbHubs = Get-PnpDevice -Class "USB" -ErrorAction SilentlyContinue | 
        Where-Object { 
            $_.FriendlyName -match "Hub" -and 
            $_.FriendlyName -notmatch "Host Controller|Root Hub"
        }
    
    Write-Output "USB_HUBS_FOUND: $($usbHubs.Count)"
    foreach ($hub in $usbHubs) {
        Write-Output "HUB: $($hub.FriendlyName)"
        Write-Output "HUB_STATUS: $($hub.Status)"
    }
    Write-Output ""
    
    # Get all USB devices (excluding controllers and hubs)
    $allUsbDevices = Get-PnpDevice -Class "USB" -ErrorAction SilentlyContinue | 
        Where-Object { 
            $_.FriendlyName -notmatch "Host Controller|Root Hub|Hub" -and
            $_.InstanceId -match "^USB\\"
        }
    
    foreach ($device in $allUsbDevices) {
        $deviceInfo = @{
            Name = $device.FriendlyName
            Status = $device.Status
            InstanceId = $device.InstanceId
            Present = ($device.Status -eq "OK")
        }
        $usbDevices += $deviceInfo
        
        if ($device.Status -eq "OK") {
            $workingDevices += $device.FriendlyName
            Write-Output "USB_DEVICE_OK: $($device.FriendlyName)"
        } else {
            $failedDevices += "$($device.FriendlyName) ($($device.Status))"
            Write-Output "USB_DEVICE_ERROR: $($device.FriendlyName) - Status: $($device.Status)"
        }
    }
    
} catch {
    Write-Output "USB_ENUMERATION_ERROR: $_"
}

Write-Output ""
Write-Output "--- USB PORT ANALYSIS ---"

# Count USB 2.0 vs USB 3.0 vs USB-C
$usb2Count = 0
$usb3Count = 0
$usbcCount = 0

try {
    # Check for USB 3.0 indicators
    $usb3Devices = Get-PnpDevice | Where-Object {
        $_.FriendlyName -match "USB 3\.0|USB 3\.1|USB 3\.2|xHCI|USB3"
    }
    $usb3Count = $usb3Devices.Count
    
    # Check for USB-C indicators
    $usbcDevices = Get-PnpDevice | Where-Object {
        $_.FriendlyName -match "USB-C|Type-C|USB4|Thunderbolt"
    }
    $usbcCount = $usbcDevices.Count
    
    # Estimate USB 2.0 (total USB devices minus 3.0 and C)
    $totalUsbDevices = $usbDevices.Count
    $usb2Count = [Math]::Max(0, $totalUsbDevices - $usb3Count - $usbcCount)
    
} catch {
    Write-Output "USB_VERSION_DETECT_ERROR: $_"
}

Write-Output "USB_2_0_PORTS: $usb2Count"
Write-Output "USB_3_0_PORTS: $usb3Count"
Write-Output "USB_C_PORTS: $usbcCount"

Write-Output ""
Write-Output "--- CONNECTIVITY TEST ---"

# Test if USB devices are actively responding
$activeConnections = 0
try {
    # Get USB devices that are currently active and working
    $activeDevices = Get-PnpDevice -Class "USB" -ErrorAction SilentlyContinue | 
        Where-Object { $_.Status -eq "OK" }
    $activeConnections = $activeDevices.Count
} catch {
    Write-Output "CONNECTIVITY_TEST_ERROR: $_"
}

Write-Output "ACTIVE_USB_CONNECTIONS: $activeConnections"

Write-Output ""
Write-Output "=== SUMMARY ==="
Write-Output "TOTAL_USB_CONTROLLERS: $($usbControllers.Count)"
Write-Output "TOTAL_USB_HUBS: $($usbHubs.Count)"
Write-Output "TOTAL_USB_DEVICES: $($usbDevices.Count)"
Write-Output "WORKING_DEVICES: $($workingDevices.Count)"
Write-Output "FAILED_DEVICES: $($failedDevices.Count)"
Write-Output "ACTIVE_CONNECTIONS: $activeConnections"
Write-Output ""

# Determine overall test result
if ($usbDevices.Count -gt 0 -and $workingDevices.Count -gt 0) {
    Write-Output "TEST_RESULT: PASS"
    Write-Output "TEST_MESSAGE: USB ports detected and functional"
} elseif ($usbDevices.Count -gt 0 -and $workingDevices.Count -eq 0) {
    Write-Output "TEST_RESULT: FAIL"
    Write-Output "TEST_MESSAGE: USB devices found but none working properly"
} else {
    Write-Output "TEST_RESULT: FAIL"
    Write-Output "TEST_MESSAGE: No USB devices detected"
}

# List working devices
if ($workingDevices.Count -gt 0) {
    Write-Output ""
    Write-Output "WORKING DEVICE LIST:"
    foreach ($device in $workingDevices) {
        Write-Output "  [OK] $device"
    }
}

# List failed devices
if ($failedDevices.Count -gt 0) {
    Write-Output ""
    Write-Output "DEVICES WITH ISSUES:"
    foreach ($device in $failedDevices) {
        Write-Output "  [ERR] $device"
    }
}
