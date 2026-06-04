@echo off
cls

echo Running enrollment test...
call enroll

echo Checking Bitlocker...
CALL BITLOCKERCHECK1.BAT

set /p enrolled=Was this unit previously enrolled (Y/N)? 

if /i "%enrolled%"=="Y" (
    call escript
) else (
    goto menu
)
