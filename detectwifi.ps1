Clear-Host
Write-Host "Network Adapter Check" -ForegroundColor Cyan
Write-Host "=====================" -ForegroundColor Cyan
Write-Host ""

function Show-AdapterSection {
    param(
        [string]$Title,
        [array]$Adapters
    )

    Write-Host $Title -ForegroundColor Cyan
    Write-Host (("-" * $Title.Length)) -ForegroundColor Cyan
    Write-Host ""

    if (-not $Adapters) {
        Write-Host "No adapters detected." -ForegroundColor Red
        Write-Host ""
        return
    }

    foreach ($adapter in $Adapters) {
        $profile = Get-NetConnectionProfile -InterfaceIndex $adapter.ifIndex -ErrorAction SilentlyContinue
        $active = $adapter.Status -eq "Up"

        Write-Host "Adapter detected:" -ForegroundColor Green
        Write-Host "  Name: $($adapter.Name)"
        Write-Host "  Description: $($adapter.InterfaceDescription)"
        Write-Host "  Adapter status: $($adapter.Status)"
        Write-Host "  Active: $(if ($active) { 'Yes' } else { 'No' })"

        if ($active -and $profile) {
            Write-Host "  Connected to network: Yes" -ForegroundColor Green
            Write-Host "  Network name: $($profile.Name)"
            Write-Host "  Network category: $($profile.NetworkCategory)"
        }
        else {
            Write-Host "  Connected to network: No" -ForegroundColor Yellow
        }

        Write-Host ""
    }
}

$allAdapters = Get-NetAdapter -Physical -ErrorAction SilentlyContinue

$wifiAdapters = $allAdapters | Where-Object {
    $_.InterfaceDescription -match 'Wireless|Wi-Fi|802\.11|WLAN' -or
    $_.Name -match 'Wi-Fi|Wireless|WLAN'
}

$ethernetAdapters = $allAdapters | Where-Object {
    $_.InterfaceDescription -notmatch 'Wireless|Wi-Fi|802\.11|WLAN|Bluetooth' -and
    $_.Name -notmatch 'Wi-Fi|Wireless|WLAN|Bluetooth'
}

Show-AdapterSection -Title "Wi-Fi Adapters" -Adapters $wifiAdapters
Show-AdapterSection -Title "Ethernet Adapters" -Adapters $ethernetAdapters

Read-Host "Press Enter to close"
