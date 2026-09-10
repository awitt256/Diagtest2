@echo off
powershell -Command "Start-Process PowerShell -ArgumentList '-NoProfile -ExecutionPolicy Bypass -Command \"Start-MpScan -ScanType QuickScan; Start-Sleep -Seconds 10; wevtutil qe Microsoft-Windows-Windows Defender/Operational /f:text /c:20 | Out-File C:\DefenderEventLog.txt -Encoding UTF8; Invoke-Item C:\DefenderEventLog.txt\"' -Verb RunAs"
