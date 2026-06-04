<#
Ensures winget is available, installs PassMark PerformanceTest from Microsoft Store by ID (9NX2VQG25JXJ),
and launches it if installation succeeds.

Notes:
- Requires Windows 10 1809+ or Windows 11.
- The optional fallback to download App Installer and dependencies is OFF by default; set $EnableOnlineWingetInstall = $true to use it.
#>

$ErrorActionPreference = 'Stop'

# -----------------------------
# Admin check
# -----------------------------
if (-not ([Security.Principal.WindowsPrincipal][Security.Principal.WindowsIdentity]::GetCurrent()
    ).IsInRole([Security.Principal.WindowsBuiltInRole] "Administrator")) {
    Write-Warning "Please run this script as an Administrator!"
    exit 1
}

# -----------------------------
# Configuration
# -----------------------------
$StoreId  = '9NX2VQG25JXJ'   # Microsoft Store product ID for PassMark PerformanceTest
$EnableOnlineWingetInstall = $false  # set to $true to attempt online install of App Installer + dependencies

# -----------------------------
# Helper functions
# -----------------------------
function Test-Winget {
    Get-Command winget -ErrorAction SilentlyContinue
}

function Register-AppInstallerIfPending {
    try {
        Add-AppxPackage -RegisterByFamilyName -MainPackage Microsoft.DesktopAppInstaller_8wekyb3d8bbwe -ErrorAction Stop
        return $true
    } catch {
        return $false
    }
}

function Invoke-Download {
    param(
        [Parameter(Mandatory)][string]$Uri,
        [Parameter(Mandatory)][string]$OutFile
    )
    Write-Host "Downloading: $Uri"
    Invoke-WebRequest -UseBasicParsing -Uri $Uri -OutFile $OutFile
}

function Install-Appx {
    param([Parameter(Mandatory)][string]$Path)
    if (-not (Test-Path $Path)) { throw "File not found: $Path" }
    Write-Host "Installing: $(Split-Path $Path -Leaf)"
    Add-AppxPackage -Path $Path
}

function Ensure-Winget {
    Write-Host "Checking for Windows Package Manager (winget)..."

    if (Test-Winget) {
        Write-Host "Windows Package Manager (winget) is already installed."
        return $true
    }

    Write-Host "Windows Package Manager (winget) not found. Attempting App Installer registration..."
    if (Register-AppInstallerIfPending) {
        Start-Sleep -Seconds 5
        if (Test-Winget) {
            Write-Host "Windows Package Manager (winget) installed successfully via registration."
            return $true
        }
    }

    if (-not $EnableOnlineWingetInstall) {
        Write-Warning "winget still not available. Set `$EnableOnlineWingetInstall = `$true to attempt online install, or install App Installer from Microsoft Store."
        return $false
    }

    # ---------- Optional Online Fallback ----------
    Write-Host "Attempting online installation of App Installer (winget) + dependencies..."
    $tmp = Join-Path $env:TEMP ("WingetInstall_" + [Guid]::NewGuid().ToString("N"))
    New-Item -ItemType Directory -Path $tmp | Out-Null
    try {
        $is64 = [Environment]::Is64BitOperatingSystem

        # Microsoft.VCLibs (UWP Desktop) – official aka.ms links
        $vclibsUrl  = if ($is64) { "https://aka.ms/Microsoft.VCLibs.x64.14.00.Desktop.appx" } else { "https://aka.ms/Microsoft.VCLibs.x86.14.00.Desktop.appx" }
        $vclibsPath = Join-Path $tmp (Split-Path $vclibsUrl -Leaf)
        Invoke-Download -Uri $vclibsUrl -OutFile $vclibsPath

        # Microsoft.UI.Xaml 2.8 (framework dependency)
        $xamlUrl  = if ($is64) { "https://github.com/microsoft/microsoft-ui-xaml/releases/latest/download/Microsoft.UI.Xaml.2.8.x64.appx" } else { "https://github.com/microsoft/microsoft-ui-xaml/releases/latest/download/Microsoft.UI.Xaml.2.8.x86.appx" }
        $xamlPath = Join-Path $tmp (Split-Path $xamlUrl -Leaf)
        Invoke-Download -Uri $xamlUrl -OutFile $xamlPath

        # App Installer (contains winget)
        $appInstallerUrl  = "https://aka.ms/getwinget"
        $appInstallerPath = Join-Path $tmp "Microsoft.DesktopAppInstaller_8wekyb3d8bbwe.msixbundle"
        Invoke-Download -Uri $appInstallerUrl -OutFile $appInstallerPath

        # Install in dependency order
        Install-Appx -Path $xamlPath
        Install-Appx -Path $vclibsPath
        Install-Appx -Path $appInstallerPath

        if (Test-Winget) { 
            Write-Host "winget installed successfully."
            return $true 
        } else {
            Write-Warning "winget still not detected after online installation."
            return $false
        }
    } catch {
        Write-Error "Failed to install App Installer/winget online: $($_.Exception.Message)"
        return $false
    } finally {
        if (Test-Path $tmp) { Remove-Item $tmp -Recurse -Force -ErrorAction SilentlyContinue }
    }
}

function Launch-PerformanceTest {
    # Try common Win32 install paths first
    $candidates = @(
        "$Env:ProgramFiles\PerformanceTest\PerformanceTest64.exe",
        "$Env:ProgramFiles\PassMark\PerformanceTest\PerformanceTest64.exe",
        "$Env:ProgramFiles(x86)\PerformanceTest\PerformanceTest.exe",
        "$Env:ProgramFiles(x86)\PassMark\PerformanceTest\PerformanceTest.exe"
    )
    foreach ($p in $candidates) {
        if (Test-Path $p) {
            Write-Host "Launching: $p"
            Start-Process -FilePath $p | Out-Null
            return $true
        }
    }

    # If it's a Store-packaged app, try via AppsFolder (Appx)
    $pkg = Get-AppxPackage | Where-Object {
        $_.Name -match 'PerformanceTest' -or $_.Publisher -match 'PassMark'
    } | Select-Object -First 1

    if ($pkg) {
        $appsFolderTarget = "shell:AppsFolder\$($pkg.PackageFamilyName)!App"
        Write-Host "Launching Store app: $appsFolderTarget"
        Start-Process explorer.exe $appsFolderTarget | Out-Null
        return $true
    }

    Write-Warning "Could not locate PerformanceTest executable or Store package to launch."
    return $false
}

# -----------------------------
# Ensure winget is available
# -----------------------------
if (-not (Ensure-Winget)) {
    Write-Error "Windows Package Manager (winget) is not available. Aborting."
    exit 2
}

# Good hygiene before install
winget source update --disable-interactivity | Out-Null

# -----------------------------
# Install by Store ID (silent)
# -----------------------------
Write-Host "Installing PassMark PerformanceTest from Microsoft Store..." -ForegroundColor Cyan

# Silent + auto-accept for unattended installs
winget install --id $StoreId --source msstore --silent --accept-package-agreements --accept-source-agreements

if ($LASTEXITCODE -eq 0) {
    Write-Host "PassMark PerformanceTest installed successfully." -ForegroundColor Green

    # Launch on success
    if (-not (Launch-PerformanceTest)) {
        Write-Warning "Installed, but auto-launch could not find the app. You can start it from Start Menu."
    }
    exit 0
} else {
    $hex = ('0x{0:X8}' -f (($LASTEXITCODE -as [int]) -band 0xFFFFFFFF))
    Write-Error "PassMark PerformanceTest installation may have encountered an issue. ExitCode=$LASTEXITCODE ($hex)"
    exit $LASTEXITCODE
}