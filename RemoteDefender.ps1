# ===================================================================
# COMPLETE REMOTE WINDOWS DEFENDER SCRIPT EXECUTION SERVER
# WARNING: USE ONLY ON TRUSTED PRIVATE NETWORKS!
# ===================================================================

# Configuration
$port = 8080
$logFile = "C:\Scripts\execution-log.txt"

# Create Scripts directory if it doesn't exist
if (!(Test-Path "C:\Scripts")) {
    New-Item -ItemType Directory -Path "C:\Scripts" -Force | Out-Null
}

# The actual Defender script (embedded)
$defenderScript = @'
# Self-elevate if not running as admin
if (-not ([Security.Principal.WindowsPrincipal] [Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole(
    [Security.Principal.WindowsBuiltinRole]::Administrator)) {
    
    if ($PSCommandPath) {
        Start-Process -FilePath "powershell.exe" -ArgumentList "-ExecutionPolicy Bypass -File `"$PSCommandPath`"" -Verb RunAs
        exit
    } else {
        Write-Host "Please run this script as Administrator" -ForegroundColor Red
        pause
        exit
    }
}

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Windows Defender Update & Scan Script" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Check if Windows Defender is running
Write-Host "[1/3] Checking Windows Defender status..." -ForegroundColor Yellow
$defenderStatus = Get-MpComputerStatus

if ($defenderStatus.AntivirusEnabled -eq $false) {
    Write-Host "ERROR: Windows Defender is not enabled!" -ForegroundColor Red
    pause
    exit
}

Write-Host "Windows Defender is enabled and running." -ForegroundColor Green
Write-Host ""

# Update Windows Defender signatures
Write-Host "[2/3] Updating Windows Defender definitions..." -ForegroundColor Yellow
try {
    Update-MpSignature -ErrorAction Stop
    Write-Host "Defender definitions updated successfully!" -ForegroundColor Green
    
    # Show current signature version
    $sigVersion = (Get-MpComputerStatus).AntivirusSignatureVersion
    Write-Host "Current signature version: $sigVersion" -ForegroundColor Cyan
} catch {
    Write-Host "WARNING: Failed to update definitions - $($_.Exception.Message)" -ForegroundColor Red
    Write-Host "Continuing with scan anyway..." -ForegroundColor Yellow
}
Write-Host ""

# Run quick system scan
Write-Host "[3/3] Starting quick system scan..." -ForegroundColor Yellow
Write-Host "Scan started at: $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')" -ForegroundColor Cyan
Write-Host ""

try {
    Start-MpScan -ScanType QuickScan -ErrorAction Stop
    Write-Host ""
    Write-Host "Scan completed successfully!" -ForegroundColor Green
    
    # Check for threats
    $threats = Get-MpThreat
    if ($threats.Count -gt 0) {
        Write-Host ""
        Write-Host "WARNING: $($threats.Count) threat(s) detected!" -ForegroundColor Red
        $threats | ForEach-Object {
            Write-Host "  - $($_.ThreatName)" -ForegroundColor Yellow
        }
    } else {
        Write-Host "No threats detected." -ForegroundColor Green
    }
    
} catch {
    Write-Host "ERROR: Scan failed - $($_.Exception.Message)" -ForegroundColor Red
}

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Script completed at: $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""
'@

# Save the defender script
$defenderScriptPath = "C:\Scripts\defender-scan.ps1"
$defenderScript | Out-File -FilePath $defenderScriptPath -Encoding UTF8 -Force

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Remote Defender Script Server" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Get IP address
$ipAddress = (Get-NetIPAddress -AddressFamily IPv4 | Where-Object {$_.InterfaceAlias -notlike "*Loopback*" -and $_.IPAddress -notlike "169.254.*"}).IPAddress | Select-Object -First 1

Write-Host "Starting web server..." -ForegroundColor Yellow
Write-Host "Access URL: http://${ipAddress}:${port}" -ForegroundColor Green
Write-Host ""
Write-Host "Press Ctrl+C to stop the server" -ForegroundColor Yellow
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Create HTTP listener
$listener = New-Object System.Net.HttpListener
$listener.Prefixes.Add("http://+:$port/")

# Add Assembly for HTML encoding
Add-Type -AssemblyName System.Web

try {
    $listener.Start()

    while ($listener.IsListening) {
        $context = $listener.GetContext()
        $request = $context.Request
        $response = $context.Response

        $timestamp = Get-Date -Format 'yyyy-MM-dd HH:mm:ss'
        $clientIP = $request.RemoteEndPoint.Address

        Write-Host "[$timestamp] Request from: $clientIP - $($request.Url.AbsolutePath)" -ForegroundColor Cyan

        # Log request
        "$timestamp - $clientIP - $($request.Url.AbsolutePath)" | Out-File -FilePath $logFile -Append

        # Handle different routes
        if ($request.Url.AbsolutePath -eq "/run") {
            # Execute the script
            Write-Host "[$timestamp] Executing Defender script..." -ForegroundColor Yellow
            
            $job = Start-Job -ScriptBlock {
                param($scriptPath)
                $output = & powershell.exe -ExecutionPolicy Bypass -File $scriptPath 2>&1 | Out-String
                return $output
            } -ArgumentList $defenderScriptPath

            # Wait for job with timeout
            $completed = Wait-Job -Job $job -Timeout 300
            
            if ($completed) {
                $output = Receive-Job -Job $job
                Remove-Job -Job $job
                
                $html = @"
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>Script Output - Windows Defender</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: linear-gradient(135deg, #1e3c72 0%, #2a5298 100%);
            min-height: 100vh;
            padding: 20px;
        }
        .container {
            background: white;
            padding: 40px;
            border-radius: 15px;
            box-shadow: 0 20px 60px rgba(0,0,0,0.4);
            max-width: 900px;
            margin: 0 auto;
            animation: slideIn 0.5s ease-out;
        }
        @keyframes slideIn {
            from { opacity: 0; transform: translateY(30px); }
            to { opacity: 1; transform: translateY(0); }
        }
        h1 {
            color: #1e3c72;
            margin-bottom: 20px;
            display: flex;
            align-items: center;
            gap: 10px;
        }
        .status {
            background: #d4edda;
            border-left: 4px solid #28a745;
            padding: 15px;
            border-radius: 5px;
            margin: 20px 0;
            color: #155724;
        }
        .output-container {
            background: #1e1e1e;
            border-radius: 8px;
            padding: 20px;
            margin: 20px 0;
            max-height: 600px;
            overflow-y: auto;
        }
        .output {
            color: #d4d4d4;
            white-space: pre-wrap;
            font-family: 'Consolas', 'Courier New', monospace;
            font-size: 13px;
            line-height: 1.6;
        }
        .btn {
            display: inline-block;
            padding: 12px 30px;
            background: #1e3c72;
            color: white;
            text-decoration: none;
            border-radius: 5px;
            font-weight: bold;
            margin-top: 20px;
            transition: all 0.3s;
        }
        .btn:hover {
            background: #2a5298;
            transform: translateY(-2px);
            box-shadow: 0 5px 15px rgba(0,0,0,0.3);
        }
        .timestamp {
            color: #6c757d;
            font-size: 14px;
            margin-top: 10px;
        }
        ::-webkit-scrollbar { width: 10px; }
        ::-webkit-scrollbar-track { background: #2d2d2d; }
        ::-webkit-scrollbar-thumb { background: #555; border-radius: 5px; }
        ::-webkit-scrollbar-thumb:hover { background: #777; }
    </style>
</head>
<body>
    <div class="container">
        <h1>✅ Script Executed Successfully</h1>
        <div class="status">
            <strong>Status:</strong> Windows Defender scan completed<br>
            <strong>Executed from:</strong> $clientIP<br>
            <strong>Computer:</strong> $env:COMPUTERNAME
        </div>
        <h3>Output:</h3>
        <div class="output-container">
            <div class="output">$([System.Web.HttpUtility]::HtmlEncode($output))</div>
        </div>
        <a href="/" class="btn">⬅️ Back to Home</a>
        <div class="timestamp">Completed at: $timestamp</div>
    </div>
</body>
</html>
"@
            } else {
                Remove-Job -Job $job -Force
                $html = @"
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>Error - Timeout</title>
    <style>
        body {
            font-family: 'Segoe UI', sans-serif;
            background: linear-gradient(135deg, #1e3c72 0%, #2a5298 100%);
            min-height: 100vh;
            display: flex;
            align-items: center;
            justify-content: center;
        }
        .container {
            background: white;
            padding: 40px;
            border-radius: 15px;
            box-shadow: 0 20px 60px rgba(0,0,0,0.4);
            text-align: center;
        }
        h1 { color: #dc3545; }
        .btn {
            display: inline-block;
            padding: 12px 30px;
            background: #1e3c72;
            color: white;
            text-decoration: none;
            border-radius: 5px;
            margin-top: 20px;
        }
    </style>
</head>
<body>
    <div class="container">
        <h1>⏱️ Script Timeout</h1>
        <p>The script took too long to execute (>5 minutes)</p>
        <a href="/" class="btn">⬅️ Back to Home</a>
    </div>
</body>
</html>
"@
            }
            
            Write-Host "[$timestamp] Script execution completed" -ForegroundColor Green
            
        } else {
            # Home page
            $html = @"
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Windows Defender Remote Scan</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: linear-gradient(135deg, #1e3c72 0%, #2a5298 100%);
            min-height: 100vh;
            display: flex;
            align-items: center;
            justify-content: center;
            padding: 20px;
        }
        .container {
            background: white;
            padding: 50px;
            border-radius: 20px;
            box-shadow: 0 20px 80px rgba(0,0,0,0.4);
            text-align: center;
            max-width: 600px;
            animation: fadeIn 0.6s ease-out;
        }
        @keyframes fadeIn {
            from { opacity: 0; transform: scale(0.95); }
            to { opacity: 1; transform: scale(1); }
        }
        h1 {
            color: #1e3c72;
            margin-bottom: 15px;
            font-size: 32px;
        }
        .subtitle {
            color: #6c757d;
            margin-bottom: 30px;
            font-size: 16px;
        }
        .info-box {
            background: #e7f3ff;
            border-left: 4px solid #1e3c72;
            padding: 20px;
            border-radius: 8px;
            margin: 25px 0;
            text-align: left;
        }
        .info-box h3 {
            color: #1e3c72;
            margin-bottom: 10px;
        }
        .info-box ul {
            margin-left: 20px;
            line-height: 1.8;
        }
        .warning {
            background: #fff3cd;
            border: 2px solid #ffc107;
            padding: 20px;
            border-radius: 8px;
            margin: 25px 0;
            color: #856404;
        }
        .btn {
            display: inline-block;
            padding: 18px 50px;
            background: linear-gradient(135deg, #1e3c72 0%, #2a5298 100%);
            color: white;
            text-decoration: none;
            border-radius: 50px;
            font-weight: bold;
            font-size: 18px;
            margin: 25px 0;
            cursor: pointer;
            border: none;
            transition: all 0.3s;
            box-shadow: 0 5px 20px rgba(30, 60, 114, 0.3);
        }
        .btn:hover {
            transform: translateY(-3px);
            box-shadow: 0 8px 30px rgba(30, 60, 114, 0.5);
        }
        .btn:active {
            transform: translateY(-1px);
        }
        .server-info {
            background: #f8f9fa;
            padding: 15px;
            border-radius: 5px;
            margin-top: 25px;
            font-size: 14px;
            color: #6c757d;
        }
        .shield-icon {
            font-size: 60px;
            margin-bottom: 20px;
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="shield-icon">🛡️</div>
        <h1>Windows Defender Scanner</h1>
        <p class="subtitle">Remote System Protection Tool</p>
        
        <div class="info-box">
            <h3>📋 What This Does:</h3>
            <ul>
                <li>Updates Windows Defender definitions</li>
                <li>Runs a quick system scan</li>
                <li>Reports any threats found</li>
                <li>Shows scan results in real-time</li>
            </ul>
        </div>
        
        <div class="warning">
            <strong>⚠️ Important:</strong> This will run with administrator privileges on:<br>
            <strong>$env:COMPUTERNAME</strong>
        </div>
        
        <form method="GET" action="/run">
            <button type="submit" class="btn">▶️ Run Windows Defender Scan</button>
        </form>
        
        <div class="server-info">
            <strong>Server:</strong> $env:COMPUTERNAME<br>
            <strong>Your IP:</strong> $clientIP<br>
            <strong>Server Time:</strong> $timestamp
        </div>
    </div>
</body>
</html>
"@
        }

        # Send response
        $buffer = [System.Text.Encoding]::UTF8.GetBytes($html)
        $response.ContentLength64 = $buffer.Length
        $response.ContentType = "text/html; charset=utf-8"
        $response.StatusCode = 200
        $response.OutputStream.Write($buffer, 0, $buffer.Length)
        $response.OutputStream.Close()
    }
}
catch {
    Write-Host "Error: $_" -ForegroundColor Red
}
finally {
    if ($listener.IsListening) {
        $listener.Stop()
    }
    Write-Host "`nServer stopped" -ForegroundColor Yellow
}