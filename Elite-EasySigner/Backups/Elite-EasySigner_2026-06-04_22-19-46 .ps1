# Elite EasySigner - v1.0.42.4
# EliteSoftware Professional Certificate Signing Utility
# Est. 2006, Updated for 2026

# Load Assemblies
Add-Type -AssemblyName System.Windows.Forms
Add-Type -AssemblyName System.Drawing

[System.Windows.Forms.Application]::EnableVisualStyles()

# Define P/Invoke to allow Drag & Drop when running as Administrator (UAC bypass for messages)
Add-Type -TypeDefinition @"
using System;
using System.Runtime.InteropServices;

public class Win32 {
    [DllImport("user32.dll", SetLastError = true)]
    public static extern bool ChangeWindowMessageFilter(uint message, uint dwFlag);
    
    public const uint MSGFLT_ALLOW = 1;
    public const uint WM_DROPFILES = 0x0233;
    public const uint WM_COPYDATA = 0x004A;
    public const uint WM_COPYGLOBALDATA = 0x0049;
}
"@

# Global variables
$scriptPath = if ($MyInvocation.MyCommand.Path) { $MyInvocation.MyCommand.Path } else { [System.Diagnostics.Process]::GetCurrentProcess().MainModule.FileName }
$scriptDir = if ($scriptPath) { [System.IO.Path]::GetDirectoryName($scriptPath) } else { (Get-Location).Path }
if (-not $scriptDir) { $scriptDir = (Get-Location).Path }
$baseName = if ($scriptPath) { [System.IO.Path]::GetFileNameWithoutExtension($scriptPath) } else { "Elite-EasySigner" }

# 1. Determine local certificate path
$defaultPfx = if ($scriptDir) { [System.IO.Path]::Combine($scriptDir, "EliteSoftware_Special.pfx") } else { "EliteSoftware_Special.pfx" }
$defaultPassword = "Minecraft145!!"

# Helper for Montserrat or Segoe UI Fallback
function New-EliteFont {
    param(
        [string]$family = "Montserrat",
        [float]$size = 9,
        [System.Drawing.FontStyle]$style = [System.Drawing.FontStyle]::Regular
    )
    try {
        $font = New-Object System.Drawing.Font($family, $size, $style)
        if ($font.Name -eq $family) {
            return $font
        }
    } catch {}
    return New-Object System.Drawing.Font("Segoe UI", $size, $style)
}

# Helper to find signtool.exe
function Find-SignTool {
    # 1. Check Windows Kits folders first (Most reliable)
    $sdkRoot = "C:\Program Files (x86)\Windows Kits"
    if (Test-Path $sdkRoot) {
        $win10Bin = Join-Path $sdkRoot "10\bin"
        if (Test-Path $win10Bin) {
            $versions = Get-ChildItem -Path $win10Bin -Directory -ErrorAction SilentlyContinue | Sort-Object Name -Descending
            foreach ($v in $versions) {
                if ($v.FullName) {
                    $signtoolPaths = @(
                        (Join-Path $v.FullName "x64\signtool.exe"),
                        (Join-Path $v.FullName "x86\signtool.exe")
                    )
                    foreach ($p in $signtoolPaths) {
                        if ($p -and (Test-Path $p)) { return $p }
                    }
                }
            }
        }
    }

    # 2. Check local directory (only as fallback)
    if ($scriptDir) {
        $localP = Join-Path $scriptDir "signtool.exe"
        if ($localP -and (Test-Path $localP)) { return $localP }
    }

    # 3. Check PATH environment variable
    $pathTool = Get-Command "signtool.exe" -ErrorAction SilentlyContinue
    if ($pathTool) { return $pathTool.Source }
    
    return ""
}

