@echo off
powershell -Command "Start-Process PowerShell -ArgumentList '-NoProfile -ExecutionPolicy Bypass -Command Start-MpScan -ScanType QuickScan' -Verb RunAs"