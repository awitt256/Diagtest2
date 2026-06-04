# Check for Computrace or Absolute Persistence Module in BIOS
    # Check if rpcnet.exe process is running
    $rpcnetProcess = Get-Process -Name "rpcnet" -ErrorAction SilentlyContinue
    if ($rpcnetProcess) {
        $rpcnetProcStatus = "RUNNING"
    } else {
        $rpcnetProcStatus = "NOT RUNNING"
    }
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

    # Check for Absolute or Computrace in Program Files and Program Files (x86)
    $programDirs = @()
    if (Test-Path "$env:ProgramFiles") { $programDirs += $env:ProgramFiles }
    if ($env:ProgramFiles_x86 -and (Test-Path $env:ProgramFiles_x86)) { $programDirs += $env:ProgramFiles_x86 }

    $absCompResults = @()

    foreach ($dir in $programDirs) {
        $matches = Get-ChildItem -Path $dir -Recurse -ErrorAction SilentlyContinue | Where-Object { $_.Name -match '(?i)absolute[\s_-]*persistence|computrace' }
        foreach ($match in $matches) {
            $absCompResults += $match.FullName
        }
    }

    if ($absCompResults.Count -gt 0) {
        $absCompSummary = "FOUND: " + ($absCompResults -join '; ')
    } else {
        $absCompSummary = "NOT FOUND"
    }
        # Try to detect Computrace/Absolute Persistence module
                # Check for rpcnet.exe in C:\Windows\System32
                $rpcnetPath = "C:\\Windows\\System32\\rpcnet.exe"
                $rpcnetResult = ""
                if (Test-Path $rpcnetPath) {
                    $rpcnetResult = "FAIL for Computrace/Absolute Persistence Module"
                } else {
                    $rpcnetResult = "NOT C:\Windows\System32\rpcnet.exe NOT DETECTED"
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
            Write-Host "--- Computrace/Absolute Detection Summary ---" -ForegroundColor Cyan
            Write-Host "Serial Number: $serialNumber"
            Write-Host "System SKU: $($systemInfo.SystemSKUNumber)"
            if ($rpcnetProcStatus -like '*NOT*') {
                Write-Host "rpcnet.exe process status: $rpcnetProcStatus" -ForegroundColor Green
            } else {
                Write-Host "rpcnet.exe process status: $rpcnetProcStatus" -ForegroundColor Red
            }
            if ($absCompSummary -like '*NOT*') {
                Write-Host "Program Files search: $absCompSummary" -ForegroundColor Green
            } else {
                Write-Host "Program Files search: $absCompSummary" -ForegroundColor Red
            }
            if ($rpcnetResult -like '*NOT*') {
                Write-Host "rpcnet.exe file status: $rpcnetResult" -ForegroundColor Green
            } else {
                Write-Host "rpcnet.exe file status: $rpcnetResult" -ForegroundColor Red
            }
            if ($result -like '*Not Detected*' -or $result -like '*Not Activated*') {
                Write-Host "Persistence module status: $result" -ForegroundColor Green
            } else {
                Write-Host "Persistence module status: $result" -ForegroundColor Red
            }
            Write-Host "------------------------------------------" -ForegroundColor Cyan
        $logFile = "Computrace_Absolute_Check_Log_${serialNumber}_${systemInfo.SystemSKUNumber}.txt"
            $logEntry = "SerialNumber: $serialNumber | SystemSKU: $($systemInfo.SystemSKUNumber) | Result: $result | rpcnet.exe: $rpcnetResult | rpcnet.exe process: $rpcnetProcStatus | ProgramFiles: $absCompSummary"
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