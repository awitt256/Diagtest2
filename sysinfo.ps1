Clear-Host

# Make errors visible and prevent early exit
$ErrorActionPreference = "Continue"

try {

    # ============================================================
    # 🔻 BEGIN SYSINFO CONTENT (PASTE YOUR CODE BELOW)
    # ============================================================

    Write-Host "==============================================================="
    Write-Host "                   SYSTEM INFORMATION REPORT"
    Write-Host "==============================================================="
    Write-Host ""
    Write-Host "Generated: $(Get-Date)"
    Write-Host ""

    Write-Host "==============================================================="
    Write-Host "                      SYSTEM IDENTIFICATION"
    Write-Host "==============================================================="
    Write-Host ""

    # SYSTEM
    Write-Host "[System]"
    try {
        $cs = Get-CimInstance Win32_ComputerSystem
        Write-Host "Manufacturer : $($cs.Manufacturer)"
        Write-Host "Model        : $($cs.Model)"
        Write-Host "System SKU   : $($cs.SystemSKUNumber)"
    } catch {
        Write-Host "Error retrieving system information"
    }

    Write-Host ""
    Write-Host "[BIOS]"
    try {
        $bios = Get-CimInstance Win32_BIOS
        Write-Host "Serial Number: $($bios.SerialNumber)"
    } catch {
        Write-Host "Error retrieving BIOS information"
    }

# STORAGE
Write-Host ""
Write-Host "==============================================================="
Write-Host "                       STORAGE INFORMATION"
Write-Host "==============================================================="
Write-Host ""

Write-Host "Logical Drive Information:"
try {
    Get-CimInstance Win32_LogicalDisk | Where-Object { $_.DriveType -eq 3 } |
    ForEach-Object {
        $totalGB = [math]::Round($_.Size / 1GB, 1)
        $freeGB  = [math]::Round($_.FreeSpace / 1GB, 1)
        $usedGB  = [math]::Round(($_.Size - $_.FreeSpace) / 1GB, 1)
        Write-Host "  Drive $($_.Caption) - Total: $totalGB GB, Free: $freeGB GB, Used: $usedGB GB"
    }
} catch {
    Write-Host "  Error retrieving drive information"
}

Write-Host ""
Write-Host "Physical Disk Information:"
try {
    Get-CimInstance Win32_DiskDrive | ForEach-Object {
        $sizeGB = [math]::Round($_.Size / 1GB, 0)
        Write-Host "  $($_.Model) - $sizeGB GB"
    }
} catch {
    Write-Host "  Error retrieving physical disk information"
}

# MEMORY
Write-Host ""
Write-Host "==============================================================="
Write-Host "                       MEMORY INFORMATION"
Write-Host "==============================================================="
Write-Host ""

Write-Host "Total System Memory:"
try {
    $cs = Get-CimInstance Win32_ComputerSystem
    $ramGB = [math]::Round($cs.TotalPhysicalMemory / 1GB, 1)
    Write-Host "  Total RAM: $ramGB GB"
} catch {
    Write-Host "  Not Available"
}

Write-Host ""
Write-Host "Memory Modules:"
try {
    Get-CimInstance Win32_PhysicalMemory | ForEach-Object {
        $capGB = [math]::Round($_.Capacity / 1GB, 0)
        $speed = if ($_.Speed) { "$($_.Speed) MHz" } else { "Unknown Speed" }
        $mfg   = if ($_.Manufacturer) { $_.Manufacturer.Trim() } else { "Unknown" }
        Write-Host "  Module: $capGB GB, $speed, $mfg"
    }
} catch {
    Write-Host "  Error retrieving memory module information"
}

# GRAPHICS
Write-Host ""
Write-Host "==============================================================="
Write-Host "                      GRAPHICS INFORMATION"
Write-Host "==============================================================="
Write-Host ""

Write-Host "Graphics Cards:"
try {
    Get-CimInstance Win32_VideoController | ForEach-Object {
        if ($_.AdapterRAM -and $_.AdapterRAM -gt 0) {
            $vramGB = [math]::Round($_.AdapterRAM / 1GB, 1)
            if ($vramGB -lt 1) {
                $vramMB = [math]::Round($_.AdapterRAM / 1MB, 0)
                Write-Host "  $($_.Name) - $vramMB MB"
            } else {
                Write-Host "  $($_.Name) - $vramGB GB"
            }
        } else {
            Write-Host "  $($_.Name) - VRAM: Not Available"
        }
    }
} catch {
    Write-Host "  Error retrieving graphics information"
}

# CPU
Write-Host ""
Write-Host "==============================================================="
Write-Host "                      PROCESSOR INFORMATION"
Write-Host "==============================================================="
Write-Host ""

Write-Host "Processor:"
try {
    $cpu = Get-CimInstance Win32_Processor | Select-Object -First 1
    Write-Host "  $($cpu.Name)"
} catch {
    Write-Host "  Not Available"
}

Write-Host ""
Write-Host "Processor Details:"
try {
    $cpu = Get-CimInstance Win32_Processor | Select-Object -First 1
    Write-Host "  Cores: $($cpu.NumberOfCores), Logical Processors: $($cpu.NumberOfLogicalProcessors), Max Speed: $($cpu.MaxClockSpeed) MHz"
} catch {
    Write-Host "  Details not available"
}

# OS
Write-Host ""
Write-Host "==============================================================="
Write-Host "                   OPERATING SYSTEM INFORMATION"
Write-Host "==============================================================="
Write-Host ""

Write-Host "Operating System:"
try {
    $os = Get-CimInstance Win32_OperatingSystem
    Write-Host "  $($os.Caption)"
} catch {
    Write-Host "  Not Available"
}

Write-Host ""
Write-Host "OS Details:"
try {
    Write-Host "  Version: $($os.Version)"
    Write-Host "  Architecture: $($os.OSArchitecture)"
} catch {
    Write-Host "  Details not available"
}

Write-Host ""
Write-Host "System Name: $env:COMPUTERNAME"
Write-Host "Current User: $env:USERNAME"

# SUMMARY
Write-Host ""
Write-Host "==============================================================="
Write-Host "                            SUMMARY"
Write-Host "==============================================================="
Write-Host ""

Write-Host "QUICK SYSTEM OVERVIEW:"
Write-Host "======================="

try {
    $cs = Get-CimInstance Win32_ComputerSystem
    $bios = Get-CimInstance Win32_BIOS
    Write-Host "Model: $($cs.Model)"
    Write-Host "Serial: $($bios.SerialNumber)"
    $ramGB = [math]::Round($cs.TotalPhysicalMemory / 1GB, 0)
    Write-Host "RAM: $ramGB GB"
} catch {
    Write-Host "Summary information not available"
}

Write-Host "Computer: $env:COMPUTERNAME"
Write-Host "User: $env:USERNAME"
Write-Host "Date: $(Get-Date)"


Write-Host ""
Write-Host "==============================================================="
Write-Host ""

# ============================================================
# 🔺 END SYSINFO CONTENT
# ============================================================

}
catch {
    Write-Host ""
    Write-Host "==============================================================="
    Write-Host "ERROR OCCURRED:"
    Write-Host "==============================================================="
    Write-Host ""
    Write-Host $_.Exception.Message
}

finally {
    Write-Host ""
    Write-Host "==============================================================="
    Write-Host "Press ENTER to exit..."
    Write-Host "==============================================================="
    $null = Read-Host
}
