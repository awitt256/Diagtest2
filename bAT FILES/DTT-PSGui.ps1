# ============================================================
# DTT GUI – CLEAN, STABLE, NO-CRASH VERSION
# ============================================================

$ErrorActionPreference = "SilentlyContinue"

Add-Type -AssemblyName PresentationFramework
Add-Type -AssemblyName System.Windows.Forms

# ---------------- DARK MODE COLORS ----------------
$BGColor     = "#1e1e1e"
$TileBG      = "#2d2d2d"
$TileHover   = "#3b3b3b"
$TileText    = "White"
$SearchBG    = "#333333"
$SearchFG    = "White"
$OutputBG    = "#1a1a1a"
$OutputFG    = "#c9c9c9"

# ---------------- MAIN WINDOW ----------------
$Window = New-Object System.Windows.Window
$Window.Title = "Diagnostics Test Tool v66"
$Window.Width = 1200
$Window.Height = 750
$Window.Background = $BGColor
$Window.WindowStartupLocation = "CenterScreen"
$Window.FontFamily = "Segoe UI"

# WPF-safe error handler
$Window.Add_DispatcherUnhandledException({
    param($sender,$args)
    [System.Windows.MessageBox]::Show("Error: $($args.Exception.Message)", "DTT Error")
    $args.Handled = $true
})

# ---------------- GRID LAYOUT ----------------
$Grid = New-Object System.Windows.Controls.Grid
$Grid.Margin = "10"
$Window.Content = $Grid

$Grid.RowDefinitions.Add((New-Object System.Windows.Controls.RowDefinition)) 
$Grid.RowDefinitions.Add((New-Object System.Windows.Controls.RowDefinition)) 
$Grid.RowDefinitions.Add((New-Object System.Windows.Controls.RowDefinition)) 

$Grid.RowDefinitions[0].Height = "60"
$Grid.RowDefinitions[1].Height = "*"
$Grid.RowDefinitions[2].Height = "260"

# ---------------- SEARCH BAR ----------------
$SearchBox = New-Object System.Windows.Controls.TextBox
$SearchBox.FontSize = 20
$SearchBox.Margin = "5"
$SearchBox.Padding = "10"
$SearchBox.Background = $SearchBG
$SearchBox.Foreground = $SearchFG
$SearchBox.ToolTip = "Type to search"
$Grid.Children.Add($SearchBox)
[System.Windows.Controls.Grid]::SetRow($SearchBox, 0)

# --- SCROLLING TILE PANEL WITH INVISIBLE SCROLLBAR ---
$TileScroll = New-Object System.Windows.Controls.ScrollViewer
$TileScroll.VerticalScrollBarVisibility = "Hidden"   # Hide scrollbar but allow scroll
$TileScroll.HorizontalScrollBarVisibility = "Disabled"
$TileScroll.Margin = "10"
$TileScroll.PanningMode = "VerticalOnly"             # Enables touch/trackpad scroll
$TileScroll.CanContentScroll = $true

# WrapPanel inside ScrollViewer
$TileWrap = New-Object System.Windows.Controls.WrapPanel
$TileWrap.ItemWidth = 170
$TileWrap.ItemHeight = 100
$TileWrap.HorizontalAlignment = "Center"
$TileWrap.VerticalAlignment = "Top"

$TileScroll.Content = $TileWrap
$Grid.Children.Add($TileScroll)
[System.Windows.Controls.Grid]::SetRow($TileScroll, 1)
# ---------------- OUTPUT BOX ----------------
$OutputBox = New-Object System.Windows.Controls.TextBox
$OutputBox.FontSize = 14
$OutputBox.IsReadOnly = $true
$OutputBox.TextWrapping = "Wrap"
$OutputBox.Background = $OutputBG
$OutputBox.Foreground = $OutputFG
$OutputBox.VerticalScrollBarVisibility = "Auto"
$OutputBox.Padding = "10"
$Grid.Children.Add($OutputBox)
[System.Windows.Controls.Grid]::SetRow($OutputBox, 2)

