# Setup Task Scheduler to run AutoGitUpload every 5 minutes
# Run as Administrator

# Ensure the script runs with administrator privileges
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

$taskName = "AutoGitUpload-Every5Minutes"
$scriptPath = Join-Path $PSScriptRoot "AutoGitUpload.ps1"

Write-Host "Setting up scheduled task: $taskName" -ForegroundColor Cyan
Write-Host "Script path: $scriptPath" -ForegroundColor Gray
Write-Host ""

# Check if script exists
if (-not (Test-Path $scriptPath)) {
    Write-Host "ERROR: AutoGitUpload.ps1 not found at $scriptPath" -ForegroundColor Red
    Read-Host "Press Enter to exit"
    exit 1
}

try {
    # Remove existing task if it exists
    $existingTask = Get-ScheduledTask -TaskName $taskName -ErrorAction SilentlyContinue
    if ($existingTask) {
        Write-Host "Removing existing task..." -ForegroundColor Yellow
        Unregister-ScheduledTask -TaskName $taskName -Confirm:$false
        Start-Sleep -Seconds 1
    }

    # Create action
    $action = New-ScheduledTaskAction `
        -Execute "powershell.exe" `
        -Argument "-NoProfile -ExecutionPolicy Bypass -File `"$scriptPath`" -Action timecheck"

    # Create trigger - every 5 minutes starting now
    $trigger = New-ScheduledTaskTrigger `
        -Once `
        -At (Get-Date) `
        -RepetitionInterval (New-TimeSpan -Minutes 5) `
        -RepetitionDuration (New-TimeSpan -Days 365)

    # Create principal (run with highest privileges)
    $principal = New-ScheduledTaskPrincipal -UserId "$env:USERDOMAIN\$env:USERNAME" -LogonType Interactive -RunLevel Highest

    # Create settings
    $settings = New-ScheduledTaskSettingsSet `
        -AllowStartIfOnBatteries `
        -DontStopIfGoingOnBatteries `
        -StartWhenAvailable `
        -RunOnlyIfNetworkAvailable

    # Register the task
    Register-ScheduledTask `
        -TaskName $taskName `
        -Action $action `
        -Trigger $trigger `
        -Principal $principal `
        -Settings $settings `
        -Force | Out-Null

    Write-Host "✓ Task created successfully!" -ForegroundColor Green
    Write-Host ""
    Write-Host "Task Details:" -ForegroundColor Cyan
    Write-Host "  Name: $taskName" -ForegroundColor Gray
    Write-Host "  Frequency: Every 5 minutes" -ForegroundColor Gray
    Write-Host "  Action: Upload new files + changes during 3:30-4:30 PM" -ForegroundColor Gray
    Write-Host ""
    Write-Host "The task will:" -ForegroundColor Yellow
    Write-Host "  • Upload ANY new files immediately (24/7)" -ForegroundColor Gray
    Write-Host "  • Upload modified files during 3:30 PM - 4:30 PM" -ForegroundColor Gray
    Write-Host "  • Skip unchanged files outside the time window" -ForegroundColor Gray
    Write-Host ""
    Write-Host "To manage the task:" -ForegroundColor Cyan
    Write-Host "  View: Get-ScheduledTask -TaskName '$taskName' | Get-ScheduledTaskInfo" -ForegroundColor Gray
    Write-Host "  Disable: Disable-ScheduledTask -TaskName '$taskName'" -ForegroundColor Gray
    Write-Host "  Enable: Enable-ScheduledTask -TaskName '$taskName'" -ForegroundColor Gray
    Write-Host "  Delete: Unregister-ScheduledTask -TaskName '$taskName' -Confirm:`$false" -ForegroundColor Gray
    Write-Host ""

    # Ask to run now
    $runNow = Read-Host "Run the upload now? (y/n)"
    if ($runNow -eq 'y' -or $runNow -eq 'yes') {
        Write-Host ""
        Write-Host "Running AutoGitUpload now..." -ForegroundColor Yellow
        & powershell -NoProfile -ExecutionPolicy Bypass -File $scriptPath -Action timecheck
    }
}
catch {
    Write-Host "ERROR: Failed to create scheduled task: $_" -ForegroundColor Red
    Read-Host "Press Enter to exit"
    exit 1
}

Write-Host ""
Write-Host "Setup complete! The scheduled task is now active." -ForegroundColor Green
Read-Host "Press Enter to exit"
