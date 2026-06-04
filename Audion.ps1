<# 
    Silent Audio Default Switcher
    - Ensures NuGet provider exists
    - Ensures AudioDeviceCmdlets exists
    - Sets preferred Playback device
    - Sets preferred Recording device
    - No terminal output
#>

$ErrorActionPreference = 'Stop'
$ProgressPreference    = 'SilentlyContinue'
$WarningPreference     = 'SilentlyContinue'
$VerbosePreference     = 'SilentlyContinue'
$InformationPreference = 'SilentlyContinue'

try {
    # Ensure NuGet provider is installed
    if (-not (Get-PackageProvider -Name NuGet -ListAvailable -ErrorAction SilentlyContinue)) {
        Install-PackageProvider -Name NuGet -MinimumVersion 2.8.5.201 -Force -ForceBootstrap -Scope CurrentUser -ErrorAction Stop | Out-Null
    }

    # Ensure PowerShellGet is available enough to install module
    if (-not (Get-Command Install-Module -ErrorAction SilentlyContinue)) {
        exit 1
    }

    # Ensure AudioDeviceCmdlets is installed and imported
    if (-not (Get-Command Get-AudioDevice -ErrorAction SilentlyContinue)) {
        Install-Module -Name AudioDeviceCmdlets -Scope CurrentUser -Force -AllowClobber -ErrorAction Stop | Out-Null
    }

    Import-Module AudioDeviceCmdlets -Force -ErrorAction Stop | Out-Null

    function Get-DefaultAudioDevice {
        try {
            $defaultPlayback = Get-AudioDevice -List | Where-Object { $_.Type -eq 'Playback' -and $_.Default -eq $true } | Select-Object -First 1
            if ($defaultPlayback) {
                return $defaultPlayback.Name
            }

            $fallback = Get-CimInstance -Namespace root\cimv2 -ClassName Win32_SoundDevice -ErrorAction SilentlyContinue |
                Where-Object { $_.Status -eq 'OK' } |
                Select-Object -First 1

            return $fallback.Name
        } catch {
            return $null
        }
    }

    function Set-DefaultPlaybackByPriority {
        param(
            [string[]]$PreferredIds
        )

        $playbacks = Get-AudioDevice -List | Where-Object { $_.Type -eq 'Playback' }

        if (-not $playbacks) {
            return $false
        }

        $target = $null
        foreach ($id in $PreferredIds) {
            $candidate = $playbacks | Where-Object { $_.Name -like "*$id*" } | Select-Object -First 1
            if ($candidate) {
                $target = $candidate
                break
            }
        }

        if (-not $target) {
            return $false
        }

        Set-AudioDevice -Index $target.Index | Out-Null
        return $true
    }

    function Set-DefaultRecordingByPriority {
        param(
            [string[]]$PreferredIds
        )

        $recordings = Get-AudioDevice -List | Where-Object { $_.Type -eq 'Recording' }

        if (-not $recordings) {
            return $true
        }

        $target = $null
        foreach ($id in $PreferredIds) {
            $candidate = $recordings | Where-Object { $_.Name -like "*$id*" } | Select-Object -First 1
            if ($candidate) {
                $target = $candidate
                break
            }
        }

        if ($target) {
            Set-AudioDevice -Index $target.Index | Out-Null
        }

        return $true
    }

    $null = Get-DefaultAudioDevice

# NEW: Only match playback devices with the word "speaker"
$preferredPlaybackIds = @(
    "speaker"
)
    $preferredRecordingIds = @(
        "Microphone Array",
        "Microphone Array (Realtek(R) Audio)",
        "Microphone Array (Conexant High Definition Audio)",
        "Microphone Array (Intel(R) Display Audio)",
        "Microphone Array (Intel High Definition Audio)",
        "Microphone Array (AMD Audio Device)",
        "Microphone Array (NVIDIA Audio Device)",
        "Microphone Array (Intel(R) Smart Sound Technology for Digital Microphones)"
    )

    $playbackOk = Set-DefaultPlaybackByPriority -PreferredIds $preferredPlaybackIds
    if (-not $playbackOk) {
        exit 1
    }

    $null = Set-DefaultRecordingByPriority -PreferredIds $preferredRecordingIds

    exit 0
}
catch {
    exit 1
}
 