# ---------------- TILE FUNCTION ----------------
function AddTile($label, $action) {

    $tile = New-Object System.Windows.Controls.Button
    $tile.Width = 170
    $tile.Height = 100
    $tile.Margin = "10"
    $tile.Background = $TileBG
    $tile.Foreground = $TileText
    $tile.BorderBrush = "#555"
    $tile.Padding = "0"
    $tile.HorizontalContentAlignment = "Center"
    $tile.VerticalContentAlignment = "Center"

    # Attach ACTION to tile Tag (critical fix)
    $tile.Tag = $action

    # Centered text
    $grid = New-Object System.Windows.Controls.Grid
    $txt = New-Object System.Windows.Controls.TextBlock
    $txt.Text = $label
    $txt.FontSize = 14
    $txt.Foreground = "White"
    $txt.TextAlignment = "Center"
    $txt.HorizontalAlignment = "Center"
    $txt.VerticalAlignment = "Center"
    $txt.TextWrapping = "Wrap"
    $grid.Children.Add($txt)
    $tile.Content = $grid

    # Hover
    $tile.Add_MouseEnter({ param($s,$e) $s.Background = $TileHover })
    $tile.Add_MouseLeave({ param($s,$e) $s.Background = $TileBG })

    # CLICK HANDLER – grab real action from tile.Tag
    $tile.Add_Click({
        $labelCopy = $label
        $actionToRun = $this.Tag
    
        $OutputBox.AppendText("`n>>> Running: $labelCopy`n")
        $OutputBox.ScrollToEnd()
    
        Start-Job -ScriptBlock {
            param($action)
    
            if ($action -is [scriptblock]) {
                & $action 2>&1 | Out-String
            }
            elseif ($action -is [string]) {
                cmd /c $action 2>&1 | Out-String
            }
            else {
                "Invalid action."
            }
        } -ArgumentList $actionToRun | Out-Null
    
        # Poll job output without freezing GUI
        $jobWatcher = {
            $jobs = Get-Job | Where-Object { $_.State -eq "Completed" }
            foreach ($job in $jobs) {
                $result = Receive-Job $job
                Remove-Job $job -Force
    
                $Window.Dispatcher.Invoke({
                    $OutputBox.AppendText("$result`n")
                    $OutputBox.ScrollToEnd()
                })
            }
        }
    
        # Use async timer to check job completion safely
        $timer = New-Object System.Windows.Threading.DispatcherTimer
        $timer.Interval = [TimeSpan]::FromMilliseconds(200)
        $timer.Add_Tick($jobWatcher)
        $timer.Start()
    })
    
    $Script:AllTiles += $tile
    $TileWrap.Children.Add($tile)
}
$Script:AllTiles = @()

