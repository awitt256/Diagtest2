@echo off
setlocal

:: ------------------------------------------------------------------
:: FULLSCREEN SPLASH SAFELY USING WINFORMS (WORKS ON ALL WINDOWS)
:: ------------------------------------------------------------------
powershell -noprofile -executionpolicy bypass -command ^
"$img = '%~dp0dtt.png'; ^
 if (Test-Path $img) { ^
    Add-Type -AssemblyName System.Windows.Forms; ^
    Add-Type -AssemblyName System.Drawing; ^
    $form = New-Object System.Windows.Forms.Form; ^
    $form.FormBorderStyle = 'None'; ^
    $form.WindowState = 'Maximized'; ^
    $form.TopMost = $true; ^
    $form.BackColor = 'Black'; ^
    $form.StartPosition = 'CenterScreen'; ^

    $picture = New-Object System.Windows.Forms.PictureBox; ^
    $picture.Image = [System.Drawing.Image]::FromFile($img); ^
    $picture.SizeMode = 'Zoom'; ^
    $picture.Dock = 'Fill'; ^
    $form.Controls.Add($picture); ^

    $form.Show(); ^
    Start-Sleep 2; ^
    $form.Close(); ^
 }
"

:: ------------------------------------------------------------------
:: RUN MAIN SCRIPT
:: ------------------------------------------------------------------
call "%~dp0dtt-batch.bat"
exit