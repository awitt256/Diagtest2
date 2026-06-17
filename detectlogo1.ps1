<#
.SYNOPSIS
    Detects and optionally removes custom HP BIOS boot logos.
.DESCRIPTION
    Checks if a custom logo is active using HP CMSL. If detected,
    prompts the user to remove it, then optionally restarts the PC.
#>

# --- Configuration ---
# If you have a BIOS Password, put it here, otherwise leave it empty ''
$biosPassword = ''

# --- Auto-elevate to Administrator ---
if (-not ([Security.Principal.WindowsPrincipal][Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)) {
    Write-Host "Requesting Administrator privileges..." -ForegroundColor Yellow
    $psExe = if (Get-Command pwsh -ErrorAction SilentlyContinue) { 'pwsh' } else { 'powershell' }
    Start-Process $psExe -ArgumentList "-NoProfile -ExecutionPolicy Bypass -File `"$PSCommandPath`"" -Verb RunAs
    return
}

# --- Script ---
Write-Host ""
Write-Host "  ==========================================" -ForegroundColor Cyan
Write-Host "   HP BIOS Boot Logo - Detect & Remove" -ForegroundColor Cyan
Write-Host "  ==========================================" -ForegroundColor Cyan
Write-Host "   Built By Anthony Witt" -ForegroundColor DarkGray
Write-Host ""

# --- Required modules ---
# HP.Private must be installed (with license accepted) before HPCMSL.
$cmslModules = @('HP.Private', 'HPCMSL')
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
    foreach ($mod in @('HPCMSL', 'HP.Private')) {
        Get-Module -Name $mod -ErrorAction SilentlyContinue | Remove-Module -Force -ErrorAction SilentlyContinue
    }

    $removedAny = $false
    foreach ($mod in @('HPCMSL', 'HP.Private')) {
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
    Write-Host ""
    Write-Host "Updating PowerShellGet (required for HP CMSL)..." -ForegroundColor Cyan

    try { [Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12 } catch {}

    try {
        $nuget = Get-PackageProvider -Name NuGet -ErrorAction SilentlyContinue
        if (-not $nuget -or $nuget.Version -lt [version]'2.8.5.201') {
            Write-Host "  Installing/updating NuGet provider..." -ForegroundColor Yellow
            Install-PackageProvider -Name NuGet -MinimumVersion 2.8.5.201 -Scope AllUsers -Force -Confirm:$false -ErrorAction Stop | Out-Null
        }
    } catch {
        Write-Host "  Could not update NuGet provider: $_" -ForegroundColor DarkYellow
    }

    try {
        $gallery = Get-PSRepository -Name PSGallery -ErrorAction SilentlyContinue
        if (-not $gallery) {
            Register-PSRepository -Default -InstallationPolicy Trusted -ErrorAction Stop
        } elseif ($gallery.InstallationPolicy -ne 'Trusted') {
            Set-PSRepository -Name PSGallery -InstallationPolicy Trusted -ErrorAction Stop
        }
    } catch {}

    try {
        $current = (Get-Module -ListAvailable -Name PowerShellGet | Sort-Object Version -Descending | Select-Object -First 1).Version
        $latest  = (Find-Module -Name PowerShellGet -ErrorAction Stop).Version
        if (-not $current -or $current -lt $latest) {
            Write-Host "  Updating PowerShellGet $current -> $latest ..." -ForegroundColor Yellow
            Install-Module -Name PowerShellGet -Scope AllUsers -Force -AllowClobber -ErrorAction Stop
            Write-Host "  PowerShellGet updated." -ForegroundColor Green
        }
    } catch {
        Write-Host "  Could not update PowerShellGet: $_" -ForegroundColor DarkYellow
    }
}

try {
    # --- Check and install required modules ---
    Write-Host "Checking required modules..." -ForegroundColor Cyan
    $allPresent = $true

    foreach ($mod in $cmslModules) {
        if (Get-Module -ListAvailable -Name $mod) {
            Write-Host "  [OK] $mod" -ForegroundColor Green
        } else {
            Write-Host "  [MISSING] $mod" -ForegroundColor Yellow
            $allPresent = $false
        }
    }

    if (-not $allPresent) {
        Update-PowerShellGet

        Write-Host ""
        Write-Host "Installing missing modules (accepting HP license)..." -ForegroundColor Yellow
        foreach ($mod in $cmslModules) {
            if (Get-Module -ListAvailable -Name $mod) { continue }
            try {
                Install-Module -Name $mod -Scope AllUsers -Force -AllowClobber -AcceptLicense -Confirm:$false -ErrorAction Stop
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
        Remove-InstalledModules
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