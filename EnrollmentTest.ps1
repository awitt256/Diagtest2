#Requires -RunAsAdministrator
<#
.SYNOPSIS
    Comprehensive Enrollment Test - Checks Autopilot, MDM/Intune, and ESP configuration.
.DESCRIPTION
    Checks all enrollment-related properties and displays them in a formatted table
    matching the Enrollment Test specification.
.NOTES
    Author: Anthony Witt
#>

$ErrorActionPreference = "SilentlyContinue"

Write-Host "=========================================================" -ForegroundColor Cyan
Write-Host "           ENROLLMENT & COMPUTRACE TEST                " -ForegroundColor Cyan
Write-Host "=========================================================" -ForegroundColor Cyan
Write-Host ""

# =========================================================
# Helper: Get OOBE Config Bit
# =========================================================
function Test-OobeBit {
    param([int]$Config, [int]$Bit)
    return ($Config -band $Bit) -gt 0
}

# =========================================================
# Helper: Computrace Detection Functions
# =========================================================
$IndicatorRegex = '(?i)rpcnet|absolute|computrace|lojack|ctes'

function New-ComputraceFinding {
    param(
        [string]$Category,
        [string]$Name,
        [string]$Status,
        [string]$Details
    )

    [pscustomobject]@{
        Category = $Category
        Name     = $Name
        Status   = $Status
        Details  = $Details
    }
}

function Safe-GetCimInstance {
    param(
        [string]$ClassName,
        [string]$Namespace = 'root/cimv2',
        [string]$Filter
    )

    try {
        $params = @{
            ClassName = $ClassName
            Namespace = $Namespace
        }

        if ($Filter) {
            $params.Filter = $Filter
        }

        Get-CimInstance @params
    }
    catch {
        @()
    }
}

function Get-BiosStateStatus {
    param(
        [string]$Name,
        [string]$CurrentValue
    )

    $normalizedName = [string]$Name
    $normalizedValue = ([string]$CurrentValue).Trim()

    if (
        $normalizedName -match '(?i)Permanent\s*Disable\s*Absolute\s*Persistence\s*Module\s*Set\s*Once' -and
        $normalizedValue -match '^(?i)(Yes|No)$'
    ) {
        return 'Info'
    }

    if ($normalizedValue -match '^(?i)(Activate|Activated|Active|Enable|Enabled|On|True)$') {
        return 'Enabled'
    }

    if ($normalizedValue -match '^(?i)(Deactivate|Deactivated|Disable|Disabled|Inactive|Off|False)$') {
        return 'Disabled'
    }

    return 'Reported'
}

function Get-ProcessIndicators {
    $targets = @(
        'rpcnet',
        'rpcnetp',
        'ctes',
        'cteshost',
        'upgrd',
        'atrack',
        'abtagent'
    )

    $found = foreach ($name in $targets) {
        $proc = Get-Process -Name $name -ErrorAction SilentlyContinue
        if ($proc) {
            foreach ($item in $proc) {
                New-ComputraceFinding -Category 'Process' -Name $item.ProcessName -Status 'Present' -Details "PID $($item.Id)"
            }
        }
    }

    if (-not $found) {
        New-ComputraceFinding -Category 'Process' -Name 'Known rpcnet/ctes and Absolute/Computrace processes' -Status 'NotFound' -Details 'No known rpcnet/ctes or Computrace-related processes were running.'
    }
    else {
        $found
    }
}

function Get-ServiceIndicators {
    $serviceNames = @(
        'rpcnet',
        'rpcnetp',
        'ctes',
        'cteshost',
        'upgrd',
        'Absolute*',
        'LoJack*'
    )

    $services = foreach ($pattern in $serviceNames) {
        Get-Service -Name $pattern -ErrorAction SilentlyContinue
    }

    if (-not $services) {
        New-ComputraceFinding -Category 'Service' -Name 'Known rpcnet/ctes and Absolute/Computrace services' -Status 'NotFound' -Details 'No known rpcnet/ctes or Computrace-related services were installed.'
        return
    }

    foreach ($svc in ($services | Sort-Object Name -Unique)) {
        New-ComputraceFinding -Category 'Service' -Name $svc.Name -Status $svc.Status.ToString() -Details "StartType: $($svc.StartType)"
    }
}

