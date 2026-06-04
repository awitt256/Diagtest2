# PowerShell script: Download NuGet provider and AudioDeviceCmdlets module into a folder called "AUDIO" on Desktop

# Resolve Desktop path and define "AUDIO" folder
$desktop = [Environment]::GetFolderPath("Desktop")
$targetFolder = Join-Path $desktop 'AUDIO'
if (-not (Test-Path $targetFolder)) { New-Item -Path $targetFolder -ItemType Directory | Out-Null }

Write-Host "`nTarget download folder: $targetFolder" -ForegroundColor Cyan

# Download NuGet provider (for PowerShell package management)
Write-Host "Downloading NuGet provider if not present..." -ForegroundColor Yellow
if (-not (Get-PackageProvider -Name NuGet -ListAvailable -ErrorAction SilentlyContinue)) {
    try {
        Install-PackageProvider -Name NuGet -MinimumVersion 2.8.5.201 -Force -Scope CurrentUser -ErrorAction Stop
        Write-Host "NuGet provider installed successfully." -ForegroundColor Green
    } catch {
        Write-Host "Failed to install NuGet provider: $($_.Exception.Message)" -ForegroundColor Red
        exit 1
    }
} else {
    Write-Host "NuGet provider already present." -ForegroundColor Green
}

# Download AudioDeviceCmdlets module package content only (does not import/install system-wide)
Write-Host "Downloading AudioDeviceCmdlets module (no system-wide install)..." -ForegroundColor Yellow
try {
    Save-Module -Name AudioDeviceCmdlets -Path $targetFolder -Force
    Write-Host "AudioDeviceCmdlets module downloaded to $targetFolder." -ForegroundColor Green
} catch {
    Write-Host "Failed to download AudioDeviceCmdlets: $($_.Exception.Message)" -ForegroundColor Red
    exit 1
}

Write-Host "`nAll done! NuGet provider is installed, and AudioDeviceCmdlets module is saved to:" -ForegroundColor Cyan
Write-Host "  $targetFolder" -ForegroundColor Yellow