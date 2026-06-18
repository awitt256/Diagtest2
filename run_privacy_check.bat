@echo off
rem Batch wrapper to execute the PowerShell privacy screen detection script
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0DetectPrivacyScreen.ps1"