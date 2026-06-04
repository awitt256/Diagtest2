[CmdletBinding()]
param(
    [switch]$AsJson,
    [switch]$NoPause
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

$IndicatorRegex = '(?i)rpcnet|absolute|computrace|lojack|ctes'

function New-Finding {
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
                New-Finding -Category 'Process' -Name $item.ProcessName -Status 'Present' -Details "PID $($item.Id)"
            }
        }
    }

    if (-not $found) {
        New-Finding -Category 'Process' -Name 'Known rpcnet/ctes and Absolute/Computrace processes' -Status 'NotFound' -Details 'No known rpcnet/ctes or Computrace-related processes were running.'
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
        New-Finding -Category 'Service' -Name 'Known rpcnet/ctes and Absolute/Computrace services' -Status 'NotFound' -Details 'No known rpcnet/ctes or Computrace-related services were installed.'
        return
    }

    foreach ($svc in ($services | Sort-Object Name -Unique)) {
        New-Finding -Category 'Service' -Name $svc.Name -Status $svc.Status.ToString() -Details "StartType: $($svc.StartType)"
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
        New-Finding -Category 'Driver' -Name 'Known rpcnet/ctes and Absolute/Computrace drivers' -Status 'NotFound' -Details 'No matching rpcnet/ctes or Computrace-related drivers were found.'
        return
    }

    foreach ($driver in $drivers) {
        $details = @(
            "State: $($driver.State)"
            "StartMode: $($driver.StartMode)"
            "Path: $($driver.PathName)"
        ) -join '; '

        New-Finding -Category 'Driver' -Name $driver.Name -Status 'Present' -Details $details
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
        New-Finding -Category 'File' -Name 'Known rpcnet/ctes and Absolute/Computrace files' -Status 'NotFound' -Details 'No known rpcnet/ctes or Computrace binaries were found in standard Windows paths.'
        return
    }

    foreach ($path in $existing) {
        $item = Get-Item $path
        New-Finding -Category 'File' -Name $item.Name -Status 'Present' -Details $item.FullName
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
                        $findings += New-Finding -Category 'Registry' -Name $property.Name -Status 'Present' -Details "$path -> $($property.Value)"
                    }
                }
            }
            catch {
            }

            continue
        }

        $findings += New-Finding -Category 'Registry' -Name (Split-Path $path -Leaf) -Status 'Present' -Details $path
    }

    if (-not $findings) {
        New-Finding -Category 'Registry' -Name 'Known rpcnet/ctes and Absolute/Computrace registry keys' -Status 'NotFound' -Details 'No matching rpcnet/ctes or Computrace-related registry indicators were found.'
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
        $findings += New-Finding -Category 'System' -Name 'Manufacturer' -Status 'Info' -Details "$($baseboard.Manufacturer) $($baseboard.Model)"
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
            $findings += New-Finding -Category 'BIOS' -Name 'Win32_BIOS text match' -Status 'Possible' -Details ($biosText.Trim())
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

        $findings += New-Finding -Category 'BIOS' -Name "Dell BIOS: $($attr.AttributeName)" -Status $status -Details $details
    }

    $lenovoSettings = Safe-GetCimInstance -Namespace 'root/wmi' -ClassName Lenovo_BiosSetting |
        Where-Object { $_.CurrentSetting -match '(?i)absolute|computrace|persistence|ctes' }

    foreach ($setting in $lenovoSettings) {
        $parts = @([string]$setting.CurrentSetting -split ',', 2)
        $settingName = if ($parts.Count -ge 1) { $parts[0].Trim() } else { 'Lenovo BIOS setting' }
        $currentValue = if ($parts.Count -ge 2) { $parts[1].Trim() } else { [string]$setting.CurrentSetting }
        $status = Get-BiosStateStatus -Name $settingName -CurrentValue $currentValue

        $findings += New-Finding -Category 'BIOS' -Name "Lenovo BIOS: $settingName" -Status $status -Details "CurrentValue: $currentValue"
    }

    $hpSettings = Safe-GetCimInstance -Namespace 'root/HP/InstrumentedBIOS' -ClassName HP_BIOSEnumeration |
        Where-Object { $_.Name -match '(?i)absolute|computrace|persistence|ctes' }

    foreach ($setting in $hpSettings) {
        $status = Get-BiosStateStatus -Name $setting.Name -CurrentValue $setting.CurrentValue
        $details = @(
            "CurrentValue: $($setting.CurrentValue)"
            "PossibleValues: $($setting.PossibleValues -join ', ')"
        ) -join '; '

        $findings += New-Finding -Category 'BIOS' -Name "HP BIOS: $($setting.Name)" -Status $status -Details $details
    }

    if (-not ($findings | Where-Object { $_.Category -eq 'BIOS' })) {
        $findings += New-Finding -Category 'BIOS' -Name 'Vendor BIOS status' -Status 'Unknown' -Details 'No vendor BIOS class exposed Computrace/Absolute status. BIOS activation may still need to be checked manually.'
    }

    $findings
}

$findings = @()
$findings += Get-ProcessIndicators
$findings += Get-ServiceIndicators
$findings += Get-DriverIndicators
$findings += Get-FileIndicators
$findings += Get-RegistryIndicators
$findings += Get-BiosIndicators

$osCategories = @('Process', 'Service', 'Driver', 'File', 'Registry')
$osPositiveFindings = @(
    $findings | Where-Object {
        $_.Category -in $osCategories -and $_.Status -ne 'NotFound'
    }
)

$biosEnabledFindings = @(
    $findings | Where-Object {
        $_.Category -eq 'BIOS' -and $_.Status -eq 'Enabled'
    }
)

$biosReviewFindings = @(
    $findings | Where-Object {
        $_.Category -eq 'BIOS' -and $_.Status -in @('Possible', 'Reported')
    }
)

if ($osPositiveFindings) {
    $resultLabel = 'FAIL'
    $resultColor = 'Red'
    $summary = 'Active OS-level Absolute/Computrace indicators were found.'
}
elseif ($biosEnabledFindings) {
    $resultLabel = 'WARN'
    $resultColor = 'Yellow'
    $summary = 'No active OS-level indicators were found, but BIOS reports Absolute/Computrace as enabled.'
}
elseif ($biosReviewFindings) {
    $resultLabel = 'WARN'
    $resultColor = 'Yellow'
    $summary = 'No active OS-level indicators were found. BIOS information was reported and should be reviewed manually.'
}
else {
    $resultLabel = 'PASS'
    $resultColor = 'Green'
    $summary = 'No active OS-level indicators were found, and BIOS did not report Absolute/Computrace as enabled.'
}

$result = [pscustomobject]@{
    ComputerName     = $env:COMPUTERNAME
    Timestamp        = (Get-Date).ToString('s')
    Result           = $resultLabel
    Summary          = $summary
    PositiveCount    = @($osPositiveFindings).Count + @($biosEnabledFindings).Count + @($biosReviewFindings).Count
    Findings         = $findings
}

if ($AsJson) {
    $result | ConvertTo-Json -Depth 5
}
else {
    Write-Host ''
    Write-Host "Computer: $($result.ComputerName)"
    Write-Host "Timestamp: $($result.Timestamp)"
    Write-Host "Result: $resultLabel" -ForegroundColor $resultColor
    Write-Host "Summary: $($result.Summary)" -ForegroundColor $resultColor
    Write-Host ''

    $result.Findings | Format-Table -AutoSize
    Write-Host ''

    if (-not $NoPause) {
        Read-Host 'Press Enter to exit'
    }
}
