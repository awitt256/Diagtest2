Write-Host "=========================================================" -ForegroundColor Cyan
Write-Host "  Enrollment and Computrace Check Built By Anthony Witt  " -ForegroundColor Cyan
Write-Host "=========================================================" -ForegroundColor Cyan
Write-Host ""

function Write-Result {
    param(
        [string]$TestName,
        [bool]$IsFound,
        [array]$Details = @(),
        [array]$CheckedLocations = @()
    )
    
    # Define column width
    $padLength = 22
    $paddedTestName = $TestName.PadRight($padLength)
    
    Write-Host "$paddedTestName : " -NoNewline
    if ($IsFound) {
        Write-Host "Enrollment found (FAIL)" -ForegroundColor Red
        if ($Details.Count -gt 0) {
            foreach ($detail in $Details) {
                Write-Host "    [!] $detail" -ForegroundColor Yellow
            }
        }
    } else {
        Write-Host "No enrollment found (PASS)" -ForegroundColor Green
    }
    
    if ($CheckedLocations.Count -gt 0) {
        Write-Host "    --- Locations Checked ---" -ForegroundColor DarkGray
        foreach ($loc in $CheckedLocations) {
            Write-Host "    $loc" -ForegroundColor DarkGray
        }
    }
    Write-Host ""
}

# 1. Check Intune / MDM Enrollment
$intuneFound = $false
$intuneDetails = @()
$intuneChecked = @(
    "Command: dsregcmd /status",
    "WMI Namespace: ROOT\CIMV2\mdm\dmmap (MDM_Client class)"
)

# dsregcmd method
$dsreg = dsregcmd /status
if ($dsreg -match "MdmEnrolled\s*:\s*YES") {
    $intuneFound = $true
    $intuneDetails += "Found via Command: dsregcmd /status (MdmEnrolled : YES)"
}

# WMI method
$wmiMdm = Get-CimInstance -Namespace "ROOT\CIMV2\mdm\dmmap" -ClassName "MDM_Client" -ErrorAction SilentlyContinue
if ($wmiMdm) {
    $intuneFound = $true
    $intuneDetails += "Found via WMI Namespace: ROOT\CIMV2\mdm\dmmap (MDM_Client class)"
}

Write-Result -TestName "Intune / MDM Status" -IsFound $intuneFound -Details $intuneDetails -CheckedLocations $intuneChecked

# 2. Check Windows Autopilot
$autopilotFound = $false
$autopilotDetails = @()
$autopilotPath = "HKLM:\SOFTWARE\Microsoft\Provisioning\Diagnostics\AutoPilot"
$autopilotChecked = @("Registry Key: $autopilotPath")

if (Test-Path $autopilotPath) {
    $autopilotProps = Get-ItemProperty -Path $autopilotPath -ErrorAction SilentlyContinue
    
    $tenantMatched = $autopilotProps.TenantMatched
    $tenantId = $autopilotProps.CloudAssignedTenantId
    
    if ($tenantMatched -eq 1 -or $tenantId) {
        $autopilotFound = $true
        $autopilotDetails += "Active Autopilot Configuration Found:"
        if ($tenantId) { $autopilotDetails += "  - Tenant ID: $tenantId" }
        if ($null -ne $tenantMatched) { $autopilotDetails += "  - Tenant Matched: $tenantMatched" }
    }
}

Write-Result -TestName "Autopilot Status" -IsFound $autopilotFound -Details $autopilotDetails -CheckedLocations $autopilotChecked

# 3. Check Computrace / Absolute
$computraceFound = $false
$computraceDetails = @()

$computraceFiles = @(
    "C:\Windows\System32\rpcnet.exe",
    "C:\Windows\System32\rpcnetp.exe",
    "C:\Windows\System32\rpcnet.dll",
    "C:\Windows\System32\rpcnetp.dll",
    "C:\Windows\SysWOW64\rpcnet.exe",
    "C:\Windows\SysWOW64\rpcnetp.exe",
    "C:\Windows\SysWOW64\rpcnet.dll",
    "C:\Windows\SysWOW64\rpcnetp.dll",
    "C:\Windows\System32\abtservice.exe",
    "C:\Windows\SysWOW64\abtservice.exe",
    "C:\Program Files (x86)\Absolute\abtservice.exe",
    "C:\Program Files (x86)\Absolute\abtagent.exe"
)

$computraceServices = @("rpcnet", "rpcnetp", "abtservice", "abtagent")
$computraceProcesses = @("rpcnet", "rpcnetp", "abtservice", "abtagent", "cgecs", "cgexe")

$computraceChecked = @()
$computraceChecked += "Files Checked:"
foreach ($f in $computraceFiles) { $computraceChecked += "  - $f" }
$computraceChecked += "Services Checked: " + ($computraceServices -join ", ")
$computraceChecked += "Processes Checked: " + ($computraceProcesses -join ", ")

foreach ($file in $computraceFiles) {
    if (Test-Path $file) {
        $computraceFound = $true
        $computraceDetails += "Found File: $file"
    }
}

foreach ($srv in $computraceServices) {
    $service = Get-Service -Name $srv -ErrorAction SilentlyContinue
    if ($service) {
        $computraceFound = $true
        $computraceDetails += "Found Service: $srv"
    }
}

foreach ($proc in $computraceProcesses) {
    $process = Get-Process -Name $proc -ErrorAction SilentlyContinue
    if ($process) {
        $computraceFound = $true
        $computraceDetails += "Found Running Process: $proc"
    }
}

Write-Result -TestName "Computrace / Absolute" -IsFound $computraceFound -Details $computraceDetails -CheckedLocations $computraceChecked

# Output result marker for Python GUI
if ($intuneFound -or $autopilotFound -or $computraceFound) {
    Write-Output "ENROLLMENT_CHECK_RESULT:FAIL"
    exit 1
} else {
    Write-Output "ENROLLMENT_CHECK_RESULT:PASS"
    exit 0
}

Read-Host "Press Enter to exit..."
