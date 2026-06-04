<#
.SYNOPSIS
    Detects and removes custom HP BIOS boot logos.
.DESCRIPTION
    Checks if a custom logo is active using HP CMSL, and runs Clear-HPFirmwareBootLogo
    if a custom logo is detected.
#>

# --- Configuration ---
# If you have a BIOS Password, put it here, otherwise leave it empty ''
$biosPassword = '' 

# --- Script ---
Write-Host "Checking for custom HP BIOS logo..." -ForegroundColor Cyan
$moduleInstalledByScript = $false
$logoChangedSuccessfully = $false

try {
    # Check if CMSL module is available
    if (-not (Get-Module -ListAvailable -Name HP.ClientManagement.Library)) {
        Write-Host "HP.ClientManagement.Library module not found. Installing..." -ForegroundColor Yellow

        try {
            Install-Module -Name HP.ClientManagement.Library -Scope CurrentUser -Force -AllowClobber -ErrorAction Stop
            $moduleInstalledByScript = $true
        }
        catch {
            Write-Error "Failed to install HP.ClientManagement.Library: $_"
            return
        }
    }

    Import-Module HP.ClientManagement.Library -ErrorAction Stop

    # Check if a custom logo is currently active in the BIOS
    $isCustomLogo = Get-HPFirmwareBootLogoIsActive

    if ($isCustomLogo) {
        Write-Host "A custom boot logo is currently installed." -ForegroundColor Yellow
    }
    else {
        Write-Host "Default HP logo is installed." -ForegroundColor Green

        if ($moduleInstalledByScript) {
            Write-Host "Uninstalling HP.ClientManagement.Library..." -ForegroundColor Yellow
            Uninstall-Module -Name HP.ClientManagement.Library -AllVersions -Force -ErrorAction Stop
            Write-Host "HP.ClientManagement.Library was removed." -ForegroundColor Green
        }

        Read-Host "No custom boot logo detected. Press Enter to exit"
        return
    }

    # Attempt to clear the logo
    Write-Host "Attempting to revert to default HP logo..." -ForegroundColor Yellow
    
    if ($biosPassword) {
        Clear-HPFirmwareBootLogo -Password $biosPassword
    } else {
        Clear-HPFirmwareBootLogo
    }
    
    $logoChangedSuccessfully = $true
    Write-Host "Logo reset command sent successfully. Please reboot to verify." -ForegroundColor Green

    if ($logoChangedSuccessfully -and $moduleInstalledByScript) {
        Write-Host "Uninstalling HP.ClientManagement.Library..." -ForegroundColor Yellow
        Uninstall-Module -Name HP.ClientManagement.Library -AllVersions -Force -ErrorAction Stop
        Write-Host "HP.ClientManagement.Library was removed." -ForegroundColor Green
    }
}
catch {
    Write-Error "Failed to change logo: $_"
}
