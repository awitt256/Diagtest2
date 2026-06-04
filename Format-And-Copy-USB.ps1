# USB Format and Copy Script
# Formats drives D: - O: (excluding G:) and copies Windows-Testing-Tool to them

$ErrorActionPreference = "Continue"

Write-Host "Script starting..." -ForegroundColor Cyan

try {
    # Run as Administrator check
    Write-Host "Checking admin privileges..." -ForegroundColor Yellow
    
    if (-NOT ([Security.Principal.WindowsPrincipal] [Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole] "Administrator")) {
        Write-Host "ERROR: This script requires Administrator privileges." -ForegroundColor Red
        Write-Host "Please close this and run the .bat file instead, or right-click the .ps1 and choose 'Run as Administrator'." -ForegroundColor Yellow
        Read-Host "`nPress Enter to exit"
        exit
    }
    
    Write-Host "Admin check passed." -ForegroundColor Green
    
    # Source directory
    $SourceDir = "C:\Users\Anthony\OneDrive - Close The Loop Inc\Documents\WinTest 3.06"
    
    Write-Host "Checking source directory: $SourceDir" -ForegroundColor Yellow
    
    # Check if source directory exists
    if (-NOT (Test-Path $SourceDir)) {
        Write-Host "ERROR: Source directory not found:" -ForegroundColor Red
        Write-Host "  $SourceDir" -ForegroundColor Red
        Write-Host "Please verify the path and try again." -ForegroundColor Yellow
        Read-Host "`nPress Enter to exit"
        exit
    }
    
    Write-Host "Source directory found." -ForegroundColor Green
    
    # Get list of available drives (D: to O:, excluding G:)
    $DrivesToCheck = @("D", "E", "F", "H", "I", "J", "K", "L", "M", "N", "O")
    $AvailableDrives = @()
    
    Write-Host "`n=== USB Drive Scanner ===" -ForegroundColor Cyan
    Write-Host "Scanning for available drives D: - O: (excluding G:)...`n"
    
    foreach ($Drive in $DrivesToCheck) {
        $DrivePath = "$($Drive):"
        if (Test-Path $DrivePath) {
            try {
                $DriveLetter = Get-Volume -DriveLetter $Drive -ErrorAction SilentlyContinue
                if ($DriveLetter) {
                    $AvailableDrives += $DrivePath
                    Write-Host "Found: $DrivePath ($($DriveLetter.FileSystemLabel))" -ForegroundColor Green
                }
            } catch {
                Write-Host "Could not read drive $Drive`: $_" -ForegroundColor Yellow
            }
        }
    }
    
    if ($AvailableDrives.Count -eq 0) {
        Write-Host "ERROR: No USB drives found in the D: - O: range." -ForegroundColor Red
        Write-Host "Make sure your USB drives are plugged in and assigned a letter in that range." -ForegroundColor Yellow
        Read-Host "`nPress Enter to exit"
        exit
    }
    
    Write-Host "`nTotal drives found: $($AvailableDrives.Count)" -ForegroundColor Cyan
    Write-Host "`nDrives to format:" -ForegroundColor Yellow
    $AvailableDrives | ForEach-Object { Write-Host "  - $_" }
    
    Write-Host "`nWARNING: This will format all listed drives!" -ForegroundColor Red
    $Confirm = Read-Host "Do you want to proceed with formatting and copying? (yes/no)"
    
    if ($Confirm -ne "yes") {
        Write-Host "Operation cancelled." -ForegroundColor Yellow
        Read-Host "`nPress Enter to exit"
        exit
    }
    
    # Format and copy to each drive
    Write-Host "`n=== Starting Format and Copy Process ===" -ForegroundColor Cyan
    
    foreach ($Drive in $AvailableDrives) {
        Write-Host "`nProcessing $Drive..." -ForegroundColor Cyan
        
        try {
            # Format the drive (quick format, NTFS)
            Write-Host "  Formatting $Drive (NTFS)..." -ForegroundColor Yellow
            $DriveLetter = $Drive.Substring(0, 1)
            
            Format-Volume -DriveLetter $DriveLetter -FileSystem NTFS -NewFileSystemLabel "USB_DRIVE" -Confirm:$false -Force
            
            Write-Host "  Format complete" -ForegroundColor Green
            
            # Copy files
            Write-Host "  Copying files from source to $Drive..." -ForegroundColor Yellow
            
            $ItemsToCopy = Get-ChildItem -Path $SourceDir -ErrorAction SilentlyContinue
            
            if ($ItemsToCopy.Count -eq 0) {
                Write-Host "  ERROR: No files found in source directory: $SourceDir" -ForegroundColor Red
                continue
            }
            
            Write-Host "  Found $($ItemsToCopy.Count) items to copy" -ForegroundColor White
            
            $CopyErrors = $false
            foreach ($Item in $ItemsToCopy) {
                try {
                    $DestPath = Join-Path -Path $Drive -ChildPath $Item.Name
                    if ($Item.PSIsContainer) {
                        Copy-Item -Path $Item.FullName -Destination $DestPath -Recurse -Force -ErrorAction Stop
                    } else {
                        Copy-Item -Path $Item.FullName -Destination $DestPath -Force -ErrorAction Stop
                    }
                    Write-Host "    - Copied: $($Item.Name)" -ForegroundColor White
                } catch {
                    Write-Host "    ERROR copying $($Item.Name): $_" -ForegroundColor Red
                    $CopyErrors = $true
                }
            }
            
            # Verify copy
            $DriveItems = @(Get-ChildItem -Path $Drive -ErrorAction SilentlyContinue)
            if ($DriveItems.Count -gt 0) {
                Write-Host "  Copy complete for $Drive ($($DriveItems.Count) items)" -ForegroundColor Green
            } else {
                Write-Host "  ERROR: Copy verification failed - no items found on drive after copy" -ForegroundColor Red
            }
            
        } catch {
            Write-Host "  ERROR processing $Drive`: $_" -ForegroundColor Red
        }
    }
    
    Write-Host "`n=== Process Complete ===" -ForegroundColor Cyan
    Write-Host "All selected drives have been formatted and populated." -ForegroundColor Green

} catch {
    Write-Host "`nFATAL ERROR: $_" -ForegroundColor Red
    Write-Host $_.Exception.StackTrace -ForegroundColor Red
}

Write-Host "`n----------------------------------------" -ForegroundColor White
Write-Host "Script finished. Review the output above." -ForegroundColor Cyan
Write-Host "----------------------------------------" -ForegroundColor White
Read-Host "`nPress Enter to close this window"