# ============================================================================
# DIAGNOSTICS TEST TOOL v65
# Built by Anthony Witt (2026)
# Full WPF GUI Application (Theme 5 — OEM Hardware Tool Style)
# Layout: Compact OEM Panel Grid
# Output Mode: Embedded console
# ============================================================================

Add-Type -AssemblyName PresentationCore,PresentationFramework,WindowsBase,system.windows.forms

# ---------------------------------------------
# WINDOW + OEM THEME BRUSHES
# ---------------------------------------------

$Window = New-Object Windows.Window
$Window.Title = "Diagnostics Test Tool v65 — Built by Anthony Witt"
$Window.Width = 1200
$Window.Height = 800
$Window.ResizeMode = "NoResize"
$Window.WindowStartupLocation = "CenterScreen"
$Window.Background = "#3A3A3A"  # OEM dark gray

# OEM brushes
$BrushPanel = New-Object Windows.Media.SolidColorBrush (Windows.Media.Color]::FromRgb(58,58,58))
$BrushButton = New-Object Windows.Media.SolidColorBrush ([Windows.Media.Color]::FromRgb(85,85,85))
$BrushButtonHover = New-Object Windows.Media.SolidColorBrush ([Windows.Media.Color]::FromRgb(110,110,110))
$BrushButtonClick = New-Object Windows.Media.SolidColorBrush ([Windows.Media.Color]::FromRgb(150,150,150))
$BrushText = "White"

# ---------------------------------------------
# MAIN LAYOUT GRID
# ---------------------------------------------
$Grid = New-Object Windows.Controls.Grid
$Grid.RowDefinitions.Add((New-Object Windows.Controls.RowDefinition))       # Search + Header
$Grid.RowDefinitions.Add((New-Object Windows.Controls.RowDefinition))       # Tool Panels
$Grid.RowDefinitions.Add((New-Object Windows.Controls.RowDefinition))       # Output Console

$Grid.RowDefinitions[0].Height = "auto"
$Grid.RowDefinitions[1].Height = "*"
$Grid.RowDefinitions[2].Height = "200"

$Window.Content = $Grid

# ============================================================================
#  TOP HEADER + SEARCH BAR
# ============================================================================

$HeaderPanel = New-Object Windows.Controls.StackPanel
$HeaderPanel.Orientation = "Vertical"
$HeaderPanel.Margin = "20"
$HeaderPanel.HorizontalAlignment = "Stretch"

$Title = New-Object Windows.Controls.TextBlock
$Title.Text = "Diagnostics Test Tool v65"
$Title.FontSize = 32
$Title.Foreground = $BrushText
$Title.Margin = "0,0,0,10"
$Title.FontWeight = "Bold"

$SearchPanel = New-Object Windows.Controls.StackPanel
$SearchPanel.Orientation = "Horizontal"
$SearchPanel.HorizontalAlignment = "Left"

$SearchLabel = New-Object Windows.Controls.TextBlock
$SearchLabel.Text = "Search:"
$SearchLabel.Foreground = $BrushText
$SearchLabel.FontSize = 18
$SearchLabel.Margin = "0,0,10,0"

$SearchBox = New-Object Windows.Controls.TextBox
$SearchBox.Width = 350
$SearchBox.FontSize = 18
$SearchBox.Margin = "0,0,0,10"

$SearchPanel.Children.Add($SearchLabel)
$SearchPanel.Children.Add($SearchBox)
$HeaderPanel.Children.Add($Title)
$HeaderPanel.Children.Add($SearchPanel)

[Windows.Controls.Grid]::SetRow($HeaderPanel, 0)
$Grid.Children.Add($HeaderPanel)

# ============================================================================
#  TOOL PANEL LAYOUT  (Compact OEM Grid)
# ============================================================================

$Panels = New-Object Windows.Controls.WrapPanel
$Panels.Margin = "20"
$Panels.HorizontalAlignment = "Left"

[Windows.Controls.Grid]::SetRow($Panels, 1)
$Grid.Children.Add($Panels)

