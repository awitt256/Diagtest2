# Auto Git Upload Script - Watches for changes and auto-commits to GitHub
# Usage: .\AutoGitUpload.ps1

param(
    [string]$Action = "start",  # "start", "setup", "uploadall", or "stop"
    [int]$DebounceSeconds = 5   # Wait 5 seconds after last change before committing
)

$global:LastCommitTime = 0
$global:IsInitialized = $false
$global:FileWatcher = $null
$RepoUrl = "https://github.com/awitt256/Diagtest2.git"
$CurrentPath = Get-Location

function Initialize-GitRepo {
    Write-Host "Initializing git repository..." -ForegroundColor Cyan
    
    # Check if .git exists
    if (-not (Test-Path ".git")) {
        git init
        git remote add origin $RepoUrl
        Write-Host "✓ Git repository initialized" -ForegroundColor Green
    } else {
        Write-Host "✓ Git repository already exists" -ForegroundColor Green
    }
    
    # Verify remote is set correctly
    $currentRemote = git config --get remote.origin.url
    if ($currentRemote -ne $RepoUrl) {
        git remote set-url origin $RepoUrl
        Write-Host "✓ Remote URL updated" -ForegroundColor Green
    }
    
    $global:IsInitialized = $true
}

function Commit-And-Push {
    param([string]$Message)
    
    try {
        # Get status first
        $status = git status --porcelain
        
        if ([string]::IsNullOrWhiteSpace($status)) {
            Write-Host "No changes to commit" -ForegroundColor Yellow
            return
        }
        
        Write-Host "Changes detected, committing..." -ForegroundColor Yellow
        
        # Add all changes
        git add -A
        
        # Commit
        if ([string]::IsNullOrWhiteSpace($Message)) {
            $Message = "Auto-upload: $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')"
        }
        
        git commit -m "$Message"
        
        # Push
        Write-Host "Pushing to GitHub..." -ForegroundColor Cyan
        git push -u origin master 2>&1
        
        Write-Host "✓ Successfully uploaded to GitHub" -ForegroundColor Green
        Write-Host ""
    }
    catch {
        Write-Host "✗ Error during commit/push: $_" -ForegroundColor Red
    }
}

function Start-FileMonitoring {
    Write-Host "Watching for file changes..." -ForegroundColor Cyan
    Write-Host "Press Ctrl+C to stop monitoring" -ForegroundColor Gray
    Write-Host ""
    
    $watcher = New-Object System.IO.FileSystemWatcher
    $watcher.Path = $CurrentPath
    $watcher.IncludeSubdirectories = $true
    $watcher.EnableRaisingEvents = $true
    
    # Exclude .git folder and common ignored files
    $ignorePatterns = @('.git', '.gitignore', '.vs', '__pycache__', 'node_modules', '*.tmp')
    
    $action = {
        $changedPath = $Event.SourceEventArgs.FullPath
        $changeType = $Event.SourceEventArgs.ChangeType
        
        # Skip ignored items
        $shouldIgnore = $false
        foreach ($pattern in $ignorePatterns) {
            if ($changedPath -like "*$pattern*") {
                $shouldIgnore = $true
                break
            }
        }
        
        if ($shouldIgnore) { return }
        
        # Debounce: only commit if 5+ seconds have passed since last commit
        $timeSinceLastCommit = (Get-Date).TotalSeconds - $global:LastCommitTime
        
        if ($timeSinceLastCommit -lt $DebounceSeconds) {
            return
        }
        
        Write-Host "[$(Get-Date -Format 'HH:mm:ss')] $changeType`: $(Split-Path $changedPath -Leaf)" -ForegroundColor White
        
        $global:LastCommitTime = (Get-Date).TotalSeconds
        
        # Schedule commit after debounce delay
        Start-Sleep -Milliseconds 500
        Commit-And-Push "Auto: $changeType $(Split-Path $changedPath -Leaf)"
    }
    
    $watcher_event = Register-ObjectEvent -InputObject $watcher -EventName "Changed" -Action $action
    
    # Keep the script running
    try {
        while ($true) { Start-Sleep -Milliseconds 100 }
    }
    finally {
        $watcher.Dispose()
        Unregister-Event -SourceIdentifier $watcher_event.Name
        Write-Host "Monitoring stopped" -ForegroundColor Yellow
    }
}

# Main logic
switch ($Action.ToLower()) {
    "setup" {
        Initialize-GitRepo
        Write-Host ""
        Write-Host "Setup complete! Run '.\AutoGitUpload.ps1 -Action start' to begin monitoring" -ForegroundColor Green
    }
    
    "uploadall" {
        Initialize-GitRepo
        Write-Host ""
        Write-Host "Uploading all current files to GitHub..." -ForegroundColor Cyan
        
        try {
            git add -A
            git commit -m "Initial upload: All current files $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')"
            git push -u origin master
            Write-Host "✓ All files successfully uploaded to GitHub!" -ForegroundColor Green
        }
        catch {
            Write-Host "✗ Error uploading files: $_" -ForegroundColor Red
        }
    }
    
    "start" {
        if (-not $global:IsInitialized) {
            Initialize-GitRepo
            Write-Host ""
        }
        Start-FileMonitoring
    }
    
    "stop" {
        Write-Host "Stop command sent" -ForegroundColor Yellow
    }
    
    default {
        Write-Host "Auto Git Upload Script" -ForegroundColor Cyan
        Write-Host ""
        Write-Host "Usage:" -ForegroundColor Yellow
        Write-Host "  .\AutoGitUpload.ps1 -Action setup     # Initialize git repo (run once)" -ForegroundColor Gray
        Write-Host "  .\AutoGitUpload.ps1 -Action uploadall # Upload all current files now" -ForegroundColor Gray
        Write-Host "  .\AutoGitUpload.ps1 -Action start     # Start watching for changes" -ForegroundColor Gray
        Write-Host "  .\AutoGitUpload.ps1 -Action start -DebounceSeconds 10  # Custom debounce delay" -ForegroundColor Gray
        Write-Host ""
        Write-Host "Examples:" -ForegroundColor Yellow
        Write-Host "  .\AutoGitUpload.ps1 -Action setup     # One-time setup" -ForegroundColor Gray
        Write-Host "  .\AutoGitUpload.ps1 -Action uploadall # Upload all files" -ForegroundColor Gray
        Write-Host "  .\AutoGitUpload.ps1 -Action start     # Start auto-uploading" -ForegroundColor Gray
    }
}
