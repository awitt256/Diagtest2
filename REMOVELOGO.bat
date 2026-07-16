@echo off
:: Run detectandremovecustomlogo.ps1 as Administrator

:: Check if already running as admin
net session >nul 2>&1
if %errorlevel% == 0 goto :run

:: Re-launch this BAT elevated via PowerShell
echo Requesting Administrator privileges...
powershell -Command "Start-Process -FilePath 'cmd.exe' -ArgumentList '/c \"%~f0\"' -Verb RunAs"
exit /b

:run
:: Check PowerShell version - use PowerShell 7 if available, otherwise PowerShell 5.1
echo Checking PowerShell version...
if exist "C:\Program Files\PowerShell\7\pwsh.exe" (
    "C:\Program Files\PowerShell\7\pwsh.exe" -Command "$v = $PSVersionTable.PSVersion; Write-Host \"PowerShell version: $($v.Major).$($v.Minor)\""
) else (
    powershell -Command "$v = $PSVersionTable.PSVersion; Write-Host \"PowerShell version: $($v.Major).$($v.Minor)\""
)

:: Install PowerShell 7 if version is too old (only check with PowerShell 5.1 since PowerShell 7 is already >= 7)
if exist "C:\Program Files\PowerShell\7\pwsh.exe" (
    echo PowerShell 7 is already installed.
) else (
    echo PowerShell 7 not found. Attempting installation...
    powershell -Command "if ($PSVersionTable.PSVersion.Major -lt 7) { Write-Host 'PowerShell version too old. Downloading PowerShell 7...' -ForegroundColor Yellow; $url = 'https://github.com/PowerShell/PowerShell/releases/download/v7.4.5/PowerShell-7.4.5-win-x64.msi'; $output = '%TEMP%\PowerShell7.msi'; Write-Host 'Downloading from: $url'; Write-Host 'Download location: $output'; try { (New-Object System.Net.WebClient).DownloadFile($url, $output); Write-Host 'Download complete.' -ForegroundColor Green; Write-Host 'File size:' (Get-Item $output).Length 'bytes' } catch { Write-Host 'Download failed: $_' -ForegroundColor Red; Read-Host 'Press Enter to exit'; exit }; Write-Host 'Installing PowerShell 7...'; Write-Host 'Running: msiexec.exe /i \"$output\" /quiet ADD_EXPLORER_CONTEXT_MENU_OPENPOWERSHELL=1 ENABLE_PSREMOTING=1 REGISTER_MANIFEST=1'; $process = Start-Process msiexec.exe -ArgumentList '/i \"$output\" /quiet ADD_EXPLORER_CONTEXT_MENU_OPENPOWERSHELL=1 ENABLE_PSREMOTING=1 REGISTER_MANIFEST=1' -Wait -PassThru; Write-Host 'MSI exit code:' $process.ExitCode; if ($process.ExitCode -eq 0) { Write-Host 'Installation completed successfully.' -ForegroundColor Green } else { Write-Host 'Installation failed with exit code:' $process.ExitCode -ForegroundColor Red; Write-Host 'Common exit codes: 1602=cancelled, 1603=fatal error, 1618=another install running' -ForegroundColor Yellow; Read-Host 'Press Enter to exit'; exit }; Start-Sleep -Seconds 5; Write-Host 'Checking if PowerShell 7 exists at: C:\Program Files\PowerShell\7\pwsh.exe'; if (Test-Path 'C:\Program Files\PowerShell\7\pwsh.exe') { Write-Host 'PowerShell 7 verified.' -ForegroundColor Green; $pwshVersion = & 'C:\Program Files\PowerShell\7\pwsh.exe' -Command '$PSVersionTable.PSVersion'; Write-Host 'PowerShell 7 version:' $pwshVersion; Write-Host 'Restarting script...' -ForegroundColor Green; Start-Process cmd.exe -ArgumentList '/c \"%~f0\"' -Verb RunAs; exit } else { Write-Host 'PowerShell 7 not found after installation. Installation may have failed.' -ForegroundColor Red; Write-Host 'Checking alternative paths...'; if (Test-Path 'C:\Program Files (x86)\PowerShell\7\pwsh.exe') { Write-Host 'Found at: C:\Program Files (x86)\PowerShell\7\pwsh.exe' -ForegroundColor Yellow } else { Write-Host 'Not found in Program Files (x86) either' -ForegroundColor Red }; Read-Host 'Press Enter to exit'; exit } } else { Write-Host 'PowerShell version is already 7 or higher. No installation needed.' -ForegroundColor Green }"
)

:: Run the PowerShell script from the same folder as this BAT file
:: Use PowerShell 7 if available, otherwise fall back to PowerShell 5.1
if exist "C:\Program Files\PowerShell\7\pwsh.exe" (
    "C:\Program Files\PowerShell\7\pwsh.exe" -NoProfile -ExecutionPolicy Bypass -File "%~dp0detectandremovecustomlogo.ps1" -LauncherPath "%~f0"
) else (
    powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%~dp0detectandremovecustomlogo.ps1" -LauncherPath "%~f0"
)