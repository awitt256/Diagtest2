@echo off
set "target=C:\Program Files (x86)\HP\HP Software Framework"

if exist "%target%\" (
  echo Software framework already installed.
) else (
  echo Installing software framework driver...
  if exist "%~dp0sf.exe" (
    echo Running sf.exe from script directory...
    "%~dp0sf.exe"
  ) else (
    echo sf.exe not found in script directory "%~dp0".
    echo Attempting to run sf.exe from PATH...
    sf.exe || echo Failed to start sf.exe.
  )
)

REM Ask user whether to restart
:askRestart
set /p "ans=Do you want to restart? (y/n): "
if /i "%ans%"=="y" (
  echo Restarting now...
  shutdown /r /t 0
  goto end
) else if /i "%ans%"=="n" (
  echo Exiting.
  goto end
) else (
  echo Please answer y or n.
  goto askRestart
)

:end
exit /b 0
