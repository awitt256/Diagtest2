$isAdminSession = ([Security.Principal.WindowsPrincipal] [Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole(
    [Security.Principal.WindowsBuiltInRole]::Administrator
)

$script:ScriptPath = if ($PSCommandPath) { $PSCommandPath } else { $MyInvocation.MyCommand.Path }
$script:ScriptDirectory = if (-not [string]::IsNullOrWhiteSpace($script:ScriptPath)) {
    Split-Path -Parent $script:ScriptPath
}
else {
    (Get-Location).Path
}
$script:LogFile = Join-Path $script:ScriptDirectory ("{0}.log" -f [System.IO.Path]::GetFileNameWithoutExtension($script:ScriptPath))

if (-not $isAdminSession) {
    $scriptPath = $script:ScriptPath

    if (-not [string]::IsNullOrWhiteSpace($scriptPath)) {
        Start-Process -FilePath "powershell.exe" -ArgumentList @(
            "-NoProfile"
            "-ExecutionPolicy", "Bypass"
            "-File", ('"{0}"' -f $scriptPath)
        ) -Verb RunAs
        exit
    }
}

$script:LastBcuFiles = $null

try {
    Start-Transcript -LiteralPath $script:LogFile -Force | Out-Null
}
catch {
    Write-Warning ("Unable to start transcript log at {0}. {1}" -f $script:LogFile, $_.Exception.Message)
}

function Get-CommonSystemData {
    $systemInfo = Get-CimInstance -ClassName Win32_ComputerSystem
    $biosInfo = Get-CimInstance -ClassName Win32_BIOS
    $processor = Get-CimInstance -ClassName Win32_Processor
    $disks = Get-CimInstance -ClassName Win32_DiskDrive
    $ramModules = Get-CimInstance -ClassName Win32_PhysicalMemory
    $gpus = Get-CimInstance -ClassName Win32_VideoController | Where-Object {
        $_.AdapterRAM -gt 0 -and
        $_.Name -notmatch "Microsoft Basic Display|Remote Display|VMware|Virtual"
    }

    return [pscustomobject]@{
        SystemInfo = $systemInfo
        BiosInfo = $biosInfo
        Processor = $processor
        Disks = $disks
        RamModules = $ramModules
        Gpus = $gpus
    }
}

function Get-AdminPasswordText {
    param(
        $Status
    )

    switch ($Status) {
        0 { "No" }
        1 { "Yes" }
        2 { "NA" }
        3 { "Unknown" }
        default { "Unknown" }
    }
}

function Get-InternalPhysicalDisks {
    param(
        [Parameter(Mandatory = $true)]
        [object[]]$Disks
    )

    return @(
        $Disks | Where-Object {
            $interfaceType = [string]$_.InterfaceType
            $model = [string]$_.Model
            $pnpDeviceId = [string]$_.PNPDeviceID

            $interfaceType -notmatch '^(?i)USB$' -and
            $model -notmatch '(?i)\bUSB\b' -and
            $pnpDeviceId -notmatch '(?i)^USBSTOR\\'
        }
    )
}

function Get-RoundedDriveCapacityGB {
    param(
        [Parameter(Mandatory = $true)]
        [double]$SizeGB
    )

    if ($SizeGB -le 32) { return 32 }
    if ($SizeGB -ge 45 -and $SizeGB -le 64) { return 64 }
    if ($SizeGB -ge 90 -and $SizeGB -le 128) { return 128 }
    if ($SizeGB -ge 160 -and $SizeGB -le 256) { return 256 }
    if ($SizeGB -ge 400 -and $SizeGB -le 512) { return 512 }
    if ($SizeGB -ge 800 -and $SizeGB -le 1024) { return 1024 }
    if ($SizeGB -ge 1800 -and $SizeGB -le 2048) { return 2048 }

    return [math]::Round($SizeGB, 2)
}

function Format-DriveCapacityLabel {
    param(
        [Parameter(Mandatory = $true)]
        [double]$SizeGB
    )

    if ($SizeGB -ge 1024) {
        $sizeTB = $SizeGB / 1024
        if ([math]::Abs($sizeTB - [math]::Round($sizeTB, 0)) -lt 0.001) {
            return ("{0} TB" -f [math]::Round($sizeTB, 0))
        }

        return ("{0:N2} TB" -f $sizeTB)
    }

    if ([math]::Abs($SizeGB - [math]::Round($SizeGB, 0)) -lt 0.001) {
        return ("{0} GB" -f [math]::Round($SizeGB, 0))
    }

    return ("{0:N2} GB" -f $SizeGB)
}

function Get-WindowsActivationData {
    return Get-CimInstance -ClassName SoftwareLicensingProduct -Filter "Name like 'Windows%'" |
        Where-Object { $_.PartialProductKey -and $_.LicenseStatus -ne $null } |
        Select-Object -First 1
}

function Write-WindowsActivationSection {
    Write-Output ""
    Write-SectionHeader -Title "Windows Activation Status"
    Write-Output "Checking activation status..."

    $activation = Get-WindowsActivationData
    if ($activation -and $activation.LicenseStatus -eq 1) {
        Write-Output "Windows is Activated."
    }
    else {
        Write-Output "Windows is not activated."
    }
}

function Write-SectionHeader {
    param(
        [Parameter(Mandatory = $true)]
        [string]$Title
    )

    $lineLength = [Math]::Max($Title.Length, 16)
    $line = "=" * $lineLength

    Write-Output $line
    Write-Output ""
    Write-Output $Title
    Write-Output $line
}

function Write-CommonSystemInfo {
    param(
        [Parameter(Mandatory = $true)]
        $Data
    )

    Write-Output "================"
    Write-Output ""
    Write-Output "System Info"
    Write-Output "================"
    Write-Output "System Serial: $($Data.BiosInfo.SerialNumber)"
    Write-Output "System SKU: $($Data.SystemInfo.SystemSKUNumber)"
    Write-Output "System Model: $($Data.SystemInfo.Model)"
    Write-Output "System Name: $($Data.SystemInfo.Name)"
    Write-Output "BIOS Password: $(Get-AdminPasswordText -Status $Data.SystemInfo.AdminPasswordStatus)"

    Write-Output "============="
    Write-Output ""
    Write-Output "CPU Info"
    Write-Output "============="
    foreach ($cpu in $Data.Processor) {
        Write-Output "Name: $($cpu.Name)"
        Write-Output "Manufacturer: $($cpu.Manufacturer)"
        Write-Output "Max Clock Speed (MHz): $($cpu.MaxClockSpeed)"
    }

    Write-Output "==============="
    Write-Output ""
    Write-Output "Hard Drives"
    Write-Output "==============="
    $internalDisks = Get-InternalPhysicalDisks -Disks $Data.Disks
    $roundedTotalGB = 0
    foreach ($disk in $internalDisks) {
        $sizeGB = if ($disk.Size) { [double]$disk.Size / 1GB } else { 0 }
        $roundedSizeGB = Get-RoundedDriveCapacityGB -SizeGB $sizeGB
        Write-Output "Model: $($disk.Model)"
        Write-Output "Size: $(Format-DriveCapacityLabel -SizeGB $roundedSizeGB)"
        $roundedTotalGB += $roundedSizeGB
    }

    if (-not $internalDisks) {
        Write-Output "No internal HDDs or SSDs detected."
    }
    elseif ($internalDisks.Count -gt 1) {
        Write-Output "Total: $(Format-DriveCapacityLabel -SizeGB $roundedTotalGB)"
    }

    Write-Output "=============="
    Write-Output ""
    Write-Output "Memory"
    Write-Output "=============="
    foreach ($ram in $Data.RamModules) {
        $ramSizeGB = [math]::Round($ram.Capacity / 1GB, 2)
        Write-Output "Name: $($ram.Manufacturer) $($ram.PartNumber)"
        Write-Output "Size: $ramSizeGB GB"
    }

    Write-Output "============="
    Write-Output ""
    Write-Output "GPU Info"
    Write-Output "============="
    foreach ($gpu in $Data.Gpus) {
        $vramGB = [math]::Round($gpu.AdapterRAM / 1GB, 2)
        Write-Output "Name: $($gpu.Name)"
        Write-Output "Video Memory: $vramGB GB"
        Write-Output ""
    }
}

function Get-ConnectedPnPDevices {
    $rawOutput = & pnputil /enum-devices /connected 2>$null
    if (-not $rawOutput) {
        return @()
    }

    $devices = @()
    $current = @{}

    foreach ($line in $rawOutput) {
        if ($line -match '^\s*$') {
            if ($current.Count -gt 0) {
                $devices += [pscustomobject]$current
                $current = @{}
            }
            continue
        }

        if ($line -match '^\s*Class Name:\s*(.+)$') {
            $current["ClassName"] = $Matches[1].Trim()
            continue
        }
        if ($line -match '^\s*Class GUID:\s*(.+)$') {
            $current["ClassGuid"] = $Matches[1].Trim()
            continue
        }
        if ($line -match '^\s*Device Description:\s*(.+)$') {
            $current["DeviceDescription"] = $Matches[1].Trim()
            continue
        }
        if ($line -match '^\s*Instance ID:\s*(.+)$') {
            $current["InstanceId"] = $Matches[1].Trim()
            continue
        }
    }

    if ($current.Count -gt 0) {
        $devices += [pscustomobject]$current
    }

    return $devices
}

function Convert-BiosEntryToText {
    param(
        [Parameter(Mandatory = $true)]
        $Entry
    )

    if ($null -eq $Entry) {
        return ""
    }

    $parts = @()
    foreach ($property in $Entry.PSObject.Properties) {
        if ($null -ne $property.Value -and "$($property.Value)".Trim()) {
            $parts += "{0}: {1}" -f $property.Name, $property.Value
        }
    }

    return ($parts -join " | ")
}

function Get-NormalizedBiosVersion {
    param(
        [string]$Value
    )

    if ([string]::IsNullOrWhiteSpace($Value)) {
        return $null
    }

    $versionMatch = [regex]::Match($Value, '(?i)\b\d{2}\.\d{2}\.\d{2}\b')
    if ($versionMatch.Success) {
        return $versionMatch.Value
    }

    return $Value.Trim()
}

function Get-HpBcuPath {
    $candidates = @(
        (Join-Path $script:ScriptDirectory "bcu\BiosConfigUtility64.exe")
        (Join-Path $script:ScriptDirectory "bcu\BiosConfigUtility.exe")
        "C:\Program Files\HP\BIOS Configuration Utility\BiosConfigUtility64.exe"
        "C:\Program Files (x86)\HP\BIOS Configuration Utility\BiosConfigUtility64.exe"
        "C:\Program Files\HP\BIOS Configuration Utility\BiosConfigUtility.exe"
        "C:\Program Files (x86)\HP\BIOS Configuration Utility\BiosConfigUtility.exe"
    )

    foreach ($candidate in $candidates) {
        if (Test-Path -LiteralPath $candidate) {
            return $candidate
        }
    }

    return $null
}

function Convert-HpBcuConfigToEntries {
    param(
        [AllowEmptyCollection()]
        [AllowEmptyString()]
        [string[]]$Content = @()
    )

    $entries = @()
    $currentSetting = $null
    $currentValue = $null
    $sawOptionForSetting = $false

    foreach ($rawLine in $Content) {
        $line = [string]$rawLine
        if ([string]::IsNullOrWhiteSpace($line)) {
            continue
        }

        $trimmed = $line.Trim()
        if ($trimmed -match '^(;|BIOSConfig\b|English$)') {
            continue
        }

        if ($trimmed -match '^[^=,:]+[:=]\s*.+$' -and $line -notmatch '^\s') {
            $separatorIndex = $trimmed.IndexOf('=')
            if ($separatorIndex -lt 0) {
                $separatorIndex = $trimmed.IndexOf(':')
            }

            if ($separatorIndex -gt 0) {
                $entries += [pscustomobject]@{
                    Setting = $trimmed.Substring(0, $separatorIndex).Trim()
                    Value = $trimmed.Substring($separatorIndex + 1).Trim()
                }
                $currentSetting = $null
                $currentValue = $null
                $sawOptionForSetting = $false
                continue
            }
        }

        if ($line -notmatch '^\s') {
            if ($currentSetting -and -not $sawOptionForSetting -and $currentValue) {
                $entries += [pscustomobject]@{
                    Setting = $currentSetting
                    Value = $currentValue
                }
            }

            $currentSetting = $trimmed
            $currentValue = $null
            $sawOptionForSetting = $false
            continue
        }

        if (-not $currentSetting) {
            continue
        }

        $optionText = $trimmed.TrimStart('*').Trim()
        if (-not $optionText) {
            continue
        }

        $sawOptionForSetting = $true

        if ($trimmed.StartsWith('*')) {
            $currentValue = $optionText
            $entries += [pscustomobject]@{
                Setting = $currentSetting
                Value = $currentValue
            }
        }
    }

    if ($currentSetting -and -not $sawOptionForSetting -and $currentValue) {
        $entries += [pscustomobject]@{
            Setting = $currentSetting
            Value = $currentValue
        }
    }

    return @($entries)
}

function Get-TrimmedFileText {
    param(
        [Parameter(Mandatory = $true)]
        [string]$Path
    )

    if (-not (Test-Path -LiteralPath $Path)) {
        return ""
    }

    $rawText = Get-Content -LiteralPath $Path -Raw -ErrorAction SilentlyContinue
    if ($null -eq $rawText) {
        return ""
    }

    return $rawText.Trim()
}

function Get-HpBiosEntries {
    $bcuPath = Get-HpBcuPath
    $outputFile = Join-Path $script:ScriptDirectory "bcu-output.txt"
    $stdOutFile = Join-Path $script:ScriptDirectory "bcu-stdout.txt"
    $stdErrFile = Join-Path $script:ScriptDirectory "bcu-stderr.txt"

    $script:LastBcuFiles = [pscustomobject]@{
        Output = $outputFile
        StdOut = $stdOutFile
        StdErr = $stdErrFile
    }

    if (-not $bcuPath) {
        return @{
            Success = $false
            Message = "HP BCU utility not found. Install HP BIOS Configuration Utility and make sure BiosConfigUtility64.exe is available."
            Entries = @()
        }
    }

    try {
        foreach ($path in @($outputFile, $stdOutFile, $stdErrFile)) {
            Set-Content -LiteralPath $path -Value "Created by HPLENDEV2.ps1 at $(Get-Date -Format s)" -Encoding ASCII
            Clear-Content -LiteralPath $path -ErrorAction SilentlyContinue
        }

        $process = Start-Process -FilePath $bcuPath -ArgumentList @("/GetConfig:`"$outputFile`"") -Wait -PassThru -NoNewWindow `
            -RedirectStandardOutput $stdOutFile -RedirectStandardError $stdErrFile

        if (-not (Test-Path -LiteralPath $outputFile)) {
            $stdOut = Get-TrimmedFileText -Path $stdOutFile
            $stdErr = Get-TrimmedFileText -Path $stdErrFile
            $detail = @($stdErr, $stdOut) | Where-Object { -not [string]::IsNullOrWhiteSpace($_) } | Select-Object -First 1

            return @{
                Success = $false
                Message = if ($detail) {
                    "HP BCU did not create a BIOS config file. $detail"
                }
                else {
                    "HP BCU did not create a BIOS config file. Exit code: $($process.ExitCode)"
                }
                Entries = @()
            }
        }

        $content = @(Get-Content -LiteralPath $outputFile -ErrorAction SilentlyContinue)
        $hasMeaningfulContent = $content | Where-Object { -not [string]::IsNullOrWhiteSpace($_) }
        if (-not $hasMeaningfulContent) {
            $stdOut = Get-TrimmedFileText -Path $stdOutFile
            $stdErr = Get-TrimmedFileText -Path $stdErrFile
            $detail = @($stdErr, $stdOut) | Where-Object { -not [string]::IsNullOrWhiteSpace($_) } | Select-Object -First 1

            return @{
                Success = $false
                Message = if ($detail) {
                    "HP BCU created an empty BIOS config file. $detail"
                }
                else {
                    "HP BCU created an empty BIOS config file."
                }
                Entries = @()
            }
        }

        $entries = Convert-HpBcuConfigToEntries -Content $content
        if (-not $entries) {
            $preview = ($content | Select-Object -First 20) -join '; '
            $isXmlSummaryOnly = $preview -match '(?i)<BIOSCONFIG\b' -and $preview -match '(?i)<SUCCESS\b'
            return @{
                Success = $false
                Message = if ($isXmlSummaryOnly) {
                    "HP BCU ran successfully but returned only the XML summary, not the BIOS setting list. This usually means BCU exported status information without readable config entries for this system."
                }
                elseif ([string]::IsNullOrWhiteSpace($preview)) {
                    "HP BCU returned a config file, but no BIOS settings could be parsed."
                }
                else {
                    "HP BCU returned a config file, but no BIOS settings could be parsed. Preview: $preview"
                }
                Entries = @()
            }
        }

        return @{
            Success = $true
            Message = $null
            Entries = $entries
        }
    }
    catch {
        return @{
            Success = $false
            Message = $_.Exception.Message
            Entries = @()
        }
    }
}

function Get-HpBiosFeatureState {
    param(
        [Parameter(Mandatory = $true)]
        [object[]]$BiosEntries,

        [Parameter(Mandatory = $true)]
        [string]$Pattern
    )

    $biosEnabledPattern = '(?i)\b(enable|enabled|on|present|installed|active|yes)\b'
    $biosDisabledPattern = '(?i)\b(disable|disabled|off|not\s*installed|absent|inactive|no)\b'

    $matchingEntries = foreach ($entry in $BiosEntries) {
        $entryText = Convert-BiosEntryToText -Entry $entry
        $settingText = if ($entry.PSObject.Properties['Setting']) { [string]$entry.Setting } else { "" }
        $valueText = if ($entry.PSObject.Properties['Value']) { [string]$entry.Value } else { "" }

        if ($settingText -match $Pattern -or $entryText -match $Pattern) {
            [pscustomobject]@{
                Text = $entryText
                Setting = $settingText
                Value = $valueText
            }
        }
    }

    if (-not $matchingEntries) {
        return "No"
    }

    foreach ($match in $matchingEntries) {
        if ($match.Value -match $biosEnabledPattern -or $match.Text -match $biosEnabledPattern) {
            return "Yes"
        }
    }

    foreach ($match in $matchingEntries) {
        if ($match.Value -match $biosDisabledPattern -or $match.Text -match $biosDisabledPattern) {
            return "No"
        }
    }

    return "Yes"
}

function Get-HpBiosSettingValue {
    param(
        [Parameter(Mandatory = $true)]
        [object[]]$BiosEntries,

        [Parameter(Mandatory = $true)]
        [string]$Pattern
    )

    $match = $BiosEntries | Where-Object {
        $_.PSObject.Properties['Setting'] -and [string]$_.Setting -match $Pattern
    } | Select-Object -First 1

    if ($match) {
        return [string]$match.Value
    }

    return $null
}

function Show-HpLoadingStep {
    param(
        [Parameter(Mandatory = $true)]
        [string]$Status,

        [Parameter(Mandatory = $true)]
        [int]$PercentComplete
    )

    Write-Progress -Activity "HP BIOS check loading" -Status $Status -PercentComplete $PercentComplete
}

function Show-StartupLoadingStep {
    param(
        [Parameter(Mandatory = $true)]
        [string]$Status,

        [Parameter(Mandatory = $true)]
        [int]$PercentComplete
    )

    Write-Progress -Activity "Starting hardware check" -Status $Status -PercentComplete $PercentComplete
}

function Invoke-HpSection {
    param(
        [Parameter(Mandatory = $true)]
        $Data
    )

    $featureDefinitions = @(
        [pscustomobject]@{
            Label = "WWAN"
            BiosPattern = "WWAN|Wireless\s*WAN|Mobile\s*Broadband|Cellular|LTE|5G|4G"
            DeviceCheck = {
                param($Devices)
                $Devices | Where-Object {
                    $_.ClassName -match '^(Net|Modem)$' -and
                    $_.DeviceDescription -match '(?i)(\bwwan\b|wireless\s*wan|mobile\s*broadband|\bcellular\b)' -and
                    $_.DeviceDescription -notmatch '(?i)(^wan\s+miniport|bluetooth\s+device\s+\(personal\s+area\s+network\)|wireless\s+button|wireless\s+radio\s+controls|manageability|virtual|vpn|pppoe|pptp|l2tp|ikev2|sstp|ip\b|ipv6|network\s+adapter)'
                } | Select-Object -First 1
            }
        }
        [pscustomobject]@{
            Label = "Fingerprint"
            BiosPattern = "Fingerprint|Finger\s*Print"
            DeviceCheck = {
                param($Devices)
                $Devices | Where-Object { $_.ClassName -eq "Biometric" } | Select-Object -First 1
            }
        }
        [pscustomobject]@{
            Label = "WLAN"
            BiosPattern = "WLAN|Wireless\s*LAN|Wi-?Fi"
            DeviceCheck = {
                param($Devices)
                $Devices | Where-Object {
                    $_.ClassName -eq "Net" -and
                    $_.DeviceDescription -match '(?i)(wireless|wlan|wi-?fi|802\.11)'
                } | Select-Object -First 1
            }
        }
        [pscustomobject]@{
            Label = "Touchscreen"
            BiosPattern = "Touchscreen|Touch\s*Screen|Digitizer|Touch\s*Panel"
            DeviceCheck = {
                param($Devices)
                $Devices | Where-Object {
                    ($_.ClassName -eq "HIDClass" -or $_.ClassName -eq "HID") -and
                    $_.DeviceDescription -match "(?i)(touch\s*screen|touchscreen|digitizer)"
                } | Select-Object -First 1
            }
        }
        [pscustomobject]@{
            Label = "Camera"
            BiosPattern = "Integrated\s*Camera|Camera"
            DeviceCheck = {
                param($Devices)
                $Devices | Where-Object {
                    $_.ClassName -in @("Camera", "Image") -or
                    $_.DeviceDescription -match '(?i)(integrated\s*camera|webcam|camera)'
                } | Select-Object -First 1
            }
        }
        [pscustomobject]@{
            Label = "Microphone"
            BiosPattern = "Microphone|Internal\s*Microphone|Audio\s*Device"
            DeviceCheck = {
                param($Devices)
                $Devices | Where-Object {
                    $_.ClassName -in @("AudioEndpoint", "MEDIA") -and
                    $_.DeviceDescription -match '(?i)(microphone|mic|array)'
                } | Select-Object -First 1
            }
        }
        [pscustomobject]@{
            Label = "NFC"
            BiosPattern = "\bNFC\b|Near\s*Field"
            DeviceCheck = {
                param($Devices)
                $Devices | Where-Object { $_.ClassName -eq "Proximity" } | Select-Object -First 1
            }
        }
        [pscustomobject]@{
            Label = "Smart Card"
            BiosPattern = "Smart\s*Card|Integrated\s*Smart\s*Card"
            DeviceCheck = {
                param($Devices)
                $Devices | Where-Object { $_.ClassGuid -eq "{50DD5230-BA8A-11D1-BF5D-0000F805F530}" } | Select-Object -First 1
            }
        }
        [pscustomobject]@{
            Label = "KB Backlight"
            BiosPattern = "Keyboard\s*Backlight|KB\s*Backlight|Backlit\s*Keyboard|Backlight"
            DeviceCheck = {
                param($Devices)
                Get-CimInstance -Namespace root\wmi -ClassName WmiMonitorBrightness -ErrorAction SilentlyContinue
            }
        }
        [pscustomobject]@{
            Label = "Sure View"
            BiosPattern = "Sure\s*View|HP\s*Sure\s*View|Privacy"
            DeviceCheck = {
                param($Devices)
                $Devices | Where-Object {
                    $_.ClassName -eq "Monitor" -and
                    $_.DeviceDescription -match '(?i)(sure\s*view|privacy|privacy\s*screen)'
                } | Select-Object -First 1
            }
        }
    )

    Show-HpLoadingStep -Status "Reading connected devices..." -PercentComplete 10
    $devices = Get-ConnectedPnPDevices
    if (-not $devices) {
        Write-Progress -Activity "HP BIOS check loading" -Completed
        Write-Output "Could not read devices from pnputil."
        return
    }

    Show-HpLoadingStep -Status "Reading HP BIOS configuration with BCU..." -PercentComplete 35
    $biosResult = Get-HpBiosEntries

    Show-HpLoadingStep -Status "Comparing BIOS versions..." -PercentComplete 55
    $bcuBiosVersionRaw = if ($biosResult.Success) {
        Get-HpBiosSettingValue -BiosEntries $biosResult.Entries -Pattern '^System\s+BIOS\s+Version$'
    }
    else {
        $null
    }
    $bcuBiosVersion = Get-NormalizedBiosVersion -Value $bcuBiosVersionRaw
    $windowsBiosVersionRaw = ($Data.BiosInfo.SMBIOSBIOSVersion, $Data.BiosInfo.Version | Where-Object { $_ } | Select-Object -First 1)
    $windowsBiosVersion = Get-NormalizedBiosVersion -Value ($windowsBiosVersionRaw | Select-Object -First 1)
    $biosVersionMatch = if ($windowsBiosVersion -and $bcuBiosVersion) {
        if ($windowsBiosVersion -eq $bcuBiosVersion) { "Yes" } else { "No" }
    }
    else {
        "Unknown"
    }

    Show-HpLoadingStep -Status "Building HP feature comparison..." -PercentComplete 80
    $comparison = foreach ($feature in $featureDefinitions) {
        $deviceMatch = & $feature.DeviceCheck $devices
        $deviceManagerValue = if ($deviceMatch) { "Yes" } else { "No" }

        $biosValue = if ($biosResult.Success) {
            Get-HpBiosFeatureState -BiosEntries $biosResult.Entries -Pattern $feature.BiosPattern
        }
        else {
            "Unknown"
        }

        [pscustomobject]@{
            Feature = $feature.Label
            BIOS = $biosValue
            "Device Manager" = $deviceManagerValue
        }
    }

    Show-HpLoadingStep -Status "Finalizing HP report..." -PercentComplete 100
    Write-Progress -Activity "HP BIOS check loading" -Completed

    Write-SectionHeader -Title "HP BIOS vs Device Manager Check"
    Write-CommonSystemInfo -Data $Data
    Write-Output ""

    Write-SectionHeader -Title "BIOS Version Check"
    Write-Output "Windows BIOS Version: $windowsBiosVersion"
    Write-Output "BCU BIOS Version: $bcuBiosVersion"
    Write-Output "Version Match: $biosVersionMatch"

    Write-Output ""
    Write-SectionHeader -Title "BIOS vs Device Manager Comparison"
    $comparison | Format-Table -AutoSize

    if ($script:LastBcuFiles) {
        Write-Output ""
        Write-SectionHeader -Title "BCU Output Files"
        Write-Output ("BCU output file: {0}" -f $script:LastBcuFiles.Output)
        Write-Output ("BCU stdout file: {0}" -f $script:LastBcuFiles.StdOut)
        Write-Output ("BCU stderr file: {0}" -f $script:LastBcuFiles.StdErr)
    }

    if (-not $biosResult.Success) {
        Write-Output ""
        Write-SectionHeader -Title "BIOS Query Note"
        Write-Output $biosResult.Message
    }
}

function Get-LenovoBiosEntries {
    $biosSettings = Get-WmiObject -Class Lenovo_BiosSetting -Namespace "root\wmi" -ErrorAction Stop

    $entries = foreach ($setting in $biosSettings) {
        $currentSetting = [string]$setting.CurrentSetting
        if ([string]::IsNullOrWhiteSpace($currentSetting)) {
            continue
        }

        $parts = $currentSetting -split ',', 2
        [pscustomobject]@{
            Setting = $parts[0].Trim()
            Value = if ($parts.Count -gt 1) { $parts[1].Trim() } else { "" }
            RawValue = $currentSetting
        }
    }

    return @($entries)
}

function Get-LenovoBiosEntriesForAliases {
    param(
        [Parameter(Mandatory = $true)]
        [object[]]$BiosEntries,

        [Parameter(Mandatory = $true)]
        [string[]]$Aliases
    )

    $normalizedAliases = $Aliases | Where-Object { -not [string]::IsNullOrWhiteSpace($_) } | ForEach-Object { $_.Trim().ToLowerInvariant() }

    return @(
        $BiosEntries | Where-Object {
            $settingName = [string]$_.Setting
            $rawValue = [string]$_.RawValue

            foreach ($alias in $normalizedAliases) {
                if ($settingName.ToLowerInvariant().Contains($alias) -or $rawValue.ToLowerInvariant().Contains($alias)) {
                    return $true
                }
            }

            return $false
        }
    )
}

function Get-LenovoBiosFeatureState {
    param(
        [Parameter(Mandatory = $true)]
        [object[]]$BiosEntries,

        [Parameter(Mandatory = $true)]
        [string[]]$Aliases,

        [Parameter()]
        [bool]$RequireExplicitPresence = $false
    )

    $biosEnabledPattern = '(?i)\b(enable|enabled|on|present|installed|active|yes)\b'
    $biosDisabledPattern = '(?i)\b(disable|disabled|off|not\s*installed|absent|inactive|no)\b'
    $biosPresentPattern = '(?i)\b(present|installed|detected|available)\b'
    $biosNotPresentPattern = '(?i)\b(not\s*installed|not\s*present|absent|not\s*available|none)\b'

    $matchingEntries = Get-LenovoBiosEntriesForAliases -BiosEntries $BiosEntries -Aliases $Aliases

    if (-not $matchingEntries) {
        if ($RequireExplicitPresence) {
            return "Unknown"
        }

        return "No"
    }

    foreach ($entry in $matchingEntries) {
        if ($entry.Value -match $biosNotPresentPattern -or $entry.RawValue -match $biosNotPresentPattern) {
            return "Not Present"
        }
    }

    foreach ($entry in $matchingEntries) {
        if ($entry.Value -match $biosPresentPattern -or $entry.RawValue -match $biosPresentPattern) {
            return "Installed"
        }
    }

    foreach ($entry in $matchingEntries) {
        if ($entry.Value -match $biosDisabledPattern -or $entry.RawValue -match $biosDisabledPattern) {
            return "Disabled"
        }
    }

    foreach ($entry in $matchingEntries) {
        if ($entry.Value -match $biosEnabledPattern -or $entry.RawValue -match $biosEnabledPattern) {
            if ($RequireExplicitPresence) {
                return "Configurable"
            }

            return "Enabled"
        }
    }

    return "Configured"
}

function Convert-LenovoBiosStateToYesNo {
    param(
        [string]$State
    )

    switch ($State) {
        "Installed" { return "Yes" }
        "Enabled" { return "Yes" }
        "Configured" { return "Yes" }
        "Disabled" { return "No" }
        "Not Present" { return "No" }
        "Configurable" { return "No" }
        "No" { return "No" }
        default { return "Unknown" }
    }
}

function Invoke-LenovoSection {
    param(
        [Parameter(Mandatory = $true)]
        $Data
    )

    $featureDefinitions = @(
        [pscustomobject]@{
            Label = "Microphone"
            BiosAliases = @("Microphone", "Internal Microphone", "Mic")
            RequireExplicitPresence = $false
            DeviceCheck = {
                param($Devices)
                $Devices | Where-Object {
                    $_.ClassName -in @("AudioEndpoint", "MEDIA") -and
                    $_.DeviceDescription -match '(?i)(microphone|mic|array)'
                } | Select-Object -First 1
            }
        }
        [pscustomobject]@{
            Label = "WWAN"
            BiosAliases = @("WWAN", "Wireless WAN", "WirelessWAN", "Mobile Broadband", "Cellular", "LTE", "5G", "4G")
            RequireExplicitPresence = $true
            DeviceCheck = {
                param($Devices)
                $Devices | Where-Object {
                    $_.ClassName -match '^(Net|Modem)$' -and
                    $_.DeviceDescription -match '(?i)(\bwwan\b|wireless\s*wan|mobile\s*broadband|\bcellular\b)' -and
                    $_.DeviceDescription -notmatch '(?i)(^wan\s+miniport|bluetooth\s+device\s+\(personal\s+area\s+network\)|wireless\s+button|wireless\s+radio\s+controls|manageability|virtual|vpn|pppoe|pptp|l2tp|ikev2|sstp|ip\b|ipv6|network\s+adapter)'
                } | Select-Object -First 1
            }
        }
        [pscustomobject]@{
            Label = "WLAN"
            BiosAliases = @("WLAN", "Wireless LAN", "WirelessLAN", "Wi-Fi", "WiFi")
            RequireExplicitPresence = $false
            DeviceCheck = {
                param($Devices)
                $Devices | Where-Object {
                    $_.ClassName -eq "Net" -and
                    $_.DeviceDescription -match '(?i)(wireless|wlan|wi-?fi|802\.11)'
                } | Select-Object -First 1
            }
        }
        [pscustomobject]@{
            Label = "Fingerprint"
            BiosAliases = @("Fingerprint", "Finger Print", "Fingerprint Reader")
            RequireExplicitPresence = $false
            DeviceCheck = {
                param($Devices)
                $Devices | Where-Object { $_.ClassName -eq "Biometric" } | Select-Object -First 1
            }
        }
        [pscustomobject]@{
            Label = "NFC"
            BiosAliases = @("NFC", "Near Field", "Near Field Communication")
            RequireExplicitPresence = $true
            DeviceCheck = {
                param($Devices)
                $Devices | Where-Object { $_.ClassName -eq "Proximity" } | Select-Object -First 1
            }
        }
        [pscustomobject]@{
            Label = "Smart Card"
            BiosAliases = @("Smart Card", "Integrated Smart Card", "Smart Card Reader")
            RequireExplicitPresence = $true
            DeviceCheck = {
                param($Devices)
                $Devices | Where-Object { $_.ClassGuid -eq "{50DD5230-BA8A-11D1-BF5D-0000F805F530}" } | Select-Object -First 1
            }
        }
        [pscustomobject]@{
            Label = "Touchscreen"
            BiosAliases = @("Touchscreen", "Touch Screen", "Digitizer", "Touch Panel", "MultiTouch", "Multi-Touch", "Touch")
            RequireExplicitPresence = $true
            DeviceCheck = {
                param($Devices)
                $Devices | Where-Object {
                    $_.ClassName -in @("HIDClass", "HID") -and
                    $_.DeviceDescription -match '(?i)(touch\s*screen|touchscreen|digitizer)'
                } | Select-Object -First 1
            }
        }
        [pscustomobject]@{
            Label = "KB Backlight"
            BiosAliases = @("Keyboard Backlight", "KB Backlight", "Backlit Keyboard", "Backlight")
            RequireExplicitPresence = $false
            DeviceCheck = {
                param($Devices)
                Get-CimInstance -Namespace root\wmi -ClassName WmiMonitorBrightness -ErrorAction SilentlyContinue
            }
        }
    )

    $biosEntries = Get-LenovoBiosEntries
    $devices = Get-ConnectedPnPDevices

    if (-not $devices) {
        throw "Could not read connected devices from pnputil."
    }

    $comparison = foreach ($feature in $featureDefinitions) {
        $deviceMatch = & $feature.DeviceCheck $devices
        $deviceManagerValue = if ($deviceMatch) { "Yes" } else { "No" }
        $biosSettingValue = Get-LenovoBiosFeatureState -BiosEntries $biosEntries -Aliases $feature.BiosAliases -RequireExplicitPresence $feature.RequireExplicitPresence
        $biosValue = Convert-LenovoBiosStateToYesNo -State $biosSettingValue

        [pscustomobject]@{
            Feature = $feature.Label
            BIOS = $biosValue
            "BIOS Detail" = $biosSettingValue
            "Device Manager" = $deviceManagerValue
        }
    }

    Write-SectionHeader -Title "Lenovo BIOS vs Device Manager Check"
    Write-CommonSystemInfo -Data $Data
    Write-Output ""
    Write-SectionHeader -Title "BIOS vs Device Manager Comparison"
    $comparison | Format-Table -AutoSize
}

function Get-DellCctkPath {
    $candidates = @(
        (Join-Path $script:ScriptDirectory "CCTK.exe")
        (Join-Path $script:ScriptDirectory "Command Configure\X86_64\CCTK.exe")
        "D:\Command Configure\X86_64\CCTK.exe"
        "C:\Program Files\Dell\Command Configure\X86_64\CCTK.exe"
        "C:\Program Files (x86)\Dell\Command Configure\X86_64\CCTK.exe"
    )

    foreach ($candidate in $candidates) {
        if (Test-Path -LiteralPath $candidate) {
            return $candidate
        }
    }

    return $null
}

function Get-NormalizedText {
    param(
        [AllowEmptyString()]
        [string]$Text
    )

    if ($null -eq $Text) {
        $Text = ''
    }

    return (($Text -replace '[^a-z0-9]', '').ToLowerInvariant())
}

function Test-EnabledValue {
    param(
        [AllowEmptyString()]
        [string]$Value
    )

    $normalized = Get-NormalizedText -Text $Value

    if ([string]::IsNullOrWhiteSpace($normalized)) {
        return $false
    }

    $enabledValues = @(
        'enable', 'enabled', 'on', 'yes', 'true', 'present',
        'installed', 'available', 'supported', 'active', 'activated'
    )

    $disabledValues = @(
        'disable', 'disabled', 'off', 'no', 'false', 'absent',
        'missing', 'notinstalled', 'unavailable', 'unsupported',
        'inactive', 'deactivated', 'none'
    )

    if ($normalized -in $enabledValues) {
        return $true
    }

    if ($normalized -in $disabledValues) {
        return $false
    }

    if ($normalized -match '^(enable|on|yes|true|present|installed|available|supported|active)') {
        return $true
    }

    if ($normalized -match '^(disable|off|no|false|absent|missing|notinstalled|unavailable|unsupported|inactive|none)') {
        return $false
    }

    return $true
}

function Get-IniFeatureMatch {
    param(
        [Parameter(Mandatory = $true)]
        [string[]]$Lines,

        [Parameter(Mandatory = $true)]
        [string[]]$Aliases,

        [string[]]$BlockedAliases = @()
    )

    $normalizedAliases = @(
        $Aliases |
        ForEach-Object { Get-NormalizedText -Text $_ } |
        Where-Object { -not [string]::IsNullOrWhiteSpace($_) }
    )
    $normalizedBlockedAliases = @(
        $BlockedAliases |
        ForEach-Object { Get-NormalizedText -Text $_ } |
        Where-Object { -not [string]::IsNullOrWhiteSpace($_) }
    )

    foreach ($line in $Lines) {
        if ([string]::IsNullOrWhiteSpace($line)) {
            continue
        }

        $trimmedLine = $line.Trim()
        if ($trimmedLine.StartsWith(';') -or $trimmedLine.StartsWith('#') -or $trimmedLine.StartsWith('[')) {
            continue
        }

        $key = $trimmedLine
        $value = ''

        if ($trimmedLine -match '^\s*([^:=]+?)\s*[:=]\s*(.*)$') {
            $key = $matches[1].Trim()
            $value = $matches[2].Trim()
        }

        $normalizedKey = Get-NormalizedText -Text $key
        $normalizedLine = Get-NormalizedText -Text $trimmedLine

        foreach ($alias in $normalizedAliases) {
            if ($normalizedBlockedAliases -contains $normalizedKey) {
                continue
            }

            if ($normalizedKey -eq $alias) {
                return [pscustomobject]@{
                    Present = (Test-EnabledValue -Value $value)
                    Detail = $trimmedLine
                }
            }

            $linePattern = '^{0}(enable|enabled|disable|disabled|on|off|yes|no|true|false|present|absent|installed|notinstalled|available|unavailable|supported|unsupported|active|inactive|activated|deactivated|none)?$' -f [regex]::Escape($alias)
            if ($normalizedLine -match $linePattern) {
                $suffix = $normalizedLine.Substring($alias.Length)
                return [pscustomobject]@{
                    Present = (Test-EnabledValue -Value $suffix)
                    Detail = $trimmedLine
                }
            }
        }
    }

    return [pscustomobject]@{
        Present = $false
        Detail = 'No matching BIOS setting found in Dell.ini'
    }
}

function Get-PnpSnapshot {
    $devices = Get-CimInstance -ClassName Win32_PnPEntity | ForEach-Object {
        $combined = @(
            $_.Name
            $_.Description
            $_.Manufacturer
            $_.PNPClass
            $_.Service
            $_.DeviceID
        ) -join ' '

        [pscustomobject]@{
            Name = [string]$_.Name
            Description = [string]$_.Description
            Manufacturer = [string]$_.Manufacturer
            PnpClass = [string]$_.PNPClass
            Service = [string]$_.Service
            DeviceId = [string]$_.DeviceID
            Normalized = Get-NormalizedText -Text $combined
        }
    }

    return @($devices)
}

function Get-DellDeviceFeatureMatch {
    param(
        [Parameter(Mandatory = $true)]
        [object[]]$Devices,

        [Parameter(Mandatory = $true)]
        [string]$FeatureName
    )

    foreach ($device in $Devices) {
        $name = [string]$device.Name
        $description = [string]$device.Description
        $manufacturer = [string]$device.Manufacturer
        $pnpClass = $device.PnpClass
        $normalized = $device.Normalized
        $detail = (($name, $description, $manufacturer, $pnpClass | Where-Object { $_ -and $_.Trim() }) -join ' | ')

        switch ($FeatureName) {
            'NFC' {
                if ($normalized -match '(^|[^a-z0-9])(nfc|nearfield|nearfieldcommunication|contactless)') {
                    return [pscustomobject]@{
                        Present = $true
                        Detail = $detail
                    }
                }
            }
            'WWAN' {
                if (
                    $normalized -match '(^|[^a-z0-9])(wwan|wirelesswan|mobilebroadband|cellular|lte|5g|4g)' -or
                    $normalized -match '(sierrawireless|fibocom|quectel|ericsson|huawei|mobilebroadbandadapter)'
                ) {
                    return [pscustomobject]@{
                        Present = $true
                        Detail = $detail
                    }
                }
            }
            'WLAN' {
                if (
                    $normalized -match '(wirelesslan|wi-?fi|wifi|wlan|80211|wirelessac|wirelessax)' -or
                    ($pnpClass -eq 'Net' -and $normalized -match 'wireless')
                ) {
                    return [pscustomobject]@{
                        Present = $true
                        Detail = $detail
                    }
                }
            }
            'MICROPHONE' {
                if (
                    $normalized -match '(microphone|micarray|mic)' -or
                    ($pnpClass -in @('AudioEndpoint', 'MEDIA') -and ($name -match 'microphone|mic' -or $description -match 'microphone|mic'))
                ) {
                    return [pscustomobject]@{
                        Present = $true
                        Detail = $detail
                    }
                }
            }
            'SMARTCARD' {
                if ($normalized -match '(smartcard|smartcardreader|smartcardreaderusb|smart card)') {
                    return [pscustomobject]@{
                        Present = $true
                        Detail = $detail
                    }
                }
            }
            'KEYBOARD BACKLIGHT' {
                if ($normalized -match '(keyboardbacklight|kbdbacklight|kbbacklight|backlitkeyboard|backlight)') {
                    return [pscustomobject]@{
                        Present = $true
                        Detail = $detail
                    }
                }
            }
            'FINGERPRINT' {
                if (
                    $normalized -match '(fingerprint|fingerprintreader|synapticswbdifp|goodixfingerprint|validitysensor|138afingerprint|elanwbfingerprint)' -or
                    (
                        $pnpClass -eq 'Biometric' -and
                        $normalized -notmatch 'windowshello|face|facial|iris'
                    )
                ) {
                    return [pscustomobject]@{
                        Present = $true
                        Detail = $detail
                    }
                }
            }
            'CAMERA' {
                if (
                    $normalized -match '(camera|webcam|integratedcamera|rgbir|ircamera)' -or
                    $pnpClass -in @('Camera', 'Image')
                ) {
                    return [pscustomobject]@{
                        Present = $true
                        Detail = $detail
                    }
                }
            }
            'BLUETOOTH' {
                if ($normalized -match 'bluetooth' -or $pnpClass -eq 'Bluetooth') {
                    return [pscustomobject]@{
                        Present = $true
                        Detail = $detail
                    }
                }
            }
        }
    }

    return [pscustomobject]@{
        Present = $false
        Detail = 'No matching device found'
    }
}

function Invoke-DellSection {
    param(
        [Parameter(Mandatory = $true)]
        $Data
    )

    $cctkPath = Get-DellCctkPath
    $outputPath = Join-Path $script:ScriptDirectory 'Dell.ini'

    if (-not $cctkPath) {
        throw "Dell Command Configure CCTK.exe not found."
    }

    & $cctkPath -o $outputPath | Out-Null

    if (-not (Test-Path -LiteralPath $outputPath)) {
        throw "Failed to export Dell BIOS configuration to $outputPath"
    }

    $lines = Get-Content -LiteralPath $outputPath
    $devices = Get-PnpSnapshot

    $featureMap = [ordered]@{
        'NFC' = @{
            Aliases = @('nfc', 'near field communication', 'nearfieldcommunication')
            BlockedAliases = @()
        }
        'WWAN' = @{
            Aliases = @('wwan', 'wireless wan', 'wirelesswan', 'mobile broadband', 'mobilebroadband')
            BlockedAliases = @('wwanautosense', 'wwanlocate', 'wwanantenna', 'wwanradio')
        }
        'WLAN' = @{
            Aliases = @('wlan', 'wireless lan', 'wirelesslan', 'wifi')
            BlockedAliases = @('wlanautosense', 'wlanradio')
        }
        'MICROPHONE' = @{
            Aliases = @('microphone', 'mic')
            BlockedAliases = @()
        }
        'SMARTCARD' = @{
            Aliases = @('smartcard', 'smart card', 'smartcardreader')
            BlockedAliases = @()
        }
        'KEYBOARD BACKLIGHT' = @{
            Aliases = @('kb backlight', 'kbbacklight', 'kbdbacklight', 'keyboard backlight', 'keyboardbacklight')
            BlockedAliases = @()
        }
        'FINGERPRINT' = @{
            Aliases = @('fingerprint', 'fingerprint reader', 'fingerprintreader', 'biometric')
            BlockedAliases = @()
        }
        'CAMERA' = @{
            Aliases = @('camera', 'webcam', 'integrated camera')
            BlockedAliases = @()
        }
        'BLUETOOTH' = @{
            Aliases = @('bluetooth')
            BlockedAliases = @()
        }
    }

    $biosStatuses = [ordered]@{}
    $deviceStatuses = [ordered]@{}

    foreach ($feature in $featureMap.GetEnumerator()) {
        $biosStatuses[$feature.Key] = Get-IniFeatureMatch -Lines $lines -Aliases $feature.Value.Aliases -BlockedAliases $feature.Value.BlockedAliases
        $deviceStatuses[$feature.Key] = Get-DellDeviceFeatureMatch -Devices $devices -FeatureName $feature.Key
    }

    Write-SectionHeader -Title "Dell BIOS vs Device Manager Check"
    Write-CommonSystemInfo -Data $Data
    Write-Output ""
    Write-SectionHeader -Title "BIOS Export File"
    Write-Output "Dell BIOS export file: $outputPath"
    Write-Output ""

    $comparison = foreach ($featureName in $featureMap.Keys) {
        [pscustomobject]@{
            Feature = $featureName
            BIOS = if ($biosStatuses[$featureName].Present) { "Yes" } else { "No" }
            "BIOS Detail" = $biosStatuses[$featureName].Detail
            "Device Manager" = if ($deviceStatuses[$featureName].Present) { "Yes" } else { "No" }
            "Device Detail" = $deviceStatuses[$featureName].Detail
        }
    }

    Write-SectionHeader -Title "BIOS vs Device Manager Comparison"
    $comparison | Format-Table -AutoSize
}

try {
    Show-StartupLoadingStep -Status "Collecting system information..." -PercentComplete 15
    $data = Get-CommonSystemData

    Show-StartupLoadingStep -Status "Detecting manufacturer..." -PercentComplete 70
    $manufacturer = [string]$data.SystemInfo.Manufacturer

    Show-StartupLoadingStep -Status "Preparing report..." -PercentComplete 100
    Write-Progress -Activity "Starting hardware check" -Completed

    Write-Output "Detected manufacturer: $manufacturer"
    Write-Output ""

    if ($manufacturer -match '(?i)hewlett-packard|hp') {
        Invoke-HpSection -Data $data
    }
    elseif ($manufacturer -match '(?i)lenovo') {
        Invoke-LenovoSection -Data $data
    }
    elseif ($manufacturer -match '(?i)dell') {
        Invoke-DellSection -Data $data
    }
    else {
        Write-Output "This script currently supports HP, Lenovo, and Dell systems only."
    }

    Write-Output ""
    Write-Output "Running Windows activation check last..."
    Write-WindowsActivationSection
}
catch {
    Write-Error ("Failed to run HPLENDELLDEV. Details: {0}" -f $_.Exception.Message)
}
finally {
    try {
        Stop-Transcript | Out-Null
    }
    catch {
    }
}

Read-Host "Press Enter to close"
