# HP Software Framework Driver Detection Script
# Detects if HP Software Framework Driver is installed on the system

Set-StrictMode -Off
$ErrorActionPreference = "Continue"

Write-Host "`n========== HP SOFTWARE FRAMEWORK DRIVER DETECTION ==========" -ForegroundColor Cyan

# Check if running as admin
$isAdmin = ([Security.Principal.WindowsPrincipal] [Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole] "Administrator")
if ($isAdmin) {
    Write-Host "Status: Running as Administrator" -ForegroundColor Green
} else {
    Write-Host "Status: Running as Standard User (some checks may be limited)" -ForegroundColor Yellow
}

# Initialize result tracking
$driverFound = $false
$results = @()

# Method 1: Check Device Manager (PnP devices)
Write-Host "`n[1/4] Checking Device Manager (PnP Devices)..." -ForegroundColor White
try {
    $pnpDevices = Get-PnpDevice -ErrorAction SilentlyContinue | Where-Object { 
        ($_.Name -like '*Framework*') -or ($_.Name -like '*HP*') -or ($_.Description -like '*Framework*')
    }
    
    $found = $false
    foreach ($device in $pnpDevices) {
        if (($device.Name -match 'Framework') -or ($device.Description -match 'Framework')) {
            $results += "✓ Found in Device Manager: $($device.Name)"
            $driverFound = $true
            $found = $true
        }
    }
    
    if (-not $found) {
        Write-Host "   No Framework drivers found in Device Manager" -ForegroundColor Gray
    }
} catch {
    Write-Host "   Error checking Device Manager: $($_.Exception.Message)" -ForegroundColor Yellow
}

# Method 2: Check Windows Registry for driver entries
Write-Host "`n[2/4] Checking Installed Programs..." -ForegroundColor White
try {
    $uninstallKeys = @(
        'HKLM:\SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall',
        'HKLM:\SOFTWARE\Wow6432Node\Microsoft\Windows\CurrentVersion\Uninstall'
    )
    
    $found = $false
    foreach ($key in $uninstallKeys) {
        if (Test-Path $key) {
            $subkeys = Get-ChildItem -Path $key -ErrorAction SilentlyContinue
            foreach ($subkey in $subkeys) {
                $props = Get-ItemProperty -Path $subkey.PSPath -ErrorAction SilentlyContinue
                if ($props.DisplayName -match 'Framework|HP Software|HPE') {
                    $results += "✓ Found Program: $($props.DisplayName)"
                    $driverFound = $true
                    $found = $true
                }
            }
        }
    }
    
    if (-not $found) {
        Write-Host "   No Framework/HP programs found" -ForegroundColor Gray
    }
} catch {
    Write-Host "   Error checking programs: $($_.Exception.Message)" -ForegroundColor Yellow
}

# Method 3: Check Windows Services for HP drivers
Write-Host "`n[3/4] Checking Windows Services..." -ForegroundColor White
try {
    $services = Get-Service -ErrorAction SilentlyContinue | Where-Object { 
        ($_.DisplayName -like '*HP*') -or ($_.DisplayName -like '*Framework*')
    }
    
    $found = $false
    foreach ($service in $services) {
        if ($service.DisplayName -match 'Framework|Driver') {
            $results += "✓ Found Service: $($service.DisplayName) (Status: $($service.Status))"
            $driverFound = $true
            $found = $true
        }
    }
    
    if (-not $found) {
        Write-Host "   No HP Framework services found" -ForegroundColor Gray
    }
} catch {
    Write-Host "   Error checking services: $($_.Exception.Message)" -ForegroundColor Yellow
}

# Method 4: Check for HP driver files in Program Files
Write-Host "`n[4/4] Checking HP Program Folders..." -ForegroundColor White
try {
    $hpPaths = @(
        'C:\Program Files\HP',
        'C:\Program Files (x86)\HP',
        'C:\Program Files\Hewlett-Packard',
        'C:\Program Files (x86)\Hewlett-Packard'
    )
    
    $found = $false
    foreach ($hpPath in $hpPaths) {
        if (Test-Path $hpPath) {
            Write-Host "   Scanning: $hpPath" -ForegroundColor Gray
            $driverFiles = Get-ChildItem -Path $hpPath -Recurse -Include "*driver*", "*framework*" -ErrorAction SilentlyContinue | Select-Object -First 5
            if ($driverFiles) {
                foreach ($file in $driverFiles) {
                    $results += "✓ Found Driver File: $($file.FullName)"
                    $driverFound = $true
                    $found = $true
                }
            }
        }
    }
    
    if (-not $found) {
        Write-Host "   No HP driver files found in Program Files" -ForegroundColor Gray
    }
} catch {
    Write-Host "   Error checking HP folders: $($_.Exception.Message)" -ForegroundColor Yellow
}

# Summary
Write-Host "`n========== SUMMARY ==========" -ForegroundColor Cyan
if ($driverFound) {
    Write-Host "`nRESULT: HP SOFTWARE FRAMEWORK DRIVER DETECTED" -ForegroundColor Green
    Write-Host "`nDetails:" -ForegroundColor White
    foreach ($result in $results) {
        Write-Host $result -ForegroundColor Green
    }
} else {
    Write-Host "`nRESULT: HP SOFTWARE FRAMEWORK DRIVER NOT DETECTED" -ForegroundColor Red
    Write-Host "`nThe Software Framework Driver does not appear to be installed on this system." -ForegroundColor Yellow
}

Write-Host "`n" -ForegroundColor Cyan
Write-Host "Scan complete. Press Enter to exit..." -ForegroundColor Gray
Read-Host
