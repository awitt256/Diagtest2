Write-Host "AUDIO INPUT CHANGER - BUILT BY ANTHONY WITT (2026)" -ForegroundColor Cyan


# PowerShell script to check if current sound output is 'Headphones (HP USB-C Dock Audio Headset)' or 'Speakers (Realtek(R) Audio)' 
 # If output is not Realtek, switch default device to Realtek
 
 # Function to get current default audio output device's friendly name
# PowerShell script to check if current sound output is 'Headphones (HP USB-C Dock Audio Headset)' or 'Speakers (Realtek(R) Audio)' 
# If output is not Realtek, switch default device to Realtek

# Function to get current default audio output device's friendly name
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

$preferredIds = @(
    "Speaker/Headphone",
    "SpeakerS/Headphones",
    "Speakers",
    "Speaker",
    "Speaker/Headphone (Realtek(R) Audio)",
    "Speakers (Realtek(R) Audio)",
    "Speakers (Realtek High Definition Audio)",
    "Speakers Realtek High Definition Audio",
    "Conexant",
    "Conexant High Definition Audio",
    "Intel HD Audio",
    "Intel High Definition Audio",
    "Intel(R) Display Audio",
    "HP Audio",
    "AMD Audio",
    "AMD Audio Device",
    "AMD High Definition Audio Device",
    "NVIDIA High Definition Audio",
    "NVIDIA Audio",
    "NVIDIA Virtual Audio Device"
)

# Get all active playback devices
$playbacks = Get-AudioDevice -List | Where-Object { $_.Type -eq 'Playback' }

$target = $null
foreach ($id in $preferredIds) {
    $candidate = $playbacks | Where-Object { $_.Name -like "*$id*" }
    if ($candidate) {
        $target = $candidate
        break
    }
}

if ($target) {
    Set-AudioDevice -Index $target.Index | Out-Null
    Write-Host "Switched audio output (speakers) to: $($target.Name)" -ForegroundColor Green
} else {
    Write-Host "Could not find a playback device containing any of:" -ForegroundColor Red
    foreach ($id in $preferredIds) {
        Write-Host "  $id" -ForegroundColor Red
    }
    Write-Host "`nAvailable playback devices on this system:" -ForegroundColor Yellow
    foreach ($dev in $playbacks) {
        Write-Host " - $($dev.Name)" -ForegroundColor Cyan
    }
    Write-Host "`nPlease check the device names in the script and try again." -ForegroundColor Magenta
    exit 1
}

# Set default recording (input) device to Microphone Array when available
$preferredInputIds = @(
    "Microphone Array",
    "Microphone Array (Realtek(R) Audio)",
    "Microphone Array (Conexant High Definition Audio)",
    "Microphone Array (Intel(R) Display Audio)",
    "Microphone Array (Intel High Definition Audio)",
    "Microphone Array (AMD Audio Device)",
    "Microphone Array (NVIDIA Audio Device)",
    "Microphone Array (Intel(R) Smart Sound Technology for Digital Microphones)"
)

$recordings = Get-AudioDevice -List | Where-Object { $_.Type -eq 'Recording' }
$inputTarget = $null
foreach ($id in $preferredInputIds) {
    $candidate = $recordings | Where-Object { $_.Name -like "*$id*" }
    if ($candidate) {
        $inputTarget = $candidate
        break
    }
}

if ($inputTarget) {
    Set-AudioDevice -Index $inputTarget.Index | Out-Null
    Write-Host "Switched audio input (microphone) to: $($inputTarget.Name)" -ForegroundColor Green
} else {
    Write-Host "No preferred 'Microphone Array' input device was found. Leaving current input device unchanged." -ForegroundColor Yellow
}

# Try to auto-install the AudioDeviceCmdlets if missing and show progress.
if (-not (Get-Command Get-AudioDevice -ErrorAction SilentlyContinue)) {
    Write-Host "`nAudioDeviceCmdlets module not found. Attempting to install..." -ForegroundColor Yellow
    try {
        # Show install progress (may prompt user confirmation)
        Install-Module -Name AudioDeviceCmdlets -Scope CurrentUser -Force -AllowClobber -Verbose
        if (Get-Command Get-AudioDevice -ErrorAction SilentlyContinue) {
            Write-Host "`nAudioDeviceCmdlets module installed successfully!" -ForegroundColor Green
            Write-Host "Please re-run this script." -ForegroundColor Yellow
        } else {
            Write-Host "`nFailed to install AudioDeviceCmdlets module." -ForegroundColor Red
            Write-Host "Install manually via:`nInstall-Module -Name AudioDeviceCmdlets -Scope CurrentUser" -ForegroundColor Yellow
        }
    } catch {
        Write-Host "`nError during installation: $($_.Exception.Message)" -ForegroundColor Red
        Write-Host "You may need to run PowerShell as Administrator or set script execution policy." -ForegroundColor Magenta
    }
    exit 1
} else {
    Write-Host "`nOperation completed successfully." -ForegroundColor Green
    exit 0
}