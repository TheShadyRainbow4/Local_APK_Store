# Elite EasySigner - v1.0.43.0
# EliteSoftware Professional Certificate Signing Utility
# Est. 2006, Updated for 2026

# --- EliteSoftware Self-Elevation ---
$isAdmin = ([Security.Principal.WindowsPrincipal][Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)
if (-not $isAdmin) {
    $scriptPath = if ($MyInvocation.MyCommand.Path) { $MyInvocation.MyCommand.Path } else { [System.Diagnostics.Process]::GetCurrentProcess().MainModule.FileName }
    $process = Start-Process -FilePath "powershell.exe" -ArgumentList "-ExecutionPolicy Bypass -File `"$scriptPath`"" -Verb RunAs -PassThru -ErrorAction SilentlyContinue
    if ($process) { exit }
}

# Load Assemblies
Add-Type -AssemblyName System.Windows.Forms
Add-Type -AssemblyName System.Drawing

[System.Windows.Forms.Application]::EnableVisualStyles()

# --- Elite P/Invoke Definitions ---
Add-Type -TypeDefinition @"
using System;
using System.Runtime.InteropServices;

public class Win32 {
    [DllImport("user32.dll", SetLastError = true)]
    public static extern bool ChangeWindowMessageFilterEx(IntPtr hWnd, uint msg, uint action, IntPtr changeFilterStruct);
    
    public const uint MSGFLT_ALLOW = 1;
    public const uint WM_DROPFILES = 0x0233;
    public const uint WM_COPYDATA = 0x004A;
    public const uint WM_COPYGLOBALDATA = 0x0049;

    [StructLayout(LayoutKind.Sequential)]
    public struct MARGINS {
        public int cxLeftWidth;
        public int cxRightWidth;
        public int cyTopHeight;
        public int cyBottomHeight;
    }

    [DllImport("dwmapi.dll")]
    public static extern int DwmExtendFrameIntoClientArea(IntPtr hWnd, ref MARGINS pMarInset);
}
"@

# Global variables
$scriptPath = if ($MyInvocation.MyCommand.Path) { $MyInvocation.MyCommand.Path } else { [System.Diagnostics.Process]::GetCurrentProcess().MainModule.FileName }
$scriptDir = if ($scriptPath) { [System.IO.Path]::GetDirectoryName($scriptPath) } else { (Get-Location).Path }
if (-not $scriptDir) { $scriptDir = (Get-Location).Path }
$baseName = if ($scriptPath) { [System.IO.Path]::GetFileNameWithoutExtension($scriptPath) } else { "Elite-EasySigner" }
$logFilePath = Join-Path $scriptDir "Elite-EasySigner_Error.log"

# Registry for UI Config
$regPath = "HKCU:\Software\EliteSoftware\EasySigner"
if (-not (Test-Path $regPath)) { New-Item -Path $regPath -Force | Out-Null }
$glassEnabled = (Get-ItemProperty -Path $regPath -Name "EnableGlass" -ErrorAction SilentlyContinue).EnableGlass -eq 1

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
        if ($font.Name -eq $family) { return $font }
    } catch {}
    return New-Object System.Drawing.Font("Segoe UI", $size, $style)
}

# Helper to find signtool.exe
function Find-SignTool {
    $sdkRoot = "C:\Program Files (x86)\Windows Kits"
    if (Test-Path $sdkRoot) {
        $win10Bin = Join-Path $sdkRoot "10\bin"
        if (Test-Path $win10Bin) {
            $versions = Get-ChildItem -Path $win10Bin -Directory -ErrorAction SilentlyContinue | Sort-Object Name -Descending
            foreach ($v in $versions) {
                if ($v.FullName) {
                    $signtoolPaths = @((Join-Path $v.FullName "x64\signtool.exe"), (Join-Path $v.FullName "x86\signtool.exe"))
                    foreach ($p in $signtoolPaths) { if ($p -and (Test-Path $p)) { return $p } }
                }
            }
        }
    }
    if ($scriptDir) {
        $localP = Join-Path $scriptDir "signtool.exe"
        if ($localP -and (Test-Path $localP)) { return $localP }
    }
    $pathTool = Get-Command "signtool.exe" -ErrorAction SilentlyContinue
    if ($pathTool) { return $pathTool.Source }
    return ""
}

try {
    # --- Create Form ---
    $form = New-Object System.Windows.Forms.Form
    $form.Text = "Elite EasySigner - v1.0.43.0"
    $form.Size = New-Object System.Drawing.Size(620, 720)
    $form.FormBorderStyle = [System.Windows.Forms.FormBorderStyle]::FixedDialog
    $form.MaximizeBox = $false
    $form.MinimizeBox = $true
    $form.StartPosition = [System.Windows.Forms.FormStartPosition]::CenterScreen
    $form.AllowDrop = $true
    $form.Font = New-EliteFont -family "Montserrat" -size 9

    if ($glassEnabled) {
        $form.BackColor = [System.Drawing.Color]::Black
    } else {
        $form.BackColor = [System.Drawing.SystemColors]::Control
    }

    # Load Icon
    $icoPath = if ($scriptDir -and $baseName) { [System.IO.Path]::Combine($scriptDir, "$baseName.ico") } else { "" }
    $exePath = if ($scriptDir -and $baseName) { [System.IO.Path]::Combine($scriptDir, "$baseName.exe") } else { "" }
    $formIcon = $null
    if ($icoPath -and (Test-Path $icoPath)) { try { $formIcon = New-Object System.Drawing.Icon($icoPath) } catch {} }
    if ($null -eq $formIcon -and $exePath -and (Test-Path $exePath)) { try { $formIcon = [System.Drawing.Icon]::ExtractAssociatedIcon($exePath) } catch {} }
    if ($formIcon) { $form.Icon = $formIcon }

    # --- Header Panel ---
    $pnlHeader = New-Object System.Windows.Forms.Panel
    $pnlHeader.Dock = [System.Windows.Forms.DockStyle]::Top
    $pnlHeader.Height = 75
    $pnlHeader.BackColor = if ($glassEnabled) { [System.Drawing.Color]::Transparent } else { [System.Drawing.Color]::White }

    $lblHeaderTitle = New-Object System.Windows.Forms.Label
    $lblHeaderTitle.Text = "Elite EasySigner"
    $lblHeaderTitle.Font = New-EliteFont -family "Montserrat" -size 12.5 -style ([System.Drawing.FontStyle]::Bold)
    $lblHeaderTitle.Location = New-Object System.Drawing.Point(15, 12)
    $lblHeaderTitle.Size = New-Object System.Drawing.Size(400, 25)
    $lblHeaderTitle.ForeColor = if ($glassEnabled) { [System.Drawing.Color]::White } else { [System.Drawing.Color]::FromArgb(40, 40, 40) }
    $lblHeaderTitle.BackColor = [System.Drawing.Color]::Transparent

    $lblHeaderSub = New-Object System.Windows.Forms.Label
    $lblHeaderSub.Text = "v1.0.43.0 - EliteSoftware Certificate Signing Utility"
    $lblHeaderSub.Font = New-EliteFont -family "Montserrat" -size 8.5 -style ([System.Drawing.FontStyle]::Regular)
    $lblHeaderSub.Location = New-Object System.Drawing.Point(15, 38)
    $lblHeaderSub.Size = New-Object System.Drawing.Size(400, 20)
    $lblHeaderSub.ForeColor = if ($glassEnabled) { [System.Drawing.Color]::LightGray } else { [System.Drawing.Color]::FromArgb(100, 100, 100) }
    $lblHeaderSub.BackColor = [System.Drawing.Color]::Transparent

    $chkGlass = New-Object System.Windows.Forms.CheckBox
    $chkGlass.Text = "Extend Frame"
    $chkGlass.Location = New-Object System.Drawing.Point(440, 15)
    $chkGlass.Size = New-Object System.Drawing.Size(100, 20)
    $chkGlass.Checked = $glassEnabled
    $chkGlass.ForeColor = if ($glassEnabled) { [System.Drawing.Color]::White } else { [System.Drawing.Color]::Black }
    $chkGlass.BackColor = [System.Drawing.Color]::Transparent

    $picHeaderIcon = New-Object System.Windows.Forms.PictureBox
    $picHeaderIcon.Location = New-Object System.Drawing.Point(545, 12)
    $picHeaderIcon.Size = New-Object System.Drawing.Size(48, 48)
    $picHeaderIcon.SizeMode = [System.Windows.Forms.PictureBoxSizeMode]::StretchImage
    $picHeaderIcon.BackColor = [System.Drawing.Color]::Transparent
    if ($formIcon) { $picHeaderIcon.Image = $formIcon.ToBitmap() }

    $pnlHeader.Controls.AddRange(@($lblHeaderTitle, $lblHeaderSub, $chkGlass, $picHeaderIcon))

    # --- Client Area ---
    $pnlClient = New-Object System.Windows.Forms.Panel
    $pnlClient.Dock = [System.Windows.Forms.DockStyle]::Fill
    $pnlClient.BackColor = if ($glassEnabled) { [System.Drawing.Color]::Transparent } else { [System.Drawing.SystemColors]::Control }

    # 1. Configuration
    $grpSettings = New-Object System.Windows.Forms.GroupBox
    $grpSettings.Text = "Signing Configuration"
    $grpSettings.Font = New-EliteFont -family "Montserrat" -size 9 -style ([System.Drawing.FontStyle]::Bold)
    $grpSettings.Location = New-Object System.Drawing.Point(12, 10)
    $grpSettings.Size = New-Object System.Drawing.Size(580, 140)
    $grpSettings.ForeColor = if ($glassEnabled) { [System.Drawing.Color]::White } else { [System.Drawing.Color]::Black }

    $txtPfx = New-Object System.Windows.Forms.TextBox
    $txtPfx.Text = if ($defaultPfx -and (Test-Path $defaultPfx)) { $defaultPfx } else { "" }
    $txtPfx.Location = New-Object System.Drawing.Point(130, 22)
    $txtPfx.Size = New-Object System.Drawing.Size(360, 23)

    $lblPfx = New-Object System.Windows.Forms.Label
    $lblPfx.Text = "PFX Certificate:"
    $lblPfx.Location = New-Object System.Drawing.Point(15, 25)
    $lblPfx.Size = New-Object System.Drawing.Size(110, 20)

    $btnBrowsePfx = New-Object System.Windows.Forms.Button
    $btnBrowsePfx.Text = "..."
    $btnBrowsePfx.Location = New-Object System.Drawing.Point(500, 21)
    $btnBrowsePfx.Size = New-Object System.Drawing.Size(65, 24)
    $btnBrowsePfx.ForeColor = [System.Drawing.Color]::Black

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
    $btnBrowseSignTool.ForeColor = [System.Drawing.Color]::Black

    $lblStatusSetting = New-Object System.Windows.Forms.Label
    $pfxExists = ($defaultPfx -and (Test-Path $defaultPfx))
    $lblStatusSetting.Text = if ($pfxExists) { "✓ Master PFX loaded automatically" } else { "⚠ Master PFX not found" }
    $lblStatusSetting.ForeColor = if ($pfxExists) { [System.Drawing.Color]::LimeGreen } else { [System.Drawing.Color]::Orange }
    $lblStatusSetting.Location = New-Object System.Drawing.Point(130, 112)
    $lblStatusSetting.Size = New-Object System.Drawing.Size(400, 20)

    $grpSettings.Controls.AddRange(@($lblPfx, $txtPfx, $btnBrowsePfx, $lblPassword, $txtPassword, $chkShowPassword, $lblSignTool, $txtSignTool, $btnBrowseSignTool, $lblStatusSetting))

    # 2. File Queue Zone
    $grpDropZone = New-Object System.Windows.Forms.GroupBox
    $grpDropZone.Text = "File Queue (Drag & Drop Here)"
    $grpDropZone.Font = New-EliteFont -family "Montserrat" -size 9 -style ([System.Drawing.FontStyle]::Bold)
    $grpDropZone.Location = New-Object System.Drawing.Point(12, 160)
    $grpDropZone.Size = New-Object System.Drawing.Size(580, 200)
    $grpDropZone.AllowDrop = $true
    $grpDropZone.ForeColor = if ($glassEnabled) { [System.Drawing.Color]::White } else { [System.Drawing.Color]::Black }

    $lbFiles = New-Object System.Windows.Forms.ListBox
    $lbFiles.Location = New-Object System.Drawing.Point(15, 25)
    $lbFiles.Size = New-Object System.Drawing.Size(550, 120)
    $lbFiles.AllowDrop = $true
    $lbFiles.HorizontalScrollbar = $true

    $btnBrowseFiles = New-Object System.Windows.Forms.Button
    $btnBrowseFiles.Text = "Browse Files"
    $btnBrowseFiles.Location = New-Object System.Drawing.Point(15, 155)
    $btnBrowseFiles.Size = New-Object System.Drawing.Size(120, 30)
    $btnBrowseFiles.ForeColor = [System.Drawing.Color]::Black

    $btnClearFiles = New-Object System.Windows.Forms.Button
    $btnClearFiles.Text = "Clear Queue"
    $btnClearFiles.Location = New-Object System.Drawing.Point(145, 155)
    $btnClearFiles.Size = New-Object System.Drawing.Size(120, 30)
    $btnClearFiles.ForeColor = [System.Drawing.Color]::Black

    $btnSignFiles = New-Object System.Windows.Forms.Button
    $btnSignFiles.Text = "Sign Files"
    $btnSignFiles.Font = New-EliteFont -family "Montserrat" -size 9 -style ([System.Drawing.FontStyle]::Bold)
    $btnSignFiles.Location = New-Object System.Drawing.Point(445, 155)
    $btnSignFiles.Size = New-Object System.Drawing.Size(120, 30)
    $btnSignFiles.ForeColor = [System.Drawing.Color]::Black

    $grpDropZone.Controls.AddRange(@($lbFiles, $btnBrowseFiles, $btnClearFiles, $btnSignFiles))

    # 3. Log
    $grpLogs = New-Object System.Windows.Forms.GroupBox
    $grpLogs.Text = "Operations Log"
    $grpLogs.Font = New-EliteFont -family "Montserrat" -size 9 -style ([System.Drawing.FontStyle]::Bold)
    $grpLogs.Location = New-Object System.Drawing.Point(12, 370)
    $grpLogs.Size = New-Object System.Drawing.Size(580, 180)
    $grpLogs.ForeColor = if ($glassEnabled) { [System.Drawing.Color]::White } else { [System.Drawing.Color]::Black }

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
    $btnClearLog.ForeColor = [System.Drawing.Color]::Black

    $lblStatusText = New-Object System.Windows.Forms.Label
    $lblStatusText.Text = "Ready"
    $lblStatusText.Location = New-Object System.Drawing.Point(15, 149)
    $lblStatusText.Size = New-Object System.Drawing.Size(450, 20)

    $grpLogs.Controls.AddRange(@($rtbLog, $btnClearLog, $lblStatusText))

    $btnExit = New-Object System.Windows.Forms.Button
    $btnExit.Text = "Exit"
    $btnExit.Location = New-Object System.Drawing.Point(507, 560)
    $btnExit.Size = New-Object System.Drawing.Size(85, 30)
    $btnExit.ForeColor = [System.Drawing.Color]::Black

    $pnlClient.Controls.AddRange(@($grpSettings, $grpDropZone, $grpLogs, $btnExit))
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
        $timestamp = "[$([DateTime]::Now.ToString('yyyy-MM-dd HH:mm:ss'))]"
        $logLine = "$timestamp [$($type.ToUpper())] $message"
        
        # UI Log
        $rtbLog.SelectionStart = $rtbLog.TextLength
        $rtbLog.SelectionColor = $color
        $rtbLog.AppendText("$logLine`r`n")
        $rtbLog.ScrollToCaret()
        $lblStatusText.Text = $message
        
        # File Log
        try { Add-Content -Path $logFilePath -Value $logLine -ErrorAction SilentlyContinue } catch {}
        
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
            if (Test-Path $bakPath) { Remove-Item $bakPath -Force }
            Move-Item -Path $filePath -Destination $bakPath -Force
            Copy-Item -Path $bakPath -Destination $filePath -Force
            
            $argsSign = @("sign", "/f", $pfx, "/p", $password, "/fd", "SHA256", "/t", "http://timestamp.digicert.com", "/v", $filePath)
            $p = Start-Process -FilePath $signtool -ArgumentList $argsSign -NoNewWindow -PassThru -Wait
            
            if ($p.ExitCode -eq 0) {
                Write-Log "Successfully signed $fileName. Backup saved." "success"
                return $true
            } else {
                Write-Log "SignTool failed for $fileName (Exit code: $($p.ExitCode))" "error"
                Copy-Item -Path $bakPath -Destination $filePath -Force
            }
        } catch {
            Write-Log "Error processing $($fileName): $($_.Exception.Message)" "error"
        }
        return $false
    }

    function Process-DroppedFiles {
        param([string[]]$files)
        foreach ($file in $files) {
            if ($file -and (Test-Path $file -PathType Leaf)) {
                if (-not $lbFiles.Items.Contains($file)) {
                    $null = $lbFiles.Items.Add($file)
                }
            }
        }
        Write-Log "Added $($files.Count) file(s) to queue." "info"
    }

    # --- Events ---
    $form.Add_Load({
        # Fix UAC Drag and Drop by applying filter to specific handles
        [Win32]::ChangeWindowMessageFilterEx($form.Handle, [Win32]::WM_DROPFILES, [Win32]::MSGFLT_ALLOW, [IntPtr]::Zero) | Out-Null
        [Win32]::ChangeWindowMessageFilterEx($form.Handle, [Win32]::WM_COPYDATA, [Win32]::MSGFLT_ALLOW, [IntPtr]::Zero) | Out-Null
        [Win32]::ChangeWindowMessageFilterEx($form.Handle, [Win32]::WM_COPYGLOBALDATA, [Win32]::MSGFLT_ALLOW, [IntPtr]::Zero) | Out-Null
        
        [Win32]::ChangeWindowMessageFilterEx($lbFiles.Handle, [Win32]::WM_DROPFILES, [Win32]::MSGFLT_ALLOW, [IntPtr]::Zero) | Out-Null
        [Win32]::ChangeWindowMessageFilterEx($lbFiles.Handle, [Win32]::WM_COPYDATA, [Win32]::MSGFLT_ALLOW, [IntPtr]::Zero) | Out-Null
        [Win32]::ChangeWindowMessageFilterEx($lbFiles.Handle, [Win32]::WM_COPYGLOBALDATA, [Win32]::MSGFLT_ALLOW, [IntPtr]::Zero) | Out-Null

        # Apply Glass Extension if enabled
        if ($glassEnabled) {
            $margins = New-Object Win32+MARGINS
            $margins.cxLeftWidth = -1
            $margins.cxRightWidth = -1
            $margins.cyTopHeight = -1
            $margins.cyBottomHeight = -1
            [Win32]::DwmExtendFrameIntoClientArea($form.Handle, [ref]$margins) | Out-Null
        }
    })

    $chkGlass.Add_CheckedChanged({
        $val = if ($chkGlass.Checked) { 1 } else { 0 }
        Set-ItemProperty -Path $regPath -Name "EnableGlass" -Value $val -Force
        
        $ans = [System.Windows.Forms.MessageBox]::Show("Frame extension requires an application restart to apply without visual glitches. Restart now?", "Elite EasySigner", [System.Windows.Forms.MessageBoxButtons]::YesNo, [System.Windows.Forms.MessageBoxIcon]::Question)
        if ($ans -eq [System.Windows.Forms.DialogResult]::Yes) {
            $scriptPath = if ($MyInvocation.MyCommand.Path) { $MyInvocation.MyCommand.Path } else { [System.Diagnostics.Process]::GetCurrentProcess().MainModule.FileName }
            Start-Process -FilePath "powershell.exe" -ArgumentList "-ExecutionPolicy Bypass -File `"$scriptPath`"" -Verb RunAs
            $form.Close()
        }
    })

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

    $btnClearFiles.Add_Click({ $lbFiles.Items.Clear(); Write-Log "Queue cleared." "info" })

    $btnSignFiles.Add_Click({
        if ($lbFiles.Items.Count -eq 0) { Write-Log "Queue is empty. Add files first." "warning"; return }
        Write-Log "Processing $($lbFiles.Items.Count) file(s)..." "info"
        $btnSignFiles.Enabled = $false
        foreach ($item in $lbFiles.Items) {
            $null = Sign-File -filePath $item
        }
        $lbFiles.Items.Clear()
        Write-Log "Batch signing complete. Queue cleared." "info"
        $btnSignFiles.Enabled = $true
    })

    $chkShowPassword.Add_Click({ $txtPassword.UseSystemPasswordChar = -not $chkShowPassword.Checked })
    $btnClearLog.Add_Click({ $rtbLog.Clear() })
    $btnExit.Add_Click({ $form.Close() })

    $dragHandler = {
        param($s, $e)
        if ($e.Data.GetDataPresent([System.Windows.Forms.DataFormats]::FileDrop)) { $e.Effect = [System.Windows.Forms.DragDropEffects]::Copy }
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
    $lbFiles.Add_DragEnter($dragHandler)
    $lbFiles.Add_DragDrop($dropHandler)

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
    $err = "CRITICAL INITIALIZATION ERROR:`n`n$($_.Exception.Message)`n`nStack Trace:`n$($_.ScriptStackTrace)"
    try { Add-Content -Path $logFilePath -Value "[$([DateTime]::Now.ToString('yyyy-MM-dd HH:mm:ss'))] [FATAL] $err" -ErrorAction SilentlyContinue } catch {}
    [System.Windows.Forms.MessageBox]::Show($err, "Elite EasySigner - Crash", [System.Windows.Forms.MessageBoxButtons]::OK, [System.Windows.Forms.MessageBoxIcon]::Error) | Out-Null
}