function Get-DriverIndicators {
    $drivers = Safe-GetCimInstance -ClassName Win32_SystemDriver |
        Where-Object {
            $_.Name -match $IndicatorRegex -or
            $_.DisplayName -match $IndicatorRegex -or
            $_.PathName -match $IndicatorRegex
        }

    if (-not $drivers) {
        New-ComputraceFinding -Category 'Driver' -Name 'Known rpcnet/ctes and Absolute/Computrace drivers' -Status 'NotFound' -Details 'No matching rpcnet/ctes or Computrace-related drivers were found.'
        return
    }

    foreach ($driver in $drivers) {
        $details = @(
            "State: $($driver.State)"
            "StartMode: $($driver.StartMode)"
            "Path: $($driver.PathName)"
        ) -join '; '

        New-ComputraceFinding -Category 'Driver' -Name $driver.Name -Status 'Present' -Details $details
    }
}

function Get-FileIndicators {
    $paths = @(
        "$env:windir\System32\rpcnet.exe",
        "$env:windir\System32\rpcnetp.exe",
        "$env:windir\System32\ctes.exe",
        "$env:windir\System32\cteshost.exe",
        "$env:windir\SysWOW64\rpcnet.exe",
        "$env:windir\SysWOW64\rpcnetp.exe",
        "$env:windir\SysWOW64\ctes.exe",
        "$env:windir\SysWOW64\cteshost.exe"
    )

    $existing = $paths | Where-Object { Test-Path $_ }

    if (-not $existing) {
        New-ComputraceFinding -Category 'File' -Name 'Known rpcnet/ctes and Absolute/Computrace files' -Status 'NotFound' -Details 'No known rpcnet/ctes or Computrace binaries were found in standard Windows paths.'
        return
    }

    foreach ($path in $existing) {
        $item = Get-Item $path
        New-ComputraceFinding -Category 'File' -Name $item.Name -Status 'Present' -Details $item.FullName
    }
}

function Get-RegistryIndicators {
    $paths = @(
        'HKLM:\SYSTEM\CurrentControlSet\Services\rpcnet',
        'HKLM:\SYSTEM\CurrentControlSet\Services\rpcnetp',
        'HKLM:\SYSTEM\CurrentControlSet\Services\ctes',
        'HKLM:\SYSTEM\CurrentControlSet\Services\cteshost',
        'HKLM:\SOFTWARE\Absolute Software',
        'HKLM:\SOFTWARE\CTES',
        'HKLM:\SOFTWARE\WOW6432Node\Absolute Software',
        'HKLM:\SOFTWARE\WOW6432Node\CTES',
        'HKLM:\SOFTWARE\Microsoft\Windows\CurrentVersion\Run'
    )

    $findings = @()

    foreach ($path in $paths) {
        if (-not (Test-Path $path)) {
            continue
        }

        if ($path -like '*\Run') {
            try {
                $props = Get-ItemProperty -Path $path
                foreach ($property in $props.PSObject.Properties) {
                    if ($property.Name -in 'PSPath', 'PSParentPath', 'PSChildName', 'PSDrive', 'PSProvider') {
                        continue
                    }

                    if ($property.Name -match $IndicatorRegex -or [string]$property.Value -match $IndicatorRegex) {
                        $findings += New-ComputraceFinding -Category 'Registry' -Name $property.Name -Status 'Present' -Details "$path -> $($property.Value)"
                    }
                }
            }
            catch {
            }

            continue
        }

        $findings += New-ComputraceFinding -Category 'Registry' -Name (Split-Path $path -Leaf) -Status 'Present' -Details $path
    }

    if (-not $findings) {
        New-ComputraceFinding -Category 'Registry' -Name 'Known rpcnet/ctes and Absolute/Computrace registry keys' -Status 'NotFound' -Details 'No matching rpcnet/ctes or Computrace-related registry indicators were found.'
    }
    else {
        $findings
    }
}

