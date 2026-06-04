

Set-ExecutionPolicy Bypass -Scope Process -Force
.\Manage-BuiltinBiosDevices.ps1

<#
.SYNOPSIS
  Detects built-in device-related BIOS settings that are not Enabled and lets you enable/disable them.

.DESCRIPTION
  Supports Lenovo (native WMI), Dell (Dell BIOS Provider PSDrive "DellSmbios:\"), and HP (HP Instrumented BIOS WMI).
  Enumerates BIOS settings, filters device-like settings via keywords, lists those not enabled, and lets you change them.
  Use -WhatIf for a dry run. Use -BiosPassword for models with BIOS password set.

.PARAMETER BiosPassword
  Optional BIOS setup password (if set on the system). Leave blank if none.

.PARAMETER WhatIf
  Dry-run mode: show what would change without setting anything.

.EXAMPLE
  .\Manage-BuiltinBiosDevices.ps1 -WhatIf

.EXAMPLE
  .\Manage-BuiltinBiosDevices.ps1 -BiosPassword "MySecurePw!"
#>

[CmdletBinding(SupportsShouldProcess=$true)]
param(
  [string]$BiosPassword,
  [switch]$WhatIf
)

function Assert-Admin {
  $isAdmin = ([Security.Principal.WindowsPrincipal] [Security.Principal.WindowsIdentity]::GetCurrent()
    ).IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)
  if (-not $isAdmin) {
    Write-Error "Run this script as Administrator."
    exit 1
  }
}

function Get-Oem {
  try {
    $m = (Get-CimInstance -ClassName Win32_ComputerSystem).Manufacturer
    switch -regex ($m) {
      'Dell'    { return 'Dell' }
      'Hewlett|HP' { return 'HP' }
      'Lenovo'  { return 'Lenovo' }
      default   { return 'Unknown' }
    }
  } catch {
    return 'Unknown'
  }
}

# Keywords that typically correspond to built-in device toggles in BIOS.
$DeviceKeywords = @(
  'Audio','Integrated Audio','Sound',
  'Camera','Webcam','Microphone','Mic',
  'Bluetooth','WLAN','Wi-Fi','WWAN','Wireless','Radio',
  'NIC','LAN','Ethernet','PXE',
  'Thunderbolt','TBT',
  'SD','Card Reader','CardReader',
  'Fingerprint','Smart Card','SmartCard','NFC','Infrared','IR',
  'Touchpad','Trackpad','Pointing Device'
)

function Test-KeywordMatch {
  param([string]$Name)
  foreach ($k in $DeviceKeywords) {
    if ($Name -match [regex]::Escape($k)) { return $true }
  }
  return $false
}

function Is-DisabledValue {
  param([string]$Value)
  if (-not $Value) { return $false }
  return ($Value -match '^(disabled|disable|off|no|none)$' -im)
}

function Normalize-BooleanValue {
  param([string]$Value)
  if (-not $Value) { return $null }
  if ($Value -match 'enable' -im) { return 'Enabled' }
  if ($Value -match 'disable' -im) { return 'Disabled' }
  if ($Value -match 'on' -im) { return 'Enabled' }
  if ($Value -match 'off' -im) { return 'Disabled' }
  return $Value
}

