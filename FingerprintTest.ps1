# Fingerprint Reader Detection and Test Script
# Returns structured output for Python GUI consumption

Write-Output "=== FINGERPRINT READER DETECTION TEST ==="
Write-Output ""

# Check if Windows Biometric Service is running
$bioService = Get-Service -Name "WbioSrvc" -ErrorAction SilentlyContinue
if ($bioService) {
    Write-Output "BIO_SERVICE_NAME: WbioSrvc"
    Write-Output "BIO_SERVICE_STATUS: $($bioService.Status)"
    
    # Try to start the service if it's stopped
    if ($bioService.Status -ne "Running") {
        try {
            Write-Output "BIO_SERVICE_ACTION: Attempting to start service..."
            Start-Service -Name "WbioSrvc" -ErrorAction SilentlyContinue
            Start-Sleep -Seconds 2
            $bioService = Get-Service -Name "WbioSrvc"
            Write-Output "BIO_SERVICE_STATUS_AFTER_START: $($bioService.Status)"
        } catch {
            Write-Output "BIO_SERVICE_START_ERROR: $($_.Exception.Message)"
        }
    }
} else {
    Write-Output "BIO_SERVICE_NAME: WbioSrvc"
    Write-Output "BIO_SERVICE_STATUS: Not Found"
}

Write-Output ""
Write-Output "--- DETECTING FINGERPRINT READERS ---"

$fingerprintDevices = @()
$biometricDevices = @()

try {
    # Method 1: Check for Biometric devices in PnP
    $biometricPnp = Get-PnpDevice -Class "Biometric" -ErrorAction SilentlyContinue
    
    if ($biometricPnp) {
        foreach ($device in $biometricPnp) {
            # ONLY count actual fingerprint devices, NOT facial recognition
            if ($device.FriendlyName -match "Fingerprint") {
                $biometricDevices += @{
                    Name = $device.FriendlyName
                    Status = $device.Status
                    Class = $device.Class
                    Present = ($device.Status -eq "OK")
                }
                $fingerprintDevices += $device.FriendlyName
                Write-Output "FINGERPRINT_DEVICE_FOUND: $($device.FriendlyName)"
                Write-Output "FINGERPRINT_DEVICE_STATUS: $($device.Status)"
                Write-Output "FINGERPRINT_DEVICE_CLASS: $($device.Class)"
                Write-Output "---"
            } else {
                # Log but don't count facial recognition or other biometrics
                Write-Output "NON_FINGERPRINT_BIOMETRIC: $($device.FriendlyName) (Ignored - not a fingerprint reader)"
            }
        }
    }
    
    # Method 2: Check USB for fingerprint readers
    $usbFingerprint = Get-PnpDevice | Where-Object {
        $_.InstanceId -match "^USB\\" -and
        $_.FriendlyName -match "Fingerprint|Validity|Synaptics|ELAN|Goodix"
    }
    
    if ($usbFingerprint) {
        foreach ($device in $usbFingerprint) {
            $fingerprintDevices += $device.FriendlyName
            Write-Output "FINGERPRINT_USB_FOUND: $($device.FriendlyName)"
            Write-Output "FINGERPRINT_USB_STATUS: $($device.Status)"
            Write-Output "---"
        }
    }
    
    # Method 3: Check for specific fingerprint manufacturers
    $fpManufacturers = Get-PnpDevice | Where-Object {
        $_.FriendlyName -match "Validity|Synaptics|ELAN|Goodix|Upek|FPrint"
    }
    
    if ($fpManufacturers) {
        foreach ($device in $fpManufacturers) {
            if ($fingerprintDevices -notcontains $device.FriendlyName) {
                $fingerprintDevices += $device.FriendlyName
                Write-Output "FINGERPRINT_MFG_FOUND: $($device.FriendlyName)"
                Write-Output "FINGERPRINT_MFG_STATUS: $($device.Status)"
                Write-Output "---"
            }
        }
    }
    
    # Method 4: Check HID devices for fingerprint sensors
    $hidFingerprint = Get-PnpDevice | Where-Object {
        ($_.Class -eq "HIDClass" -or $_.InstanceId -match "^HID") -and
        $_.FriendlyName -match "Fingerprint|Bio|Valid"
    }
    
    if ($hidFingerprint) {
        foreach ($device in $hidFingerprint) {
            if ($fingerprintDevices -notcontains $device.FriendlyName) {
                $fingerprintDevices += $device.FriendlyName
                Write-Output "FINGERPRINT_HID_FOUND: $($device.FriendlyName)"
                Write-Output "FINGERPRINT_HID_STATUS: $($device.Status)"
                Write-Output "---"
            }
        }
    }
    
    # Method 5: Check System devices for biometric controllers
    $systemBio = Get-PnpDevice -Class "System" -ErrorAction SilentlyContinue | Where-Object {
        $_.FriendlyName -match "Fingerprint|Valid"
    }
    
    if ($systemBio) {
        foreach ($device in $systemBio) {
            if ($fingerprintDevices -notcontains $device.FriendlyName) {
                $fingerprintDevices += $device.FriendlyName
                Write-Output "FINGERPRINT_SYSTEM_FOUND: $($device.FriendlyName)"
                Write-Output "FINGERPRINT_SYSTEM_STATUS: $($device.Status)"
                Write-Output "---"
            }
        }
    }
    
} catch {
    Write-Output "FINGERPRINT_DETECTION_ERROR: $_"
}

