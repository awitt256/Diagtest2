@echo off
REM =====================================================
REM Windows Test Tool Launch Script
REM =====================================================
REM This script launches the Windows Test - Close the Loop application
REM with specific configuration parameters for automated testing.

@echo off
REM =====================================================
REM Windows Test Tool Launch Script
REM =====================================================
REM This script launches the Windows Test - Close the Loop application
REM with specific configuration parameters for automated testing.
REM
REM ARGUMENTS:
REM ----------
REM --tenantId=<GUID>
REM   Description: Unique identifier for the tenant/organization
REM   Example: --tenantId=36650844-da39-4b72-bf8f-ec989db49a27
REM   Required: Yes
REM
REM --finalAction=<action>
REM   Description: Specifies the final action to perform after testing
REM   Valid values: sysprep or shutdown
REM   Example: --finalAction=sysprep
REM   Required: Yes
REM
REM USAGE EXAMPLES:
REM --------------
REM Basic usage with sysprep:
REM   launch-tool.bat
REM
REM Custom tenant ID with shutdown:
REM   "Windows Test - Close the Loop.exe" --tenantId=36650844-da39-4b72-bf8f-ec989db49a27 --finalAction=shutdown
REM
REM Custom tenant ID with restart:
REM   "Windows Test - Close the Loop.exe" --tenantId=36650844-da39-4b72-bf8f-ec989db49a27 --finalAction=restart
REM
REM No final action (manual control):
REM   "Windows Test - Close the Loop.exe" --tenantId=36650844-da39-4b72-bf8f-ec989db49a27 --finalAction=none
REM
REM =====================================================

REM -----------------------------------------------------
REM Capture computer serial number (BIOS / system product)
REM Uses PowerShell CIM/WMI, works across vendors
REM Fallback sets value to 'unknown' if retrieval fails
REM -----------------------------------------------------
setlocal EnableDelayedExpansion

set "SERIAL_NUMBER="

for /f "delims=" %%A in ('powershell.exe -NoProfile -ExecutionPolicy Bypass -Command "try { $sn = (Get-CimInstance -ClassName Win32_BIOS -ErrorAction Stop).SerialNumber; if ([string]::IsNullOrWhiteSpace($sn)) { $sn = (Get-CimInstance -ClassName Win32_ComputerSystemProduct -ErrorAction Stop).IdentifyingNumber } $sn = $sn.Trim(); $sn } catch { try { $sn = (Get-WmiObject -Class Win32_BIOS).SerialNumber; if ([string]::IsNullOrWhiteSpace($sn)) { $sn = (Get-WmiObject -Class Win32_ComputerSystemProduct).IdentifyingNumber } $sn = $sn.Trim(); $sn } catch { '' } }"') do set "SERIAL_NUMBER=%%A"

if not defined SERIAL_NUMBER set "SERIAL_NUMBER=unknown"

REM Launch audio8.ps1 in PowerShell
PowerShell -NoProfile -ExecutionPolicy Bypass -File "%~dp0audio9ps1.ps1"
if %errorlevel% neq 0 (
	echo audio9ps1.ps1 failed. Aborting Windows Test launch.
	exit /b %errorlevel%
)
"Windows Test - Close the Loop.exe" --tenantId=36650844-da39-4b72-bf8f-ec989db49a27 --finalAction=sysprep --lang=en-US --serialNumber=%SERIAL_NUMBER% --no-sandbox