# ---- DELL (DellBIOSProvider) ----
function Get-DellSettings {
  $result = @()
  try {
    if (-not (Get-PSDrive -Name DellSmbios -ErrorAction SilentlyContinue)) {
      Import-Module DellBIOSProvider -ErrorAction Stop | Out-Null
    }
    if (-not (Get-PSDrive -Name DellSmbios -ErrorAction SilentlyContinue)) {
      Write-Warning "Dell BIOS Provider (DellBIOSProvider) not found. Install Dell BIOS Provider to manage Dell BIOS from PowerShell."
      return @()
    }
    $items = Get-ChildItem "DellSmbios:\BIOSSettings" -ErrorAction Stop
    foreach ($i in $items) {
      # Attempt to read properties defensively across versions
      $name   = $i.AttributeName
      if (-not $name) { $name = $i.Name }
      $curr   = $i.CurrentValue
      if (-not $curr -and $i.PSObject.Properties.Name -contains 'Value') { $curr = $i.Value }
      $poss   = @()
      if ($i.PSObject.Properties.Name -contains 'PossibleValues' -and $i.PossibleValues) {
        $poss = [string[]]$i.PossibleValues
      } else {
        $poss = @('Enabled','Disabled')
      }
      if ($name -and (Test-KeywordMatch -Name $name)) {
        $result += [PSCustomObject]@{
          OEM          = 'Dell'
          Name         = $name
          Current      = (Normalize-BooleanValue $curr)
          Possible     = $poss -join ', '
          RawPossible  = $poss
          SetDelegate  = {
            param([string]$Desired)
            $path = "DellSmbios:\BIOSSettings\$($name)"
            if ($WhatIf) {
              Write-Host "[WhatIf] Dell -> Set $name = $Desired"
              return @{ Status='WhatIf' }
            }
            try {
              Set-Item -Path $path -Value $Desired -ErrorAction Stop | Out-Null
              return @{ Status='Success' }
            } catch {
              return @{ Status='Error'; Message=$_.Exception.Message }
            }
          }.GetNewClosure()
        }
      }
    }
  } catch {
    Write-Warning "Error reading Dell BIOS settings: $($_.Exception.Message)"
  }
  return $result
}

# ---- HP (HP Instrumented BIOS) ----
function Get-HPSettings {
  $result = @()
  try {
    $ns = 'root\HP\InstrumentedBIOS'
    $enum = Get-WmiObject -Namespace $ns -Class HP_BIOSEnumeration -ErrorAction SilentlyContinue
    if (-not $enum) {
      # Alternative class name on some generations:
      $enum = Get-WmiObject -Namespace $ns -Class HP_BiosEnumeration -ErrorAction SilentlyContinue
    }
    if (-not $enum) {
      Write-Warning "HP Instrumented BIOS WMI not found. Install HP BIOS/WMI interface (often preinstalled on HP business PCs)."
      return @()
    }
    foreach ($e in $enum) {
      $name = $e.Name
      $curr = $e.CurrentValue
      $poss = @()
      if ($e.PSObject.Properties.Name -contains 'PossibleValues' -and $e.PossibleValues) {
        $poss = [string[]]$e.PossibleValues
      } elseif ($e.PSObject.Properties.Name -contains 'Possible' -and $e.Possible) {
        $poss = [string[]]$e.Possible
      } else {
        $poss = @('Enabled','Disabled')
      }
      if ($name -and (Test-KeywordMatch -Name $name)) {
        $result += [PSCustomObject]@{
          OEM          = 'HP'
          Name         = $name
          Current      = (Normalize-BooleanValue $curr)
          Possible     = $poss -join ', '
          RawPossible  = $poss
          SetDelegate  = {
            param([string]$Desired)
            if ($WhatIf) {
              Write-Host "[WhatIf] HP -> Set $name = $Desired"
              return @{ Status='WhatIf' }
            }
            try {
              # Two common interfaces across generations:
              $ns = 'root\HP\InstrumentedBIOS'
              $iface = Get-WmiObject -Namespace $ns -Class HP_BIOSSettingInterface -ErrorAction SilentlyContinue
              if (-not $iface) {
                $iface = Get-WmiObject -Namespace $ns -Class HP_BiosSettingInterface -ErrorAction SilentlyContinue
              }
              if (-not $iface) { throw "HP BIOSSettingInterface not available." }
              $null = $iface.SetBiosSetting($name, $Desired, $BiosPassword)
              # Some generations need an explicit commit:
              if ($iface.PSObject.Methods.Name -contains 'SaveChanges') {
                $null = $iface.SaveChanges()
              }
              return @{ Status='Success' }
            } catch {
              return @{ Status='Error'; Message=$_.Exception.Message }
            }
          }.GetNewClosure()
        }
      }
    }
  } catch {
    Write-Warning "Error reading HP BIOS settings: $($_.Exception.Message)"
  }
  return $result
}