try {
    # Allow Drag & Drop messages through UAC filter
    [Win32]::ChangeWindowMessageFilter([Win32]::WM_DROPFILES, [Win32]::MSGFLT_ALLOW) | Out-Null
    [Win32]::ChangeWindowMessageFilter([Win32]::WM_COPYGLOBALDATA, [Win32]::MSGFLT_ALLOW) | Out-Null
    [Win32]::ChangeWindowMessageFilter([Win32]::WM_COPYDATA, [Win32]::MSGFLT_ALLOW) | Out-Null

    # --- Create Form ---
    $form = New-Object System.Windows.Forms.Form
    $form.Text = "Elite EasySigner - v1.0.42.4"
    $form.Size = New-Object System.Drawing.Size(620, 620)
    $form.FormBorderStyle = [System.Windows.Forms.FormBorderStyle]::FixedDialog
    $form.MaximizeBox = $false
    $form.MinimizeBox = $true
    $form.StartPosition = [System.Windows.Forms.FormStartPosition]::CenterScreen
    $form.AllowDrop = $true
    $form.Font = New-EliteFont -family "Montserrat" -size 9

    # Load Icon
    $icoPath = if ($scriptDir -and $baseName) { [System.IO.Path]::Combine($scriptDir, "$baseName.ico") } else { "" }
    $exePath = if ($scriptDir -and $baseName) { [System.IO.Path]::Combine($scriptDir, "$baseName.exe") } else { "" }
    $formIcon = $null

    if ($icoPath -and (Test-Path $icoPath)) {
        try { $formIcon = New-Object System.Drawing.Icon($icoPath) } catch {}
    }
    if ($null -eq $formIcon -and $exePath -and (Test-Path $exePath)) {
        try { $formIcon = [System.Drawing.Icon]::ExtractAssociatedIcon($exePath) } catch {}
    }
    if ($null -eq $formIcon) {
        # Last attempt fallback to hardcoded name in same dir
        $fallbackIco = if ($scriptDir) { Join-Path $scriptDir "Elite-EasySigner.ico" } else { "" }
        if ($fallbackIco -and (Test-Path $fallbackIco)) {
            try { $formIcon = New-Object System.Drawing.Icon($fallbackIco) } catch {}
        }
    }
    if ($formIcon) {
        $form.Icon = $formIcon
    }

    # --- Header Panel ---
    $pnlHeader = New-Object System.Windows.Forms.Panel
    $pnlHeader.Dock = [System.Windows.Forms.DockStyle]::Top
    $pnlHeader.Height = 75
    $pnlHeader.BackColor = [System.Drawing.Color]::White

    $lblHeaderTitle = New-Object System.Windows.Forms.Label
    $lblHeaderTitle.Text = "Elite EasySigner"
    $lblHeaderTitle.Font = New-EliteFont -family "Montserrat" -size 12.5 -style ([System.Drawing.FontStyle]::Bold)
    $lblHeaderTitle.Location = New-Object System.Drawing.Point(15, 12)
    $lblHeaderTitle.Size = New-Object System.Drawing.Size(400, 25)
    $lblHeaderTitle.ForeColor = [System.Drawing.Color]::FromArgb(40, 40, 40)

    $lblHeaderSub = New-Object System.Windows.Forms.Label
    $lblHeaderSub.Text = "v1.0.42.4 - EliteSoftware Certificate Signing Utility"
    $lblHeaderSub.Font = New-EliteFont -family "Montserrat" -size 8.5 -style ([System.Drawing.FontStyle]::Regular)
    $lblHeaderSub.Location = New-Object System.Drawing.Point(15, 38)
    $lblHeaderSub.Size = New-Object System.Drawing.Size(400, 20)
    $lblHeaderSub.ForeColor = [System.Drawing.Color]::FromArgb(100, 100, 100)

    $picHeaderIcon = New-Object System.Windows.Forms.PictureBox
    $picHeaderIcon.Location = New-Object System.Drawing.Point(545, 12)
    $picHeaderIcon.Size = New-Object System.Drawing.Size(48, 48)
    $picHeaderIcon.SizeMode = [System.Windows.Forms.PictureBoxSizeMode]::StretchImage
    if ($formIcon) {
        $picHeaderIcon.Image = $formIcon.ToBitmap()
    }

    $lblHeaderDivider = New-Object System.Windows.Forms.Label
    $lblHeaderDivider.Height = 2
    $lblHeaderDivider.Dock = [System.Windows.Forms.DockStyle]::Bottom
    $lblHeaderDivider.BorderStyle = [System.Windows.Forms.BorderStyle]::Fixed3D
    $pnlHeader.Controls.AddRange(@($lblHeaderTitle, $lblHeaderSub, $picHeaderIcon, $lblHeaderDivider))

    # --- Client Area ---
    $pnlClient = New-Object System.Windows.Forms.Panel
    $pnlClient.Dock = [System.Windows.Forms.DockStyle]::Fill
    $pnlClient.BackColor = [System.Drawing.SystemColors]::Control

    # 1. Configuration
    $grpSettings = New-Object System.Windows.Forms.GroupBox
    $grpSettings.Text = "Signing Configuration"
    $grpSettings.Font = New-EliteFont -family "Montserrat" -size 9 -style ([System.Drawing.FontStyle]::Bold)
    $grpSettings.Location = New-Object System.Drawing.Point(12, 10)
    $grpSettings.Size = New-Object System.Drawing.Size(580, 140)

    $txtPfx = New-Object System.Windows.Forms.TextBox
    $txtPfx.Text = if ($defaultPfx -and (Test-Path $defaultPfx)) { $defaultPfx } else { "" }
    $txtPfx.Font = New-EliteFont -family "Montserrat" -size 8.5
    $txtPfx.Location = New-Object System.Drawing.Point(130, 22)
    $txtPfx.Size = New-Object System.Drawing.Size(360, 23)

    $lblPfx = New-Object System.Windows.Forms.Label
    $lblPfx.Text = "PFX Certificate:"
    $lblPfx.Font = New-EliteFont -family "Montserrat" -size 8.5
    $lblPfx.Location = New-Object System.Drawing.Point(15, 25)
    $lblPfx.Size = New-Object System.Drawing.Size(110, 20)

    $btnBrowsePfx = New-Object System.Windows.Forms.Button
    $btnBrowsePfx.Text = "..."
    $btnBrowsePfx.Location = New-Object System.Drawing.Point(500, 21)
    $btnBrowsePfx.Size = New-Object System.Drawing.Size(65, 24)

    $txtPassword = New-Object System.Windows.Forms.TextBox
    $txtPassword.Text = $defaultPassword
    $txtPassword.UseSystemPasswordChar = $true
    $txtPassword.Location = New-Object System.Drawing.Point(130, 52)
    $txtPassword.Size = New-Object System.Drawing.Size(260, 23)

    $lblPassword = New-Object System.Windows.Forms.Label
    $lblPassword.Text = "PFX Password:"
    $lblPassword.Location = New-Object System.Drawing.Point(15, 55)
    $lblPassword.Size = New-Object System.Drawing.Size(110, 20)

    $chkShowPassword = New-Object System.Windows.Forms.CheckBox
    $chkShowPassword.Text = "Show"
    $chkShowPassword.Location = New-Object System.Drawing.Point(400, 54)
    $chkShowPassword.Size = New-Object System.Drawing.Size(80, 20)

    $txtSignTool = New-Object System.Windows.Forms.TextBox
    $txtSignTool.Text = Find-SignTool
    $txtSignTool.Location = New-Object System.Drawing.Point(130, 82)
    $txtSignTool.Size = New-Object System.Drawing.Size(360, 23)

    $lblSignTool = New-Object System.Windows.Forms.Label
    $lblSignTool.Text = "SignTool Path:"
    $lblSignTool.Location = New-Object System.Drawing.Point(15, 85)
    $lblSignTool.Size = New-Object System.Drawing.Size(110, 20)

    $btnBrowseSignTool = New-Object System.Windows.Forms.Button
    $btnBrowseSignTool.Text = "..."
    $btnBrowseSignTool.Location = New-Object System.Drawing.Point(500, 81)
    $btnBrowseSignTool.Size = New-Object System.Drawing.Size(65, 24)

    $lblStatusSetting = New-Object System.Windows.Forms.Label
    $pfxExists = ($defaultPfx -and (Test-Path $defaultPfx))
    $lblStatusSetting.Text = if ($pfxExists) { "✓ Master PFX loaded automatically" } else { "⚠ Master PFX not found" }
    $lblStatusSetting.ForeColor = if ($pfxExists) { [System.Drawing.Color]::DarkGreen } else { [System.Drawing.Color]::DarkOrange }
    $lblStatusSetting.Font = New-EliteFont -family "Montserrat" -size 8 -style ([System.Drawing.FontStyle]::Italic)
    $lblStatusSetting.Location = New-Object System.Drawing.Point(130, 112)
    $lblStatusSetting.Size = New-Object System.Drawing.Size(400, 20)

    $grpSettings.Controls.AddRange(@($lblPfx, $txtPfx, $btnBrowsePfx, $lblPassword, $txtPassword, $chkShowPassword, $lblSignTool, $txtSignTool, $btnBrowseSignTool, $lblStatusSetting))

    # 2. Drag & Drop Zone
    $grpDropZone = New-Object System.Windows.Forms.GroupBox
    $grpDropZone.Text = "Drag & Drop Files Here to Sign"
    $grpDropZone.Font = New-EliteFont -family "Montserrat" -size 9 -style ([System.Drawing.FontStyle]::Bold)
    $grpDropZone.Location = New-Object System.Drawing.Point(12, 160)
    $grpDropZone.Size = New-Object System.Drawing.Size(580, 140)
    $grpDropZone.AllowDrop = $true

    $lblDropPrompt = New-Object System.Windows.Forms.Label
    $lblDropPrompt.Text = "DRAG AND DROP EXE, DLL, CPL, MUI, MUN, OCX FILES HERE"
    $lblDropPrompt.Font = New-EliteFont -family "Montserrat" -size 9 -style ([System.Drawing.FontStyle]::Bold)
    $lblDropPrompt.ForeColor = [System.Drawing.Color]::FromArgb(60, 60, 60)
    $lblDropPrompt.TextAlign = [System.Drawing.ContentAlignment]::TopCenter
    $lblDropPrompt.Location = New-Object System.Drawing.Point(10, 25)
    $lblDropPrompt.Size = New-Object System.Drawing.Size(560, 25)
    $lblDropPrompt.AllowDrop = $true

    $lblDropSubPrompt = New-Object System.Windows.Forms.Label
    $lblDropSubPrompt.Text = "Originals will be backed up to 'Original_Unsigned-Components' as .bak"
    $lblDropSubPrompt.Font = New-EliteFont -family "Montserrat" -size 8 -style ([System.Drawing.FontStyle]::Italic)
    $lblDropSubPrompt.ForeColor = [System.Drawing.Color]::DimGray
    $lblDropSubPrompt.TextAlign = [System.Drawing.ContentAlignment]::TopCenter
    $lblDropSubPrompt.Location = New-Object System.Drawing.Point(10, 50)
    $lblDropSubPrompt.Size = New-Object System.Drawing.Size(560, 20)
    $lblDropSubPrompt.AllowDrop = $true

    $btnBrowseFiles = New-Object System.Windows.Forms.Button
    $btnBrowseFiles.Text = "OR BROWSE FOR FILES TO SIGN..."
    $btnBrowseFiles.Font = New-EliteFont -family "Montserrat" -size 8.5 -style ([System.Drawing.FontStyle]::Bold)
    $btnBrowseFiles.Location = New-Object System.Drawing.Point(165, 85)
    $btnBrowseFiles.Size = New-Object System.Drawing.Size(250, 32)
    $btnBrowseFiles.UseVisualStyleBackColor = $true

    $grpDropZone.Controls.AddRange(@($lblDropPrompt, $lblDropSubPrompt, $btnBrowseFiles))

    # 3. Log
    $grpLogs = New-Object System.Windows.Forms.GroupBox
    $grpLogs.Text = "Operations Log"
    $grpLogs.Font = New-EliteFont -family "Montserrat" -size 9 -style ([System.Drawing.FontStyle]::Bold)
    $grpLogs.Location = New-Object System.Drawing.Point(12, 310)
    $grpLogs.Size = New-Object System.Drawing.Size(580, 180)

    $rtbLog = New-Object System.Windows.Forms.RichTextBox
    $rtbLog.Location = New-Object System.Drawing.Point(15, 25)
    $rtbLog.Size = New-Object System.Drawing.Size(550, 115)
    $rtbLog.ReadOnly = $true
    $rtbLog.Font = New-Object System.Drawing.Font("Consolas", 8.5)
    $rtbLog.BackColor = [System.Drawing.Color]::White

    $btnClearLog = New-Object System.Windows.Forms.Button
    $btnClearLog.Text = "Clear Log"
    $btnClearLog.Location = New-Object System.Drawing.Point(480, 146)
    $btnClearLog.Size = New-Object System.Drawing.Size(85, 24)

    $lblStatusText = New-Object System.Windows.Forms.Label
    $lblStatusText.Text = "Ready"
    $lblStatusText.Location = New-Object System.Drawing.Point(15, 149)
    $lblStatusText.Size = New-Object System.Drawing.Size(450, 20)
    $grpLogs.Controls.AddRange(@($rtbLog, $btnClearLog, $lblStatusText))

    $pnlClient.Controls.AddRange(@($grpSettings, $grpDropZone, $grpLogs))
    $form.Controls.AddRange(@($pnlClient, $pnlHeader))

    # --- Functions ---

    function Write-Log {
        param([string]$message, [string]$type = "info")
        $color = [System.Drawing.Color]::Black
        switch ($type.ToLower()) {
            "success" { $color = [System.Drawing.Color]::DarkGreen }
            "error"   { $color = [System.Drawing.Color]::DarkRed }
            "warning" { $color = [System.Drawing.Color]::DarkOrange }
        }
        $rtbLog.SelectionStart = $rtbLog.TextLength
        $rtbLog.SelectionColor = $color
        $rtbLog.AppendText("[$([DateTime]::Now.ToString('HH:mm:ss'))] [$($type.ToUpper())] $message`r`n")
        $rtbLog.ScrollToCaret()
        $lblStatusText.Text = $message
        [System.Windows.Forms.Application]::DoEvents()
    }

    function Sign-File {
        param([string]$filePath)
        if (-not $filePath -or -not (Test-Path $filePath)) { return $false }
        
        $pfx = $txtPfx.Text.Trim()
        $password = $txtPassword.Text
        $signtool = $txtSignTool.Text.Trim()
        
        if (-not $signtool -or -not (Test-Path $signtool)) { Write-Log "SignTool not found." "error"; return $false }
        if (-not $pfx -or -not (Test-Path $pfx)) { Write-Log "PFX not found." "error"; return $false }
        
        $fileDir = [System.IO.Path]::GetDirectoryName($filePath)
        $fileName = [System.IO.Path]::GetFileName($filePath)
        
        $origDir = Join-Path $fileDir "Original_Unsigned-Components"
        if (-not (Test-Path $origDir)) { $null = New-Item -ItemType Directory -Path $origDir -Force }
        
        $bakPath = Join-Path $origDir "$fileName.bak"
        
        try {
            # 1. Backup original to .bak
            if (Test-Path $bakPath) { Remove-Item $bakPath -Force }
            Move-Item -Path $filePath -Destination $bakPath -Force
            
            # 2. Copy it back to original name (this will be the one we sign)
            Copy-Item -Path $bakPath -Destination $filePath -Force
            
            # 3. Sign the file in place
            $argsSign = @("sign", "/f", $pfx, "/p", $password, "/fd", "SHA256", "/t", "http://timestamp.digicert.com", "/v", $filePath)
            $p = Start-Process -FilePath $signtool -ArgumentList $argsSign -NoNewWindow -PassThru -Wait
            
            if ($p.ExitCode -eq 0) {
                Write-Log "Successfully signed $fileName. Original backed up as .bak" "success"
                return $true
            } else {
                Write-Log "SignTool failed for $fileName (Exit code: $($p.ExitCode))" "error"
                # Restore from backup if signing failed
                Copy-Item -Path $bakPath -Destination $filePath -Force
            }
        } catch {
            Write-Log "Error processing $($fileName): $($_.Exception.Message)" "error"
        }
        return $false
    }

    function Process-DroppedFiles {
        param([string[]]$files)
        if ($files.Count -gt 0) {
            Write-Log "Processing $($files.Count) file(s)..." "info"
            foreach ($file in $files) {
                if ($file -and (Test-Path $file -PathType Leaf)) {
                    $null = Sign-File -filePath $file
                }
            }
            Write-Log "Batch processing complete." "info"
        }
    }

    # --- Events ---
    $btnBrowsePfx.Add_Click({
        $d = New-Object System.Windows.Forms.OpenFileDialog
        $d.Filter = "PFX Files (*.pfx)|*.pfx|All files (*.*)|*.*"
        if ($d.ShowDialog() -eq [System.Windows.Forms.DialogResult]::OK) { $txtPfx.Text = $d.FileName }
    })

    $btnBrowseSignTool.Add_Click({
        $d = New-Object System.Windows.Forms.OpenFileDialog
        $d.Filter = "signtool.exe|signtool.exe|All files (*.*)|*.*"
        if ($d.ShowDialog() -eq [System.Windows.Forms.DialogResult]::OK) { $txtSignTool.Text = $d.FileName }
    })

    $btnBrowseFiles.Add_Click({
        $d = New-Object System.Windows.Forms.OpenFileDialog
        $d.Filter = "Signed Files (*.exe;*.dll;*.cpl;*.mui;*.mun;*.ocx)|*.exe;*.dll;*.cpl;*.mui;*.mun;*.ocx|All files (*.*)|*.*"
        $d.Multiselect = $true
        if ($d.ShowDialog() -eq [System.Windows.Forms.DialogResult]::OK) {
            Process-DroppedFiles -files $d.FileNames
        }
    })

    $chkShowPassword.Add_Click({ $txtPassword.UseSystemPasswordChar = -not $chkShowPassword.Checked })
    $btnClearLog.Add_Click({ $rtbLog.Clear() })

    $dragHandler = {
        param($s, $e)
        if ($e.Data.GetDataPresent([System.Windows.Forms.DataFormats]::FileDrop)) { 
            $e.Effect = [System.Windows.Forms.DragDropEffects]::Copy 
        }
    }
    $dropHandler = {
        param($s, $e)
        $files = $e.Data.GetData([System.Windows.Forms.DataFormats]::FileDrop)
        if ($files) { Process-DroppedFiles -files $files }
    }

    $form.Add_DragEnter($dragHandler)
    $form.Add_DragDrop($dropHandler)
    $grpDropZone.Add_DragEnter($dragHandler)
    $grpDropZone.Add_DragDrop($dropHandler)
    $lblDropPrompt.Add_DragEnter($dragHandler)
    $lblDropPrompt.Add_DragDrop($dropHandler)
    $lblDropSubPrompt.Add_DragEnter($dragHandler)
    $lblDropSubPrompt.Add_DragDrop($dropHandler)

    # Handle Command Line Arguments (Drop on EXE icon)
    $form.Add_Shown({
        if ($args -and $args.Count -gt 0) {
            Write-Log "Files passed via command line detected." "info"
            Process-DroppedFiles -files $args
        }
    })

    Write-Log "Elite EasySigner Initialized." "info"
    $null = $form.ShowDialog()
    $form.Dispose()

} catch {
    [System.Windows.Forms.MessageBox]::Show("CRITICAL INITIALIZATION ERROR:`n`n$($_.Exception.Message)`n`nStack Trace:`n$($_.ScriptStackTrace)", "Elite EasySigner - Crash", [System.Windows.Forms.MessageBoxButtons]::OK, [System.Windows.Forms.MessageBoxIcon]::Error) | Out-Null
}
