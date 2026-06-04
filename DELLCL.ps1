# 1. Import the Dell BIOS Provider Module
Import-Module DellBIOSProvider

# 2. Navigate to the BIOS settings location
Set-Location DellSmbios:\Security

# 3. Get the Custom Logo setting
$logoSetting = Get-Item -Path CustomLogo

# 4. Check the state
if ($logoSetting.Value -eq "Enabled") {
    Write-Host "Custom Boot Logo is ENABLED." -ForegroundColor Yellow
} else {
    Write-Host "Custom Boot Logo is Disabled (Default Dell logo is active)." -ForegroundColor Green
}

# Return to home
Set-Location C:\
