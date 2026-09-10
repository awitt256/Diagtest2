# Check and set default microphone input to 'Microphone Array' if not already set
$desiredMic = "Microphone Array"
$dockMic = "Microphone (HP USB-C Dock Audio Headset)"

# Get current default recording device
function Get-DefaultMicDevice {
    if (Get-Command Get-AudioDevice -ErrorAction SilentlyContinue) {
        return (Get-AudioDevice -List | Where-Object { $_.Type -eq 'Recording' -and $_.Default -eq $true }).Name
    } else {
        return $null
    }
}

function Set-DefaultMicDevice {
    param([string]$PartialName)
    if (Get-Command Set-AudioDevice -ErrorAction SilentlyContinue) {
        $target = Get-AudioDevice -List | Where-Object { $_.Type -eq 'Recording' -and $_.Name -like "*$PartialName*" }
        if ($target) {
            Set-AudioDevice -Index $target.Index | Out-Null
            Write-Host "Default microphone set to: $($target.Name)" -ForegroundColor Green
        } else {
            Write-Host "Could not find recording device matching: $PartialName" -ForegroundColor Red
        }
    } else {
        Write-Host "The AudioDeviceCmdlets PowerShell module is required (Install-Module -Name AudioDeviceCmdlets)" -ForegroundColor Yellow
    }
}

$defaultMic = Get-DefaultMicDevice
if ($defaultMic) {
    Write-Host "Current default microphone: $defaultMic" -ForegroundColor Cyan
    if ($defaultMic -like "*$desiredMic*") {
        Write-Host "Microphone input is already set to Microphone Array." -ForegroundColor Green
    } else {
        Write-Host "Microphone input is not Microphone Array. Attempting to switch..." -ForegroundColor Yellow
        try {
            Set-DefaultMicDevice -PartialName $desiredMic
        } catch {
            Write-Host "An error occurred while attempting to switch microphone devices: $($_.Exception.Message)" -ForegroundColor Red
            Write-Host "`nPress Enter to close the window..." -ForegroundColor Yellow
            Read-Host
            exit 1
        }
    }
} else {
    Write-Host "Could not determine current default microphone device." -ForegroundColor Red
}
# Ensure NuGet package provider is installed
if (-not (Get-PackageProvider -Name NuGet -ErrorAction SilentlyContinue)) {
    Write-Host "`nNuGet package provider not found. Attempting to install..." -ForegroundColor Yellow
    try {
        Install-PackageProvider -Name NuGet -Force -Scope CurrentUser -Verbose
        Import-PackageProvider -Name NuGet -Force
        if (-not (Get-PackageProvider -Name NuGet -ErrorAction SilentlyContinue)) {
            Write-Host "`nFailed to install NuGet package provider. Please try installing manually." -ForegroundColor Red
            Write-Host "Install-PackageProvider -Name NuGet -Force -Scope CurrentUser" -ForegroundColor Yellow
            Write-Host "`nPress Enter to exit..."
            Read-Host
            exit 1
        } else {
            Write-Host "`nNuGet package provider installed successfully! Continuing..." -ForegroundColor Green
        }
    } catch {
        Write-Host "`nError during NuGet installation: $($_.Exception.Message)" -ForegroundColor Red
        Write-Host "You may need to run PowerShell as Administrator or set script execution policy." -ForegroundColor Magenta
        Write-Host "`nPress Enter to exit..."
        Read-Host
        exit 1
    }
}


# Ensure AudioDeviceCmdlets module is installed at the very beginning
if (-not (Get-Command Get-AudioDevice -ErrorAction SilentlyContinue)) {
    Write-Host "`nAudioDeviceCmdlets module not found. Attempting to install..." -ForegroundColor Yellow
    try {
        Install-Module -Name AudioDeviceCmdlets -Scope CurrentUser -Force -AllowClobber -Verbose
        if (-not (Get-Command Get-AudioDevice -ErrorAction SilentlyContinue)) {
            Write-Host "`nFailed to install AudioDeviceCmdlets module. Please try installing manually:" -ForegroundColor Red
            Write-Host "Install-Module -Name AudioDeviceCmdlets -Scope CurrentUser" -ForegroundColor Yellow
            Write-Host "`nPress Enter to exit..."
            Read-Host
            exit 1
        } else {
            Write-Host "`nAudioDeviceCmdlets module installed successfully! Continuing..." -ForegroundColor Green
        }
    } catch {
        Write-Host "`nError during installation: $($_.Exception.Message)" -ForegroundColor Red
        Write-Host "You may need to run PowerShell as Administrator or set script execution policy." -ForegroundColor Magenta
        Write-Host "`nPress Enter to exit..."
        Read-Host
        exit 1
    }
}

