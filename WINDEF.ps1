# Self-elevate if not running as admin
if (-not ([Security.Principal.WindowsPrincipal] [Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole(
    [Security.Principal.WindowsBuiltinRole]::Administrator)) {
    
    if ($PSCommandPath) {
        Start-Process -FilePath "powershell.exe" -ArgumentList "-ExecutionPolicy Bypass -File `"$PSCommandPath`"" -Verb RunAs
        exit
    } else {
        Write-Host "Please run this script as Administrator" -ForegroundColor Red
        pause
        exit
    }
}

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Windows Defender Update & Scan Script" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Check if Windows Defender is running
Write-Host "[1/3] Checking Windows Defender status..." -ForegroundColor Yellow
$defenderStatus = Get-MpComputerStatus

if ($defenderStatus.AntivirusEnabled -eq $false) {
    Write-Host "ERROR: Windows Defender is not enabled!" -ForegroundColor Red
    pause
    exit
}

Write-Host "Windows Defender is enabled and running." -ForegroundColor Green
Write-Host ""

# Update Windows Defender signatures
Write-Host "[2/3] Updating Windows Defender definitions..." -ForegroundColor Yellow
try {
    Update-MpSignature -ErrorAction Stop
    Write-Host "Defender definitions updated successfully!" -ForegroundColor Green
    
    # Show current signature version
    $sigVersion = (Get-MpComputerStatus).AntivirusSignatureVersion
    Write-Host "Current signature version: $sigVersion" -ForegroundColor Cyan
} catch {
    Write-Host "WARNING: Failed to update definitions - $($_.Exception.Message)" -ForegroundColor Red
    Write-Host "Continuing with scan anyway..." -ForegroundColor Yellow
}
Write-Host ""

# Run quick system scan
Write-Host "[3/3] Starting quick system scan..." -ForegroundColor Yellow
Write-Host "Scan started at: $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')" -ForegroundColor Cyan
Write-Host ""

try {
    Start-MpScan -ScanType QuickScan -ErrorAction Stop
    Write-Host ""
    Write-Host "Scan completed successfully!" -ForegroundColor Green
    
    # Check for threats
    $threats = Get-MpThreat
    if ($threats.Count -gt 0) {
        Write-Host ""
        Write-Host "WARNING: $($threats.Count) threat(s) detected!" -ForegroundColor Red
        $threats | ForEach-Object {
            Write-Host "  - $($_.ThreatName)" -ForegroundColor Yellow
        }
    } else {
        Write-Host "No threats detected." -ForegroundColor Green
    }
    
} catch {
    Write-Host "ERROR: Scan failed - $($_.Exception.Message)" -ForegroundColor Red
}

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Script completed at: $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""
pause