function Get-BiosIndicators {
    $findings = @()

    $baseboard = Safe-GetCimInstance -ClassName Win32_ComputerSystem
    $bios = Safe-GetCimInstance -ClassName Win32_BIOS

    if ($baseboard) {
        $findings += New-ComputraceFinding -Category 'System' -Name 'Manufacturer' -Status 'Info' -Details "$($baseboard.Manufacturer) $($baseboard.Model)"
    }

    if ($bios) {
        $biosText = @(
            $bios.Manufacturer
            $bios.Name
            $bios.Description
            ($bios.BIOSVersion -join ' ')
            ($bios.SMBIOSBIOSVersion)
        ) -join ' '

        if ($biosText -match '(?i)absolute|computrace|ctes') {
            $findings += New-ComputraceFinding -Category 'BIOS' -Name 'Win32_BIOS text match' -Status 'Possible' -Details ($biosText.Trim())
        }
    }

    $dellAttrs = Safe-GetCimInstance -Namespace 'root/dcim/sysman/biosattributes' -ClassName EnumerationAttribute |
        Where-Object { $_.AttributeName -match '(?i)absolute|computrace|persistence|ctes' }

    foreach ($attr in $dellAttrs) {
        $status = Get-BiosStateStatus -Name $attr.AttributeName -CurrentValue $attr.CurrentValue
        $details = @(
            "CurrentValue: $($attr.CurrentValue)"
            "PossibleValues: $($attr.PossibleValues -join ', ')"
        ) -join '; '

        $findings += New-ComputraceFinding -Category 'BIOS' -Name "Dell BIOS: $($attr.AttributeName)" -Status $status -Details $details
    }

    $lenovoSettings = Safe-GetCimInstance -Namespace 'root/wmi' -ClassName Lenovo_BiosSetting |
        Where-Object { $_.CurrentSetting -match '(?i)absolute|computrace|persistence|ctes' }

    foreach ($setting in $lenovoSettings) {
        $parts = @([string]$setting.CurrentSetting -split ',', 2)
        $settingName = if ($parts.Count -ge 1) { $parts[0].Trim() } else { 'Lenovo BIOS setting' }
        $currentValue = if ($parts.Count -ge 2) { $parts[1].Trim() } else { [string]$setting.CurrentSetting }
        $status = Get-BiosStateStatus -Name $settingName -CurrentValue $currentValue

        $findings += New-ComputraceFinding -Category 'BIOS' -Name "Lenovo BIOS: $settingName" -Status $status -Details "CurrentValue: $currentValue"
    }

    $hpSettings = Safe-GetCimInstance -Namespace 'root/HP/InstrumentedBIOS' -ClassName HP_BIOSEnumeration |
        Where-Object { $_.Name -match '(?i)absolute|computrace|persistence|ctes' }

    foreach ($setting in $hpSettings) {
        $status = Get-BiosStateStatus -Name $setting.Name -CurrentValue $setting.CurrentValue
        $details = @(
            "CurrentValue: $($setting.CurrentValue)"
            "PossibleValues: $($setting.PossibleValues -join ', ')"
        ) -join '; '

        $findings += New-ComputraceFinding -Category 'BIOS' -Name "HP BIOS: $($setting.Name)" -Status $status -Details $details
    }

    if (-not ($findings | Where-Object { $_.Category -eq 'BIOS' })) {
        $findings += New-ComputraceFinding -Category 'BIOS' -Name 'Vendor BIOS status' -Status 'Unknown' -Details 'No vendor BIOS class exposed Computrace/Absolute status. BIOS activation may still need to be checked manually.'
    }

    $findings
}

