# Ensure HP Client Management Script Library is installed
# Install-Module -Name HP.ClientManagement.Library

# Check if a custom logo is currently active in the BIOS
$isCustomLogo = Get-HPFirmwareBootLogoIsActive

if ($isCustomLogo) {
    Write-Host "A custom boot logo is currently installed."
} else {
    Write-Host "Default HP logo is installed."
}
