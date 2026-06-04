Function Get-ESPDiagnostics {
    [CmdletBinding()]
    param(
        [Parameter(Mandatory = $False)] [String] $CABFile = $null,
        [Parameter(Mandatory = $False)] [String] $ZIPFile = $null,
        [Parameter(Mandatory = $False)] [Switch] $Online = $false,
        [Parameter(Mandatory = $False)] [Switch] $AllSessions = $false,
        [Parameter(Mandatory = $False)] [Switch] $ShowPolicies = $false,
        [Parameter(Mandatory = $false)] [string]$Tenant,
        [Parameter(Mandatory = $false)] [string]$AppId,
        [Parameter(Mandatory = $false)] [string]$AppSecret
    )

    Begin {
        $script:useFile = $false
        $tenantId = $null
        $forcedEnrollment = $null
        $forcedEnrollmentModified = $false  # Nueva variable para rastrear cambios
        $tenantIdModified = $false          # Nueva variable para rastrear cambios de TenantID
        
        try {
            $autopilotRegPath = "HKLM:\\SOFTWARE\\Microsoft\\Provisioning\\Diagnostics\\AutoPilot"
            if (Test-Path $autopilotRegPath) {
                $tenantId = (Get-ItemProperty -Path $autopilotRegPath).TenantId
                $forcedEnrollment = (Get-ItemProperty -Path $autopilotRegPath).isForcedEnrollmentEnabled
                
                # 🆕 NUEVA FUNCIONALIDAD: Limpiar EnrollmentTenantID si existe
                if ($tenantId) {
                    try {
                        Write-Host "⚠️ EnrollmentTenantID detectado: $tenantId. Limpiando..." -ForegroundColor Yellow
                        
                        # Backup del valor original
                        $originalTenantId = $tenantId
                        
                        # Limpiar el TenantId (establecer como cadena vacía o eliminar la propiedad)
                        Remove-ItemProperty -Path $autopilotRegPath -Name "TenantId" -ErrorAction SilentlyContinue
                        
                        # Verificar que se eliminó
                        $newTenantId = $null
                        try {
                            $newTenantId = (Get-ItemProperty -Path $autopilotRegPath).TenantId
                        } catch {
                            # La propiedad no existe, lo cual es lo que queremos
                        }
                        
                        if (-not $newTenantId) {
                            $tenantIdModified = $true
                            $tenantId = $null  # Actualizar la variable local
                            Write-Host "✅ EnrollmentTenantID limpiado exitosamente (era: $originalTenantId)" -ForegroundColor Green
                        } else {
                            Write-Host "❌ Error: No se pudo limpiar EnrollmentTenantID" -ForegroundColor Red
                        }
                    } catch {
                        Write-Host "❌ Error al limpiar EnrollmentTenantID: $($_.Exception.Message)" -ForegroundColor Red
                    }
                } else {
                    Write-Host "ℹ️ EnrollmentTenantID ya está vacío o no existe" -ForegroundColor Cyan
                }
                
                # ⚠️ FUNCIONALIDAD: Verificar y cambiar ForcedEnrollment si está habilitado
                if ($forcedEnrollment -eq 1) {
                    try {
                        Write-Host "⚠️ ForcedEnrollment detectado como habilitado (1). Cambiando a deshabilitado (0)..." -ForegroundColor Yellow
                        Set-ItemProperty -Path $autopilotRegPath -Name "isForcedEnrollmentEnabled" -Value 0
                        
                        # Verificar que el cambio se aplicó correctamente
                        $newValue = (Get-ItemProperty -Path $autopilotRegPath).isForcedEnrollmentEnabled
                        if ($newValue -eq 0) {
                            $forcedEnrollmentModified = $true
                            $forcedEnrollment = 0  # Actualizar la variable local
                            Write-Host "✅ ForcedEnrollment cambiado exitosamente a 0" -ForegroundColor Green
                        } else {
                            Write-Host "❌ Error: No se pudo cambiar ForcedEnrollment" -ForegroundColor Red
                        }
                    } catch {
                        Write-Host "❌ Error al modificar ForcedEnrollment: $($_.Exception.Message)" -ForegroundColor Red
                    }
                } else {
                    Write-Host "ℹ️ ForcedEnrollment ya está deshabilitado o no está configurado" -ForegroundColor Cyan
                }
            }
        } catch {
            # Silently continue
        }

        # Preparación de directorio temporal (para CAB/ZIP si aplica)
        if ($CABFile -or $ZIPFile) {
            if (-not (Test-Path "$($env:TEMP)\\ESPStatus.tmp")) {
                New-Item -Path "$($env:TEMP)\\ESPStatus.tmp" -ItemType "directory" | Out-Null
            }
            Remove-Item -Path "$($env:TEMP)\\ESPStatus.tmp\\*.*" -Force -Recurse
            $script:useFile = $true

            # CAB
            if ($CABFile) {
                $fileList = @(
                    "MdmDiagReport_RegistryDump.reg",
                    "microsoft-windows-devicemanagement-enterprise-diagnostics-provider-admin.evtx",
                    "microsoft-windows-user device registration-admin.evtx",
                    "AutopilotDDSZTDFile.json",
                    "*.csv"
                )
                $fileList | ForEach-Object {
                    $null = & expand.exe "$CABFile" -F:$_ "$($env:TEMP)\\ESPStatus.tmp\\"
                }
            }
            # ZIP
            else {
                Expand-Archive -Path $ZIPFile -DestinationPath "$($env:TEMP)\\ESPStatus.tmp\\"
            }

            # Procesamiento del CSV (Hardware hash)
            $csvFile = (Get-ChildItem "$($env:TEMP)\\ESPStatus.tmp\\*.csv" -ErrorAction SilentlyContinue | Select-Object -First 1).FullName
            if ($csvFile) {
                $csv = Get-Content $csvFile | ConvertFrom-Csv
                $hash = $csv.'Hardware Hash'
            }

            # Ajuste del .reg
            $content = Get-Content -Path "$($env:TEMP)\\ESPStatus.tmp\\MdmDiagReport_RegistryDump.reg"
            $content = $content -replace "\\[HKEY_CURRENT_USER\\\\", "[HKEY_CURRENT_USER\\ESPStatus.tmp\\USER\\"
            $content = $content -replace "\\[HKEY_LOCAL_MACHINE\\\\", "[HKEY_CURRENT_USER\\ESPStatus.tmp\\MACHINE\\"
            $content = $content -replace '^ "', '"'
            $content = $content -replace '^ @', '@'
            $content = $content -replace 'DWORD:', 'dword:'
            "Windows Registry Editor Version 5.00" | Set-Content -Path "$($env:TEMP)\\ESPStatus.tmp\\MdmDiagReport_Edited.reg"
            $content | Add-Content -Path "$($env:TEMP)\\ESPStatus.tmp\\MdmDiagReport_Edited.reg"

            # Limpieza en HKCU:\\ESPStatus.tmp si existía
            if (Test-Path "HKCU:\\ESPStatus.tmp") {
                Remove-Item -Path "HKCU:\\ESPStatus.tmp" -Recurse -Force
            }

            # Importar el .reg
            $null = & reg.exe IMPORT "$($env:TEMP)\\ESPStatus.tmp\\MdmDiagReport_Edited.reg" 2>&1

            # Rutas locales simuladas (offline)
            $script:provisioningPath = "HKCU:\\ESPStatus.tmp\\MACHINE\\software\\microsoft\\provisioning"
            $script:autopilotDiagPath = "HKCU:\\ESPStatus.tmp\\MACHINE\\software\\microsoft\\provisioning\\Diagnostics\\Autopilot"
            $script:omadmPath        = "HKCU:\\ESPStatus.tmp\\MACHINE\\software\\microsoft\\provisioning\\OMADM"
            $script:path             = "HKCU:\\ESPStatus.tmp\\MACHINE\\Software\\Microsoft\\Windows\\Autopilot\\EnrollmentStatusTracking\\ESPTrackingInfo\\Diagnostics"
            $script:msiPath          = "HKCU:\\ESPStatus.tmp\\MACHINE\\Software\\Microsoft\\EnterpriseDesktopAppManagement"
            $script:officePath       = "HKCU:\\ESPStatus.tmp\\MACHINE\\Software\\Microsoft\\OfficeCSP"
            $script:sidecarPath      = "HKCU:\\ESPStatus.tmp\\MACHINE\\Software\\Microsoft\\IntuneManagementExtension\\Win32Apps"
            $script:enrollmentsPath  = "HKCU:\\ESPStatus.tmp\\MACHINE\\software\\microsoft\\enrollments"
        }
        else {
            # Rutas reales (live)
            $script:provisioningPath = "HKLM:\\software\\microsoft\\provisioning"
            $script:autopilotDiagPath = "HKLM:\\software\\microsoft\\provisioning\\Diagnostics\\Autopilot"
            $script:omadmPath        = "HKLM:\\software\\microsoft\\provisioning\\OMADM"
            $script:path             = "HKLM:\\Software\\Microsoft\\Windows\\Autopilot\\EnrollmentStatusTracking\\ESPTrackingInfo\\Diagnostics"
            $script:msiPath          = "HKLM:\\Software\\Microsoft\\EnterpriseDesktopAppManagement"
            $script:officePath       = "HKLM:\\Software\\Microsoft\\OfficeCSP"
            $script:sidecarPath      = "HKLM:\\Software\\Microsoft\\IntuneManagementExtension\\Win32Apps"
            $script:enrollmentsPath  = "HKLM:\\Software\\Microsoft\\enrollments"

            # Hash en vivo
            try {
                $hash = (Get-WmiObject -Namespace root/cimv2/mdm/dmmap -Class MDM_DevDetail_Ext01 -Filter "InstanceID='Ext' AND ParentID='./DevDetail'").DeviceHardwareData
            } catch {
                $hash = $null
            }
        }

        $script:officeStatus = @{
            "0" = "None"
            "10" = "Initialized"
            "20" = "Download In Progress"
            "25" = "Pending Download Retry"
            "30" = "Download Failed"
            "40" = "Download Completed"
            "48" = "Pending User Session"
            "50" = "Enforcement In Progress"
            "55" = "Pending Enforcement Retry"
            "60" = "Enforcement Failed"
            "70" = "Success / Enforcement Completed"
        }
        $script:espStatus = @{
            "1" = "Not Installed"
            "2" = "Downloading / Installing"
            "3" = "Success / Installed"
            "4" = "Error / Failed"
        }
        $script:policyStatus = @{
            "0" = "Not Processed"
            "1" = "Processed"
        }

        # Timeline general
        $script:observedTimeline = @()
    }

    Process {
        # -----------------------------------------------------
        # Funciones internas
        # -----------------------------------------------------

        Function Connect-ToGraph {
            param(
                [Parameter(Mandatory = $false)] [string]$Tenant,
                [Parameter(Mandatory = $false)] [string]$AppId,
                [Parameter(Mandatory = $false)] [string]$AppSecret,
                [Parameter(Mandatory = $false)] [string]$scopes
            )
            Process {
                Import-Module Microsoft.Graph.Authentication -ErrorAction SilentlyContinue
                $version = (Get-Module Microsoft.Graph.Authentication | Select-Object -ExpandProperty Version).Major

                if ($AppId) {
                    $body = @{
                        grant_type    = "client_credentials"
                        client_id     = $AppId
                        client_secret = $AppSecret
                        scope         = "https://graph.microsoft.com/.default"
                    }
                    $response = Invoke-RestMethod -Method Post -Uri "https://login.microsoftonline.com/$Tenant/oauth2/v2.0/token" -Body $body
                    $accessToken = $response.access_token
                    if ($version -eq 2) {
                        $accesstokenfinal = ConvertTo-SecureString -String $accessToken -AsPlainText -Force
                    }
                    else {
                        Select-MgProfile -Name Beta
                        $accesstokenfinal = $accessToken
                    }
                    $graph = Connect-MgGraph -AccessToken $accesstokenfinal
                }
                else {
                    if ($version -eq 1) {
                        Select-MgProfile -Name Beta
                    }
                    $graph = Connect-ToGraph -Scopes $scopes
                }
                $graph
            }
        }

        Function RecordStatus {
            param(
                [Parameter(Mandatory = $true)] [String] $detail,
                [Parameter(Mandatory = $true)] [String] $status,
                [Parameter(Mandatory = $true)] [String] $color,
                [Parameter(Mandatory = $true)] [datetime] $date
            )
            $found = $script:observedTimeline | Where-Object { $_.Detail -eq $detail -and $_.Status -eq $status }
            if (-not $found) {
                if ($status -like "Downloading*") {
                    $adjustedDate = $date.AddSeconds(1)
                }
                else {
                    $adjustedDate = $date
                }
                $script:observedTimeline += [PSCustomObject]@{
                    Date   = $adjustedDate
                    Detail = $detail
                    Status = $status
                    Color  = $color
                }
            }
        }

        Function AddDisplay {
            param(
                [Parameter(Mandatory = $true)] [ref]$items
            )
            $items.Value | ForEach-Object {
                Add-Member -InputObject $_ -NotePropertyName display -NotePropertyValue $AllSessions
            }
            if ($items.Value.Count -ge 1) {
                $items.Value[$items.Value.Count - 1].display = $true
            }
        }

        Function ProcessApps {
            param(
                [Parameter(Mandatory = $true, ValueFromPipeline = $True)] [Microsoft.Win32.RegistryKey] $currentKey,
                [Parameter(Mandatory = $true)] $currentUser,
                [Parameter(Mandatory = $true, ValueFromPipelineByPropertyName = $True)] [bool] $display
            )
            Process {
                $currentKey.Property | ForEach-Object {
                    if ($_.StartsWith("./Device/Vendor/MSFT/EnterpriseDesktopAppManagement/MSI/")) {
                        $msiKey   = [URI]::UnescapeDataString(($_.Split("/"))[6])
                        $fullPath = "$msiPath\\$currentUser\\MSI\\$msiKey"
                        if (Test-Path $fullPath) {
                            $status  = (Get-ItemProperty -Path $fullPath).Status
                            $msiFile = (Get-ItemProperty -Path $fullPath).CurrentDownloadUrl
                        }
                        if (-not $status) { $status = 0 }
                        if ($msiFile -match "IntuneWindowsAgent.msi") {
                            $msiKey = "Intune Management Extensions ($msiKey)"
                        }
                        elseif ($Online) {
                            $found = $apps | Where-Object { $_.ProductCode -contains $msiKey }
                            $msiKey = "$($found.DisplayName) ($msiKey)"
                        }
                        elseif ($currentUser -eq "S-0-0-00-0000000000-0000000000-000000000-000") {
                            if (Test-Path "HKLM:\\Software\\Microsoft\\Windows\\CurrentVersion\\Uninstall\\$msiKey") {
                                $displayName = (Get-ItemProperty -Path "HKLM:\\Software\\Microsoft\\Windows\\CurrentVersion\\Uninstall\\$msiKey").DisplayName
                                $msiKey = "$displayName ($msiKey)"
                            }
                        }
                        if ($status -eq 70) {
                            RecordStatus -detail "MSI $msiKey" -status $officeStatus[$status.ToString()] -color "Green" -date $currentKey.PSChildName
                        }
                        elseif ($status -eq 60) {
                            RecordStatus -detail "MSI $msiKey" -status $officeStatus[$status.ToString()] -color "Red" -date $currentKey.PSChildName
                        }
                        else {
                            RecordStatus -detail "MSI $msiKey" -status $officeStatus[$status.ToString()] -color "Yellow" -date $currentKey.PSChildName
                        }
                    }
                    elseif ($_.StartsWith("./Vendor/MSFT/Office/Installation/")) {
                        $status    = Get-ItemPropertyValue -Path $currentKey.PSPath -Name $_
                        $officeKey = [URI]::UnescapeDataString(($_.Split("/"))[5])
                        $fullPath  = "$officepath\\$officeKey"
                        $oStatus   = $null
                        if (Test-Path $fullPath) {
                            $oStatus = (Get-ItemProperty -Path $fullPath).FinalStatus
                            if (-not $oStatus) {
                                $oStatus = (Get-ItemProperty -Path $fullPath).Status
                                if (-not $oStatus) {
                                    $oStatus = "None"
                                }
                            }
                        }
                        else {
                            $oStatus = "None"
                        }
                        if ($officeStatus.Keys -contains $oStatus.ToString()) {
                            $officeStatusText = $officeStatus[$oStatus.ToString()]
                        }
                        else {
                            $officeStatusText = $oStatus
                        }
                        if ($status -eq 1) {
                            RecordStatus -detail "Office $officeKey" -status "$($policyStatus[$status.ToString()]) / $officeStatusText" -color "Green" -date $currentKey.PSChildName
                        }
                        else {
                            RecordStatus -detail "Office $officeKey" -status "$($policyStatus[$status.ToString()]) / $officeStatusText" -color "Yellow" -date $currentKey.PSChildName
                        }
                    }
                }
            }
        }

        Function ProcessModernApps {
            param(
                [Parameter(Mandatory = $true, ValueFromPipeline = $True)] [Microsoft.Win32.RegistryKey] $currentKey,
                [Parameter(Mandatory = $true)] $currentUser,
                [Parameter(Mandatory = $true, ValueFromPipelineByPropertyName = $True)] [bool] $display
            )
            Process {
                $currentKey.Property | ForEach-Object {
                    $status = (Get-ItemPropertyValue -path $currentKey.PSPath -Name $_).ToString()
                    if ($_.StartsWith("./User/Vendor/MSFT/EnterpriseModernAppManagement/AppManagement/")) {
                        $appID = [URI]::UnescapeDataString(($_.Split("/"))[7])
                        $type  = "User UWP"
                    }
                    elseif ($_.StartsWith("./Device/Vendor/MSFT/EnterpriseModernAppManagement/AppManagement/")) {
                        $appID = [URI]::UnescapeDataString(($_.Split("/"))[7])
                        $type  = "Device UWP"
                    }
                    else {
                        $appID = $_
                        $type  = "Unknown UWP"
                    }
                    if ($status -eq "1") {
                        RecordStatus -detail "UWP $appID" -status $policyStatus[$status] -color "Green" -date $currentKey.PSChildName
                    }
                }
            }
        }

        Function ProcessSidecar {
            param(
                [Parameter(Mandatory = $true, ValueFromPipeline = $True)] [Microsoft.Win32.RegistryKey] $currentKey,
                [Parameter(Mandatory = $true)] $currentUser,
                [Parameter(Mandatory = $true, ValueFromPipelineByPropertyName = $True)] [bool] $display
            )
            Begin {
                if (-not $script:DOEvents -and (-not $script:useFile)) {
                    try {
                        $script:DOEvents = Get-DeliveryOptimizationLog |
                            Where-Object { $_.Function -match "(DownloadStart)|(DownloadCompleted)" -and $_.Message -like "*.intunewin*" }
                    } catch {
                        $script:DOEvents = $null
                    }
                }
            }
            Process {
                $currentKey.Property | ForEach-Object {
                    $win32Key = [URI]::UnescapeDataString(($_.Split("/"))[9])
                    $status   = Get-ItemPropertyValue -path $currentKey.PSPath -Name $_
                    if ($Online) {
                        $found   = $apps | Where-Object { $win32Key -match $_.Id }
                        if ($found) {
                            $win32Key = "$($found.DisplayName) ($win32Key)"
                        }
                    }
                    $appGuid    = $win32Key.Substring(9) -replace "\\)", ""
                    $sidecarApp = "$sidecarPath\\$currentUser\\$appGuid"
                    $exitCode   = $null
                    if (Test-Path $sidecarApp) {
                        $exitCode = (Get-ItemProperty -Path $sidecarApp).ExitCode
                    }
                    if ($status -eq "3") {
                        RecordStatus -detail "Win32 $win32Key" -status $espStatus[$status.ToString()] -color "Green" -date $currentKey.PSChildName
                    }
                    elseif ($status -eq "4") {
                        RecordStatus -detail "Win32 $win32Key" -status $espStatus[$status.ToString()] -color "Red" -date $currentKey.PSChildName
                    }
                    else {
                        if ($status -ne "1") {
                            RecordStatus -detail "Win32 $win32Key" -status $espStatus[$status.ToString()] -color "Yellow" -date $currentKey.PSChildName
                        }
                        if ($status -eq "2" -and $script:DOEvents) {
                            $script:DOEvents | Where-Object { $_.Message -ilike "*$appGuid*" } |
                                ForEach-Object {
                                    RecordStatus -detail "Win32 $win32Key" -status "DO $($_.Function.Substring(32))" -color "Yellow" -date $_.TimeCreated.ToLocalTime()
                                }
                        }
                    }
                }
            }
        }

        Function ProcessPolicies {
            param(
                [Parameter(Mandatory = $true, ValueFromPipeline = $True)] [Microsoft.Win32.RegistryKey] $currentKey,
                [Parameter(Mandatory = $true, ValueFromPipelineByPropertyName = $True)] [bool] $display
            )
            Process {
                $currentKey.Property | ForEach-Object {
                    $status = Get-ItemPropertyValue -path $currentKey.PSPath -Name $_
                    if ($status -eq "1") {
                        RecordStatus -detail "Policy $_" -status $policyStatus[$status.ToString()] -color "Green" -date $currentKey.PSChildName
                    }
                }
            }
        }

        Function ProcessCerts {
            param(
                [Parameter(Mandatory = $true, ValueFromPipeline = $True)] [Microsoft.Win32.RegistryKey] $currentKey,
                [Parameter(Mandatory = $true, ValueFromPipelineByPropertyName = $True)] [bool] $display
            )
            Process {
                $currentKey.Property | ForEach-Object {
                    $certKey = [URI]::UnescapeDataString(($_.Split("/"))[6])
                    $status  = Get-ItemPropertyValue -path $currentKey.PSPath -Name $_
                    if ($Online) {
                        $found = $policies | Where-Object { $certKey.Replace("_","-") -match $_.Id }
                        if ($found) {
                            $certKey = "$($found.DisplayName) ($certKey)"
                        }
                    }
                    if ($status -eq "1") {
                        RecordStatus -detail "Cert $certKey" -status $policyStatus[$status.ToString()] -color "Green" -date $currentKey.PSChildName
                    }
                }
            }
        }

        Function ProcessNodeCache {
            Process {
                $nodeCount = 0
                while ($true) {
                    $nodePath = "$provisioningPath\\NodeCache\\CSP\\Device\\MS DM Server\\Nodes\\$nodeCount"
                    $node = Get-ItemProperty -Path $nodePath -ErrorAction SilentlyContinue
                    if (-not $node) { break }
                    $nodeCount++
                }
            }
        }

        Function TrimMSI {
            param (
                [object] $event,
                [string] $sidecarProductCode
            )
            if ($event.Properties[0].Value -eq $sidecarProductCode) {
                return "Intune Management Extension"
            }
            elseif ($event.Properties[0].Value.StartsWith("{{")) {
                $r = $event.Properties[0].Value.Substring(1, $event.Properties[0].Value.Length - 2)
            }
            else {
                $r = $event.Properties[0].Value
            }
            if (Test-Path "HKLM:\\Software\\Microsoft\\Windows\\CurrentVersion\\Uninstall\\$r") {
                $displayName = (Get-ItemProperty -Path "HKLM:\\Software\\Microsoft\\Windows\\CurrentVersion\\Uninstall\\$r").DisplayName
                return "$displayName ($r)"
            }
            else {
                return $r
            }
        }

        Function ProcessEvents {
            Process {
                $productCode = 'IME-Not-Yet-Installed'
                if (Test-Path "$msiPath\\S-0-0-00-0000000000-0000000000-000000000-000\\MSI") {
                    Get-ChildItem -Path "$msiPath\\S-0-0-00-0000000000-0000000000-000000000-000\\MSI" |
                        ForEach-Object {
                            $file = (Get-ItemProperty -Path $_.PSPath).CurrentDownloadUrl
                            if ($file -match "IntuneWindowsAgent.msi") {
                                $productCode = Get-ItemPropertyValue -Path $_.PSPath -Name ProductCode
                            }
                        }
                }

                if ($script:useFile) {
                    # Device Management events (offline EVTX)
                    $admEvtx = "$($env:TEMP)\\ESPStatus.tmp\\microsoft-windows-devicemanagement-enterprise-diagnostics-provider-admin.evtx"
                    if (Test-Path $admEvtx) {
                        $events = Get-WinEvent -Path $admEvtx -Oldest |
                            Where-Object { ($_.Id -in 1905,1906,1920,1922) -or $_.Id -in (72,100,107,109,110,111) }
                    }
                }
                else {
                    # Device Management events (live)
                    try {
                        $events = Get-WinEvent -LogName Microsoft-Windows-DeviceManagement-Enterprise-Diagnostics-Provider/Admin -Oldest |
                            Where-Object { ($_.Id -in 1905,1906,1920,1922) -or $_.Id -in (72,100,107,109,110,111) }
                    } catch {
                        $events = @()
                    }
                }

                if ($events) {
                    $events | ForEach-Object {
                        $message = $_.Message
                        $detail  = "Sidecar"
                        $color   = "Yellow"
                        $event   = $_
                        switch ($_.Id) {
                            { $_ -in (110,109) } {
                                $detail = "Offline Domain Join"
                                switch ($event.Properties[0].Value) {
                                    0 {
                                        $message = "Offline domain join not configured"
                                    }
                                    1 {
                                        $message = "Waiting for ODJ blob"
                                    }
                                    2 {
                                        $message = "Processed ODJ blob"
                                    }
                                    3 {
                                        $message = "Timed out waiting for ODJ blob or connectivity"
                                        $color   = "Red"
                                    }
                                }
                            }
                            111 {
                                $detail  = "Offline Domain Join"
                                $message = "Starting wait for ODJ blob"
                            }
                            107 {
                                $detail  = "Offline Domain Join"
                                $message = "Successfully applied ODJ blob"
                                $color   = 'Green'
                            }
                            100 {
                                $detail  = "Offline Domain Join"
                                $message = "Could not establish connectivity"
                                $color   = "Red"
                            }
                            72 {
                                $detail = "MDM Enrollment"
                                $color  = "Green"
                            }
                            1905 {
                                $detail  = (TrimMSI $event $productCode)
                                $message = "Download started"
                            }
                            1906 {
                                $detail  = (TrimMSI $event $productCode)
                                $message = "Download finished"
                            }
                            1920 {
                                $detail  = (TrimMSI $event $productCode)
                                $message = "Installation started"
                            }
                            1922 {
                                $detail  = (TrimMSI $event $productCode)
                                $message = "Installation finished"
                                $color   = "Green"
                            }
                        }
                        RecordStatus -detail $detail -date $_.TimeCreated -status $message -color $color
                    }
                }

                # Device registration events
                $userRegEvents = $null
                if ($script:useFile) {
                    $userDevReg = "$($env:TEMP)\\ESPStatus.tmp\\microsoft-windows-user device registration-admin.evtx"
                    if (Test-Path $userDevReg) {
                        $userRegEvents = Get-WinEvent -Path $userDevReg -Oldest |
                            Where-Object { $_.Id -in (306,101,304) }
                    }
                }
                else {
                    try {
                        $userRegEvents = Get-WinEvent -LogName 'Microsoft-Windows-User Device Registration/Admin' -Oldest |
                            Where-Object { $_.Id -in (306,101,304) }
                    } catch {
                        $userRegEvents = @()
                    }
                }

                if ($userRegEvents) {
                    $userRegEvents | ForEach-Object {
                        $detail = "Device Registration"
                        $color  = "Yellow"
                        switch ($_.Id) {
                            101 {
                                $detail  = "Device Registration"
                                $message = "SCP discovery successful."
                            }
                            304 {
                                $detail  = "Device Registration"
                                $message = "Hybrid AADJ device registration failed."
                                $color   = "Red"
                            }
                            306 {
                                $detail  = "Device Registration"
                                $message = "Hybrid AADJ device registration succeeded."
                                $color   = "Green"
                            }
                        }
                        RecordStatus -detail $detail -date $_.TimeCreated -status $message -color $color
                    }
                }
            }
        }

        # -----------------------------------------------------
        # Variables/objetos de salida
        # -----------------------------------------------------
        $Results = [PSCustomObject]@{
            IsAutopilotDevice            = $false
            Profile                      = $null
            TenantDomain                 = $null
            TenantID                     = $null
            ZTDID                        = $null
            EntDMID                      = $null
            CloudAssignedOOBE            = $null
            Scenario                     = $null
            SkipKeyboard                 = $false
            EnablePatchDownload          = $false
            SkipUpgradeUX                = $false
            TPMRequired                  = $false
            AADDeviceAuth                = $false
            TPMAttestation               = $false
            SkipEULA                     = $false
            SkipOEMRegistration          = $false
            SkipExpressSettings          = $false
            DisallowAdmin                = $false
            DeviceESPEnabled             = $false
            UserESPEnabled               = $false
            ESPTimeout                   = 0
            ESPBlocking                  = $false
            Observations                 = @()
            ObservedTimeline             = @()
            EnrollmentTenantID           = $tenantId
            EnrollmentTenantIDModified   = $tenantIdModified        # 🆕 Nueva propiedad
            ForcedEnrollment             = $forcedEnrollment
            ForcedEnrollmentModified     = $forcedEnrollmentModified  # 🆕 Nueva propiedad
        }

        # -----------------------------------------------------
        # Conexión a Graph si se requiere
        # -----------------------------------------------------
        if ($Online) {
            $deviceManagementModule = Get-Module -ListAvailable -Name Microsoft.Graph.Beta.DeviceManagement
            $corporateManagementModule = Get-Module -ListAvailable -Name Microsoft.Graph.Beta.Devices.CorporateManagement

            if (-not $deviceManagementModule -or -not $corporateManagementModule) {
                try {
                    Import-Module Microsoft.Graph.Beta.DeviceManagement -ErrorAction Stop
                    Import-Module Microsoft.Graph.Beta.Devices.CorporateManagement -ErrorAction Stop
                }
                catch {
                    Install-Module Microsoft.Graph.Beta.DeviceManagement -Force -AllowClobber
                    Install-Module Microsoft.Graph.Beta.Devices.CorporateManagement -Force -AllowClobber
                }
            }
            Import-Module Microsoft.Graph.Beta.DeviceManagement
            Import-Module Microsoft.Graph.Beta.Devices.CorporateManagement

            if ($AppId -and $AppSecret -and $Tenant) {
                $graph = Connect-ToGraph -Tenant $Tenant -AppId $AppId -AppSecret $AppSecret
            }
            else {
                $graph = Connect-ToGraph -Scopes "DeviceManagementApps.Read.All, DeviceManagementConfiguration.Read.All"
            }
            try {
                $script:apps     = Get-MgBetaDeviceAppManagementMobileApp -All
                $script:policies = Get-MgBetaDeviceManagementConfigurationPolicy -All
            } catch {
                $script:apps     = @()
                $script:policies = @()
            }
        }

        # -----------------------------------------------------
        # Detección de Autopilot
        # -----------------------------------------------------
        $values = $null
        try {
            $values = Get-ItemProperty -Path $autopilotDiagPath -ErrorAction Stop
        } catch {
            # No es autopilot o no existe la key
        }

        if (-not $values -or -not $values.CloudAssignedTenantId) {
            $Results.Observations += "This is not an Autopilot device."
        }
        else {
            # Sí es Autopilot
            $Results.IsAutopilotDevice = $true
            $Results.Profile           = $values.DeploymentProfileName
            $Results.TenantDomain      = $values.CloudAssignedTenantDomain
            $Results.TenantID          = $values.CloudAssignedTenantId
            $Results.CloudAssignedOOBE = $values.CloudAssignedOobeConfig

            # Correlaciones
            try {
                $correlations = Get-ItemProperty "$autopilotDiagPath\\EstablishedCorrelations"
                $Results.ZTDID  = $correlations.ZTDRegistrationID
                $Results.EntDMID= $correlations.EntDMID
            } catch {}

            # Flags de OOBE
            if (($values.CloudAssignedOobeConfig -band 1024) -gt 0) { $Results.SkipKeyboard        = $true }
            if (($values.CloudAssignedOobeConfig -band 512)  -gt 0) { $Results.EnablePatchDownload = $true }
            if (($values.CloudAssignedOobeConfig -band 256)  -gt 0) { $Results.SkipUpgradeUX       = $true }
            if (($values.CloudAssignedOobeConfig -band 128)  -gt 0) { $Results.TPMRequired         = $true }
            if (($values.CloudAssignedOobeConfig -band 64)   -gt 0) { $Results.AADDeviceAuth       = $true }
            if (($values.CloudAssignedOobeConfig -band 32)   -gt 0) { $Results.TPMAttestation      = $true }
            if (($values.CloudAssignedOobeConfig -band 16)   -gt 0) { $Results.SkipEULA            = $true }
            if (($values.CloudAssignedOobeConfig -band 8)    -gt 0) { $Results.SkipOEMRegistration = $true }
            if (($values.CloudAssignedOobeConfig -band 4)    -gt 0) { $Results.SkipExpressSettings = $true }
            if (($values.CloudAssignedOobeConfig -band 2)    -gt 0) { $Results.DisallowAdmin       = $true }

            # Ver si es Hybrid o AAD
            $jsonFile = if ($script:useFile) {
                "$($env:TEMP)\\ESPStatus.tmp\\AutopilotDDSZTDFile.json"
            }
            else {
                "$($env:WINDIR)\\ServiceState\\wmansvc\\AutopilotDDSZTDFile.json"
            }

            if (Test-Path $jsonFile) {
                $json = Get-Content $jsonFile | ConvertFrom-Json
                $date = [datetime]$json.PolicyDownloadDate
                RecordStatus -date $date -detail "Autopilot profile" -status "Profile downloaded" -color "Yellow"

                if ($json.CloudAssignedDomainJoinMethod -eq 1) {
                    $Results.Scenario = "Hybrid Azure AD Join"
                }
                else {
                    $Results.Scenario = "Azure AD Join"
                }
            }
            else {
                $Results.Scenario = "Not available (JSON not found)"
            }
        }

        # -----------------------------------------------------
        # ESP
        # -----------------------------------------------------
        try {
            Get-ChildItem $enrollmentsPath -ErrorAction SilentlyContinue |
                Where-Object { Test-Path "$($_.PSPath)\\FirstSync" } | ForEach-Object {
                    $properties = Get-ItemProperty "$($_.PSPath)\\FirstSync"
                    $Results.DeviceESPEnabled = ($properties.SkipDeviceStatusPage -eq 0)
                    $Results.UserESPEnabled   = ($properties.SkipUserStatusPage -eq 0)
                    $Results.ESPTimeout       = $properties.SyncFailureTimeout
                    if ($properties.BlockInStatusPage -eq 0) {
                        $Results.ESPBlocking = $false
                    }
                    else {
                        $Results.ESPBlocking = $true
                    }
                }
        } catch {}

        # -----------------------------------------------------
        # OA3Tool para Hardware Hash (opcional)
        # -----------------------------------------------------
        $adkPath = $null
        $oa3Tool = $null
        try {
            $adkPath = Get-ItemPropertyValue "HKLM:\\Software\\Microsoft\\Windows Kits\\Installed Roots" -Name KitsRoot10 -ErrorAction SilentlyContinue
        } catch {}

        if ($null -ne $adkPath) {
            $oa3Tool = Join-Path $adkPath "Assessment and Deployment Kit\\Deployment Tools\\$($env:PROCESSOR_ARCHITECTURE)\\Licensing\\OA30\\oa3tool.exe"
        }

        if ($hash -and $oa3Tool -and (Test-Path $oa3Tool)) {
            try {
                $commandLineArgs = "/decodehwhash:$hash"
                $output = & "$oa3Tool" $commandLineArgs
                if ($output.Count -gt 12) {
                    [xml] $hashXML = $output | Select-Object -Skip 8 -First ($output.Count - 12)
                    RecordStatus -date (Get-Date) -detail "Hardware info" -status "Detected" -color "Yellow"
                }
            } catch {}
        }

        # -----------------------------------------------------
        # Eventos
        # -----------------------------------------------------
        ProcessEvents

        # -----------------------------------------------------
        # Policies (ShowPolicies)
        # -----------------------------------------------------
        if ($ShowPolicies) {
            ProcessNodeCache | Out-Null
        }

        # -----------------------------------------------------
        # ESPTrackingInfo
        # -----------------------------------------------------
        if (Test-Path $path) {
            # DEVICE
            try {
                if (Test-Path "$path\\ExpectedPolicies") {
                    [array]$items = Get-ChildItem "$path\\ExpectedPolicies"
                    AddDisplay ([ref]$items)
                    $items | ProcessPolicies
                }
                if (Test-Path "$path\\ExpectedMSIAppPackages") {
                    [array]$items = Get-ChildItem "$path\\ExpectedMSIAppPackages"
                    AddDisplay ([ref]$items)
                    $items | ProcessApps -currentUser "S-0-0-00-0000000000-0000000000-000000000-000"
                }
                if (Test-Path "$path\\ExpectedModernAppPackages") {
                    [array]$items = Get-ChildItem "$path\\ExpectedModernAppPackages"
                    AddDisplay ([ref]$items)
                    $items | ProcessModernApps -currentUser "S-0-0-00-0000000000-0000000000-000000000-000"
                }
                if (Test-Path "$path\\Sidecar") {
                    [array]$sidecarItems = Get-ChildItem "$path\\Sidecar" | Where-Object {
                        $_.Property -match "./Device" -and $_.Name -notmatch "LastLoggedState"
                    }
                    AddDisplay ([ref]$sidecarItems)
                    $sidecarItems | ProcessSidecar -currentUser "00000000-0000-0000-0000-000000000000"
                }
                if (Test-Path "$path\\ExpectedSCEPCerts") {
                    [array]$certItems = Get-ChildItem "$path\\ExpectedSCEPCerts"
                    AddDisplay ([ref]$certItems)
                    $certItems | ProcessCerts
                }
            } catch {}

            # USERS
            Get-ChildItem "$path" -ErrorAction SilentlyContinue |
                Where-Object { $_.PSChildName.StartsWith("S-") } | ForEach-Object {
                    $userPath = $_.PSPath
                    $userSid  = $_.PSChildName
                    try {
                        if (Test-Path "$userPath\\ExpectedPolicies") {
                            [array]$items = Get-ChildItem "$userPath\\ExpectedPolicies"
                            AddDisplay ([ref]$items)
                            $items | ProcessPolicies
                        }
                        if (Test-Path "$userPath\\ExpectedMSIAppPackages") {
                            [array]$items = Get-ChildItem "$userPath\\ExpectedMSIAppPackages"
                            AddDisplay ([ref]$items)
                            $items | ProcessApps -currentUser $userSid
                        }
                        if (Test-Path "$userPath\\ExpectedModernAppPackages") {
                            [array]$items = Get-ChildItem "$userPath\\ExpectedModernAppPackages"
                            AddDisplay ([ref]$items)
                            $items | ProcessModernApps -currentUser $userSid
                        }
                        if (Test-Path "$userPath\\Sidecar") {
                            [array]$sidecarItems = Get-ChildItem "$userPath\\Sidecar" | Where-Object {
                                $_.Property -match "./User"
                            }
                            AddDisplay ([ref]$sidecarItems)
                            $sidecarItems | ProcessSidecar -currentUser $userSid
                        }
                        if (Test-Path "$userPath\\ExpectedSCEPCerts") {
                            [array]$certItems = Get-ChildItem "$userPath\\ExpectedSCEPCerts"
                            AddDisplay ([ref]$certItems)
                            $certItems | ProcessCerts
                        }
                    } catch {}
                }
        }

        # Cargar timeline
        $Results.ObservedTimeline = $script:observedTimeline | Sort-Object -Property Date

    }

    End {
        if (Test-Path "HKCU:\\ESPStatus.tmp") {
            Remove-Item -Path "HKCU:\\ESPStatus.tmp" -Recurse -Force
        }
        $Results | ConvertTo-Json -Depth 10
    }
}

Get-ESPDiagnostics | Out-String