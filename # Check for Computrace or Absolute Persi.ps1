# ===============================================
#   COMPUTRACE DETECTION TOOL
#   BUILT BY ANTHONY WITT 2026
# ===============================================
# Check for Computrace or Absolute Persistence Module in BIOS
try {
    $wmiQuery = Get-WmiObject -Namespace "root\cimv2" -Class Win32_SystemEnclosure -ErrorAction Stop
    $systemInfo = Get-WmiObject -Class Win32_ComputerSystemProduct -ErrorAction Stop
    
    # Check for Computrace
    $computrace = Get-WmiObject -Namespace "root\cimv2" -Query "SELECT * FROM Win32_BIOS" | Select-Object -ExpandProperty SerialNumber
    
    # Check via registry for Computrace/Absolute
    $regPath = "HKLM:\SOFTWARE\Absolute Software\Absolute"
    $computraceActive = Test-Path $regPath
    
    # Check for Computrace or Absolute Persistence Module in BIOS
    try {
        $systemInfo = Get-CimInstance Win32_ComputerSystem | Select-Object -First 1
        Write-Host "Manufacturer : $($systemInfo.Manufacturer)"
        Write-Host "Model        : $($systemInfo.Model)"
        Write-Host "System SKU   : $($systemInfo.SystemSKUNumber)"
        $biosInfo = Get-WmiObject -Class Win32_BIOS

            $serialNumber = $biosInfo.SerialNumber
            $sku = $systemInfo.SystemSKUNumber

            Write-Host "BIOS Manufacturer: $($biosInfo.Manufacturer)"
            Write-Host "BIOS Version: $($biosInfo.SMBIOSBIOSVersion)"
            Write-Host "BIOS Serial Number: $serialNumber"
            Write-Host "System SKU: $sku"

        # Try to detect Computrace/Absolute Persistence module
                # Check for rpcnet.exe in C:\Windows\System32
                $rpcnetPath = "C:\\Windows\\System32\\rpcnet.exe"
                $rpcnetResult = ""
                if (Test-Path $rpcnetPath) {
                    $rpcnetResult = "FAIL for Computrace/Absolute Persistence Module"
                    Write-Host "rpcnet.exe detected in C:\\Windows\\System32! $rpcnetResult" -ForegroundColor Red
                } else {
                    $rpcnetResult = "NOT C:\\Windows\\System32\\rpcnet.exe NOT DETECTED"
                    Write-Host $rpcnetResult -ForegroundColor Green
                }
        $computraceStatus = $null
        try {
            $computraceStatus = Get-WmiObject -Namespace root\absolute -Class computrace -ErrorAction SilentlyContinue
        } catch {}

        $result = ""
        if ($computraceStatus) {
            Write-Host "Computrace/Absolute Persistence module detected!"
            if ($computraceStatus.ActivationStatus -eq 1) {
                $result = "Activated"
                Write-Host "Status: Activated"
            } elseif ($computraceStatus.ActivationStatus -eq 2) {
                $result = "Disabled"
                Write-Host "Status: Disabled"
            } elseif ($computraceStatus.ActivationStatus -eq 0) {
                $result = "Not Activated"
                Write-Host "Status: Not Activated"
            } else {
                $result = "Unknown ($($computraceStatus.ActivationStatus))"
                Write-Host "Status: Unknown ($($computraceStatus.ActivationStatus))"
            }
        } else {
            $result = "Not Detected"
            Write-Host "Computrace/Absolute Persistence module not detected."
        }

        # Log results to file
        $logFile = "Computrace_Absolute_Check_Log_${serialNumber}_${systemInfo.SystemSKUNumber}.txt"
            $logEntry = "SerialNumber: $serialNumber | SystemSKU: $($systemInfo.SystemSKUNumber) | Result: $result | rpcnet.exe: $rpcnetResult"
        Add-Content -Path $logFile -Value $logEntry
        Write-Host "Results logged to $logFile"
    }
    catch {
        Write-Host "Error checking BIOS settings: $_" -ForegroundColor Yellow
    }
}
catch {
    Write-Host "Error checking BIOS settings: $_" -ForegroundColor Yellow
}