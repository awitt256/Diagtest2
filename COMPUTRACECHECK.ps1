# COMPUTRACE / ABSOLUTE PERSISTENCE DETECTION TOOL - BUILT BY ANTHONY WITT 2026
Write-Host "=============================================================" -ForegroundColor Cyan
Write-Host "COMPUTRACE / ABSOLUTE PERSISTENCE DETECTION TOOL" -ForegroundColor Cyan
Write-Host "BUILT BY ANTHONY WITT 2026" -ForegroundColor Cyan
Write-Host "=============================================================" -ForegroundColor Cyan
Write-Host ""

# Check for Computrace or Absolute Persistence Module in BIOS
    # Check if rpcnet.exe or rpcnetp.exe process is running
    $rpcnetProcess = Get-Process -Name "rpcnet","rpcnetp" -ErrorAction SilentlyContinue
    if ($rpcnetProcess) {
        $rpcnetProcStatus = "RUNNING (rpcnet/rpcnetp)"
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

    # Check BootExecute in Session Manager
    $bootExecuteSummary = "NOT CHECKED"
    $bootExecuteOk = $true
    try {
        $sessionMgrKey = "HKLM:\SYSTEM\CurrentControlSet\Control\Session Manager"
        if (Test-Path $sessionMgrKey) {
            $sessionMgr = Get-ItemProperty -Path $sessionMgrKey -Name BootExecute -ErrorAction SilentlyContinue
            if ($sessionMgr -and $sessionMgr.BootExecute) {
                $bootExecuteRaw = $sessionMgr.BootExecute
                if ($bootExecuteRaw -is [array]) {
                    $bootExecuteValue = ($bootExecuteRaw -join ', ')
                } else {
                    $bootExecuteValue = [string]$bootExecuteRaw
                }

                if ($bootExecuteValue -match '(?i)rpcnet|absolute|computrace') {
                    $bootExecuteSummary = "SUSPICIOUS: $bootExecuteValue"
                    $bootExecuteOk = $false
                } elseif ($bootExecuteValue -eq "autocheck autochk *") {
                    $bootExecuteSummary = "DEFAULT: $bootExecuteValue"
                } else {
                    $bootExecuteSummary = "CUSTOM: $bootExecuteValue"
                }
            } else {
                $bootExecuteSummary = "BootExecute not set"
            }
        } else {
            $bootExecuteSummary = "Session Manager key not found"
        }
    } catch {
        $bootExecuteSummary = "Error reading BootExecute: $_"
        $bootExecuteOk = $false
    }
    
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
                # Check for rpcnet.exe / rpcnetp.exe in System32 and SysWOW64
                $rpcnetPaths = @(
                    "C:\Windows\System32\rpcnet.exe",
                    "C:\Windows\System32\rpcnetp.exe",
                    "C:\Windows\SysWOW64\rpcnet.exe",
                    "C:\Windows\SysWOW64\rpcnetp.exe"
                )
                $rpcnetFound = $false
                foreach ($p in $rpcnetPaths) {
                    if (Test-Path $p) { $rpcnetFound = $true; break }
                }
                $rpcnetResult = ""
                if ($rpcnetFound) {
                    $rpcnetResult = "FAIL for Computrace/Absolute Persistence Module (rpcnet/rpcnetp present)"
                } else {
                    $rpcnetResult = "rpcnet*.exe NOT DETECTED (System32 & SysWOW64)"
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
            $allSafe = $true
            if ($rpcnetProcStatus -like '*NOT*') {
                Write-Host "rpcnet/rpcnetp process: " -NoNewline; Write-Host "NOT DETECTED" -ForegroundColor Green
            } else {
                Write-Host "rpcnet/rpcnetp process: " -NoNewline; Write-Host "FAIL" -ForegroundColor Red
                $allSafe = $false
            }
            if ($absCompSummary -like '*NOT*') {
                Write-Host "Program Files search: " -NoNewline; Write-Host "NOT DETECTED" -ForegroundColor Green
            } else {
                Write-Host "Program Files search: " -NoNewline; Write-Host "FAIL" -ForegroundColor Red
                $allSafe = $false
            }
            if ($bootExecuteOk) {
                Write-Host "Registry BootExecute: " -NoNewline; Write-Host "NOT DETECTED" -ForegroundColor Green
            } else {
                Write-Host "Registry BootExecute: " -NoNewline; Write-Host "FAIL" -ForegroundColor Red
                $allSafe = $false
            }
            if ($rpcnetResult -like '*NOT*') {
                Write-Host "rpcnet/rpcnetp file: " -NoNewline; Write-Host "NOT DETECTED" -ForegroundColor Green
            } else {
                Write-Host "rpcnet/rpcnetp file: " -NoNewline; Write-Host "FAIL" -ForegroundColor Red
                $allSafe = $false
            }
            if ($result -like '*Not Detected*' -or $result -like '*Not Activated*') {
                Write-Host "Persistence module: " -NoNewline; Write-Host "NOT DETECTED" -ForegroundColor Green
            } else {
                Write-Host "Persistence module: " -NoNewline; Write-Host "FAIL" -ForegroundColor Red
                $allSafe = $false
            }
            if ($allSafe) {
                Write-Host ""
                Write-Host "FINAL RESULT: PASS" -ForegroundColor Green
            } else {
                Write-Host ""
                Write-Host "FINAL RESULT: FAIL" -ForegroundColor Red
            }
            Write-Host ""
            Write-Host "------------------------------------------" -ForegroundColor Cyan
        $logFile = "Computrace_Absolute_Check_Log_${serialNumber}_${systemInfo.SystemSKUNumber}.txt"
            $logEntry = "SerialNumber: $serialNumber | SystemSKU: $($systemInfo.SystemSKUNumber) | Result: $result | rpcnet*.exe: $rpcnetResult | rpcnet/rpcnetp process: $rpcnetProcStatus | ProgramFiles: $absCompSummary | BootExecute: $bootExecuteSummary"
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