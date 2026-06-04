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
$requiredModules = @('HPCMSL')
$installedByScript = @()

function Remove-InstalledModules {
    Write-Host ""
    Write-Host "Uninstalling HP CMSL Modules..." -ForegroundColor Yellow
    if ($installedByScript.Count -gt 0) {
        foreach ($mod in $installedByScript) {
            try {
                Uninstall-Module -Name $mod -AllVersions -Force -ErrorAction Stop
                Write-Host "  Removed: $mod" -ForegroundColor DarkGray
            }
            catch {
                Write-Host "  Could not remove $mod : $_" -ForegroundColor DarkRed
            }
        }
        Write-Host "Module cleanup complete." -ForegroundColor Green
    } else {
        Write-Host "  No modules to remove (HPCMSL was already installed)." -ForegroundColor DarkGray
    }
}

try {
    # --- Ensure NuGet provider is installed ---
    Write-Host "Checking NuGet package provider..." -ForegroundColor Cyan
    $nuget = Get-PackageProvider -Name NuGet -ErrorAction SilentlyContinue
    if (-not $nuget -or $nuget.Version -lt [Version]'2.8.5.201') {
        Write-Host "  [MISSING] NuGet provider - Installing..." -ForegroundColor Yellow
        Install-PackageProvider -Name NuGet -MinimumVersion 2.8.5.201 -Scope AllUsers -Force -Confirm:$false | Out-Null
        Write-Host "  [OK] NuGet provider installed." -ForegroundColor Green
    } else {
        Write-Host "  [OK] NuGet provider" -ForegroundColor Green
    }

    # --- Ensure PSGallery is trusted ---
    Write-Host "Checking PSGallery trust..." -ForegroundColor Cyan
    $gallery = Get-PSRepository -Name PSGallery -ErrorAction SilentlyContinue
    if (-not $gallery) {
        Write-Host "  [MISSING] PSGallery not registered - Registering..." -ForegroundColor Yellow
        Register-PSRepository -Default -InstallationPolicy Trusted
        Write-Host "  [OK] PSGallery registered and trusted." -ForegroundColor Green
    } elseif ($gallery.InstallationPolicy -ne 'Trusted') {
        Write-Host "  [UNTRUSTED] PSGallery - Setting to Trusted..." -ForegroundColor Yellow
        Set-PSRepository -Name PSGallery -InstallationPolicy Trusted
        Write-Host "  [OK] PSGallery is now trusted." -ForegroundColor Green
    } else {
        Write-Host "  [OK] PSGallery is trusted." -ForegroundColor Green
    }
    Write-Host ""

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
        Write-Host ""
        Write-Host "Installing missing modules..." -ForegroundColor Yellow
        foreach ($mod in $requiredModules) {
            if (-not (Get-Module -ListAvailable -Name $mod)) {
                try {
                    Install-Module -Name $mod -Scope AllUsers -Force -AllowClobber -Confirm:$false -ErrorAction Stop
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
    Remove-InstalledModules

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