<#
.SYNOPSIS
  Ensures winget is present; if not, installs it (via App Installer + deps) and then
  installs PassMark PerformanceTest 11.1.1008 silently from the Microsoft Store.

.NOTES
  - Requires Windows 10 1809+ or Windows 11.
  - Internet is needed the *first time* if winget/App Installer are missing.
  - Logs to C:\ProgramData\WingetLogs\PerfTest_setup.log
#>

# -----------------------
#   Admin / Logging
# -----------------------
$ErrorActionPreference = 'Stop'

# Auto-elevate if needed
$curr = [Security.Principal.WindowsIdentity]::GetCurrent()
$principal = New-Object Security.Principal.WindowsPrincipal($curr)
if (-not $principal.IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)) {
    $psi = New-Object System.Diagnostics.ProcessStartInfo
    $psi.FileName = "powershell.exe"
    $psi.Arguments = "-NoProfile -ExecutionPolicy Bypass -File `"$PSCommandPath`""
    $psi.Verb = "runas"
    try {
        $p = [System.Diagnostics.Process]::Start($psi)
        $p.WaitForExit()
        exit $p.ExitCode
    } catch {
        Write-Error "Elevation cancelled. Exiting."
        exit 1
    }
}

# Logging
$LogDir = "C:\ProgramData\WingetLogs"
$null = New-Item -Path $LogDir -ItemType Directory -Force -ErrorAction SilentlyContinue
$LogFile = Join-Path $LogDir "PerfTest_setup.log"
Start-Transcript -Path $LogFile -Append | Out-Null

# -----------------------
#   Helper Functions
# -----------------------
function Test-Winget {
    return [bool](Get-Command winget -ErrorAction SilentlyContinue)
}

function Invoke-Download {
    param(
        [Parameter(Mandatory)]
        [string]$Uri,
        [Parameter(Mandatory)]
        [string]$OutFile
    )
    Write-Host "Downloading: $Uri"
    Invoke-WebRequest -UseBasicParsing -Uri $Uri -OutFile $OutFile
}

function Install-Appx {
    param([Parameter(Mandatory)][string]$Path)
    if (-not (Test-Path $Path)) { throw "File not found: $Path" }
    Write-Host "Installing package: $([System.IO.Path]::GetFileName($Path))"
    Add-AppxPackage -Path $Path
}

function Register-AppInstallerIfPending {
    # If winget is missing right after first user logon, the Store may not have
    # finalized App Installer registration yet. This registration call can help.
    # Ref: MS Learn guidance.  [1](https://learn.microsoft.com/en-us/windows/package-manager/winget/)
    try {
        Add-AppxPackage -RegisterByFamilyName -MainPackage Microsoft.DesktopAppInstaller_8wekyb3d8bbwe -ErrorAction Stop
    } catch {
        # Ignore if not applicable
    }
}

function Ensure-Winget {
    if (Test-Winget) { return $true }

    Write-Host "winget not found. Attempting quick registration..."
    Register-AppInstallerIfPending
    if (Test-Winget) { return $true }

    Write-Host "winget still missing. Proceeding with online install of App Installer + dependencies..."

    # Prepare temp workspace
    $tmp = Join-Path $env:TEMP ("WingetInstall_" + [Guid]::NewGuid().ToString("N"))
    $null = New-Item -ItemType Directory -Path $tmp

    try {
        # --- Download dependencies first ---
        # VCLibs (UWP Desktop) - official aka.ms stable links (x64/x86 as needed).  [3](https://www.stefanobordoni.cloud/howto-install-winget-from-command-line/)
        $is64 = [Environment]::Is64BitOperatingSystem
        $vclibsUrl = if ($is64) { "https://aka.ms/Microsoft.VCLibs.x64.14.00.Desktop.appx" } else { "https://aka.ms/Microsoft.VCLibs.x86.14.00.Desktop.appx" }
        $vclibsPath = Join-Path $tmp (Split-Path $vclibsUrl -Leaf)
        Invoke-Download -Uri $vclibsUrl -OutFile $vclibsPath

        # Microsoft.UI.Xaml 2.x (latest stable direct asset).  [3](https://www.stefanobordoni.cloud/howto-install-winget-from-command-line/)
        $xamlUrl = if ($is64) {
            "https://github.com/microsoft/microsoft-ui-xaml/releases/latest/download/Microsoft.UI.Xaml.2.8.x64.appx"
        } else {
            "https://github.com/microsoft/microsoft-ui-xaml/releases/latest/download/Microsoft.UI.Xaml.2.8.x86.appx"
        }
        $xamlPath = Join-Path $tmp (Split-Path $xamlUrl -Leaf)
        Invoke-Download -Uri $xamlUrl -OutFile $xamlPath

        # App Installer (contains winget). Short link resolves to current bundle.  [4](https://learn.microsoft.com/en-us/answers/questions/3897366/microsoft-store-app-installer-wont-update)
        $appInstallerUrl = "https://aka.ms/getwinget"
        $appInstallerPath = Join-Path $tmp "Microsoft.DesktopAppInstaller_8wekyb3d8bbwe.msixbundle"
        Invoke-Download -Uri $appInstallerUrl -OutFile $appInstallerPath

        # Install in dependency order
        Install-Appx -Path $xamlPath
        Install-Appx -Path $vclibsPath
        Install-Appx -Path $appInstallerPath

        # Final check
        if (-not (Test-Winget)) {
            throw "winget was not found after App Installer install."
        }
        return $true
    } catch {
        Write-Error "Failed to install App Installer/winget: $($_.Exception.Message)"
        return $false
    } finally {
        # Cleanup temp files
        if (Test-Path $tmp) { Remove-Item $tmp -Recurse -Force -ErrorAction SilentlyContinue }
    }
}

function Install-PerformanceTest {
    # Install PassMark PerformanceTest 11.1.1008 from Microsoft Store silently
    # Using exact ID and source ensures we target the Store listing. 
    # (winges include 'msstore' for Microsoft Store.)  [6](https://github.com/microsoft/winget-cli)
    $PackageId = "PassMark.PassMarkPerformanceTest"
    $Version   = "11.1.1008"
    $args = @(
        "install",
        "--id", $PackageId,
        "--version", $Version,
        "--source", "msstore",
        "--exact",
        "--silent",
        "--accept-package-agreements",
        "--accept-source-agreements",
        "--disable-interactivity"
    )
    Write-Host "Installing PassMark PerformanceTest $Version from Microsoft Store via winget..."
    $proc = Start-Process -FilePath "winget" -ArgumentList $args -Wait -PassThru
    if ($proc.ExitCode -ne 0) {
        throw "winget install returned exit code $($proc.ExitCode)."
    }
    Write-Host "PassMark PerformanceTest $Version installed successfully."
}

# -----------------------
#   Execution
# -----------------------
try {
    # Update sources if winget already exists
    if (Test-Winget) {
        Write-Host "winget detected. Updating sources..."
        winget source update --disable-interactivity | Out-Null
    } else {
        if (-not (Ensure-Winget)) {
            throw "winget could not be installed automatically. See $LogFile for details."
        }
        Write-Host "winget installed successfully."
        winget source update --disable-interactivity | Out-Null
    }

    # Install the app
    Install-PerformanceTest

    Stop-Transcript | Out-Null
    exit 0
}
catch {
    Write-Error "ERROR: $($_.Exception.Message)"
    Stop-Transcript | Out-Null
    exit 1
}