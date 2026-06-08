# Setup Auto Git Upload Scheduled Task
# Run as Administrator in PowerShell

# Ensure admin privileges
$principal = New-Object Security.Principal.WindowsPrincipal([Security.Principal.WindowsIdentity]::GetCurrent())
if (-not $principal.IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)) {
    Write-Host "This script requires Administrator privileges. Attempting to relaunch elevated..." -ForegroundColor Yellow
    $scriptPath = $MyInvocation.MyCommand.Path
    if ($PSScriptRoot) {
        $scriptPath = Join-Path $PSScriptRoot (Split-Path -Leaf $MyInvocation.MyCommand.Path)
    }
    Start-Process powershell -ArgumentList "-NoProfile -ExecutionPolicy Bypass -File `"$scriptPath`"" -Verb RunAs -Wait
    exit 0
}

$scriptPath = Join-Path $PSScriptRoot "AutoGitUpload.ps1"

if (-not (Test-Path $scriptPath)) {
    Write-Host "ERROR: AutoGitUpload.ps1 not found!" -ForegroundColor Red
    Read-Host "Press Enter to exit"
    exit 1
}

Write-Host "Setting up Auto Git Upload task..." -ForegroundColor Cyan
Write-Host "Script path: $scriptPath" -ForegroundColor Gray
Write-Host ""

try {
    # Delete old task if it exists
    $existingTask = Get-ScheduledTask -TaskName "AutoGitUpload-Every5Minutes" -ErrorAction SilentlyContinue
    if ($existingTask) {
        Write-Host "Removing old task..." -ForegroundColor Yellow
        Unregister-ScheduledTask -TaskName "AutoGitUpload-Every5Minutes" -Confirm:$false -ErrorAction SilentlyContinue
        Start-Sleep -Seconds 1
    }

    # Create the action (what to run)
    $action = New-ScheduledTaskAction `
        -Execute "powershell.exe" `
        -Argument "-NoProfile -ExecutionPolicy Bypass -File `"$scriptPath`" -Action timecheck"

    # Create trigger - run every 5 minutes starting at 8 AM on weekdays
    $trigger = New-ScheduledTaskTrigger -Once -At (Get-Date) -RepetitionInterval (New-TimeSpan -Minutes 5) -RepetitionDuration (New-TimeSpan -Days 365)

    # Create the principal (who runs it)
    $principal = New-ScheduledTaskPrincipal `
        -UserId "$env:USERDOMAIN\$env:USERNAME" `
        -LogonType Interactive `
        -RunLevel Highest

    # Create settings
    $settings = New-ScheduledTaskSettingsSet `
        -AllowStartIfOnBatteries `
        -DontStopIfGoingOnBatteries `
        -StartWhenAvailable `
        -RunOnlyIfNetworkAvailable

    # Register the task
    Register-ScheduledTask `
        -TaskName "AutoGitUpload-Every5Minutes" `
        -Action $action `
        -Trigger $trigger `
        -Principal $principal `
        -Settings $settings `
        -Force | Out-Null

    Write-Host "✓ Task created successfully!" -ForegroundColor Green
    Write-Host ""
    Write-Host "Task Details:" -ForegroundColor Cyan
    Write-Host "  Name: AutoGitUpload-Every5Minutes" -ForegroundColor Gray
    Write-Host "  Frequency: Every 5 minutes (24/7)" -ForegroundColor Gray
    Write-Host "  Schedule enforced by: PowerShell script" -ForegroundColor Gray
    Write-Host ""
    Write-Host "Active hours (enforced by script):" -ForegroundColor Yellow
    Write-Host "  Days: Monday-Friday ONLY" -ForegroundColor Gray
    Write-Host "  Time: 8:00 AM - 4:30 PM" -ForegroundColor Gray
    Write-Host ""
    Write-Host "What it does:" -ForegroundColor Cyan
    Write-Host "  - Uploads NEW files when detected (any time)" -ForegroundColor Gray
    Write-Host "  - Uploads MODIFIED files during business hours (Mon-Fri 8AM-4:30PM)" -ForegroundColor Gray
    Write-Host ""

    # Verify the task was created
    Start-Sleep -Seconds 1
    $verifyTask = Get-ScheduledTask -TaskName "AutoGitUpload-Every5Minutes" -ErrorAction SilentlyContinue
    if ($verifyTask) {
        Write-Host "✓ Task verification: FOUND in Task Scheduler" -ForegroundColor Green
    }
    else {
        Write-Host "✗ Task verification: NOT FOUND" -ForegroundColor Red
    }
}
catch {
    Write-Host "ERROR: Failed to create task" -ForegroundColor Red
    Write-Host $_.Exception.Message -ForegroundColor Red
}

Write-Host ""
Read-Host "Press Enter to exit"