# =========================================================
# 1. Gather Enrollment Status
# =========================================================
$enrollmentStatus = "Not Enrolled"
$isMdmEnrolled = $false

# dsregcmd check
$dsreg = dsregcmd /status
if ($dsreg -match "MdmEnrolled\s*:\s*YES") {
    $isMdmEnrolled = $true
    $enrollmentStatus = "Enrolled"
}
if ($dsreg -match "AzureAdJoined\s*:\s*YES") {
    if ($enrollmentStatus -eq "Not Enrolled") { $enrollmentStatus = "Azure AD Joined" }
    else { $enrollmentStatus += " / Azure AD Joined" }
}

# WMI MDM check
$wmiMdm = Get-CimInstance -Namespace "ROOT\CIMV2\mdm\dmmap" -ClassName "MDM_Client" -ErrorAction SilentlyContinue
if ($wmiMdm) {
    $isMdmEnrolled = $true
    if ($enrollmentStatus -eq "Not Enrolled") { $enrollmentStatus = "MDM Enrolled" }
}

# =========================================================
# 2. Gather Autopilot Data
# =========================================================
$autopilotRegPath = "HKLM:\SOFTWARE\Microsoft\Provisioning\Diagnostics\AutoPilot"
$autopilotValues = $null
$isAutopilotDevice = "NO"
$profileConfigured = "NO"
$organizationDomain = "Not configured"
$organizationId = "Not available"
$ztdId = "Not assigned"
$entDmId = "Not available"
$cloudAssignedOobe = "Not configured"
$joinType = "Azure AD Join"
$skipKeyboard = "NO"
$updateDownloads = "DISABLED"
$skipUpgradeUx = "NO"
$tpmRequired = "NO"
$aadDeviceAuth = "DISABLED"
$tpmAttestation = "DISABLED"
$skipEula = "NO"
$skipOemReg = "NO"
$skipExpress = "NO"
$disallowAdmin = "NO"
$enrollmentTenantId = $null
$forcedEnrollment = "NO"

if (Test-Path $autopilotRegPath) {
    $autopilotValues = Get-ItemProperty -Path $autopilotRegPath -ErrorAction SilentlyContinue
    $enrollmentTenantId = $autopilotValues.TenantId
    $forcedEnrollmentValue = $autopilotValues.isForcedEnrollmentEnabled

    if ($forcedEnrollmentValue -eq 1) { $forcedEnrollment = "YES" }
    else { $forcedEnrollment = "NO" }

    if ($autopilotValues.CloudAssignedTenantId) {
        $isAutopilotDevice = "YES"
        $organizationId = $autopilotValues.CloudAssignedTenantId
        $organizationDomain = if ($autopilotValues.CloudAssignedTenantDomain) { $autopilotValues.CloudAssignedTenantDomain } else { "Configured" }
        $profileConfigured = if ($autopilotValues.DeploymentProfileName) { $autopilotValues.DeploymentProfileName } else { "YES" }

        if ($autopilotValues.CloudAssignedOobeConfig -ne $null) {
            $oobe = [int]$autopilotValues.CloudAssignedOobeConfig
            $cloudAssignedOobe = "0x$($oobe.ToString('X4'))"

            if (Test-OobeBit -Config $oobe -Bit 1024) { $skipKeyboard = "YES" }
            if (Test-OobeBit -Config $oobe -Bit 512)  { $updateDownloads = "ENABLED" }
            if (Test-OobeBit -Config $oobe -Bit 256)  { $skipUpgradeUx = "YES" }
            if (Test-OobeBit -Config $oobe -Bit 128)  { $tpmRequired = "YES" }
            if (Test-OobeBit -Config $oobe -Bit 64)   { $aadDeviceAuth = "ENABLED" }
            if (Test-OobeBit -Config $oobe -Bit 32)   { $tpmAttestation = "ENABLED" }
            if (Test-OobeBit -Config $oobe -Bit 16)   { $skipEula = "YES" }
            if (Test-OobeBit -Config $oobe -Bit 8)    { $skipOemReg = "YES" }
            if (Test-OobeBit -Config $oobe -Bit 4)    { $skipExpress = "YES" }
            if (Test-OobeBit -Config $oobe -Bit 2)    { $disallowAdmin = "YES" }
        }
    }

    # Correlations
    $correlationsPath = "$autopilotRegPath\EstablishedCorrelations"
    if (Test-Path $correlationsPath) {
        $corr = Get-ItemProperty -Path $correlationsPath -ErrorAction SilentlyContinue
        if ($corr.ZTDRegistrationID) { $ztdId = $corr.ZTDRegistrationID }
        if ($corr.EntDMID)           { $entDmId = $corr.EntDMID }
    }

    # Join Type from JSON
    $jsonFile = "$env:WINDIR\ServiceState\wmansvc\AutopilotDDSZTDFile.json"
    if (Test-Path $jsonFile) {
        try {
            $json = Get-Content $jsonFile | ConvertFrom-Json
            if ($json.CloudAssignedDomainJoinMethod -eq 1) { $joinType = "Hybrid Azure AD Join" }
            elseif ($json.CloudAssignedDomainJoinMethod -eq 0) { $joinType = "Azure AD Join" }
            else { $joinType = "Unknown ($($json.CloudAssignedDomainJoinMethod))" }
        } catch {
            $joinType = "Azure AD Join"
        }
    }
}

