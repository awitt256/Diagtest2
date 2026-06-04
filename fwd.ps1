# Check for HP Software Framework Folder
# Simple detection script for C:\Program Files (x86)\HP\HP Software Framework

Write-Host "`n========== HP SOFTWARE FRAMEWORK FOLDER DETECTION ==========" -ForegroundColor Cyan

# Define the path to check
$folderPath = "C:\Program Files (x86)\HP\Software Framework"

Write-Host "`nChecking for folder: $folderPath" -ForegroundColor White

# Check if the folder exists
if (Test-Path -Path $folderPath -PathType Container) {
    Write-Host "`n✓ FOLDER FOUND" -ForegroundColor Green
    Write-Host "`nThe folder exists at: $folderPath" -ForegroundColor Green
    
    # List contents if folder exists
    Write-Host "`nFolder contents:" -ForegroundColor White
    $items = Get-ChildItem -Path $folderPath -ErrorAction SilentlyContinue
    if ($items) {
        foreach ($item in $items) {
            $type = if ($item.PSIsContainer) { "[FOLDER]" } else { "[FILE]" }
            Write-Host "  $type $($item.Name)" -ForegroundColor Gray
        }
    } else {
        Write-Host "  (folder is empty)" -ForegroundColor Gray
    }
} else {
    Write-Host "`n✗ SOFTWARE FRAMEWORK NOT INSTALLED" -ForegroundColor Red
    Write-Host "`nThe folder does not exist at: $folderPath" -ForegroundColor Red

    # Check if partial path exists
    Write-Host "`nChecking if parent directories exist..." -ForegroundColor Yellow

    $hpPath = "C:\Program Files (x86)\HP"
    if (Test-Path -Path $hpPath) {
        Write-Host "  ✓ Found: C:\Program Files (x86)\HP" -ForegroundColor Green
        Write-Host "`n  Folders in HP directory:" -ForegroundColor White
        $subFolders = Get-ChildItem -Path $hpPath -Directory -ErrorAction SilentlyContinue
        if ($subFolders) {
            foreach ($folder in $subFolders) {
                Write-Host "    [FOLDER] $($folder.Name)" -ForegroundColor Gray
            }
        } else {
            Write-Host "    (no subfolders)" -ForegroundColor Gray
        }
    } else {
        Write-Host "  ✗ Not found: C:\Program Files (x86)\HP" -ForegroundColor Red

        $progPath = "C:\Program Files (x86)"
        if (Test-Path -Path $progPath) {
            Write-Host "  ✓ Found: C:\Program Files (x86)" -ForegroundColor Green
        } else {
            Write-Host "  ✗ Not found: C:\Program Files (x86)" -ForegroundColor Red
        }
    }

    # Folder not found: run D:\sf.exe if available
    Write-Host "`n========================================================" -ForegroundColor Cyan
    Write-Host "Attempting to run D:\sf.exe (if present)" -ForegroundColor Yellow
    Write-Host "========================================================" -ForegroundColor Cyan
    Write-Host ""
    $dSf = 'D:\sf.exe'
    if (Test-Path -Path $dSf) {
        try {
            & $dSf
        } catch {
            Write-Host "`n✗ Error running D:\sf.exe: $($_.Exception.Message)" -ForegroundColor Red
        }
    } else {
        Write-Host "D:\sf.exe not found; skipping execution." -ForegroundColor Gray
    }
}

Write-Host "`n========================================================" -ForegroundColor Cyan
Write-Host "`nPress Enter to exit..." -ForegroundColor Gray
Read-Host