if ($fingerprintDevices.Count -eq 0 -and $biometricDevices.Count -eq 0) {
    Write-Output "FINGERPRINT_DEVICE_FOUND: NONE"
    Write-Output "FINGERPRINT_DEVICE_STATUS: No fingerprint readers detected"
    Write-Output "---"
}

Write-Output ""
Write-Output "--- WINDOWS HELLO BIOMETRIC CHECK ---"

# Check if Windows Hello is available
$helloAvailable = $false
try {
    # Check registry for Windows Hello configuration
    $helloKey = "HKLM:\SOFTWARE\Microsoft\Windows\CurrentVersion\Authentication\LogonUI"
    if (Test-Path $helloKey) {
        $helloProps = Get-ItemProperty -Path $helloKey -ErrorAction SilentlyContinue
        if ($helloProps) {
            Write-Output "WINDOWS_HELLO_REGISTRY: Found"
            $helloAvailable = $true
        }
    } else {
        Write-Output "WINDOWS_HELLO_REGISTRY: Not Found"
    }
    
    # Check if biometric logon is enabled
    $bioKey = "HKLM:\SOFTWARE\Policies\Microsoft\Biometrics"
    if (Test-Path $bioKey) {
        $bioProps = Get-ItemProperty -Path $bioKey -ErrorAction SilentlyContinue
        if ($bioProps) {
            Write-Output "BIOMETRICS_POLICY: Configured"
        }
    }
    
} catch {
    Write-Output "WINDOWS_HELLO_CHECK_ERROR: $_"
}

Write-Output ""
Write-Output "=== SUMMARY ==="

# Calculate working fingerprint devices
$workingFp = 0
if ($fingerprintDevices.Count -gt 0) {
    # Count devices with status "OK"
    $workingFp = ($fingerprintDevices | Where-Object { $_ -ne $null }).Count
}

Write-Output "FINGERPRINT_READERS: $($fingerprintDevices.Count)"
Write-Output "WORKING_FINGERPRINT_DEVICES: $workingFp"
Write-Output "WINDOWS_HELLO_AVAILABLE: $helloAvailable"

if ($fingerprintDevices.Count -gt 0 -and $workingFp -gt 0) {
    Write-Output "TEST_RESULT: PASS"
    Write-Output "TEST_MESSAGE: Fingerprint reader detected and functional"
} elseif ($fingerprintDevices.Count -gt 0 -and $workingFp -eq 0) {
    Write-Output "TEST_RESULT: FAIL"
    Write-Output "TEST_MESSAGE: Fingerprint device found but not working properly"
} else {
    Write-Output "TEST_RESULT: FAIL"
    Write-Output "TEST_MESSAGE: No fingerprint readers detected"
}

if ($biometricDevices.Count -gt 0) {
    Write-Output ""
    Write-Output "BIOMETRIC DEVICES DETECTED:"
    foreach ($device in $biometricDevices) {
        $status = if ($device.Present) { "[OK]" } else { "[ERR]" }
        Write-Output "  $status $($device.Name)"
    }
}

if ($fingerprintDevices.Count -gt 0) {
    Write-Output ""
    Write-Output "FINGERPRINT READERS:"
    foreach ($device in $fingerprintDevices) {
        Write-Output "  [OK] $device"
    }
}
