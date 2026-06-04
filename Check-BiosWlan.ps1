<#
.SYNOPSIS
Checks whether WLAN/Wi-Fi is enabled in BIOS.

.DESCRIPTION
Queries supported BIOS providers for WLAN/Wi-Fi settings:
- HP BIOS Configuration Utility, if available
- Lenovo_BiosSetting WMI provider
- Dell Command | Monitor BIOS attribute providers

If a BIOS WLAN/Wi-Fi option is found and enabled, the script prints:
WLAN ENABLED

If no BIOS WLAN option is found, or the BIOS setting is disabled, the script prints:
NO WLAN DETECTED IN BIOS

.PARAMETER Detailed
Shows the matched BIOS setting and provider details after the required status line.

.PARAMETER Json
Outputs a JSON object instead of plain text.

.PARAMETER NoAutoElevate
Prevents the script from relaunching itself as Administrator.

.PARAMETER UseSavedBcuOutput
If live HP BIOS queries fail, also checks .\bcu-output.txt in this script folder.
Use this only when that file was generated from the unit being checked.

.PARAMETER WaitForEnter
Waits for Enter before closing, useful when double-clicking or launching from a batch file.

.EXAMPLE
.\Check-BiosWlan.ps1

.EXAMPLE
.\Check-BiosWlan.ps1 -Detailed
#>

[CmdletBinding()]
param(
    [switch]$Detailed,
    [switch]$Json,
    [switch]$NoAutoElevate,
    [switch]$UseSavedBcuOutput,
    [switch]$WaitForEnter
)

$WlanNamePattern = '(?i)(\bWLAN\b|Wireless\s*LAN|Wireless\s*Network\s*Device|Wi-?Fi|Wireless\s+Device|Integrated\s+Wireless|Internal\s+Wireless)'
$EnabledPattern = '(?i)^\s*(enable|enabled|on|yes|active|available|present|installed|true)\s*$'
$DisabledPattern = '(?i)^\s*(disable|disabled|off|no|inactive|unavailable|absent|not\s+installed|false)\s*$'

