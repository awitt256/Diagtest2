# Get Serial Number
$sn = (Get-CimInstance -ClassName Win32_BIOS).SerialNumber
Write-Host "Getting SN: $sn"

# Confirm SN Match
$snMatch = Read-Host "Does SN match? (Y/N)"
if ($snMatch -ieq "Y") {
    # Get System SKU
    $sku = (Get-CimInstance -ClassName Win32_ComputerSystem).SystemSKUNumber
    Write-Host "Getting System SKU: $sku"
    
    # Confirm SKU Match
    $skuMatch = Read-Host "Does SKU match? (Y/N)"
    if ($skuMatch -ieq "Y") {
        Write-Host "SN and SKU confirmed. Running your script..."
        # --- Place your next script or logic here ---
    }
    else {
        Write-Host "SKU did not match. Exiting."
    }
}
else {
    Write-Host "SN did not match. Exiting."
}
