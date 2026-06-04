# InstallByBrand.ps1
# DO NOT use #Requires -RunAsAdministrator here; we self-elevate below.

$ErrorActionPreference = 'Continue'
$Host.UI.RawUI.WindowTitle = "InstallByBrand (Launching...)"

# -----------------------------
# Resolve script directory - Anthony's preference
# Priority:
#   1) win test folder (Desktop)
#   2) D:\
#   3) Actual script folder
# -----------------------------
$desktopPreferred = "C:\Users\Anthony\Desktop\win test 2.5.17"
$driveDFallback   = "D:\"

# Default to the script's real location
$scriptDir = if ($PSScriptRoot) {
    $PSScriptRoot
} else {
    Split-Path -Path $MyInvocation.MyCommand.Definition -Parent
}

# Override with preferred locations if available
if (Test-Path -LiteralPath $desktopPreferred) {
    $scriptDir = $desktopPreferred
}
elseif (Test-Path -LiteralPath $driveDFallback) {
    $scriptDir = $driveDFallback
}

# Normalize and switch working directory
$scriptDir = (Resolve-Path -LiteralPath $scriptDir).Path
Set-Location -Path $scriptDir

Write-Host "Using script directory: $scriptDir"
Write-Host "Script file: $PSCommandPath"
Write-Host "Launched from: $((Get-Location).Path)"
Write-Host ""

# -----------------------------
# Self-elevate if not admin
# -----------------------------
$principal = [Security.Principal.WindowsPrincipal] [Security.Principal.WindowsIdentity]::GetCurrent()
$amAdmin   = $principal.IsInRole([Security.Principal.WindowsBuiltinRole]::Administrator)

if (-not $amAdmin) {
    Write-Host "Elevation required. Relaunching as administrator..." -ForegroundColor Yellow

    # Use the same PS host that is running now (works for Windows PowerShell & PowerShell 7)
    $psExe = (Get-Process -Id $PID).Path

    # If PSCommandPath is null (e.g., pasted in console), build a path to this script by name in $scriptDir
    if (-not $PSCommandPath) {
        $thisScript = Join-Path $scriptDir 'InstallByBrand.ps1'
    } else {
        $thisScript = $PSCommandPath
    }

    if (-not (Test-Path -LiteralPath $thisScript)) {
        Write-Host "ERROR: Unable to find the script to relaunch at: $thisScript" -ForegroundColor Red
        exit 1
    }

    $args  = @(
        '-NoLogo', '-NoProfile',
        '-ExecutionPolicy', 'Bypass',
        '-NoExit',                             # keep the elevated window open on completion/error
        '-File', "`"$thisScript`""
    )

    Start-Process -FilePath $psExe -ArgumentList $args -Verb RunAs -WorkingDirectory $scriptDir
    Write-Host "Elevated instance launched. This window will close now." -ForegroundColor DarkGray
    Start-Sleep -Seconds 1
    exit
}

$Host.UI.RawUI.WindowTitle = "InstallByBrand (Elevated)"
Write-Host "Running elevated as $env:USERNAME" -ForegroundColor Green
Write-Host ""

# -----------------------------
# Helper: Invoke a local PS1 safely (no EXEs) and return [bool] success
# - Unblocks file (removes MOTW)
# - Sets ExecutionPolicy to Bypass for this process
# - Uses call operator '&'
# - Returns $true if the script ran without terminating error
# -----------------------------
function Invoke-LocalScript {
    param([Parameter(Mandatory)][string]$FileName)

    $fullPath = Join-Path $scriptDir $FileName
    Write-Host "Looking for script: $fullPath"
    if (Test-Path -LiteralPath $fullPath) {
        try {
            # Remove MOTW if present to avoid RemoteSigned "Security error"
            Unblock-File -LiteralPath $fullPath -ErrorAction SilentlyContinue
            # Ensure policy cannot block this invocation in this process
            Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass -Force

            Write-Host "Running: $fullPath" -ForegroundColor Cyan
            & $fullPath -ErrorAction Stop
            return $true
        }
        catch {
            Write-Host ("Script '{0}' threw an error." -f $FileName) -ForegroundColor Red
            $_ | Format-List * -Force

            # Quick diagnostics to spot policy/host issues
            Write-Host "`nDiagnostics:" -ForegroundColor DarkYellow
            Write-Host ("  LanguageMode: {0}" -f $ExecutionContext.SessionState.LanguageMode)
            Write-Host "  ExecutionPolicy (scopes):"
            Get-ExecutionPolicy -List | Format-Table -Auto | Out-String | Write-Host
            return $false
        }
    }
    else {
        Write-Host ("Script '{0}' not found at {1}" -f $FileName, $fullPath) -ForegroundColor Yellow
        return $false
    }
}

