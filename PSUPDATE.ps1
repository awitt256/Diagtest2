<#
.SYNOPSIS
    Automatically updates PowerShell 7 to the latest stable version using Winget.
.DESCRIPTION
    Checks if Winget is available, finds the latest Microsoft.PowerShell package,
    and runs a silent, automated upgrade if a newer version exists.
#>

$PackageId = "Microsoft.PowerShell"

# 1. Verify Winget availability
if (-not (Get-Command winget -ErrorAction SilentlyContinue)) {
    Write-Error "Winget is not installed or available in the current environment context."
    Exit 1
}

# 2. Check for available upgrades
Write-Output "Checking for PowerShell 7 updates..."
$checkUpdate = winget upgrade --id $PackageId | Out-String

if ($checkUpdate -match "No available upgrade found" -or $checkUpdate -match "No installed package found") {
    Write-Output "PowerShell 7 is already up to date or not installed via Winget."
}
else {
    Write-Output "Newer version detected. Upgrading PowerShell 7..."
    
    # 3. Execute silent upgrade
    $arguments = @(
        "upgrade",
        "--id", $PackageId,
        "--silent",
        "--accept-source-agreements",
        "--accept-package-agreements"
    )
    
    Start-Process -FilePath "winget.exe" -ArgumentList $arguments -NoNewWindow -Wait
    Write-Output "Upgrade process completed successfully."
}