# ---------------- ALL 43 TILES (CLEANED & FIXED) ----------------
function Get-SystemInfoReport {

    $output = New-Object System.Text.StringBuilder
    $append = { param($t) $output.AppendLine($t) | Out-Null }

    & $append "==============================================================="
    & $append "                   SYSTEM INFORMATION REPORT"
    & $append "==============================================================="
    & $append ""
    & $append "Generated: $(Get-Date)"
    & $append ""

    & $append "==============================================================="
    & $append "                      SYSTEM IDENTIFICATION"
    & $append "==============================================================="
    & $append ""

    # SYSTEM
    & $append "[System]"
    try {
        $cs = Get-CimInstance Win32_ComputerSystem
        & $append "Manufacturer : $($cs.Manufacturer)"
        & $append "Model        : $($cs.Model)"
        & $append "System SKU   : $($cs.SystemSKUNumber)"
    } catch {
        & $append "Error retrieving system information"
    }

    & $append ""
    & $append "[BIOS]"
    try {
        $bios = Get-CimInstance Win32_BIOS
        & $append "Serial Number: $($bios.SerialNumber)"
    } catch {
        & $append "Error retrieving BIOS information"
    }

    # STORAGE
    & $append ""
    & $append "==============================================================="
    & $append "                       STORAGE INFORMATION"
    & $append "==============================================================="
    & $append ""

    & $append "Logical Drive Information:"
    try {
        Get-CimInstance Win32_LogicalDisk | Where-Object { $_.DriveType -eq 3 } |
        ForEach-Object {
            $totalGB = [math]::Round($_.Size / 1GB, 1)
            $freeGB  = [math]::Round($_.FreeSpace / 1GB, 1)
            $usedGB  = [math]::Round(($_.Size - $_.FreeSpace) / 1GB, 1)
            & $append "  Drive $($_.Caption) - Total: $totalGB GB, Free: $freeGB GB, Used: $usedGB GB"
        }
    } catch {
        & $append "  Error retrieving drive information"
    }

    & $append ""
    & $append "Physical Disk Information:"
    try {
        Get-CimInstance Win32_DiskDrive | ForEach-Object {
            $sizeGB = [math]::Round($_.Size / 1GB, 0)
            & $append "  $($_.Model) - $sizeGB GB"
        }
    } catch {
        & $append "  Error retrieving physical disk information"
    }

    # MEMORY
    & $append ""
    & $append "==============================================================="
    & $append "                       MEMORY INFORMATION"
    & $append "==============================================================="
    & $append ""

    & $append "Total System Memory:"
    try {
        $ramGB = [math]::Round($cs.TotalPhysicalMemory / 1GB, 1)
        & $append "  Total RAM: $ramGB GB"
    } catch {
        & $append "  Not Available"
    }

    & $append ""
    & $append "Memory Modules:"
    try {
        Get-CimInstance Win32_PhysicalMemory | ForEach-Object {
            $capGB = [math]::Round($_.Capacity / 1GB, 0)
            $speed = if ($_.Speed) { "$($_.Speed) MHz" } else { "Unknown Speed" }
            $mfg   = if ($_.Manufacturer) { $_.Manufacturer.Trim() } else { "Unknown" }
            & $append "  Module: $capGB GB, $speed, $mfg"
        }
    } catch {
        & $append "  Error retrieving memory module information"
    }

    # GRAPHICS
    & $append ""
    & $append "==============================================================="
    & $append "                      GRAPHICS INFORMATION"
    & $append "==============================================================="
    & $append ""

    & $append "Graphics Cards:"
    try {
        Get-CimInstance Win32_VideoController | ForEach-Object {
            if ($_.AdapterRAM -and $_.AdapterRAM -gt 0) {
                $vramGB = [math]::Round($_.AdapterRAM / 1GB, 1)
                if ($vramGB -lt 1) {
                    $vramMB = [math]::Round($_.AdapterRAM / 1MB, 0)
                    & $append "  $($_.Name) - $vramMB MB"
                } else {
                    & $append "  $($_.Name) - $vramGB GB"
                }
            } else {
                & $append "  $($_.Name) - VRAM: Not Available"
            }
        }
    } catch {
        & $append "  Error retrieving graphics information"
    }

    # CPU
    & $append ""
    & $append "==============================================================="
    & $append "                      PROCESSOR INFORMATION"
    & $append "==============================================================="
    & $append ""

    try {
        $cpu = Get-CimInstance Win32_Processor | Select-Object -First 1
        & $append "Processor: $($cpu.Name)"
        & $append "  Cores: $($cpu.NumberOfCores)"
        & $append "  Logical CPUs: $($cpu.NumberOfLogicalProcessors)"
        & $append "  Max Speed: $($cpu.MaxClockSpeed) MHz"
    } catch {
        & $append "  CPU information unavailable"
    }

    # OS
    & $append ""
    & $append "==============================================================="
    & $append "                   OPERATING SYSTEM INFORMATION"
    & $append "==============================================================="
    & $append ""

    try {
        $os = Get-CimInstance Win32_OperatingSystem
        & $append "Operating System: $($os.Caption)"
        & $append "Version: $($os.Version)"
        & $append "Architecture: $($os.OSArchitecture)"
    } catch {
        & $append "  OS information unavailable"
    }

    & $append ""
    & $append "System Name: $env:COMPUTERNAME"
    & $append "Current User: $env:USERNAME"

    # SUMMARY
    & $append ""
    & $append "==============================================================="
    & $append "                            SUMMARY"
    & $append "==============================================================="
    & $append ""

    try {
        & $append "Model: $($cs.Model)"
        & $append "Serial: $($bios.SerialNumber)"
        & $append "RAM: $ramGB GB"
    } catch {
        & $append "Summary not available"
    }

    & $append "Computer: $env:COMPUTERNAME"
    & $append "User: $env:USERNAME"
    & $append "Date: $(Get-Date)"
    & $append "==============================================================="

    return $output.ToString()
}