# =========================================================
# 3. Gather ESP / Enrollment Page Settings
# =========================================================
$deviceStatusPage = "DISABLED"
$userStatusPage = "DISABLED"
$setupTimeout = "No limit"
$blockingDuringSetup = "NO"

$enrollmentsPath = "HKLM:\SOFTWARE\Microsoft\Enrollments"
if (Test-Path $enrollmentsPath) {
    Get-ChildItem $enrollmentsPath -ErrorAction SilentlyContinue |
        Where-Object { Test-Path "$($_.PSPath)\FirstSync" } | ForEach-Object {
            $props = Get-ItemProperty "$($_.PSPath)\FirstSync" -ErrorAction SilentlyContinue
            if ($props) {
                if ($props.SkipDeviceStatusPage -eq 0) { $deviceStatusPage = "ENABLED" }
                else { $deviceStatusPage = "DISABLED" }

                if ($props.SkipUserStatusPage -eq 0) { $userStatusPage = "ENABLED" }
                else { $userStatusPage = "DISABLED" }

                if ($props.SyncFailureTimeout -ne $null -and $props.SyncFailureTimeout -gt 0) {
                    $setupTimeout = "$($props.SyncFailureTimeout) minutes"
                }

                if ($props.BlockInStatusPage -ne 0) { $blockingDuringSetup = "YES" }
                else { $blockingDuringSetup = "NO" }
            }
        }
}

# =========================================================
# 4. Detect Computrace / Absolute Persistence
# =========================================================
Write-Host "" 
Write-Host "---------------------------------------------------------" -ForegroundColor Cyan
Write-Host "  COMPUTRACE / ABSOLUTE PERSISTENCE DETECTION" -ForegroundColor Cyan
Write-Host "---------------------------------------------------------" -ForegroundColor Cyan
Write-Host ""

$computraceFindings = @()
$computraceFindings += Get-ProcessIndicators
$computraceFindings += Get-ServiceIndicators
$computraceFindings += Get-DriverIndicators
$computraceFindings += Get-FileIndicators
$computraceFindings += Get-RegistryIndicators
$computraceFindings += Get-BiosIndicators

$osCategories = @('Process', 'Service', 'Driver', 'File', 'Registry')
$osPositiveFindings = @(
    $computraceFindings | Where-Object {
        $_.Category -in $osCategories -and $_.Status -ne 'NotFound'
    }
)