# ---- LENOVO (Lenovo WMI) ----
function Get-LenovoSettings {
  $result = @()
  try {
    $cls = Get-WmiObject -Namespace root\wmi -Class Lenovo_BiosSetting -ErrorAction SilentlyContinue
    if (-not $cls) {
      Write-Warning "Lenovo BIOS WMI interface not found. Ensure Lenovo BIOS WMI driver is installed."
      return @()
    }
    foreach ($s in $cls) {
      # CurrentSetting is typically "Name,Value"
      if (-not $s.CurrentSetting) { continue }
      $parts = $s.CurrentSetting -split ',', 2
      if ($parts.Count -lt 2) { continue }
      $name = $parts[0].Trim()
      $curr = $parts[1].Trim()
      # Possible values are sometimes in a separate property or may be absent
      $poss = @('Enabled','Disabled')
      if ($s.PSObject.Properties.Name -contains 'PossibleValues' -and $s.PossibleValues) {
        $poss = [string[]]$s.PossibleValues
      }
      if ($name -and (Test-KeywordMatch -Name $name)) {
        $result += [PSCustomObject]@{
          OEM          = 'Lenovo'
          Name         = $name
          Current      = (Normalize-BooleanValue $curr)
          Possible     = $poss -join ', '
          RawPossible  = $poss
          SetDelegate  = {
            param([string]$Desired)
            if ($WhatIf) {
              Write-Host "[WhatIf] Lenovo -> Set $name = $Desired"
              return @{ Status='WhatIf' }
            }
            try {
              $setter = Get-WmiObject -Namespace root\wmi -Class Lenovo_SetBiosSetting -ErrorAction Stop
              $saver  = Get-WmiObject -Namespace root\wmi -Class Lenovo_SaveBiosSettings -ErrorAction Stop
              $pair   = "$name,$Desired"
              $r1 = $setter.SetBiosSetting($pair)
              $r2 = $saver.SaveBiosSettings()
              return @{ Status='Success'; SetReturn=$r1; SaveReturn=$r2 }
            } catch {
              return @{ Status='Error'; Message=$_.Exception.Message }
            }
          }.GetNewClosure()
        }
      }
    }
  } catch {
    Write-Warning "Error reading Lenovo BIOS settings: $($_.Exception.Message)"
  }
  return $result
}

# ---- MAIN ----
Assert-Admin

$manufacturer = Get-Oem
Write-Host "Detected OEM: $manufacturer" -ForegroundColor Cyan
Write-Host ""

$all = @()
switch ($manufacturer) {
  'Dell'   { $all = Get-DellSettings }
  'HP'     { $all = Get-HPSettings }
  'Lenovo' { $all = Get-LenovoSettings }
  default  {
    Write-Warning "Unsupported/unknown OEM. The script supports Dell, HP, and Lenovo where their BIOS providers are present."
    $all = @()
  }
}

if (-not $all -or $all.Count -eq 0) {
  Write-Host "No BIOS device-like settings were discovered (or provider not present)." -ForegroundColor Yellow
  Write-Host "Tip: You can add/remove keywords inside the script to match your environment." -ForegroundColor DarkGray
  exit 0
}

# Prepare view
$view = $all | Sort-Object OEM, Name | Select-Object OEM, Name, Current, Possible
Write-Host "`n== All device-like BIOS settings detected ==" -ForegroundColor Green
$idx = 1
$indexed = @()
foreach ($row in $all | Sort-Object OEM, Name) {
  $indexed += [PSCustomObject]@{
    Index    = $idx
    OEM      = $row.OEM
    Name     = $row.Name
    Current  = $row.Current
    Possible = $row.Possible
    _Obj     = $row
  }
  $idx++
}
$indexed | Format-Table Index, OEM, Name, Current, Possible -AutoSize

$disabled = $indexed | Where-Object { Is-DisabledValue -Value $_.Current }
if ($disabled.Count -gt 0) {
  Write-Host "`n== Not Enabled (candidates) ==" -ForegroundColor Yellow
  $disabled | Format-Table Index, OEM, Name, Current, Possible -AutoSize
} else {
  Write-Host "`nNo device-like settings are disabled." -ForegroundColor Green
}

