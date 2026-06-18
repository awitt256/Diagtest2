# Detect Lenovo Privacy Screen Presence
# This script attempts to determine if the current Lenovo device has a Privacy Guard (hardware privacy screen)
# It uses multiple heuristics:
# 1. Checks for a PnP device with "Privacy Guard" in its friendly name.
# 2. Checks if the Lenovo Elliptic Virtual Lock service (used for HPD) is present.
# 3. Queries Lenovo BIOS settings via the Lenovo_BiosSetting WMI class if available.
# The script outputs a clear result.

function Test-PrivacyGuardDevice {
    try {
        $devices = Get-PnpDevice -Class Monitor -ErrorAction SilentlyContinue | Where-Object { $_.FriendlyName -match "Privacy Guard" }
        return $devices -ne $null
    } catch {
        return $false
    }
}

function Test-EllipticService {
    try {
        $svc = Get-Service -Name *Elliptic* -ErrorAction SilentlyContinue
        return $svc -ne $null
    } catch {
        return $false
    }
}

function Test-BiosPrivacySetting {
    try {
        $biosSettings = Get-CimInstance -Namespace root\\WMI -ClassName Lenovo_BiosSetting -ErrorAction SilentlyContinue
        if ($null -eq $biosSettings) { return $false }
        # Look for a BIOS setting that mentions privacy screen or privacy guard
        $match = $biosSettings | Where-Object { $_.CurrentSetting -match "Privacy" -or $_.CurrentSetting -match "Guard" }
        return $match -ne $null
    } catch {
        return $false
    }
}

$hasPrivacyGuard = Test-PrivacyGuardDevice
$hasElliptic = Test-EllipticService
$hasBiosSetting = Test-BiosPrivacySetting

if ($hasPrivacyGuard -or $hasElliptic -or $hasBiosSetting) {
    Write-Output "Privacy screen detected on this Lenovo device."
    if ($hasPrivacyGuard) { Write-Output "- Detected via PnP device (Privacy Guard)." }
    if ($hasElliptic) { Write-Output "- Detected via Elliptic Virtual Lock service." }
    if ($hasBiosSetting) { Write-Output "- Detected via Lenovo BIOS setting." }
} else {
    Write-Output "No privacy screen detected on this Lenovo device."
}
