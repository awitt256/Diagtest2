@echo off
:: Batch script to launch the PowerShell Enrollment Checker

powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0CheckEnrollment.ps1"
