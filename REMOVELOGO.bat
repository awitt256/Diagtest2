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
:: Check PowerShell version
echo Checking PowerShell version...
powershell -Command "$v = $PSVersionTable.PSVersion; Write-Host \"PowerShell version: $($v.Major).$($v.Minor)\""
powershell -Command "if ($PSVersionTable.PSVersion.Major -lt 7) { Write-Host 'PowerShell version too old. Downloading PowerShell 7...' -ForegroundColor Yellow; $url = 'https://github.com/PowerShell/PowerShell/releases/download/v7.4.5/PowerShell-7.4.5-win-x64.msi'; $output = '%TEMP%\PowerShell7.msi'; Write-Host 'Downloading from: $url'; (New-Object System.Net.WebClient).DownloadFile($url, $output); Write-Host 'Installing PowerShell 7...'; Start-Process msiexec.exe -ArgumentList '/i \"$output\" /quiet ADD_EXPLORER_CONTEXT_MENU_OPENPOWERSHELL=1 ENABLE_PSREMOTING=1 REGISTER_MANIFEST=1' -Wait; Write-Host 'PowerShell 7 installed successfully. Restarting script with PowerShell 7...'; Start-Sleep -Seconds 2; Start-Process 'C:\Program Files\PowerShell\7\pwsh.exe' -ArgumentList '-NoProfile -ExecutionPolicy Bypass -File \"%~f0\"' -Verb RunAs; exit }"
echo PowerShell version is compatible.

:: Run the PowerShell script from the same folder as this BAT file
:: Use PowerShell 7 if available, otherwise fall back to PowerShell 5.1
if exist "C:\Program Files\PowerShell\7\pwsh.exe" (
    "C:\Program Files\PowerShell\7\pwsh.exe" -NoProfile -ExecutionPolicy Bypass -File "%~dp0detectandremovecustomlogo.ps1" -LauncherPath "%~f0"
) else (
    powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%~dp0detectandremovecustomlogo.ps1" -LauncherPath "%~f0"
)