::[Bat To Exe Converter]
::
::YAwzoRdxOk+EWAjk
::fBw5plQjdCyDJGyX8VAjFDpaWAyNMnKGIrAP4/z0/9aQq0NdQOcsbM+JlOHAcbcv7lHwO58u2Ro=
::YAwzuBVtJxjWCl3EqQJgSA==
::ZR4luwNxJguZRRnk
::Yhs/ulQjdF+5
::cxAkpRVqdFKZSzk=
::cBs/ulQjdF+5
::ZR41oxFsdFKZSDk=
::eBoioBt6dFKZSDk=
::cRo6pxp7LAbNWATEpCI=
::egkzugNsPRvcWATEpCI=
::dAsiuh18IRvcCxnZtBJQ
::cRYluBh/LU+EWAnk
::YxY4rhs+aU+IeA==
::cxY6rQJ7JhzQF1fEqQIGZk0DLA==
::ZQ05rAF9IBncCkqN+0xwdVs0
::ZQ05rAF9IAHYFVzEqQJQ
::eg0/rx1wNQPfEVWB+kM9LVsJDGQ=
::fBEirQZwNQPfEVWB+kM9LVsJDGQ=
::cRolqwZ3JBvQF1fEqQJQ
::dhA7uBVwLU+EWDk=
::YQ03rBFzNR3SWATElA==
::dhAmsQZ3MwfNWATElA==
::ZQ0/vhVqMQ3MEVWAtB9wSA==
::Zg8zqx1/OA3MEVWAtB9wSA==
::dhA7pRFwIByZRRnk
::Zh4grVQjdCyDJGyX8VAjFDpaWAyNMnKGIrAP4/z0/9aQq0NdQOcsbM+JlOHAcbcvznHQJNgozn86
::YB416Ek+ZG8=
::
::
::978f952a14a936cc963da21a135fa983
@echo off
cd /d "%~dp0"

:: SHOW SPLASH IMAGE (NO CONSOLE)
powershell -noprofile -nologo -windowstyle hidden ^
  Add-Type -AssemblyName PresentationCore,PresentationFramework; ^
  $img = "%~dp0dtt.png"; ^
  if (Test-Path $img) { ^
      $bm = New-Object System.Windows.Media.Imaging.BitmapImage; ^
      $bm.BeginInit(); ^
      $bm.UriSource = $img; ^
      $bm.EndInit(); ^
      $w = New-Object System.Windows.Window; ^
      $w.WindowStyle = 'None'; ^
      $w.ResizeMode = 'NoResize'; ^
      $w.WindowStartupLocation = 'CenterScreen'; ^
      $w.AllowsTransparency = $true; ^
      $w.Topmost = $true; ^
      $w.Background = 'Transparent'; ^
      $imgCtrl = New-Object System.Windows.Controls.Image; ^
      $imgCtrl.Source = $bm; ^
      $w.Content = $imgCtrl; ^
      $w.Width  = $bm.PixelWidth; ^
      $w.Height = $bm.PixelHeight; ^
      $w.Show(); ^
      Start-Sleep 3; ^
      $w.Close(); ^
  }

:: SHOW REAL CONSOLE FOR dtt.bat  
start "" cmd.exe /k "%~dp0dtt.bat"
exit