$isAdminSession = ([Security.Principal.WindowsPrincipal] [Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole(
    [Security.Principal.WindowsBuiltInRole]::Administrator
)

if (-not $isAdminSession -and -not $NoAutoElevate) {
    $scriptPath = if ($PSCommandPath) { $PSCommandPath } else { $MyInvocation.MyCommand.Path }
    if (-not [string]::IsNullOrWhiteSpace($scriptPath)) {
        $arguments = @(
            '-NoProfile',
            '-ExecutionPolicy', 'Bypass',
            '-File', ('"{0}"' -f $scriptPath)
        )

        if ($Detailed) { $arguments += '-Detailed' }
        if ($Json) { $arguments += '-Json' }
        if ($UseSavedBcuOutput) { $arguments += '-UseSavedBcuOutput' }
        if ($WaitForEnter) { $arguments += '-WaitForEnter' }

        Start-Process -FilePath 'powershell.exe' -ArgumentList $arguments -Verb RunAs
        exit
    }
}

function New-BiosWlanResult {
    param(
        [string]$Provider,
        [string]$SettingName,
        [string]$Value,
        [string]$RawValue,
        [string]$Message
    )

    $enabled = $false
    if ($Value -match $EnabledPattern) {
        $enabled = $true
    }
    elseif ($RawValue -match '(?i)\*(enable|enabled|on|yes|active|present|installed)') {
        $enabled = $true
    }

    [pscustomobject]@{
        Provider = $Provider
        SettingName = $SettingName
        Value = $Value
        RawValue = $RawValue
        IsEnabled = $enabled
        Message = $Message
    }
}

function Get-HpBcuPath {
    $candidates = @(
        (Join-Path $PSScriptRoot 'bcu\BiosConfigUtility64.exe'),
        (Join-Path $PSScriptRoot 'bcu\BiosConfigUtility.exe'),
        'C:\Program Files\HP\BIOS Configuration Utility\BiosConfigUtility64.exe',
        'C:\Program Files (x86)\HP\BIOS Configuration Utility\BiosConfigUtility64.exe',
        'C:\Program Files\HP\BIOS Configuration Utility\BiosConfigUtility.exe',
        'C:\Program Files (x86)\HP\BIOS Configuration Utility\BiosConfigUtility.exe'
    )

    foreach ($candidate in $candidates) {
        if (Test-Path -LiteralPath $candidate) {
            return $candidate
        }
    }

    $null
}

function Convert-HpBcuConfigToEntries {
    param([string[]]$Content)

    $entries = @()
    $currentName = $null
    $currentOptions = @()

    foreach ($line in $Content) {
        $trimmed = $line.Trim()

        if (-not $trimmed -or $trimmed.StartsWith(';') -or $trimmed -eq 'BIOSConfig 1.0') {
            continue
        }

        $isOption = $line -match '^\s+'
        if (-not $isOption) {
            if ($currentName) {
                $selected = $currentOptions | Where-Object { $_.StartsWith('*') } | Select-Object -First 1
                $entries += [pscustomobject]@{
                    Name = $currentName
                    Value = if ($selected) { $selected.TrimStart('*').Trim() } else { $null }
                    RawValue = ($currentOptions -join '; ')
                }
            }

            $currentName = $trimmed
            $currentOptions = @()
            continue
        }

        if ($currentName) {
            $currentOptions += $trimmed
        }
    }

    if ($currentName) {
        $selected = $currentOptions | Where-Object { $_.StartsWith('*') } | Select-Object -First 1
        $entries += [pscustomobject]@{
            Name = $currentName
            Value = if ($selected) { $selected.TrimStart('*').Trim() } else { $null }
            RawValue = ($currentOptions -join '; ')
        }
    }

    $entries
}

function Get-HpBiosWlanState {
    $bcuPath = Get-HpBcuPath
    if (-not $bcuPath) {
        return $null
    }

    $outputFile = Join-Path $env:TEMP ("hp-bios-config-{0}.txt" -f ([guid]::NewGuid()))

    try {
        & $bcuPath "/GetConfig:$outputFile" | Out-Null
        if ($LASTEXITCODE -ne 0 -or -not (Test-Path -LiteralPath $outputFile)) {
            return $null
        }

        $entries = Convert-HpBcuConfigToEntries -Content (Get-Content -LiteralPath $outputFile -ErrorAction Stop)
        $match = $entries |
            Where-Object {
                $_.Name -match $WlanNamePattern -and
                $_.Name -notmatch '(?i)(WWAN|WAN|Bluetooth|Auto\s*Switch|Button|Wake\s*on\s*LAN|LAN\s*/\s*WLAN)'
            } |
            Select-Object -First 1

        if ($match) {
            return New-BiosWlanResult -Provider 'HP BCU' -SettingName $match.Name -Value $match.Value -RawValue $match.RawValue -Message 'Matched HP BIOS Configuration Utility setting.'
        }
    }
    catch {
        return $null
    }
    finally {
        if (Test-Path -LiteralPath $outputFile) {
            Remove-Item -LiteralPath $outputFile -Force -ErrorAction SilentlyContinue
        }
    }

    $null
}

function Get-HpWmiBiosWlanState {
    $classes = @(
        'HP_BIOSEnumeration',
        'HPBIOS_BIOSEnumeration',
        'HP_BIOSSetting',
        'HPBIOS_BIOSSetting'
    )

    foreach ($className in $classes) {
        try {
            $instances = Get-CimInstance -Namespace root\HP\InstrumentedBIOS -ClassName $className -ErrorAction Stop
        }
        catch {
            continue
        }

        foreach ($instance in $instances) {
            $name = [string]$instance.Name
            if (-not $name) {
                $name = [string]$instance.DisplayName
            }

            if ($name -match $WlanNamePattern -and $name -notmatch '(?i)(WWAN|WAN|Bluetooth|Auto\s*Switch|Button|Wake\s*on\s*LAN|LAN\s*/\s*WLAN)') {
                $value = [string]$instance.CurrentValue
                if (-not $value) {
                    $value = [string]$instance.Value
                }

                return New-BiosWlanResult -Provider 'HP WMI' -SettingName $name -Value $value -RawValue ($instance | Out-String).Trim() -Message "Matched HP BIOS WMI class $className."
            }
        }
    }

    $null
}

function Get-SavedHpBcuWlanState {
    if (-not $UseSavedBcuOutput) {
        return $null
    }

    $savedPath = Join-Path $PSScriptRoot 'bcu-output.txt'
    if (-not (Test-Path -LiteralPath $savedPath)) {
        return $null
    }

    try {
        $entries = Convert-HpBcuConfigToEntries -Content (Get-Content -LiteralPath $savedPath -ErrorAction Stop)
    }
    catch {
        return $null
    }

    $match = $entries |
        Where-Object {
            $_.Name -match $WlanNamePattern -and
            $_.Name -notmatch '(?i)(WWAN|WAN|Bluetooth|Auto\s*Switch|Button|Wake\s*on\s*LAN|LAN\s*/\s*WLAN)'
        } |
        Select-Object -First 1

    if ($match) {
        return New-BiosWlanResult -Provider 'Saved HP BCU output' -SettingName $match.Name -Value $match.Value -RawValue $match.RawValue -Message 'Matched saved bcu-output.txt. Confirm this file was generated from the current unit.'
    }

    $null
}

function Get-LenovoBiosWlanState {
    try {
        $settings = Get-CimInstance -Namespace root\wmi -ClassName Lenovo_BiosSetting -ErrorAction Stop
    }
    catch {
        return $null
    }

    foreach ($setting in $settings) {
        if (-not $setting.CurrentSetting) {
            continue
        }

        $parts = ([string]$setting.CurrentSetting).Split(',', 2)
        if ($parts.Count -lt 2) {
            continue
        }

        $name = $parts[0].Trim()
        $value = $parts[1].Trim()

        if ($name -match $WlanNamePattern -and $name -notmatch '(?i)(WWAN|WAN|Bluetooth|Auto\s*Switch|Wake\s*on\s*LAN)') {
            return New-BiosWlanResult -Provider 'Lenovo WMI' -SettingName $name -Value $value -RawValue $setting.CurrentSetting -Message 'Matched Lenovo BIOS WMI setting.'
        }
    }

    $null
}

function Get-DellBiosWlanState {
    $namespaces = @(
        'root\dcim\sysman\biosattributes',
        'root\dcim\sysman'
    )
    $classes = @(
        'EnumerationAttribute',
        'IntegerAttribute',
        'StringAttribute'
    )

    foreach ($namespace in $namespaces) {
        foreach ($className in $classes) {
            try {
                $instances = Get-CimInstance -Namespace $namespace -ClassName $className -ErrorAction Stop
            }
            catch {
                continue
            }

            foreach ($instance in $instances) {
                $name = [string]$instance.AttributeName
                if (-not $name) {
                    $name = [string]$instance.DisplayName
                }

                if ($name -match $WlanNamePattern -and $name -notmatch '(?i)(WWAN|WAN|Bluetooth|Auto\s*Switch|Wake\s*on\s*LAN|Wireless\s*Switch)') {
                    $value = [string]$instance.CurrentValue
                    return New-BiosWlanResult -Provider 'Dell Command Monitor' -SettingName $name -Value $value -RawValue ($instance | Out-String).Trim() -Message "Matched Dell BIOS provider $namespace/$className."
                }
            }
        }
    }

    $null
}

function Get-WifiAdapterState {
    $wifiPattern = '(?i)(wi-?fi|wireless|wlan|802\.11)'

    try {
        $adapter = Get-NetAdapter -ErrorAction Stop |
            Where-Object {
                $_.InterfaceDescription -match $wifiPattern -or
                $_.Name -match $wifiPattern
            } |
            Sort-Object @{ Expression = { if ($_.Status -eq 'Up') { 0 } else { 1 } } }, Name |
            Select-Object -First 1

        if ($adapter) {
            return [pscustomobject]@{
                Detected = $true
                Name = $adapter.Name
                Description = $adapter.InterfaceDescription
                AdapterStatus = [string]$adapter.Status
                ConnectedToNetwork = if ($adapter.Status -eq 'Up') { 'Yes' } else { 'No' }
                Source = 'Get-NetAdapter'
            }
        }
    }
    catch {
        # Fall back to CIM below.
    }

    try {
        $adapter = Get-CimInstance -ClassName Win32_NetworkAdapter -ErrorAction Stop |
            Where-Object {
                $_.Name -match $wifiPattern -or
                $_.Description -match $wifiPattern -or
                $_.NetConnectionID -match $wifiPattern
            } |
            Sort-Object @{ Expression = { if ($_.NetConnectionStatus -eq 2) { 0 } else { 1 } } }, NetConnectionID |
            Select-Object -First 1

        if ($adapter) {
            $status = switch ($adapter.NetConnectionStatus) {
                0 { 'Disconnected' }
                1 { 'Connecting' }
                2 { 'Connected' }
                3 { 'Disconnecting' }
                4 { 'Hardware not present' }
                5 { 'Hardware disabled' }
                6 { 'Hardware malfunction' }
                7 { 'Media disconnected' }
                8 { 'Authenticating' }
                9 { 'Authentication succeeded' }
                10 { 'Authentication failed' }
                11 { 'Invalid address' }
                12 { 'Credentials required' }
                default { if ($adapter.NetEnabled) { 'Enabled' } else { 'Disconnected' } }
            }

            return [pscustomobject]@{
                Detected = $true
                Name = if ($adapter.NetConnectionID) { $adapter.NetConnectionID } else { 'Wi-Fi' }
                Description = $adapter.Description
                AdapterStatus = $status
                ConnectedToNetwork = if ($adapter.NetConnectionStatus -eq 2) { 'Yes' } else { 'No' }
                Source = 'Win32_NetworkAdapter'
            }
        }
    }
    catch {
        # No usable adapter provider was available.
    }

    [pscustomobject]@{
        Detected = $false
        Name = $null
        Description = $null
        AdapterStatus = 'Not detected'
        ConnectedToNetwork = 'No'
        Source = $null
    }
}

$system = Get-CimInstance -ClassName Win32_ComputerSystem -ErrorAction SilentlyContinue
$bios = Get-CimInstance -ClassName Win32_BIOS -ErrorAction SilentlyContinue

$result = $null
foreach ($providerCheck in @(
    { Get-HpWmiBiosWlanState },
    { Get-HpBiosWlanState },
    { Get-SavedHpBcuWlanState },
    { Get-LenovoBiosWlanState },
    { Get-DellBiosWlanState }
)) {
    $result = & $providerCheck
    if ($result) {
        break
    }
}

if (-not $result) {
    $result = [pscustomobject]@{
        Provider = $null
        SettingName = $null
        Value = $null
        RawValue = $null
        IsEnabled = $false
        Message = 'No WLAN/Wi-Fi BIOS setting was found, or the system does not expose BIOS settings to Windows.'
    }
}

$status = if ($result.IsEnabled) { 'WLAN ENABLED' } else { 'NO WLAN DETECTED IN BIOS' }
$wifiAdapter = Get-WifiAdapterState

if ($Json) {
    [pscustomobject]@{
        Status = $status
        ComputerName = $env:COMPUTERNAME
        Manufacturer = $system.Manufacturer
        Model = $system.Model
        BiosVersion = $bios.SMBIOSBIOSVersion
        Provider = $result.Provider
        SettingName = $result.SettingName
        Value = $result.Value
        IsEnabled = $result.IsEnabled
        Message = $result.Message
        WifiAdapter = $wifiAdapter
    } | ConvertTo-Json -Depth 4
}
else {
    Write-Output $status
    Write-Output ""
    Write-Host "Wi-Fi Adapter Check" -ForegroundColor Cyan
    Write-Host "====================" -ForegroundColor Cyan
    Write-Output ""

    if ($wifiAdapter.Detected) {
        Write-Host "Wi-Fi card detected:" -ForegroundColor Green
        Write-Output ("  Name: {0}" -f $wifiAdapter.Name)
        Write-Output ("  Description: {0}" -f $wifiAdapter.Description)
        Write-Output ("  Adapter status: {0}" -f $wifiAdapter.AdapterStatus)
        Write-Host ("  Connected to network: {0}" -f $wifiAdapter.ConnectedToNetwork) -ForegroundColor Yellow
    }
    else {
        Write-Host "No Wi-Fi card detected." -ForegroundColor Red
        Write-Output "  Name: Not found"
        Write-Output "  Description: Not found"
        Write-Output "  Adapter status: Not detected"
        Write-Host "  Connected to network: No" -ForegroundColor Yellow
    }

    if ($Detailed) {
        Write-Output ""
        [pscustomobject]@{
            ComputerName = $env:COMPUTERNAME
            Manufacturer = $system.Manufacturer
            Model = $system.Model
            BiosVersion = $bios.SMBIOSBIOSVersion
            Provider = $result.Provider
            SettingName = $result.SettingName
            Value = $result.Value
            Message = $result.Message
        } | Format-List
    }

    Write-Output ""
    Read-Host "Press Enter to close"
}