function New-DiagButton($Label, $Action) {
    $Btn = New-Object Windows.Controls.Button
    $Btn.Content = $Label
    $Btn.Background = $BrushButton
    $Btn.Foreground = $BrushText
    $Btn.FontSize = 18
    $Btn.Width = 250
    $Btn.Height = 60
    $Btn.Margin = "10"
    $Btn.BorderBrush = "Black"
    $Btn.BorderThickness = 2

    $Btn.Add_MouseEnter({
        $_.Source.Background = $BrushButtonHover
    })
    $Btn.Add_MouseLeave({
        $_.Source.Background = $BrushButton
    })
    $Btn.Add_MouseDown({
        $_.Source.Background = $BrushButtonClick
    })
    $Btn.Add_MouseUp({
        $_.Source.Background = $BrushButton
    })

    $Btn.Add_Click({
        Invoke-DiagAction $Action
    })

    return $Btn
}

# ============================================================================
#  OUTPUT CONSOLE
# ============================================================================

$OutputBox = New-Object Windows.Controls.TextBox
$OutputBox.Background = "Black"
$OutputBox.Foreground = "Lime"
$OutputBox.FontFamily = "Consolas"
$OutputBox.FontSize = 16
$OutputBox.IsReadOnly = $true
$OutputBox.TextWrapping = "Wrap"
$OutputBox.VerticalScrollBarVisibility = "Visible"
$OutputBox.HorizontalScrollBarVisibility = "Disabled"
$OutputBox.Margin = "10"

[Windows.Controls.Grid]::SetRow($OutputBox, 2)
$Grid.Children.Add($OutputBox)

function Write-Log($msg) {
    $OutputBox.AppendText("$msg`n")
    $OutputBox.ScrollToEnd()
}

# ============================================================================
# ACTION WRAPPER  
# ============================================================================
function Invoke-DiagAction($Action) {
    Write-Log ">>> Running: $Action"

    switch ($Action) {

        "SystemInfo"          { Get-CimInstance Win32_ComputerSystem | Out-String | Write-Log }
        "Bitlocker"           { manage-bde -status | Out-String | Write-Log }
        "HotkeysTest"         { Write-Log "Hotkey test tool pending external EXE call..." }
        "DeviceManager"       { Start-Process devmgmt.msc }
        "BatteryTest"         { powercfg /batteryreport | Out-String | Write-Log }
        "SpeakerTest"         { Write-Log "Playing test sound..."; Start-Process "st.mp3" }
        "MicTest"             { Start-Process "soundcheck.exe" }
        "CameraTest"          { Start-Process "microsoft.windows.camera:" }
        "Activation"          { slmgr /xpr | Out-String | Write-Log }
        "KeyboardTest"        { Start-Process "kb.exe" }
        "Notepad"             { Start-Process notepad.exe }
        "WindowsUpdate"       { Write-Log "Launching Windows Update..." }
        "WindowsTest"         { Start-Process "launch-tool.bat" }
        "SerialSKU"           { Get-CimInstance Win32_BIOS | Out-String | Write-Log }
        "AudioSwitch"         { Start-Process ".\AUDIOrun.bat" }
        "SFC"                 { sfc /scannow | Out-String | Write-Log }
        "SMART"               { Get-CimInstance Win32_DiskDrive | Out-String | Write-Log }
        "MemoryDiagnostic"    { Start-Process "mdsched.exe" }
        "DiskCleanup"         { Start-Process cleanmgr.exe }
        "StressSuite"         { Start-Process "occt.exe" }
        "PerformanceTests"    { Start-Process "Install-PerfTest-WithWinget.bat" }
        "USBPortTest"         { Start-Process "USBTreeView.exe" }
        "SSDTest"             { Start-Process "CrystalDiskInfo.exe" }
        "NetworkSettings"     { Start-Process "ms-settings:network" }
        "WiFiInfo"            { netsh wlan show interfaces | Out-String | Write-Log }
        "CameraSettings"      { Start-Process "ms-settings:privacy-webcam" }
        "ActivationSettings"  { Start-Process "ms-settings:activation" }
        "SoundSettings"       { Start-Process "ms-settings:sound" }
        "AccountMenu"         { Start-Process "control.exe" "/name Microsoft.UserAccounts" }
        "DateTimeSettings"    { Start-Process "ms-settings:dateandtime" }
        "LanguageRegion"      { Start-Process "ms-settings:regionlanguage" }
        "Defender"            { Start-Process "wd.bat" }
        "CheckKey"            { Start-Process "WK.exe" }
        "WindowsVersion"      { Start-Process "winver.exe" }
        "Computrace"          { Start-Process ".\Computrace.bat" }
        "Sysprep"             { Start-Process "sysprep.exe" }
        "TaskManager"         { Start-Process taskmgr.exe }
        "EventViewer"         { Start-Process eventvwr.msc }
        "ClearTemp"           {
            Write-Log "Clearing temporary files..."
            Remove-Item "$env:TEMP\*" -Recurse -Force -ErrorAction SilentlyContinue
            Write-Log "Done."
        }
        "Restart"             { Restart-Computer -Force }
        "Shutdown"            { Stop-Computer -Force }
        default               { Write-Log "Unknown Action: $Action" }
    }
}

