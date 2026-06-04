# Script to detect missing drivers and download only driver updates from Windows Update
# Run as Administrator. Saves a log of all drivers downloaded and installed.

# Ensure the script runs with administrator privileges; try to auto-elevate if not
$principal = New-Object Security.Principal.WindowsPrincipal([Security.Principal.WindowsIdentity]::GetCurrent())
if (-not $principal.IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)) {
    Write-Host "Script is not running as Administrator. Attempting to relaunch elevated..." -ForegroundColor Yellow
    $scriptPath = $MyInvocation.MyCommand.Definition
    $pwshCmd = if (Get-Command pwsh -ErrorAction SilentlyContinue) { 'pwsh' } else { 'powershell' }
    $argList = @('-NoProfile', '-ExecutionPolicy', 'Bypass', '-File', $scriptPath)
    try {
        Start-Process -FilePath $pwshCmd -ArgumentList $argList -Verb RunAs -WindowStyle Normal
    }
    catch {
        Write-Host "Elevation cancelled or failed: $_" -ForegroundColor Red
    }
    exit 1
}

# --- Log file: all drivers downloaded and installed ---
# Get system info first (needed for log filename)
$bios = Get-WmiObject Win32_BIOS -ErrorAction SilentlyContinue
$serial = if ($bios -and $bios.SerialNumber) { $bios.SerialNumber.Trim() } else { "Unknown" }
$systemModel = "Unknown"
$systemSku = "Unknown"
Get-CimInstance Win32_ComputerSystem -ErrorAction SilentlyContinue | ForEach-Object {
    if ($_.Model) { $systemModel = $_.Model.Trim() }
    if ($_.SystemSKUNumber) { $systemSku = $_.SystemSKUNumber.Trim() }
}

# Sanitize serial and SKU for use in filename (remove invalid characters)
$serialSafe = $serial -replace '[<>:"/\\|?*]', '_' -replace '\s+', '_'
$skuSafe = $systemSku -replace '[<>:"/\\|?*]', '_' -replace '\s+', '_'

# Determine script directory - use PSScriptRoot if available, otherwise try MyInvocation, fallback to current directory
if ($PSScriptRoot) {
    $scriptDir = $PSScriptRoot
}
elseif ($MyInvocation.MyCommand.Definition) {
    $scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Definition
}
elseif ($MyInvocation.MyCommand.Path) {
    $scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
}
else {
    $scriptDir = (Get-Location).Path
}
# Ensure we have a valid directory path
if ([string]::IsNullOrWhiteSpace($scriptDir)) {
    $scriptDir = (Get-Location).Path
}
$logDir = Join-Path $scriptDir "DriverLogs"
if (-not (Test-Path $logDir)) { New-Item -ItemType Directory -Path $logDir -Force | Out-Null }
$logFile = Join-Path $logDir "${serialSafe}_${skuSafe}_$(Get-Date -Format 'yyyyMMdd_HHmmss').log"
$script:DriversInstalledThisRun = @()

function Write-DriverLog {
    param([string]$Message, [switch]$NoConsole)
    $timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
    $line = "[$timestamp] $Message"
    try { Add-Content -Path $logFile -Value $line -Encoding UTF8 -ErrorAction Stop } catch { Write-Host "Log write failed: $_" -ForegroundColor Red }
    if (-not $NoConsole) { Write-Host $Message }
}

$header = @"
================================================================================
DRIVER INSTALL LOG - Drivers Downloaded and Installed
================================================================================
Computer Serial : $serial
System SKU      : $systemSku
System Model    : $systemModel
--------------------------------------------------------------------------------
Log started     : $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')
Log file        : $logFile
================================================================================
"@
Set-Content -Path $logFile -Value $header -Encoding UTF8 -Force
Write-Host "Log file: $logFile" -ForegroundColor Gray

Write-Host "Checking for missing drivers..." -ForegroundColor Green

# Make non-terminating errors throw so catch can handle them
$ErrorActionPreference = 'Stop'

