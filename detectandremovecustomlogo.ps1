<#
.SYNOPSIS
    Detects and optionally removes custom HP BIOS boot logos.
.DESCRIPTION
    Checks if a custom logo is active using HP CMSL. If detected,
    prompts the user to remove it, then optionally restarts the PC.
#>

param(
    [string]$LauncherPath = (Join-Path $PSScriptRoot 'REMOVELOGO.bat')
)

# --- Configuration ---
# If you have a BIOS Password, put it here, otherwise leave it empty ''
$biosPassword = ''

# --- Auto-elevate to Administrator ---
if (-not ([Security.Principal.WindowsPrincipal][Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)) {
    Write-Host "Requesting Administrator privileges..." -ForegroundColor Yellow
    $psExe = if (Get-Command pwsh -ErrorAction SilentlyContinue) { 'pwsh' } else { 'powershell' }
    Start-Process $psExe -ArgumentList "-NoProfile -ExecutionPolicy Bypass -File `"$PSCommandPath`" -LauncherPath `"$LauncherPath`"" -Verb RunAs
    return
}

# --- Check PowerShell version ---
if ($PSVersionTable.PSVersion.Major -lt 7) {
    Write-Host "ERROR: This script requires PowerShell 7 or later." -ForegroundColor Red
    Write-Host "Current version: $($PSVersionTable.PSVersion.Major).$($PSVersionTable.PSVersion.Minor)" -ForegroundColor Red
    Write-Host "Please run the batch file (REMOVELOGO.bat) to install PowerShell 7 automatically." -ForegroundColor Yellow
    if ($LauncherPath -and (Test-Path $LauncherPath)) {
        Write-Host "Restarting batch file to install PowerShell 7..." -ForegroundColor Yellow
        Start-Process cmd.exe -ArgumentList "/c `"$LauncherPath`"" -Verb RunAs
    }
    Read-Host "Press Enter to exit"
    exit
}

# --- Script ---
Write-Host ""
Write-Host "  ==========================================" -ForegroundColor Cyan
Write-Host "   HP BIOS Boot Logo - Detect & Remove" -ForegroundColor Cyan
Write-Host "  ==========================================" -ForegroundColor Cyan
Write-Host "   Built By Anthony Witt" -ForegroundColor DarkGray
Write-Host ""

# --- Required modules ---
$requiredModules = @('HPCMSL')
$installedByScript = @()

function Remove-InstalledModules {
    param(
        [switch]$ForceAll
    )

    Write-Host ""
    Write-Host "Uninstalling HP CMSL library..." -ForegroundColor Yellow

    if (-not $ForceAll -and $installedByScript.Count -eq 0) {
        Write-Host "  No modules to remove (HPCMSL was already installed)." -ForegroundColor DarkGray
        return
    }

    # Unload modules from this session before uninstalling from disk.
    foreach ($mod in @('HPCMSL')) {
        Get-Module -Name $mod -ErrorAction SilentlyContinue | Remove-Module -Force -ErrorAction SilentlyContinue
    }

    $removedAny = $false
    foreach ($mod in @('HPCMSL')) {
        if (-not (Get-Module -ListAvailable -Name $mod)) { continue }
        try {
            Uninstall-Module -Name $mod -AllVersions -Force -ErrorAction Stop
            Write-Host "  Removed: $mod" -ForegroundColor DarkGray
            $removedAny = $true
        }
        catch {
            Write-Host "  Retrying $mod removal in a new session..." -ForegroundColor Yellow
            $uninstallCmd = "Get-Module -Name '$mod' -ErrorAction SilentlyContinue | Remove-Module -Force; Uninstall-Module -Name '$mod' -AllVersions -Force -ErrorAction Stop"
            try {
                & powershell.exe -NoProfile -Command $uninstallCmd
                Write-Host "  Removed: $mod" -ForegroundColor DarkGray
                $removedAny = $true
            }
            catch {
                Write-Host "  Could not remove $mod : $_" -ForegroundColor DarkRed
            }
        }
    }

    if ($removedAny) {
        Write-Host "HP CMSL cleanup complete." -ForegroundColor Green
    }
}

function Update-PowerShellGet {
    # HP CMSL installs from the PowerShell Gallery, which needs a current
    # NuGet provider and PowerShellGet. Update them before installing HPCMSL.
    # Returns $true when PowerShellGet was upgraded (caller should restart).
    Write-Host ""
    Write-Host "Updating PowerShellGet (required for HP CMSL)..." -ForegroundColor Cyan

    $psGetUpdated = $false

    # TLS 1.2 is required to reach the PowerShell Gallery on older systems.
    try { [Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12 } catch {}

    # NuGet package provider.
    try {
        $nuget = Get-PackageProvider -Name NuGet -ErrorAction SilentlyContinue
        if (-not $nuget -or $nuget.Version -lt [version]'2.8.5.201') {
            Write-Host "  Installing/updating NuGet provider..." -ForegroundColor Yellow
            Install-PackageProvider -Name NuGet -MinimumVersion 2.8.5.201 -Scope CurrentUser -Force -ErrorAction Stop | Out-Null
        }
    } catch {
        Write-Host "  Could not update NuGet provider: $_" -ForegroundColor DarkYellow
    }

    # Trust the PowerShell Gallery so installs don't prompt.
    try {
        if ((Get-PSRepository -Name PSGallery -ErrorAction SilentlyContinue).InstallationPolicy -ne 'Trusted') {
            Set-PSRepository -Name PSGallery -InstallationPolicy Trusted -ErrorAction Stop
        }
    } catch {}

    # Update PowerShellGet itself if a newer version exists.
    try {
        $current = (Get-Module -ListAvailable -Name PowerShellGet | Sort-Object Version -Descending | Select-Object -First 1).Version
        $latest  = (Find-Module -Name PowerShellGet -ErrorAction Stop).Version
        if (-not $current -or $current -lt $latest) {
            Write-Host "  Updating PowerShellGet $current -> $latest ..." -ForegroundColor Yellow
            Install-Module -Name PowerShellGet -Scope CurrentUser -Force -AllowClobber -ErrorAction Stop
            Write-Host "  PowerShellGet updated." -ForegroundColor Green
            $psGetUpdated = $true
        } else {
            Write-Host "  PowerShellGet is already current ($current)." -ForegroundColor Green
        }
    } catch {
        Write-Host "  Could not update PowerShellGet: $_" -ForegroundColor DarkYellow
    }

    return $psGetUpdated
}

function Restart-Launcher {
    Write-Host ""
    Write-Host "Restarting launcher to load updated PowerShellGet..." -ForegroundColor Yellow

    if ($LauncherPath -and (Test-Path -LiteralPath $LauncherPath)) {
        Start-Process -FilePath 'cmd.exe' -ArgumentList '/c', "`"$LauncherPath`"" -Wait
        return
    }

    $psExe = if (Get-Command pwsh -ErrorAction SilentlyContinue) { 'pwsh' } else { 'powershell' }
    Start-Process -FilePath $psExe -ArgumentList "-NoProfile -ExecutionPolicy Bypass -File `"$PSCommandPath`" -LauncherPath `"$LauncherPath`"" -Wait
}

try {
    # --- Check and install required modules ---
    Write-Host "Checking required modules..." -ForegroundColor Cyan
    $allPresent = $true

    foreach ($mod in $requiredModules) {
        if (Get-Module -ListAvailable -Name $mod) {
            Write-Host "  [OK] $mod" -ForegroundColor Green
        } else {
            Write-Host "  [MISSING] $mod" -ForegroundColor Yellow
            $allPresent = $false
        }
    }

    if (-not $allPresent) {
        # Make sure PowerShellGet / NuGet are current before installing HP CMSL.
        if (Update-PowerShellGet) {
            Restart-Launcher
            return
        }

        Write-Host ""
        Write-Host "Installing missing modules..." -ForegroundColor Yellow
        foreach ($mod in $requiredModules) {
            if (-not (Get-Module -ListAvailable -Name $mod)) {
                try {
                    Install-Module -Name $mod -Scope CurrentUser -Force -AllowClobber -AcceptLicense -Confirm:$false -ErrorAction Stop
                    $installedByScript += $mod
                    Write-Host "  Installed: $mod" -ForegroundColor Green
                }
                catch {
                    Write-Host "  Failed to install ${mod}: $_" -ForegroundColor Red
                    Read-Host "Press Enter to exit"
                    return
                }
            }
        }
    }

    # Import all required modules
    foreach ($mod in $requiredModules) {
        Import-Module $mod -ErrorAction Stop
    }

    # --- Detection ---
    Write-Host ""
    Write-Host "Checking for custom HP BIOS logo..." -ForegroundColor Cyan
    $isCustomLogo = Get-HPFirmwareBootLogoIsActive

    if (-not $isCustomLogo) {
        Write-Host "Default HP logo is installed. No custom logo detected." -ForegroundColor Green
        Remove-InstalledModules

        $restartAnswer = Read-Host "Do you want to restart your PC now? (y/n)"
        if ($restartAnswer -match '^[Yy]') {
            Write-Host "Restarting in 5 seconds... (press Ctrl+C to cancel)" -ForegroundColor Yellow
            Start-Sleep -Seconds 5
            Restart-Computer -Force
        } else {
            Read-Host "Press Enter to exit"
        }
        return
    }

    Write-Host "A custom boot logo is currently installed." -ForegroundColor Yellow

    # --- Prompt to remove ---
    $removeAnswer = Read-Host "Do you want to remove the custom logo? (y/n)"

    if ($removeAnswer -notmatch '^[Yy]') {
        Write-Host "No changes made." -ForegroundColor Gray
        Read-Host "Press Enter to exit"
        return
    }

    # --- Remove the logo ---
    Write-Host "Attempting to revert to default HP logo..." -ForegroundColor Yellow

    if ($biosPassword) {
        Clear-HPFirmwareBootLogo -Password $biosPassword
    } else {
        Clear-HPFirmwareBootLogo
    }

    Write-Host "Logo reset command sent successfully." -ForegroundColor Green
    Remove-InstalledModules -ForceAll

    # --- Prompt to restart ---
    $restartAnswer = Read-Host "Do you want to restart your PC now? (y/n)"

    if ($restartAnswer -match '^[Yy]') {
        Write-Host "Restarting in 5 seconds... (press Ctrl+C to cancel)" -ForegroundColor Yellow
        Start-Sleep -Seconds 5
        Restart-Computer -Force
    } else {
        Write-Host "Please restart your PC manually to see the change." -ForegroundColor Gray
        Read-Host "Press Enter to exit"
    }
}
catch {
    Write-Host "Failed: $_" -ForegroundColor Red
    Read-Host "Press Enter to exit"
}
