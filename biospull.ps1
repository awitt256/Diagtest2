
# Get-HPBiosSettings.ps1
[CmdletBinding()]
param(
    [string]$Namespace = 'root\hp\instrumentedBIOS',
    [string]$ClassName = 'hp_biosEnumeration'
)

function Get-HPBiosSettings {
    [CmdletBinding()]
    param(
        [string]$Namespace,
        [string]$ClassName
    )

    $raw = if ($PSVersionTable.PSVersion.Major -ge 6) {
        Get-CimInstance -Namespace $Namespace -ClassName $ClassName -ErrorAction Stop
    } else {
        Get-WmiObject  -Namespace $Namespace -Class     $ClassName -ErrorAction Stop
    }

    $raw |
        ForEach-Object {
            $current  = $_.'currentvalue'    ; if ($current  -is [array])  { $current  = $current  -join '; ' }
            $possible = $_.'possiblevalues'  ; if ($possible -is [array]) { $possible = $possible -join '; ' }
            [pscustomobject]@{
                Setting            = $_.'Name'
                'Current Value'    = $current
                'Possible Values'  = $possible
            }
        } |
        Sort-Object Setting
}

try {
    if (-not (Get-CimInstance -Namespace 'root\hp' -ClassName __NAMESPACE -ErrorAction SilentlyContinue |
              Where-Object Name -eq 'instrumentedBIOS')) {
        Write-Warning "HP Instrumented BIOS provider not found (root\hp\instrumentedBIOS)."
        return
    }

    Get-HPBiosSettings -Namespace $Namespace -ClassName $ClassName | Format-Table -AutoSize
}
catch {
    Write-Error $_
}
