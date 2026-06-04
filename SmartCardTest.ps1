# Smart Card Reader Detection and Test Script
# Returns structured output for Python GUI consumption

Write-Output "=== SMART CARD READER TEST ==="
Write-Output ""

# Check if Smart Card Service is running
$scService = Get-Service -Name "SCardSvr" -ErrorAction SilentlyContinue
if ($scService) {
    Write-Output "SERVICE_NAME: SCardSvr"
    Write-Output "SERVICE_STATUS: $($scService.Status)"
} else {
    Write-Output "SERVICE_NAME: SCardSvr"
    Write-Output "SERVICE_STATUS: Not Found"
}

# Get Smart Card Readers
Write-Output ""
Write-Output "--- DETECTING SMART CARD READERS ---"

$readers = @()
try {
    # Method 1: WMI/PnP Device detection
    $pnpReaders = Get-PnpDevice -Class "SmartCardReader" -ErrorAction SilentlyContinue
    if ($pnpReaders) {
        foreach ($reader in $pnpReaders) {
            $readers += @{
                Name = $reader.FriendlyName
                Status = $reader.Status
                Present = ($reader.Status -eq "OK")
            }
            Write-Output "READER_FOUND: $($reader.FriendlyName)"
            Write-Output "READER_STATUS: $($reader.Status)"
            Write-Output "READER_CLASS: SmartCardReader"
            Write-Output "---"
        }
    }
    
    # Method 2: Check USB devices for smart card readers
    if ($readers.Count -eq 0) {
        $usbReaders = Get-PnpDevice | Where-Object { 
            $_.FriendlyName -match "smart.*card" -or 
            $_.FriendlyName -match "cac.*reader" -or
            $_.FriendlyName -match "scr331" -or
            $_.FriendlyName -match "omnikey"
        }
        
        if ($usbReaders) {
            foreach ($reader in $usbReaders) {
                $readers += @{
                    Name = $reader.FriendlyName
                    Status = $reader.Status
                    Present = ($reader.Status -eq "OK")
                }
                Write-Output "READER_FOUND: $($reader.FriendlyName)"
                Write-Output "READER_STATUS: $($reader.Status)"
                Write-Output "READER_CLASS: USB"
                Write-Output "---"
            }
        }
    }
} catch {
    Write-Output "READER_DETECTION_ERROR: $_"
}

if ($readers.Count -eq 0) {
    Write-Output "READER_FOUND: NONE"
    Write-Output "READER_STATUS: No smart card readers detected"
    Write-Output "---"
}

# Summary
Write-Output ""
Write-Output "=== SUMMARY ==="
Write-Output "TOTAL_READERS: $($readers.Count)"
if ($readers.Count -gt 0) {
    $workingReaders = ($readers | Where-Object { $_.Present }).Count
    Write-Output "WORKING_READERS: $workingReaders"
    if ($workingReaders -gt 0) {
        Write-Output "TEST_RESULT: PASS"
    } else {
        Write-Output "TEST_RESULT: FAIL"
    }
} else {
    Write-Output "WORKING_READERS: 0"
    Write-Output "TEST_RESULT: FAIL"
}