Write-Host ""
Write-Host "Options:" -ForegroundColor Cyan
Write-Host "  [A] Enable all disabled above"
Write-Host "  [S] Select specific items with action (e.g., 1:E,3:D,5:E)"
Write-Host "  [Q] Quit without changes"
Write-Host ""
$choice = Read-Host "Choose A/S/Q"

if ($choice -match '^[Qq]$') {
  Write-Host "No changes made." -ForegroundColor Cyan
  exit 0
}

$changes = @()

if ($choice -match '^[Aa]$') {
  foreach ($it in $disabled) {
    # Find an 'Enabled' variant acceptable to OEM (case-insensitive match)
    $enabledOption = $it._Obj.RawPossible | Where-Object { $_ -match 'enable' -or $_ -match 'on' }
    if (-not $enabledOption) { $enabledOption = @('Enabled') }
    $changes += [PSCustomObject]@{
      Target = $it
      Desired = $enabledOption[0]
    }
  }
} elseif ($choice -match '^[Ss]$') {
  Write-Host "Enter selections in the form: index:Value pairs separated by commas." -ForegroundColor DarkGray
  Write-Host "Examples: 2:Enabled  or  1:E,3:D  (E/D also accepted)" -ForegroundColor DarkGray
  $spec = Read-Host "Selection"
  if ([string]::IsNullOrWhiteSpace($spec)) {
    Write-Host "No selections provided. Exiting."
    exit 0
  }
  $pairs = $spec -split '\s*,\s*'
  foreach ($p in $pairs) {
    if ($p -notmatch '^\s*(\d+)\s*:\s*([A-Za-z]+)\s*$') { continue }
    $ix = [int]$Matches[1]
    $valRaw = $Matches[2]
    $target = $indexed | Where-Object { $_.Index -eq $ix }
    if (-not $target) {
      Write-Warning "Index $ix not found."
      continue
    }
    # Normalize shorthand E/D to Enabled/Disabled
    $desired = switch -regex ($valRaw) {
      '^(e|enable|enabled|on)$'   { 'Enabled'; break }
      '^(d|disable|disabled|off)$' { 'Disabled'; break }
      default { $valRaw }
    }
    # If desired not in RawPossible, keep as-is; OEM may accept the string anyway
    $changes += [PSCustomObject]@{
      Target  = $target
      Desired = $desired
    }
  }
} else {
  Write-Host "Invalid choice. Exiting." -ForegroundColor Yellow
  exit 0
}

if ($changes.Count -eq 0) {
  Write-Host "Nothing to change." -ForegroundColor Cyan
  exit 0
}

Write-Host "`n== Planned changes ==" -ForegroundColor Green
$changes | ForEach-Object {
  "{0}: {1} -> {2}" -f $_.Target.Name, $_.Target.Current, $_.Desired
}

if ($PSCmdlet.ShouldProcess("BIOS","Apply changes")) {
  foreach ($chg in $changes) {
    $o = $chg.Target._Obj
    $desired = $chg.Desired
    # Try to map to a vendor-accepted option (case-insensitive)
    $accept = $o.RawPossible | Where-Object { $_ -ieq $desired }
    if (-not $accept -and $desired -match 'enable') {
      $accept = $o.RawPossible | Where-Object { $_ -match 'enable|on' }
    }
    if (-not $accept -and $desired -match 'disable') {
      $accept = $o.RawPossible | Where-Object { $_ -match 'disable|off' }
    }
    if (-not $accept -or $accept.Count -eq 0) { $accept = @($desired) }
    $use = $accept[0]

    $res = & $o.SetDelegate.Invoke($use)
    if ($res.Status -eq 'Success' -or $res.Status -eq 'WhatIf') {
      Write-Host "OK: $($chg.Target.Name) -> $use ($($chg.Target.OEM))" -ForegroundColor Green
    } else {
      Write-Host "ERROR: $($chg.Target.Name) -> $use ($($chg.Target.OEM)) : $($res.Message)" -ForegroundColor Red
    }
  }
  Write-Host "`nNOTE: Changes may require a reboot to take effect." -ForegroundColor Yellow
  Write-Host "If BitLocker is enabled and you altered TPM/Secure Boot/Virtualization, suspend BitLocker before reboot to avoid recovery prompts." -ForegroundColor Yellow
}

