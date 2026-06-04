# ...existing code...

# Self-elevate if not running as admin
if (-not ([Security.Principal.WindowsPrincipal] [Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole(
    [Security.Principal.WindowsBuiltinRole]::Administrator)) {
    Start-Process -FilePath "powershell.exe" -ArgumentList "-ExecutionPolicy Bypass -File `"$PSCommandPath`"" -Verb RunAs
    exit
}

# Determine script folder (works when run from ISE or as file)
$scriptDir = if ($PSScriptRoot) { $PSScriptRoot } else { Split-Path -Path $MyInvocation.MyCommand.Definition -Parent }

function Launch-Exe {
    param([string]$exeName)

    # Prefer executable in the script directory, fallback to PATH
    $local = Join-Path $scriptDir $exeName
    if (Test-Path $local) {
        $pathToRun = $local
    } else {
        $cmd = Get-Command $exeName -ErrorAction SilentlyContinue
        if ($cmd) { $pathToRun = $cmd.Source } else { $pathToRun = $null }
    }

    if ($null -ne $pathToRun) {
        try {
            Start-Process -FilePath $pathToRun -Wait
        } catch {
            Write-Host ("Failed to start {0}`n{1}" -f $exeName, $_.Exception.Message)
        }
    } else {
        Write-Host "$exeName not found in script folder ($scriptDir) or in PATH. Skipping."
    }
}
# Get the computer manufacturer
$manufacturer = (Get-CimInstance -ClassName Win32_ComputerSystem).Manufacturer.Trim()
Write-Host "Detected manufacturer: $manufacturer"

switch ($manufacturer) {
    "Lenovo" {
        Launch-Exe "LenovoHK.EXE"
        $answer = Read-Host "Did the Lenovo Hotkeys install correctly? (Y/N)"
        if ($answer -notmatch '^(Y|y)') {
            Write-Host "Attempting LHK2 install..."
            Launch-Exe "LHK2.EXE"
        }
    }
    "HP" {
        Launch-Exe "13.EXE"
        Launch-Exe "69.EXE"

        $sfAnswer = Read-Host "Do you need to install the software framework driver? (Y/N)"
        if ($sfAnswer -match '^(Y|y)') {
            Launch-Exe "sf.EXE"
        } else {
            Read-Host "Press Enter to continue..."
        }
    }
    Default {
        Write-Host "Manufacturer $manufacturer not specifically handled."
        Read-Host "Press Enter to continue..."
    }
}

# ...existing code...