# PowerShell script to check if current sound output is 'Headphones (HP USB-C Dock Audio Headset)' or 'Speakers (Realtek(R) Audio)' 
# If output is not Realtek, switch default device to Realtek

# Function to get current default audio output device's friendly name

# ...existing code...

function Get-DefaultAudioDevice {
    $default = Get-CimInstance -Namespace root\cimv2 -ClassName Win32_SoundDevice | Where-Object {
        $_.Status -eq "OK"
    }
    # Use Get-AudioDevice from AudioDeviceCmdlets if available for more precision
    if (Get-Command Get-AudioDevice -ErrorAction SilentlyContinue) {
        return (Get-AudioDevice -List | Where-Object { $_.Type -eq 'Playback' -and $_.Default -eq $true }).Name
    } else {
        # Fall back to WMI, which may not reflect the real default
        return $default[0].Name
    }
}

# Function to set default audio device to a given partial device name match
function Set-DefaultAudioDevice {
    param([string]$PartialName)
    if (Get-Command Set-AudioDevice -ErrorAction SilentlyContinue) {
        $target = Get-AudioDevice -List | Where-Object { $_.Type -eq 'Playback' -and $_.Name -like "*$PartialName*" }
        if ($target) {
            Set-AudioDevice -Index $target.Index | Out-Null
            Write-Host "Default audio device set to: $($target.Name)" -ForegroundColor Green
        } else {
            Write-Host "Could not find playback device matching: $PartialName" -ForegroundColor Red
        }
    } else {
        Write-Host "The AudioDeviceCmdlets PowerShell module is required (Install-Module -Name AudioDeviceCmdlets)" -ForegroundColor Yellow
    }
}

# Main execution
$defaultDevice = Get-DefaultAudioDevice

Write-Host "Current default audio device: $defaultDevice" -ForegroundColor Cyan

$hpDockId = "Headphones (HP USB-C Dock Audio Headset)"
$realtekId = "Speakers (Realtek(R) Audio)"

if ($defaultDevice -like "*$realtekId*") {
    Write-Host "Output is already using Realtek speakers." -ForegroundColor Green
} else {
    Write-Host "Output is not Realtek. Attempting to switch to Realtek speakers..." -ForegroundColor Yellow
    try {
        Set-DefaultAudioDevice -PartialName $realtekId
    } catch {
        Write-Host "An error occurred while attempting to switch audio devices: $($_.Exception.Message)" -ForegroundColor Red
        Write-Host "`nPress Enter to close the window..." -ForegroundColor Yellow
        Read-Host
        exit 1
    }
}


# ...existing code...

$realtekId = "Speakers (Realtek(R) Audio)"
# Get all active playback devices
$playbacks = Get-AudioDevice -List | Where-Object { $_.Type -eq 'Playback' }
$realtek = $playbacks | Where-Object { $_.Name -like "*$realtekId*" }

if ($realtek) {
    Set-AudioDevice -Index $realtek.Index | Out-Null
    Write-Host "Switched audio output to: $($realtek.Name)" -ForegroundColor Green
} else {
    Write-Host "Could not find a playback device containing:`n  $realtekId" -ForegroundColor Red
    Write-Host "`nAvailable playback devices on this system:" -ForegroundColor Yellow
    foreach ($dev in $playbacks) {
        Write-Host " - $($dev.Name)" -ForegroundColor Cyan
    }
    Write-Host "`nPlease check the device name in the script and try again." -ForegroundColor Magenta
    exit 1
    # Removed invalid catch block
Write-Host "`nOperation completed. Press Enter to close the window..."