$biosEnabledFindings = @(
    $computraceFindings | Where-Object {
        $_.Category -eq 'BIOS' -and $_.Status -eq 'Enabled'
    }
)

$biosReviewFindings = @(
    $computraceFindings | Where-Object {
        $_.Category -eq 'BIOS' -and $_.Status -in @('Possible', 'Reported')
    }
)

if ($osPositiveFindings) {
    $computraceResult = 'FAIL'
    $computraceColor = 'Red'
    $computraceSummary = 'Active OS-level Absolute/Computrace indicators were found.'
}
elseif ($biosEnabledFindings) {
    $computraceResult = 'WARN'
    $computraceColor = 'Yellow'
    $computraceSummary = 'No active OS-level indicators were found, but BIOS reports Absolute/Computrace as enabled.'
}
elseif ($biosReviewFindings) {
    $computraceResult = 'WARN'
    $computraceColor = 'Yellow'
    $computraceSummary = 'No active OS-level indicators were found. BIOS information was reported and should be reviewed manually.'
}
else {
    $computraceResult = 'PASS'
    $computraceColor = 'Green'
    $computraceSummary = 'No active OS-level indicators were found, and BIOS did not report Absolute/Computrace as enabled.'
}

Write-Host "Computrace Result: $computraceResult" -ForegroundColor $computraceColor
Write-Host "Summary: $computraceSummary" -ForegroundColor $computraceColor
Write-Host ""

# Display Computrace findings in table format
$computraceFindings | Format-Table -AutoSize
Write-Host ""

# =========================================================
# 5. Build Observations
# =========================================================
$observations = @()
if ($isAutopilotDevice -eq "NO") {
    $observations += "This is not an Autopilot device."
}
if ($enrollmentStatus -eq "Not Enrolled") {
    $observations += "Device is not enrolled"
}
if ($isAutopilotDevice -eq "YES" -and $enrollmentStatus -eq "Not Enrolled") {
    $observations += "Autopilot profile present but device is not yet enrolled."
}
if ($computraceResult -eq "FAIL") {
    $observations += "Computrace/Absolute Persistence detected - requires investigation."
}
elseif ($computraceResult -eq "WARN") {
    $observations += "Computrace/Absolute BIOS indicators detected - review recommended."
}

# =========================================================
# 6. Build Output Table
# =========================================================
$output = [ordered]@{
    "Enrollment Status"          = $enrollmentStatus
    "Autopilot Device"           = $isAutopilotDevice
    "Profile Configured"         = $profileConfigured
    "Organization Domain"        = $organizationDomain
    "Organization ID"            = $organizationId
    "Zero Touch Device ID"       = $ztdId
    "Enterprise Management ID"   = $entDmId
    "Cloud Assigned OOBE"        = $cloudAssignedOobe
    "Join Type"                  = $joinType
    "Skip Keyboard Setup"        = $skipKeyboard
    "Update Downloads"           = $updateDownloads
    "Skip Upgrade Experience"    = $skipUpgradeUx
    "TPM Chip Required"          = $tpmRequired
    "AAD Device Authentication"  = $aadDeviceAuth
    "TPM Attestation"            = $tpmAttestation
    "Skip License Agreement"     = $skipEula
    "Skip OEM Registration"      = $skipOemReg
    "Skip Express Settings"      = $skipExpress
    "Disallow Local Admin"       = $disallowAdmin
    "Device Status Page"         = $deviceStatusPage
    "User Status Page"           = $userStatusPage
    "Setup Timeout"              = $setupTimeout
    "Blocking During Setup"      = $blockingDuringSetup
    "Computrace Result"          = $computraceResult
    "Computrace Summary"         = $computraceSummary
    "Observations"               = if ($observations.Count -gt 0) { $observations -join "; " } else { "None" }
    "Enrollment Organization ID" = if ($enrollmentTenantId) { $enrollmentTenantId } else { "Not available" }
    "Forced Enrollment"          = $forcedEnrollment
}

