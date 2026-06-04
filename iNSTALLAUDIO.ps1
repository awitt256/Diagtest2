# Built by Anthony Witt

Write-Host "BUILT BY ANTHONY WITT 2026" -ForegroundColor Cyan

# PowerShell script to silently install NuGet and AudioDeviceCmdlets with clear success/failure output

# Make sure we use TLS 1.2 (needed on some systems to reach PSGallery)
[Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12

# Progress variables
$nugetActivity = "Installing NuGet provider"

# Ensure NuGet provider is installed (silently, with progress)
try {
    Write-Progress -Activity $nugetActivity -Status "Checking for existing NuGet provider..." -PercentComplete 10

    if (-not (Get-PackageProvider -Name NuGet -ListAvailable -ErrorAction SilentlyContinue)) {
        Write-Host "NuGet provider not found. Installing..." -ForegroundColor Yellow
        Write-Progress -Activity $nugetActivity -Status "Downloading and installing NuGet provider..." -PercentComplete 40

        Install-PackageProvider -Name NuGet `
            -MinimumVersion 2.8.5.201 `
            -Scope CurrentUser `
            -Force `
            -ForceBootstrap `
            -Confirm:$false `
            -ErrorAction Stop | Out-Null

        Write-Progress -Activity $nugetActivity -Status "NuGet provider installed." -PercentComplete 90
        Write-Host "NuGet provider installed successfully." -ForegroundColor Green
    }
    else {
        Write-Progress -Activity $nugetActivity -Status "NuGet provider already installed." -PercentComplete 90
        Write-Host "NuGet provider is already installed." -ForegroundColor Green
    }

    Write-Progress -Activity $nugetActivity -Status "Completed." -PercentComplete 100 -Completed
} catch {
    Write-Progress -Activity $nugetActivity -Status "Failed." -PercentComplete 100 -Completed
    Write-Host "INSTALLATION FAIL (NuGet provider)" -ForegroundColor Red
    exit 1
}

# Ensure PSGallery is trusted so Install-Module won't prompt
try {
    $psGallery = Get-PSRepository -Name 'PSGallery' -ErrorAction SilentlyContinue
    if (-not $psGallery) {
        Register-PSRepository -Default -ErrorAction Stop
        $psGallery = Get-PSRepository -Name 'PSGallery' -ErrorAction Stop
    }

    if ($psGallery.InstallationPolicy -ne 'Trusted') {
        Set-PSRepository -Name 'PSGallery' -InstallationPolicy Trusted -ErrorAction Stop
    }
} catch {
    # Failed to set PSGallery as trusted, continue anyway
}

# Install AudioDeviceCmdlets module for current user (silently, always accept)
try {
    Write-Host "Installing AudioDeviceCmdlets module..." -ForegroundColor Yellow

    Install-Module -Name AudioDeviceCmdlets `
        -Scope CurrentUser `
        -Force `
        -AllowClobber `
        -Confirm:$false `
        -ErrorAction Stop | Out-Null

    Write-Host "INSTALLATION SUCCESSFUL" -ForegroundColor Green
    exit 0
} catch {
    Write-Host "INSTALLATION FAIL (AudioDeviceCmdlets)" -ForegroundColor Red
    exit 1
}