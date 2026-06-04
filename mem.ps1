# Get memory info from Win32_OperatingSystem (values in KB)
$os = Get-CimInstance Win32_OperatingSystem

$totalKB = [double]$os.TotalVisibleMemorySize
$freeKB  = [double]$os.FreePhysicalMemory
$usedKB  = $totalKB - $freeKB

# Convert KB → GB
$totalGB = [math]::Round(($totalKB * 1KB) / 1GB, 2)
$freeGB  = [math]::Round(($freeKB  * 1KB) / 1GB, 2)
$usedGB  = [math]::Round(($usedKB  * 1KB) / 1GB, 2)

# Percentages
$pctUsed = [math]::Round(($usedKB / $totalKB) * 100, 2)
$pctFree = [math]::Round(($freeKB / $totalKB) * 100, 2)

# Display results
Write-Host "Total Memory (GB): $totalGB"
Write-Host "Used Memory  (GB): $usedGB"
Write-Host "Free Memory  (GB): $freeGB"
Write-Host "Percent Used:      $pctUsed`%"
Write-Host "Percent Free:      $pctFree`%"

# Prevent auto-close if script is double-clicked
Write-Host "`nPress any key to exit..."
$null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")