# -----------------------------
# Helper: Report devices with missing drivers / errors
# - Missing drivers: ConfigManagerErrorCode = 28
# - Other problems:  ConfigManagerErrorCode != 0 and != 28
# -----------------------------
function Get-DriverIssueReport {
    [CmdletBinding()]
    param()

    $all = Get-CimInstance Win32_PnPEntity -ErrorAction SilentlyContinue

    $missing = @()
    $other   = @()

    foreach ($d in $all) {
        $code = $d.ConfigManagerErrorCode
        if ($code -eq 28) {
            $missing += [pscustomobject]@{
                Name         = $d.Name
                PNPClass     = $d.PNPClass
                Manufacturer = $d.Manufacturer
                ErrorCode    = $code
                DeviceID     = $d.PNPDeviceID
                HardwareIDs  = ($d.HardwareID -join '; ')
            }
        }
        elseif ($code -ne 0) {
            $other += [pscustomobject]@{
                Name         = $d.Name
                PNPClass     = $d.PNPClass
                Manufacturer = $d.Manufacturer
                ErrorCode    = $code
                DeviceID     = $d.PNPDeviceID
                HardwareIDs  = ($d.HardwareID -join '; ')
            }
        }
    }

    [pscustomobject]@{
        MissingDrivers = $missing
        OtherErrors    = $other
    }
}

function Show-DriverIssueReport {
    [CmdletBinding()]
    param()

    $report = Get-DriverIssueReport

    Write-Host ""
    Write-Host "================ Device Manager Health Report ================" -ForegroundColor Cyan

    if ($report.MissingDrivers.Count -gt 0) {
        Write-Host "`n** Missing Drivers Detected (Error Code 28) **" -ForegroundColor Yellow
        $report.MissingDrivers |
            Sort-Object PNPClass, Name |
            Select-Object Name, PNPClass, Manufacturer, ErrorCode, DeviceID, HardwareIDs |
            Format-Table -AutoSize
    } else {
        Write-Host "`nNo missing drivers (Error Code 28) found." -ForegroundColor Green
    }

    if ($report.OtherErrors.Count -gt 0) {
        Write-Host "`n** Other Device Errors Detected (ErrorCode != 0, != 28) **" -ForegroundColor Yellow
        $report.OtherErrors |
            Sort-Object ErrorCode, PNPClass, Name |
            Select-Object Name, PNPClass, Manufacturer, ErrorCode, DeviceID, HardwareIDs |
            Format-Table -AutoSize
    } else {
        Write-Host "`nNo other device errors found." -ForegroundColor Green
    }

    Write-Host "==============================================================" -ForegroundColor Cyan
}

# -----------------------------
# Detect manufacturer
# -----------------------------
try {
    $manufacturer = (Get-CimInstance -ClassName Win32_ComputerSystem -ErrorAction Stop).Manufacturer.Trim()
} catch {
    Write-Host "Failed to query manufacturer via CIM: $($_.Exception.Message)" -ForegroundColor Red
    $manufacturer = ""
}

Write-Host "Detected manufacturer: $manufacturer"

# Run Device Manager check RIGHT AFTER printing manufacturer
Show-DriverIssueReport

# Track success of brand-specific install
$installSucceeded = $false

switch -Regex ($manufacturer) {
    # ---------- Lenovo ----------
    '^Lenovo$' {
        $installSucceeded = Invoke-LocalScript -FileName 'LSU.ps1'

        if ($installSucceeded) {
            # Optional confirmation preserves your UX
            $answer = Read-Host "Did the Lenovo utilities install correctly? (Y/N)"
            if ($answer -notmatch '^(?i)Y$') {
                $installSucceeded = $false
                Write-Host "Operator indicated install did not complete successfully." -ForegroundColor Yellow
            }
        }
    }

    # ---------- HP ----------
    '^(HP|Hewlett-Packard|HP Inc\.)$' {
        $installSucceeded = Invoke-LocalScript -FileName 'InstallHPDrivers.ps1'
    }

    # ---------- Dell ----------
    '^(Dell|Dell Inc\.)$' {
        $installSucceeded = Invoke-LocalScript -FileName 'DellCommandUpdate.ps1'
    }

    # ---------- Default ----------
    Default {
        Write-Host "Manufacturer '$manufacturer' is not explicitly handled." -ForegroundColor Yellow
        $installSucceeded = $false
    }
}

# -----------------------------
# Prompt to restart on success
# -----------------------------
if ($installSucceeded) {
    $resp = Read-Host "Installation completed. Do you want to restart now? (Y/N)"
    if ($resp -match '^(?i)Y$') {
        Write-Host "Restarting now..." -ForegroundColor Cyan
        Restart-Computer -Force
        # No code after this will run
    } else {
        Write-Host "OK - exiting without restart." -ForegroundColor Yellow
        exit
    }
}