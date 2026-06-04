# ------------------------------------------------------------
#  InstallHPDrivers.ps1 (Hardened)
# ------------------------------------------------------------
#  Purpose
#    • Retrieves serial number, SKU, and model via CIM
#    • Sets ExecutionPolicy only at Process scope (no GPO conflicts)
#    • Ensures NuGet provider & PSGallery trust
#    • Installs the HPDrivers PowerShell module
#
#  Author:  Anthony Witt
#  Date:    2026‑03‑11
# ------------------------------------------------------------

$ErrorActionPreference = 'Stop'

Write-Host "=== InstallHPDrivers.ps1 starting at $(Get-Date) ===" -ForegroundColor Cyan

# ---------- Hardening header ----------
try {
    # Unblock this script in case it has MOTW
    if ($PSCommandPath) { Unblock-File -LiteralPath $PSCommandPath -ErrorAction SilentlyContinue }

    # Force TLS 1.2 on Windows PowerShell 5.1
    if ($PSVersionTable.PSVersion.Major -lt 6) {
        [Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12
        Write-Host "TLS set to 1.2" -ForegroundColor DarkGray
    }

    # Avoid GPO/policy conflicts: use Process scope only
    Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass -Force
    Write-Host "ExecutionPolicy(Process)=Bypass" -ForegroundColor DarkGray

    # Ensure PSGallery exists and is Trusted
    $repo = Get-PSRepository -Name 'PSGallery' -ErrorAction SilentlyContinue
    if (-not $repo) {
        Register-PSRepository -Default -ErrorAction SilentlyContinue
        $repo = Get-PSRepository -Name 'PSGallery' -ErrorAction SilentlyContinue
    }
    if ($repo -and $repo.InstallationPolicy -ne 'Trusted') {
        Set-PSRepository -Name 'PSGallery' -InstallationPolicy Trusted -ErrorAction SilentlyContinue
        Write-Host "PSGallery set to Trusted." -ForegroundColor DarkGray
    }

    # Ensure NuGet provider
    $minNuGet = [Version]'2.8.5.201'
    $nuget = Get-PackageProvider -Name NuGet -ErrorAction SilentlyContinue
    if (-not $nuget -or $nuget.Version -lt $minNuGet) {
        Write-Host "Installing NuGet provider v$minNuGet..." -ForegroundColor Yellow
        Install-PackageProvider -Name NuGet -RequiredVersion $minNuGet -Force | Out-Null
    } else {
        Write-Host "NuGet provider OK (v$($nuget.Version))." -ForegroundColor DarkGray
    }

    # Optionally refresh PowerShellGet (don’t fail if locked)
    Install-Module -Name PowerShellGet -Force -AllowClobber -ErrorAction SilentlyContinue

} catch {
    Write-Warning "Hardening header warning: $($_.Exception.Message)"
}
# ---------- End hardening header ----------

# ---------- 1. Gather system information ----------
Write-Host "`n=== System Information (CIM) ===" -ForegroundColor Cyan
try {
    $serial = (Get-CimInstance Win32_BIOS).SerialNumber
    $sku    = (Get-CimInstance Win32_ComputerSystemProduct).SKUNumber
    if (-not $sku) { $sku = (Get-CimInstance Win32_ComputerSystem).SystemSKUNumber }
    $model  = (Get-CimInstance Win32_ComputerSystem).Model

    Write-Host "Serial Number : $serial"
    Write-Host "System SKU    : $sku"
    Write-Host "System Model  : $model"
} catch {
    Write-Warning "Unable to read CIM properties: $($_.Exception.Message)"
}
Write-Host ""

# ---------- 2. Install HPDrivers module ----------
$moduleName = 'HPDrivers'
Write-Host "Installing/Updating $moduleName..." -ForegroundColor Yellow

# Try AllUsers first (since you run elevated), then fallback to CurrentUser
$installed = $false
try {
    Install-Module -Name $moduleName -Force -Scope AllUsers -ErrorAction Stop
    $installed = $true
} catch {
    Write-Warning "AllUsers install failed: $($_.Exception.Message) — trying CurrentUser..."
    try {
        Install-Module -Name $moduleName -Force -Scope CurrentUser -ErrorAction Stop
        $installed = $true
    } catch {
        Write-Error "Failed to install ${moduleName}: $($_.Exception.Message)"
        Write-Host "`nDiagnostics:" -ForegroundColor DarkYellow
        Write-Host ("  PSVersion:    {0}" -f $PSVersionTable.PSVersion)
        Write-Host ("  PSEdition:    {0}" -f $PSVersionTable.PSEdition)
        Write-Host ("  Host:         {0}" -f $Host.Name)
        Write-Host ("  LanguageMode: {0}" -f $ExecutionContext.SessionState.LanguageMode)
        Write-Host "  ExecutionPolicy (scopes):"
        Get-ExecutionPolicy -List | Format-Table -Auto
        throw
    }
}

if ($installed) {
    Import-Module $moduleName -ErrorAction Stop
    Write-Host "$moduleName installed and imported." -ForegroundColor Green
}

Write-Host "`nInstallation complete." -ForegroundColor Yellow

# Optional: pause so the console window stays open when run by double‑click
Read-Host -Prompt "Press Enter to exit"