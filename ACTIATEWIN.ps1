$ErrorActionPreference = "SilentlyContinue"
$ProgressPreference = "SilentlyContinue"
$WarningPreference = "SilentlyContinue"

# --- OS info ---
$os = Get-CimInstance Win32_OperatingSystem -Property Caption, Version | Select-Object -First 1

# --- BIOS/UEFI OEM DPK ---
$biosKey = (Get-CimInstance -ClassName SoftwareLicensingService -Property OA3xOriginalProductKey).OA3xOriginalProductKey

# --- Registry backup key ---
$regKey = (Get-ItemProperty "HKLM:\SOFTWARE\Microsoft\Windows NT\CurrentVersion\SoftwareProtectionPlatform" -Name BackupProductKeyDefault -ErrorAction SilentlyContinue).BackupProductKeyDefault

$availableKey = if ($biosKey) { $biosKey } elseif ($regKey) { $regKey } else { $null }

# --- Helper: obtener el SKU realmente instalado (el único con PartialProductKey) ---
function Get-InstalledWindowsProduct {
    Get-CimInstance -ClassName SoftwareLicensingProduct `
        -Filter "ApplicationId='55c92734-d682-4d71-983e-d6ec3f16059f' AND PartialProductKey IS NOT NULL" `
        -Property Name, LicenseStatus, PartialProductKey, GracePeriodRemaining |
        Select-Object -First 1
}

function Get-LicenseStatusText($status) {
    switch ($status) {
        0 { "Unlicensed" }
        1 { "Licensed" }
        2 { "Out-of-Box Grace Period" }
        3 { "Out-of-Tolerance Grace Period" }
        4 { "Non-Genuine Grace Period" }
        5 { "Notification" }
        6 { "Extended Grace" }
        default { "Unknown ($status)" }
    }
}

# --- Admin check ---
$isAdmin = ([Security.Principal.WindowsPrincipal][Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)
$adminWarning = $null

# --- Estado inicial ---
$product = Get-InstalledWindowsProduct
$licenseStatus = if ($product) { [int]$product.LicenseStatus } else { 0 }
$licenseName   = if ($product) { $product.Name } else { $null }
$partialKey    = if ($product) { $product.PartialProductKey } else { $null }
$licenseActive = if ($licenseStatus -eq 1) { 1 } else { 0 }

# --- Si NO está activa y tenemos key disponible, intentar activar ---
if ($licenseActive -eq 0 -and $availableKey) {
    if ($isAdmin) {
        Start-Process -FilePath "cscript.exe" -ArgumentList "//nologo", "C:\Windows\System32\slmgr.vbs", "/ipk", $availableKey -Wait -WindowStyle Hidden
        Start-Process -FilePath "cscript.exe" -ArgumentList "//nologo", "C:\Windows\System32\slmgr.vbs", "/ato" -Wait -WindowStyle Hidden
        Start-Sleep -Seconds 5

        $product = Get-InstalledWindowsProduct
        $licenseStatus = if ($product) { [int]$product.LicenseStatus } else { 0 }
        $licenseName   = if ($product) { $product.Name } else { $null }
        $partialKey    = if ($product) { $product.PartialProductKey } else { $null }
        $licenseActive = if ($licenseStatus -eq 1) { 1 } else { 0 }
    } else {
        $adminWarning = "Se requieren privilegios de administrador para instalar y activar la clave de producto."
    }
}

$statusText = Get-LicenseStatusText $licenseStatus

@{
    source            = if ($biosKey) { "BIOS/UEFI OEM" } elseif ($regKey) { "Registry" } else { "None" }
    licenseDetails    = if ($licenseName) { "$statusText - $licenseName" } else { $statusText }
    activated         = $licenseActive
    licenseStatus     = $licenseStatus
    licenseStatusText = $statusText
    keyWindows        = if ($availableKey) { $availableKey } else { "No license found" }
    partialKey        = $partialKey
    adminWarning      = $adminWarning
    os                = $os.Version
    edition           = $os.Caption
    timestamp         = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
    error             = $null
} | ConvertTo-Json -Compress