# =========================================================
# 7. Build & Display Formatted Table
# =========================================================
$maxKeyLength = ($output.Keys | Measure-Object -Property Length -Maximum).Maximum
$lineWidth = $maxKeyLength + 40
$txtLines = [System.Collections.Generic.List[string]]::new()

function Add-TxtLine {
    param([string]$Line)
    $txtLines.Add($Line)
}

# Header
$sepLine = "-" * $lineWidth
Add-TxtLine $sepLine
Add-TxtLine "Enrollment Test"
Add-TxtLine $sepLine
$headerProperty = "Property".PadRight($maxKeyLength)
Add-TxtLine "$headerProperty | Value"
Add-TxtLine $sepLine

Write-Host $sepLine -ForegroundColor Gray
Write-Host "Enrollment Test" -ForegroundColor Cyan
Write-Host $sepLine -ForegroundColor Gray
Write-Host "$headerProperty | Value" -ForegroundColor White
Write-Host $sepLine -ForegroundColor Gray

# Rows
foreach ($key in $output.Keys) {
    $paddedKey = $key.PadRight($maxKeyLength)
    $value = $output[$key]

    Add-TxtLine "$paddedKey | $value"

    # Color coding
    $color = "White"
    if ($key -eq "Enrollment Status" -and $value -ne "Not Enrolled") { $color = "Yellow" }
    if ($key -eq "Autopilot Device" -and $value -eq "YES") { $color = "Yellow" }
    if ($key -eq "Forced Enrollment" -and $value -eq "YES") { $color = "Red" }
    if ($value -eq "ENABLED") { $color = "Green" }
    if ($value -eq "DISABLED") { $color = "DarkGray" }
    if ($key -eq "Observations" -and $value -ne "None") { $color = "Yellow" }
    if ($key -eq "Computrace Result" -and $value -eq "FAIL") { $color = "Red" }
    if ($key -eq "Computrace Result" -and $value -eq "WARN") { $color = "Yellow" }
    if ($key -eq "Computrace Result" -and $value -eq "PASS") { $color = "Green" }

    Write-Host "$paddedKey | " -NoNewline -ForegroundColor Gray
    Write-Host "$value" -ForegroundColor $color
}

Add-TxtLine $sepLine
Write-Host $sepLine -ForegroundColor Gray
Write-Host ""
Add-TxtLine ""

# =========================================================
# 8. Observations Section
# =========================================================
if ($observations.Count -gt 0) {
    Add-TxtLine "Observations"
    Write-Host "Observations" -ForegroundColor White
    foreach ($obs in $observations) {
        Add-TxtLine "  * $obs"
        Write-Host "  * $obs" -ForegroundColor Yellow
    }
    Add-TxtLine ""
    Write-Host ""
}

# =========================================================
# 9. Save to TXT and JSON
# =========================================================
$timestamp = Get-Date -Format 'yyyyMMdd_HHmmss'
$txtPath = "$env:TEMP\EnrollmentTest_$timestamp.txt"
$jsonPath = "$env:TEMP\EnrollmentTest_$timestamp.json"

$txtLines | Out-File -FilePath $txtPath -Encoding UTF8
$output | ConvertTo-Json | Out-File -FilePath $jsonPath -Encoding UTF8

Write-Host "Text report saved to: $txtPath" -ForegroundColor Green
Write-Host "JSON report saved to: $jsonPath" -ForegroundColor DarkGray
Write-Host ""

# Output result marker for Python GUI
if ($computraceResult -eq "FAIL" -or $enrollmentStatus -ne "Not Enrolled" -or $isAutopilotDevice -eq "YES") {
    Write-Output "ENROLLMENT_CHECK_RESULT:FAIL"
    exit 1
} else {
    Write-Output "ENROLLMENT_CHECK_RESULT:PASS"
    exit 0
}

Read-Host "Press Enter to exit..."
