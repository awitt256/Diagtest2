# --------------------------------------------------------------
#  GetSystemInfoAndUpdates.ps1
# --------------------------------------------------------------
#  Description:
#    • Displays Manufacturer, Model, SystemFamily
#    • Silently prepares NuGet + PSGallery (no prompts)
#    • Installs LSUClient silently
#    • Loads LSUClient & retrieves LS Update data
#    • Prompts for restart if updates found
# --------------------------------------------------------------

$ErrorActionPreference = 'Stop'

# -----------------------------
# 1) System information
# -----------------------------
Write-Host "=== System Information ===" -ForegroundColor Cyan
try {
    Get-CimInstance Win32_ComputerSystem |
        Select-Object Manufacturer, Model, SystemFamily |
        Format-List
}
catch {
    Write-Warning "Failed to read system info: $($_.Exception.Message)"
}

# -----------------------------
# 1.5) Silent NuGet + PSGallery prep + LSUClient install
# -----------------------------
try {
    # Safe temporary execution policy
    Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass -Force -Confirm:$false

    # TLS 1.2 for older PS
    if ($PSVersionTable.PSVersion.Major -lt 6) {
        try { [Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12 } catch {}
    }

    # Ensure PSGallery exists
    $repo = Get-PSRepository -Name PSGallery -ErrorAction SilentlyContinue
    if (-not $repo) {
        Register-PSRepository -Default -ErrorAction SilentlyContinue
        $repo = Get-PSRepository -Name PSGallery -ErrorAction SilentlyContinue
    }

    # Make PSGallery trusted (prevents Y/N prompt)
    if ($repo -and $repo.InstallationPolicy -ne 'Trusted') {
        Set-PSRepository -Name PSGallery -InstallationPolicy Trusted -ErrorAction SilentlyContinue
    }

    # SILENT NuGet bootstrap
    Install-PackageProvider -Name NuGet `
        -RequiredVersion 2.8.5.201 `
        -Force -ForceBootstrap -Confirm:$false `
        -ErrorAction Stop | Out-Null

    # Install LSUClient module silently
    Write-Host "Installing LSUClient module silently..." -ForegroundColor Yellow
    Install-Module LSUClient -Force -Scope AllUsers -Confirm:$false -ErrorAction Stop

    Write-Host "LSUClient module installed." -ForegroundColor Green
}
catch {
    Write-Warning "Module prep/install step encountered an issue: $($_.Exception.Message)"
}

# -----------------------------
# 2) LS Update information
# -----------------------------
Write-Host "`n=== LS Update Information ===" -ForegroundColor Cyan

# Try importing LSUClient now that we installed it
$lsuLoaded = $false
try {
    Import-Module LSUClient -ErrorAction Stop
    $lsuLoaded = $true
    Write-Host "LSUClient module loaded successfully." -ForegroundColor Green
}
catch {
    Write-Warning "LSUClient module could not be loaded: $($_.Exception.Message)"
}

# Retrieve updates
try {
    if ($lsuLoaded -and (Get-Command Get-LSUpdate -ErrorAction SilentlyContinue)) {

        $updates = Get-LSUpdate | Tee-Object -Variable updates

        if ($updates) {
            Write-Host "`nLS Update list captured in `$updates variable." -ForegroundColor Green
            Write-Host "Updates installed successfully." -ForegroundColor Yellow

            # Restart prompt
            $resp = Read-Host -Prompt "Restart computer now? (Y/N)"
            if ($resp -match '^(?i)Y$') {
                Write-Host "Restarting computer..." -ForegroundColor Cyan
                Restart-Computer -Force
            }
            else {
                Write-Host "Exiting without restart." -ForegroundColor Cyan
            }
        }
        else {
            Write-Host "No updates were retrieved." -ForegroundColor Yellow
        }
    }
    else {
        Write-Warning "Get-LSUpdate not available. LSUClient may not support this device."
    }
}
catch {
    Write-Warning "Failed to retrieve LS Update data: $($_.Exception.Message)"
}
finally {
    $ErrorActionPreference = 'Continue'
}

# Keep the window open when double-clicked
Read-Host -Prompt "Press Enter to exit"