try {

    # Get all devices with driver problems
    $devicesWithIssues = @()
    $pnpDevices = Get-WmiObject Win32_PnPEntity | Where-Object { $_.ConfigManagerErrorCode -ne 0 }

    if ($pnpDevices.Count -eq 0) {
        Write-Host "No devices with missing drivers found." -ForegroundColor Green
        Write-DriverLog "No devices with missing drivers found. Exiting." -NoConsole
        exit 0
    }

    Write-Host "Found the following devices with missing/problematic drivers:" -ForegroundColor Yellow
    foreach ($device in $pnpDevices) {
        Write-Host "  - $($device.Name)" -ForegroundColor Cyan
        $devicesWithIssues += $device
    }

    Write-Host "`nSearching Windows Update for available driver updates..." -ForegroundColor Green

    # Create Windows Update COM object
    $updateSession = New-Object -ComObject Microsoft.Update.Session
    $updateSearcher = $updateSession.CreateUpdateSearcher()

    # Search for ALL available updates
    try {
        $searchResult = $updateSearcher.Search("IsInstalled=0")
        Write-Host "Found $($searchResult.Updates.Count) available updates" -ForegroundColor Green
    }
    catch {
        Write-Host "ERROR: Failed to search Windows Update. Error: $_" -ForegroundColor Red
        exit 1
    }

    # Filter for driver-only updates
    # Driver updates are identified by:
    # - Category = "Drivers"
    # - NOT containing "Cumulative", "Security", "Preview", or "Service Pack"
    $driverUpdates = @()

    foreach ($update in $searchResult.Updates) {
        $categories = $update.Categories
        $isDriver = $false
        $isOtherUpdate = $false
    
        # Check if it's categorized as a driver
        foreach ($category in $categories) {
            if ($category.Name -eq "Drivers") {
                $isDriver = $true
            }
            # Exclude if it contains other update types
            if ($category.Name -match "Cumulative|Security|Preview|Service Pack|Software|Update Rollup") {
                $isOtherUpdate = $true
                break
            }
        }
    
        # Additional filter: Check title/description to exclude non-driver updates
        $title = $update.Title
        if ($title -match "Cumulative|Security|Preview|Rollup|Windows \d+ Update|Feature Update|KB\d+") {
            $isOtherUpdate = $true
        }
    
        if ($isDriver -and -not $isOtherUpdate) {
            $driverUpdates += $update
            Write-Host "  Driver Update Found: $($update.Title)" -ForegroundColor Green
            Write-DriverLog "Driver available: $($update.Title) (ID: $($update.Identity.UpdateID))" -NoConsole
        }
    }

    if ($driverUpdates.Count -eq 0) {
        Write-Host "`nNo driver-only updates found in Windows Update." -ForegroundColor Yellow
        Write-DriverLog "No driver-only updates found. Exiting." -NoConsole
        exit 0
    }

    Write-Host "`nDriver updates available: $($driverUpdates.Count)" -ForegroundColor Green
    Write-Host "`nInstalling driver updates..." -ForegroundColor Green

    # Show the list of driver updates found (numbered)
    Write-Host "`nDriver updates found:" -ForegroundColor Cyan
    $i = 1
    foreach ($update in $driverUpdates) {
        Write-Host "[$i/$($driverUpdates.Count)] $($update.Title) (ID: $($update.Identity.UpdateID))" -ForegroundColor Cyan
        $i++
    }

    # Download and install each driver update one-by-one so we can show progress
    foreach ($index in 0..($driverUpdates.Count - 1)) {
        $update = $driverUpdates[$index]
        $num = $index + 1
        $driverTitle = $update.Title
        $driverId = $update.Identity.UpdateID
        Write-Host "`n[$num/$($driverUpdates.Count)] Preparing: $driverTitle" -ForegroundColor Yellow
        Write-DriverLog "DOWNLOADING: $driverTitle (UpdateID: $driverId)" -NoConsole

        $singleColl = New-Object -ComObject Microsoft.Update.UpdateColl
        $singleColl.Add($update) | Out-Null

        try {
            Write-Host "[$num] Downloading..." -ForegroundColor Yellow
            $downloader = $updateSession.CreateUpdateDownloader()
            $downloader.Updates = $singleColl
            $downloadResult = $downloader.Download()

            if ($downloadResult.ResultCode -eq 2) {
                Write-Host "[$num] Download succeeded." -ForegroundColor Green
                Write-DriverLog "  Download SUCCESS: $driverTitle" -NoConsole
            }
            else {
                Write-Host "[$num] Download completed with result code: $($downloadResult.ResultCode)" -ForegroundColor Yellow
                Write-DriverLog "  Download result $($downloadResult.ResultCode): $driverTitle" -NoConsole
            }

            Write-Host "[$num] Installing..." -ForegroundColor Yellow
            Write-DriverLog "INSTALLING: $driverTitle" -NoConsole
            $installer = $updateSession.CreateUpdateInstaller()
            $installer.Updates = $singleColl
            $installResult = $installer.Install()

            if ($installResult.ResultCode -eq 2) {
                Write-Host "[$num] Installed successfully." -ForegroundColor Green
                Write-DriverLog "  Install SUCCESS: $driverTitle (UpdateID: $driverId)" -NoConsole
                $script:DriversInstalledThisRun += [PSCustomObject]@{ Title = $driverTitle; UpdateID = $driverId; Status = "Installed" }
            }
            elseif ($installResult.ResultCode -eq 3) {
                Write-Host "[$num] Installed but a restart is required." -ForegroundColor Yellow
                Write-DriverLog "  Install SUCCESS (restart required): $driverTitle (UpdateID: $driverId)" -NoConsole
                $script:DriversInstalledThisRun += [PSCustomObject]@{ Title = $driverTitle; UpdateID = $driverId; Status = "Installed-RestartRequired" }
            }
            else {
                Write-Host "[$num] Installation completed with result code: $($installResult.ResultCode)" -ForegroundColor Yellow
                Write-DriverLog "  Install result $($installResult.ResultCode): $driverTitle (UpdateID: $driverId)" -NoConsole
                $script:DriversInstalledThisRun += [PSCustomObject]@{ Title = $driverTitle; UpdateID = $driverId; Status = "ResultCode-$($installResult.ResultCode)" }
            }

        }
        catch {
            Write-Host "[$num] ERROR during download/install: $_" -ForegroundColor Red
            Write-DriverLog "  ERROR: $driverTitle - $_" -NoConsole
            $err = $_ | Out-String
            try {
                $logPath = Join-Path $env:TEMP 'InstallMissingDrivers_error.log'
                "$([datetime]::UtcNow) - Error for update ${driverId}: $err" | Out-File -FilePath $logPath -Append -Encoding UTF8
                Write-Host "[$num] Error details saved to: $logPath" -ForegroundColor Yellow
            }
            catch {
                Write-Host "[$num] Failed to write log: $_" -ForegroundColor Red
            }
        }
    }

    # Save summary of all drivers downloaded and installed to the log
    Write-DriverLog "" -NoConsole
    Write-DriverLog "========== DRIVERS DOWNLOADED AND INSTALLED (SUMMARY) ==========" -NoConsole
    if ($script:DriversInstalledThisRun.Count -gt 0) {
        $n = 1
        foreach ($d in $script:DriversInstalledThisRun) {
            Write-DriverLog "  $n. $($d.Title) | UpdateID: $($d.UpdateID) | $($d.Status)" -NoConsole
            $n++
        }
        Write-DriverLog "Total: $($script:DriversInstalledThisRun.Count) driver(s) downloaded and installed." -NoConsole
    }
    else {
        Write-DriverLog "  (No drivers were successfully installed this run.)" -NoConsole
    }
    Write-DriverLog "=================================================================" -NoConsole
    Write-DriverLog "Log ended: $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')" -NoConsole

    Write-Host "`nScript completed! Log saved to: $logFile" -ForegroundColor Green

}
catch {
    Write-Host "ERROR: An unhandled exception occurred:" -ForegroundColor Red
    Write-Host $_.Exception.Message -ForegroundColor Red
    $errorDetails = $_ | Out-String
    try {
        $logPath = Join-Path $env:TEMP 'InstallMissingDrivers_error.log'
        "$([datetime]::UtcNow) - $errorDetails" | Out-File -FilePath $logPath -Append -Encoding UTF8
        Write-Host "Error details saved to: $logPath" -ForegroundColor Yellow
    }
    catch {
        Write-Host "Failed to write log: $_" -ForegroundColor Red
    }
}
finally {
    $restart = Read-Host -Prompt "Script completed. Do you want to restart now? (yes/no)"
    if ($restart -eq 'yes' -or $restart -eq 'y') {
        Write-Host "Restarting in 10 seconds..." -ForegroundColor Yellow
        Start-Sleep -Seconds 10
        shutdown /r /t 0
    }
    else {
        Write-Host "Exiting without restart." -ForegroundColor Green
        Read-Host -Prompt "Press Enter to exit"
    }
}