AddTile "System Info" {
    $OutputBox.AppendText("Running System Info...`n")
    $OutputBox.AppendText( (Get-SystemInfoReport) + "`n" )
    $OutputBox.ScrollToEnd()
}

AddTile "Bitlocker Check"           "$PSScriptRoot\Tools\bitlockercheck1.bat"
AddTile "Hotkeys Test" "powershell.exe -NoExit -File `"$PSScriptRoot\Tools\HK.ps1`""AddTile "Device Manager"            "start devmgmt.msc"
AddTile "Battery Test"              "start `"$PSScriptRoot\Apps\bat`""
AddTile "Speaker Test"              "start `"$PSScriptRoot\Media\st.mp3`""
AddTile "Mic Test"                  "start `"$PSScriptRoot\Apps\soundcheck.exe`""
AddTile "Camera Test"               "start microsoft.windows.camera:"
AddTile "Windows Activation"        "$PSScriptRoot\Tools\ACT.bat"
AddTile "Keyboard Test"             "start `"$PSScriptRoot\Apps\KBtest.exe`""
AddTile "Notepad"                   "start notepad"
AddTile "Windows Update"            "start ms-settings:windowsupdate"
AddTile "Windows Test"              "$PSScriptRoot\Tools\windowsTest.bat"
AddTile "Serial & SKU"              "powershell -command `"Get-CimInstance Win32_BIOS | ft SerialNumber`""
AddTile "Audio Output"              "$PSScriptRoot\Tools\AUDIOrun.bat"
AddTile "SFC Scan"                  "sfc /scannow"
AddTile "SMART Health"              "powershell -command `"Get-CimInstance Win32_DiskDrive | ft Model,Status`""
AddTile "Memory Test"               "mdsched.exe"
AddTile "Disk Cleanup"              "cleanmgr"
AddTile "Stress Test Suite"         "$PSScriptRoot\Tools\stressSuite.bat"
AddTile "Performance Tests"         "$PSScriptRoot\Tools\performanceTests.bat"
AddTile "USB Port Test"             "start `"$PSScriptRoot\Apps\USBTreeView.exe`""
AddTile "SSD Info"                  "start `"$PSScriptRoot\Apps\CrystalDiskInfo.exe`""
AddTile "Network Settings"          "start ms-settings:network"
AddTile "WiFi Info"                 "netsh wlan show interfaces"
AddTile "Camera Settings"           "start ms-settings:privacy-webcam"
AddTile "Activation Settings"       "start ms-settings:activation"
AddTile "Sound Settings"            "start ms-settings:sound"
AddTile "Account Menu"              "start ms-settings:otherusers"
AddTile "Date/Time Settings"        "start ms-settings:dateandtime"
AddTile "Region & Language"         "start ms-settings:regionlanguage"
AddTile "Windows Defender"          "$PSScriptRoot\Tools\wd.bat"
AddTile "Check Windows Key"         "start `"$PSScriptRoot\Apps\WK.exe`""
AddTile "Windows Version"           "start winver"
AddTile "Computrace Check"          "$PSScriptRoot\Tools\Computrace.bat"
AddTile "Sysprep Options"           "$PSScriptRoot\Tools\Sysprep.bat"
AddTile "Task Manager" {
    $psi = New-Object System.Diagnostics.ProcessStartInfo
    $psi.FileName = "C:\Windows\System32\Taskmgr.exe"
    $psi.UseShellExecute = $true
    [System.Diagnostics.Process]::Start($psi) | Out-Null
}
AddTile "Clear Temp Files"          "$PSScriptRoot\Tools\cleartemp.bat"
AddTile "Restart"                   "shutdown /r /t 0"
AddTile "Shutdown"                  "shutdown /s /t 0"
AddTile "Exit Program"              "exit"

# ---------------- REAL-TIME SEARCH ----------------
$SearchBox.Add_TextChanged({
    $filter = $SearchBox.Text.ToLower()
    $TileWrap.Children.Clear()
    foreach ($tile in $Script:AllTiles) {
        if ($tile.Content.ToLower().Contains($filter)) {
            $TileWrap.Children.Add($tile)
        }
    }
})

# ---------------- RUN WINDOW ----------------
$Window.ShowDialog() | Out-Null