# ============================================================================
# CREATE ALL BUTTONS
# ============================================================================

$ButtonMap = @{
    "System Info"          = "SystemInfo"
    "Bitlocker Check"      = "Bitlocker"
    "Hotkeys Test"         = "HotkeysTest"
    "Device Manager"       = "DeviceManager"
    "Battery Test"         = "BatteryTest"
    "Speaker Test"         = "SpeakerTest"
    "Mic Test"             = "MicTest"
    "Camera Test"          = "CameraTest"
    "Windows Activation"   = "Activation"
    "Keyboard Test"        = "KeyboardTest"
    "Notepad"              = "Notepad"
    "Windows Update"       = "WindowsUpdate"
    "Windows Test"         = "WindowsTest"
    "Show Serial/SKU"      = "SerialSKU"
    "Audio Output"         = "AudioSwitch"
    "System File Checker"  = "SFC"
    "SMART Drive Health"   = "SMART"
    "Memory Diagnostic"    = "MemoryDiagnostic"
    "Disk Cleanup"         = "DiskCleanup"
    "Stress Test Suite"    = "StressSuite"
    "Performance Tests"    = "PerformanceTests"
    "USB Port Test"        = "USBPortTest"
    "SSD Test"             = "SSDTest"
    "Network Settings"     = "NetworkSettings"
    "WiFi Info"            = "WiFiInfo"
    "Camera Settings"      = "CameraSettings"
    "Activation Settings"  = "ActivationSettings"
    "Sound Settings"       = "SoundSettings"
    "Account Menu"         = "AccountMenu"
    "Date/Time Settings"   = "DateTimeSettings"
    "Language/Region"      = "LanguageRegion"
    "Defender"             = "Defender"
    "Windows Key"          = "CheckKey"
    "Windows Version"      = "WindowsVersion"
    "Computrace Check"     = "Computrace"
    "Sysprep Options"      = "Sysprep"
    "Task Manager"         = "TaskManager"
    "Event Viewer"         = "EventViewer"
    "Clear Temp Files"     = "ClearTemp"
    "Restart"              = "Restart"
    "Shutdown"             = "Shutdown"
}

foreach ($item in $ButtonMap.GetEnumerator()) {
    $Panels.Children.Add( (New-DiagButton $item.Key $item.Value) )
}

# ============================================================================
# SEARCH FILTERING
# ============================================================================
$SearchBox.Add_TextChanged({
    $query = $SearchBox.Text.ToLower()

    foreach ($btn in $Panels.Children) {
        if ($btn.Content.ToLower().Contains($query)) {
            $btn.Visibility = "Visible"
        } else {
            $btn.Visibility = "Collapsed"
        }
    }
})

# ============================================================================
# RUN APPLICATION
# ============================================================================
$Window.ShowDialog() | Out-Null