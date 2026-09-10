START ENROLL
TIMEOUT 15 
@echo off
set /p enrolled=Is unit enrolled? (Y/N): 
if /I "%enrolled%"=="N" (
    call sd.bat
)