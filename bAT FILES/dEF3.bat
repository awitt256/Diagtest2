@echo off
powershell -Command "Start-Process PowerShell -ArgumentList '-NoProfile -ExecutionPolicy Bypass -Command \"Start-MpScan -ScanType QuickScan; Start-Sleep -Seconds 10; Get-MpThreatDetection | Format-Table -AutoSize | Out-String | Write-Host\"' -Verb RunAs"
