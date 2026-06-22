# Ensure the script is running with administrative privileges
$isAdmin = ([Security.Principal.WindowsPrincipal][Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)

if (-not $isAdmin) {
    Write-Warning "This diagnostic utility must be run as an Administrator to query root\WMI classes."
    Exit
}

$OutputFilename = "getac_bios_settings.txt"

Write-Host "============================================================" -ForegroundColor Cyan
Write-Host "        GETAC COMETLAKE WMI BIOS EXTRACTION UTILITY       " -ForegroundColor Cyan
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host "[*] Connecting to local root\WMI framework..." -ForegroundColor Yellow

# Getac enterprise target classes to cycle through
$TargetClasses = @("Getac_BiosSetting", "Getac_WMI", "Getac_BiosMethod")
$BiosObjects = $null
$ActiveClass = ""

# Locate which WMI class is active on this generation of hardware
foreach ($Cls in $TargetClasses) {
    try {
        $BiosObjects = Get-CimInstance -Namespace "root\WMI" -ClassName $Cls -ErrorAction Stop
        if ($BiosObjects) {
            $ActiveClass = $Cls
            break
        }
    } catch {
        continue
    }
}

if (-not $BiosObjects) {
    Write-Host "`n[!] Error: Could not locate a valid Getac_Bios WMI class." -ForegroundColor Red
    Write-Host "    Ensure this script is running on a genuine Getac unit." -ForegroundColor LightRed
    Exit
}

Write-Host "[+] Found Active Getac Class: $ActiveClass" -ForegroundColor Green
Write-Host "[+] Found $($BiosObjects.Count) configuration elements." -ForegroundColor Green
Write-Host "[*] Writing settings out to '$OutputFilename'..." -ForegroundColor Yellow

# Open file and dump out data structural attributes 
try {
    $Stream = [System.IO.StreamWriter]::$OutputFilename
    $Stream.WriteLine("=" * 70)
    $Stream.WriteLine(" GETAC WMI BIOS EXPORT REPORT")
    $Stream.WriteLine(" Target Class Source: $ActiveClass")
    $Stream.WriteLine("=" * 70 + "`r`n")

    $Index = 1
    foreach ($Obj in $BiosObjects) {
        $Stream.WriteLine("[$Index] Setting Entry")
        $Stream.WriteLine("-" * 40)

        # Get all properties for this WMI object dynamically, ignoring system metadata properties
        $Properties = $Obj.CimClass.CimClassProperties | Where-Object { $_.Name -notlike "__*" } | Sort-Object Name

        foreach ($Prop in $Properties) {
            $PropName = $Prop.Name
            try {
                $Value = $Obj.$PropName
                
                # Format arrays/lists nicely if multiple options exist
                if ($Value -is [array] -or $Value -is [System.Collections.IEnumerable] -and $Value -isnot [string]) {
                    $ValueStr = $Value -join ", "
                } else {
                    $ValueStr = [string]$Value
                }

                # Print out property with consistent left alignment padding
                $Stream.WriteLine("{0,-25}: {1}" -f $PropName, $ValueStr)
            } catch {
                $Stream.WriteLine("{0,-25}: [Error Reading Property]" -f $PropName)
            }
        }

        $Stream.WriteLine("`r`n" + "=" * 50 + "`r`n")
        $Index++
    }

    $Stream.Close()
    
    $AbsolutePath = Resolve-Path $OutputFilename
    Write-Host "`n[SUCCESS] Diagnostics saved successfully to: $AbsolutePath" -ForegroundColor Green

} catch {
    Write-Host "`n[CRITICAL FAILURE] Failed to write out to report file: $_" -ForegroundColor Red
}