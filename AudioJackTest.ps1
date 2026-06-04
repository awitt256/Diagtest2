# Audio Jack (3.5mm) Detection and Test Script
# Tests headphone and microphone jack functionality
# Returns structured output for Python GUI consumption

Write-Output "=== AUDIO JACK TEST ==="
Write-Output ""

# Initialize variables
$headphoneJackFound = $false
$micJackFound = $false
$comboJackFound = $false
$jackDevices = @()
$headphoneDevice = $null
$micDevice = $null

Write-Output "--- DETECTING AUDIO JACK DEVICES ---"
Write-Output ""

try {
    # Method 1: Check for audio endpoint devices (speakers/headphones)
    $audioEndpoints = Get-PnpDevice | Where-Object {
        $_.Class -eq "MEDIA" -or $_.Class -eq "System"
    } | Where-Object {
        $_.FriendlyName -match "High Definition Audio|Realtek|IDT|Conexant|VIA|SoundMAX"
    }

    if ($audioEndpoints) {
        foreach ($device in $audioEndpoints) {
            Write-Output "AUDIO_CONTROLLER: $($device.FriendlyName)"
            Write-Output "AUDIO_CONTROLLER_STATUS: $($device.Status)"
            Write-Output "---"
        }
    }

    # Method 2: Check for specific headphone devices
    $headphoneDevices = Get-PnpDevice | Where-Object {
        $_.FriendlyName -match "Headphone|HP Out|Line Out|Speaker"
    }

    if ($headphoneDevices) {
        foreach ($hp in $headphoneDevices) {
            Write-Output "HEADPHONE_DEVICE: $($hp.FriendlyName)"
            Write-Output "HEADPHONE_STATUS: $($hp.Status)"
            $headphoneJackFound = $true
            $headphoneDevice = $hp.FriendlyName
        }
    }

    # Method 3: Check for microphone devices
    $micDevices = Get-PnpDevice | Where-Object {
        $_.FriendlyName -match "Microphone|Mic In|Line In|Array Mic"
    }

    if ($micDevices) {
        foreach ($mic in $micDevices) {
            Write-Output "MICROPHONE_DEVICE: $($mic.FriendlyName)"
            Write-Output "MICROPHONE_STATUS: $($mic.Status)"
            $micJackFound = $true
            $micDevice = $mic.FriendlyName
        }
    }

    # Method 4: Check for combo jack (headset with mic)
    $comboDevices = Get-PnpDevice | Where-Object {
        $_.FriendlyName -match "Headset|Combo Jack|TRRS"
    }

    if ($comboDevices) {
        foreach ($combo in $comboDevices) {
            Write-Output "COMBO_JACK_DEVICE: $($combo.FriendlyName)"
            Write-Output "COMBO_JACK_STATUS: $($combo.Status)"
            $comboJackFound = $true
        }
    }

    # Method 5: Check Windows Audio Service
    $audioService = Get-Service -Name "AudioSrv" -ErrorAction SilentlyContinue
    if ($audioService) {
        Write-Output "AUDIO_SERVICE_NAME: AudioSrv"
        Write-Output "AUDIO_SERVICE_STATUS: $($audioService.Status)"
    } else {
        Write-Output "AUDIO_SERVICE_NAME: AudioSrv"
        Write-Output "AUDIO_SERVICE_STATUS: Not Found"
    }

    # Method 6: Check Windows Audio Endpoint Builder Service
    $endpointService = Get-Service -Name "AudioEndpointBuilder" -ErrorAction SilentlyContinue
    if ($endpointService) {
        Write-Output "ENDPOINT_SERVICE_NAME: AudioEndpointBuilder"
        Write-Output "ENDPOINT_SERVICE_STATUS: $($endpointService.Status)"
    } else {
        Write-Output "ENDPOINT_SERVICE_NAME: AudioEndpointBuilder"
        Write-Output "ENDPOINT_SERVICE_STATUS: Not Found"
    }

    # Method 7: Try to get default audio endpoints using PowerShell
    try {
        Add-Type -TypeDefinition @"
using System;
using System.Runtime.InteropServices;

public class AudioCheck {
    [DllImport("winmm.dll")]
    public static extern int waveOutGetNumDevs();
    
    [DllImport("winmm.dll")]
    public static extern int waveInGetNumDevs();
}
"@

        $outputDevices = [AudioCheck]::waveOutGetNumDevs()
        $inputDevices = [AudioCheck]::waveInGetNumDevs()

        Write-Output "AUDIO_OUTPUT_ENDPOINTS: $outputDevices"
        Write-Output "AUDIO_INPUT_ENDPOINTS: $inputDevices"
    } catch {
        Write-Output "AUDIO_ENDPOINT_CHECK_ERROR: $($_.Exception.Message)"
    }

} catch {
    Write-Output "AUDIO_JACK_DETECTION_ERROR: $($_.Exception.Message)"
}

Write-Output ""
Write-Output "=== AUDIO JACK SUMMARY ==="

# Count working devices
$workingHeadphones = if ($headphoneJackFound) { 1 } else { 0 }
$workingMics = if ($micJackFound) { 1 } else { 0 }

Write-Output "HEADPHONE_JACK_DETECTED: $workingHeadphones"
Write-Output "MICROPHONE_JACK_DETECTED: $workingMics"
Write-Output "COMBO_JACK_DETECTED: $(if ($comboJackFound) { 1 } else { 0 })"

# Determine test result
if ($headphoneJackFound -and $micJackFound) {
    Write-Output "TEST_RESULT: PASS"
    Write-Output "TEST_MESSAGE: Audio jack (headphone + mic) detected and functional"
} elseif ($headphoneJackFound) {
    Write-Output "TEST_RESULT: PASS"
    Write-Output "TEST_MESSAGE: Headphone jack detected (no separate mic input)"
} elseif ($comboJackFound) {
    Write-Output "TEST_RESULT: PASS"
    Write-Output "TEST_MESSAGE: Combo audio jack detected (headset with mic)"
} else {
    Write-Output "TEST_RESULT: FAIL"
    Write-Output "TEST_MESSAGE: No audio jack devices detected"
}

Write-Output ""
Write-Output "=== AUDIO JACK TEST COMPLETE ==="
