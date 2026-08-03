# Elite EasySigner - v1.0.42.2
# EliteSoftware Professional Certificate Signing Utility
# Est. 2006, Updated for 2026

# Load Assemblies
Add-Type -AssemblyName System.Windows.Forms
Add-Type -AssemblyName System.Drawing

[System.Windows.Forms.Application]::EnableVisualStyles()

# Global variables
$scriptPath = if ($MyInvocation.MyCommand.Path) { $MyInvocation.MyCommand.Path } else { [System.Diagnostics.Process]::GetCurrentProcess().MainModule.FileName }
$scriptDir = [System.IO.Path]::GetDirectoryName($scriptPath)
$baseName = [System.IO.Path]::GetFileNameWithoutExtension($scriptPath)

# 1. Determine local certificate path
$defaultPfx = [System.IO.Path]::Combine($scriptDir, "EliteSoftware_Special.pfx")
if ($defaultPfx -and -not (Test-Path $defaultPfx)) {
    $defaultPfx = [System.IO.Path]::Combine($PSScriptRoot, "EliteSoftware_Special.pfx")
}
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
    # 1. Check current directory/script directory
    $localPaths = @(
        (Join-Path $scriptDir "signtool.exe"),
        (Join-Path $PSScriptRoot "signtool.exe")
    )
    foreach ($p in $localPaths) {
        if ($p -and (Test-Path $p)) { return $p }
    }

    # 2. Check PATH environment variable
    $pathTool = Get-Command "signtool.exe" -ErrorAction SilentlyContinue
    if ($pathTool) { return $pathTool.Source }

    # 3. Check Windows Kits folders
    $sdkRoot = "C:\Program Files (x86)\Windows Kits"
    if (Test-Path $sdkRoot) {
        $win10Bin = Join-Path $sdkRoot "10\bin"
        if (Test-Path $win10Bin) {
            $versions = Get-ChildItem -Path $win10Bin -Directory -ErrorAction SilentlyContinue | 
                        Sort-Object Name -Descending
            foreach ($v in $versions) {
                $signtoolPaths = @(
                    (Join-Path $v.FullName "x64\signtool.exe"),
                    (Join-Path $v.FullName "x86\signtool.exe")
                )
                foreach ($p in $signtoolPaths) {
                    if ($p -and (Test-Path $p)) { return $p }
                }
            }
            $directPaths = @(
                (Join-Path $win10Bin "x64\signtool.exe"),
                (Join-Path $win10Bin "x86\signtool.exe")
            )
            foreach ($p in $directPaths) {
                if ($p -and (Test-Path $p)) { return $p }
            }
        }
        $win81Bin = Join-Path $sdkRoot "8.1\bin"
        if (Test-Path $win81Bin) {
            $signtoolPaths = @(
                (Join-Path $win81Bin "x64\signtool.exe"),
                (Join-Path $win81Bin "x86\signtool.exe")
            )
            foreach ($p in $signtoolPaths) {
                if ($p -and (Test-Path $p)) { return $p }
            }
        }
    }

    # 4. Check Program Files / Program Files (x86) generally
    $progFiles = @($env:ProgramFiles, ${env:ProgramFiles(x86)})
    foreach ($pf in $progFiles) {
        if ($pf) {
            $sdkPath = Join-Path $pf "Microsoft SDKs\Windows"
            if (Test-Path $sdkPath) {
                $signtoolPaths = Get-ChildItem -Path $sdkPath -Filter "signtool.exe" -Recurse -File -ErrorAction SilentlyContinue |
                                 Sort-Object LastWriteTime -Descending
                if ($signtoolPaths) {
                    return $signtoolPaths[0].FullName
                }
            }
        }
    }
    return ""
}

# --- Create Form ---
$form = New-Object System.Windows.Forms.Form
$form.Text = "Elite EasySigner - v1.0.42.2"
$form.Size = New-Object System.Drawing.Size(620, 580)
$form.FormBorderStyle = [System.Windows.Forms.FormBorderStyle]::FixedDialog
$form.MaximizeBox = $false
$form.MinimizeBox = $true
$form.StartPosition = [System.Windows.Forms.FormStartPosition]::CenterScreen
$form.AllowDrop = $true
$form.Font = New-EliteFont -family "Montserrat" -size 9

# Load Icon
$icoPath = [System.IO.Path]::Combine($scriptDir, "$baseName.ico")
$exePath = [System.IO.Path]::Combine($scriptDir, "$baseName.exe")
$formIcon = $null

if ($icoPath -and (Test-Path $icoPath)) {
    try { $formIcon = New-Object System.Drawing.Icon($icoPath) } catch {}
}
if ($null -eq $formIcon -and $exePath -and (Test-Path $exePath)) {
    try { $formIcon = [System.Drawing.Icon]::ExtractAssociatedIcon($exePath) } catch {}
}
if ($null -eq $formIcon) {
    $fallbackIco = [System.IO.Path]::Combine($PSScriptRoot, "Elite-EasySigner.ico")
    if ($fallbackIco -and (Test-Path $fallbackIco)) {
        try { $formIcon = New-Object System.Drawing.Icon($fallbackIco) } catch {}
    }
}
if ($formIcon) {
    $form.Icon = $formIcon
}

# --- Header Panel (Vista Wizard style) ---
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
$lblHeaderSub.Text = "v1.0.42.2 - EliteSoftware Certificate Signing Utility"
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

# --- Main Client Area Panel ---
$pnlClient = New-Object System.Windows.Forms.Panel
$pnlClient.Dock = [System.Windows.Forms.DockStyle]::Fill
$pnlClient.BackColor = [System.Drawing.SystemColors]::Control

# 1. Configuration GroupBox
$grpSettings = New-Object System.Windows.Forms.GroupBox
$grpSettings.Text = "Signing Configuration"
$grpSettings.Font = New-EliteFont -family "Montserrat" -size 9 -style ([System.Drawing.FontStyle]::Bold)
$grpSettings.Location = New-Object System.Drawing.Point(12, 10)
$grpSettings.Size = New-Object System.Drawing.Size(580, 140)

$lblPfx = New-Object System.Windows.Forms.Label
$lblPfx.Text = "PFX Certificate:"
$lblPfx.Font = New-EliteFont -family "Montserrat" -size 8.5 -style ([System.Drawing.FontStyle]::Regular)
$lblPfx.Location = New-Object System.Drawing.Point(15, 25)
$lblPfx.Size = New-Object System.Drawing.Size(110, 20)

$txtPfx = New-Object System.Windows.Forms.TextBox
$txtPfx.Text = if ($defaultPfx -and (Test-Path $defaultPfx)) { $defaultPfx } else { "" }
$txtPfx.Font = New-EliteFont -family "Montserrat" -size 8.5 -style ([System.Drawing.FontStyle]::Regular)
$txtPfx.Location = New-Object System.Drawing.Point(130, 22)
$txtPfx.Size = New-Object System.Drawing.Size(360, 23)

$btnBrowsePfx = New-Object System.Windows.Forms.Button
$btnBrowsePfx.Text = "..."
$btnBrowsePfx.Font = New-EliteFont -family "Montserrat" -size 8.5 -style ([System.Drawing.FontStyle]::Regular)
$btnBrowsePfx.Location = New-Object System.Drawing.Point(500, 21)
$btnBrowsePfx.Size = New-Object System.Drawing.Size(65, 24)

$lblPassword = New-Object System.Windows.Forms.Label
$lblPassword.Text = "PFX Password:"
$lblPassword.Font = New-EliteFont -family "Montserrat" -size 8.5 -style ([System.Drawing.FontStyle]::Regular)
$lblPassword.Location = New-Object System.Drawing.Point(15, 55)
$lblPassword.Size = New-Object System.Drawing.Size(110, 20)

$txtPassword = New-Object System.Windows.Forms.TextBox
$txtPassword.Text = $defaultPassword
$txtPassword.UseSystemPasswordChar = $true
$txtPassword.Font = New-EliteFont -family "Montserrat" -size 8.5 -style ([System.Drawing.FontStyle]::Regular)
$txtPassword.Location = New-Object System.Drawing.Point(130, 52)
$txtPassword.Size = New-Object System.Drawing.Size(260, 23)

$chkShowPassword = New-Object System.Windows.Forms.CheckBox
$chkShowPassword.Text = "Show"
$chkShowPassword.Font = New-EliteFont -family "Montserrat" -size 8.5 -style ([System.Drawing.FontStyle]::Regular)
$chkShowPassword.Location = New-Object System.Drawing.Point(400, 54)
$chkShowPassword.Size = New-Object System.Drawing.Size(80, 20)

$lblSignTool = New-Object System.Windows.Forms.Label
$lblSignTool.Text = "SignTool Path:"
$lblSignTool.Font = New-EliteFont -family "Montserrat" -size 8.5 -style ([System.Drawing.FontStyle]::Regular)
$lblSignTool.Location = New-Object System.Drawing.Point(15, 85)
$lblSignTool.Size = New-Object System.Drawing.Size(110, 20)

$txtSignTool = New-Object System.Windows.Forms.TextBox
$txtSignTool.Text = Find-SignTool
$txtSignTool.Font = New-EliteFont -family "Montserrat" -size 8.5 -style ([System.Drawing.FontStyle]::Regular)
$txtSignTool.Location = New-Object System.Drawing.Point(130, 82)
$txtSignTool.Size = New-Object System.Drawing.Size(360, 23)

$btnBrowseSignTool = New-Object System.Windows.Forms.Button
$btnBrowseSignTool.Text = "..."
$btnBrowseSignTool.Font = New-EliteFont -family "Montserrat" -size 8.5 -style ([System.Drawing.FontStyle]::Regular)
$btnBrowseSignTool.Location = New-Object System.Drawing.Point(500, 81)
$btnBrowseSignTool.Size = New-Object System.Drawing.Size(65, 24)

$lblStatusSetting = New-Object System.Windows.Forms.Label
$lblStatusSetting.Text = if ($defaultPfx -and (Test-Path $defaultPfx)) { "✓ Master PFX loaded automatically" } else { "⚠ Master PFX not found in script folder" }
$lblStatusSetting.Font = New-EliteFont -family "Montserrat" -size 8 -style ([System.Drawing.FontStyle]::Italic)
$lblStatusSetting.ForeColor = if ($defaultPfx -and (Test-Path $defaultPfx)) { [System.Drawing.Color]::DarkGreen } else { [System.Drawing.Color]::DarkOrange }
$lblStatusSetting.Location = New-Object System.Drawing.Point(130, 112)
$lblStatusSetting.Size = New-Object System.Drawing.Size(400, 20)

$grpSettings.Controls.AddRange(@(
    $lblPfx, $txtPfx, $btnBrowsePfx,
    $lblPassword, $txtPassword, $chkShowPassword,
    $lblSignTool, $txtSignTool, $btnBrowseSignTool,
    $lblStatusSetting
))

# 2. Drag and Drop GroupBox
$grpDropZone = New-Object System.Windows.Forms.GroupBox
$grpDropZone.Text = "Drag & Drop Files Here to Sign"
$grpDropZone.Font = New-EliteFont -family "Montserrat" -size 9 -style ([System.Drawing.FontStyle]::Bold)
$grpDropZone.Location = New-Object System.Drawing.Point(12, 160)
$grpDropZone.Size = New-Object System.Drawing.Size(580, 110)
$grpDropZone.AllowDrop = $true

$lblDropPrompt = New-Object System.Windows.Forms.Label
$lblDropPrompt.Text = "DRAG AND DROP EXE, DLL, CPL, MUI, MUN, OCX FILES HERE`n`nCopies will be signed in 'Signed_Components'`nOriginals will be preserved in 'Original_Unsigned-Components'"
$lblDropPrompt.Font = New-EliteFont -family "Montserrat" -size 8.5 -style ([System.Drawing.FontStyle]::Bold)
$lblDropPrompt.ForeColor = [System.Drawing.Color]::DimGray
$lblDropPrompt.TextAlign = [System.Drawing.ContentAlignment]::MiddleCenter
$lblDropPrompt.Dock = [System.Windows.Forms.DockStyle]::Fill
$lblDropPrompt.AllowDrop = $true

$grpDropZone.Controls.Add($lblDropPrompt)

# 3. Operations Log GroupBox
$grpLogs = New-Object System.Windows.Forms.GroupBox
$grpLogs.Text = "Operations Log"
$grpLogs.Font = New-EliteFont -family "Montserrat" -size 9 -style ([System.Drawing.FontStyle]::Bold)
$grpLogs.Location = New-Object System.Drawing.Point(12, 280)
$grpLogs.Size = New-Object System.Drawing.Size(580, 160)

$rtbLog = New-Object System.Windows.Forms.RichTextBox
$rtbLog.Location = New-Object System.Drawing.Point(15, 25)
$rtbLog.Size = New-Object System.Drawing.Size(550, 95)
$rtbLog.ReadOnly = $true
$rtbLog.Font = New-Object System.Drawing.Font("Consolas", 8.5)
$rtbLog.BackColor = [System.Drawing.Color]::White
$rtbLog.ForeColor = [System.Drawing.Color]::Black

$btnClearLog = New-Object System.Windows.Forms.Button
$btnClearLog.Text = "Clear Log"
$btnClearLog.Font = New-EliteFont -family "Montserrat" -size 8 -style ([System.Drawing.FontStyle]::Regular)
$btnClearLog.Location = New-Object System.Drawing.Point(480, 126)
$btnClearLog.Size = New-Object System.Drawing.Size(85, 24)

$lblStatusText = New-Object System.Windows.Forms.Label
$lblStatusText.Text = "Ready"
$lblStatusText.Font = New-EliteFont -family "Montserrat" -size 8.5 -style ([System.Drawing.FontStyle]::Regular)
$lblStatusText.Location = New-Object System.Drawing.Point(15, 129)
$lblStatusText.Size = New-Object System.Drawing.Size(450, 20)

$grpLogs.Controls.AddRange(@($rtbLog, $btnClearLog, $lblStatusText))

$pnlClient.Controls.AddRange(@($grpSettings, $grpDropZone, $grpLogs))

$form.Controls.AddRange(@($pnlClient, $pnlHeader))

# --- Functions ---

function Write-Log {
    param(
        [string]$message,
        [string]$type = "info"
    )
    $color = [System.Drawing.Color]::Black
    switch ($type.ToLower()) {
        "success" { $color = [System.Drawing.Color]::DarkGreen }
        "error"   { $color = [System.Drawing.Color]::DarkRed }
        "warning" { $color = [System.Drawing.Color]::DarkOrange }
        "info"    { $color = [System.Drawing.Color]::FromArgb(40, 40, 40) }
    }
    
    $rtbLog.SelectionStart = $rtbLog.TextLength
    $rtbLog.SelectionLength = 0
    $rtbLog.SelectionColor = $color
    
    $timestamp = [DateTime]::Now.ToString("HH:mm:ss")
    $rtbLog.AppendText("[$timestamp] [$($type.ToUpper())] $message`r`n")
    $rtbLog.SelectionColor = $rtbLog.ForeColor
    $rtbLog.ScrollToCaret()
    
    $lblStatusText.Text = $message
    if ($type -eq "error") {
        $lblStatusText.ForeColor = [System.Drawing.Color]::DarkRed
    } else {
        $lblStatusText.ForeColor = [System.Drawing.SystemColors]::ControlText
    }
}

function Sign-File {
    param(
        [string]$filePath
    )
    
    if (-not $filePath -or -not (Test-Path $filePath)) {
        Write-Log "File not found: $filePath" "error"
        return $false
    }
    
    $pfx = $txtPfx.Text.Trim()
    $password = $txtPassword.Text
    $signtool = $txtSignTool.Text.Trim()
    
    if (-not $signtool -or -not (Test-Path $signtool)) {
        Write-Log "SignTool path is invalid or empty. Please select signtool.exe." "error"
        return $false
    }
    
    if (-not $pfx -or -not (Test-Path $pfx)) {
        Write-Log "PFX certificate path is invalid or empty. Please select a .pfx file." "error"
        return $false
    }
    
    $fileDir = [System.IO.Path]::GetDirectoryName($filePath)
    $fileName = [System.IO.Path]::GetFileName($filePath)
    $fileExt = [System.IO.Path]::GetExtension($filePath).ToLower()
    
    # Define subdirectory paths
    $signedDir = [System.IO.Path]::Combine($fileDir, "Signed_Components")
    $origDir = [System.IO.Path]::Combine($fileDir, "Original_Unsigned-Components")
    
    # Create subdirectories
    try {
        if ($signedDir -and -not (Test-Path $signedDir)) {
            $null = New-Item -ItemType Directory -Path $signedDir -Force
        }
        if ($origDir -and -not (Test-Path $origDir)) {
            $null = New-Item -ItemType Directory -Path $origDir -Force
        }
    } catch {
        Write-Log "Failed to create Signed_Components or Original_Unsigned-Components directories: $_" "error"
        return $false
    }
    
    $signedFilePath = [System.IO.Path]::Combine($signedDir, $fileName)
    $origFilePath = [System.IO.Path]::Combine($origDir, $fileName)
    
    Write-Log "Processing: $fileName ($fileExt)" "info"
    
    # Copy original to Signed_Components
    try {
        Copy-Item -Path $filePath -Destination $signedFilePath -Force
    } catch {
        Write-Log "Failed to copy file to Signed_Components: $_" "error"
        return $false
    }
    
    # Sign the copy in Signed_Components
    Write-Log "Signing copy of $fileName..." "info"
    
    # Argument array for signtool
    $argsList = @("sign", "/f", $pfx, "/p", $password, "/fd", "SHA256", "/t", "http://timestamp.digicert.com", "/v", $signedFilePath)
    
    # Output redirection files to temp
    $tempOut = [System.IO.Path]::Combine($env:TEMP, "signtool_out.txt")
    $tempErr = [System.IO.Path]::Combine($env:TEMP, "signtool_err.txt")
    
    if ($tempOut -and (Test-Path $tempOut)) { Remove-Item $tempOut -Force }
    if ($tempErr -and (Test-Path $tempErr)) { Remove-Item $tempErr -Force }
    
    try {
        $process = Start-Process -FilePath $signtool -ArgumentList $argsList -NoNewWindow -PassThru -Wait -RedirectStandardOutput $tempOut -RedirectStandardError $tempErr
        $exitCode = $process.ExitCode
    } catch {
        Write-Log "Exception occurred while launching signtool.exe: $_" "error"
        # Clean up copied file on exception
        if ($signedFilePath -and (Test-Path $signedFilePath)) { Remove-Item $signedFilePath -Force }
        return $false
    }
    
    $stdout = if ($tempOut -and (Test-Path $tempOut)) { Get-Content $tempOut -Raw -ErrorAction SilentlyContinue } else { "" }
    $stderr = if ($tempErr -and (Test-Path $tempErr)) { Get-Content $tempErr -Raw -ErrorAction SilentlyContinue } else { "" }
    
    if ($exitCode -eq 0) {
        Write-Log "SignTool succeeded for $fileName." "success"
        
        # Move original file to Original_Unsigned-Components
        try {
            Move-Item -Path $filePath -Destination $origFilePath -Force
            Write-Log "Moved original [$fileName] to 'Original_Unsigned-Components'." "success"
            Write-Log "Saved signed [$fileName] in 'Signed_Components'." "success"
            return $true
        } catch {
            Write-Log "Signed copy successfully, but failed to move original file: $_" "warning"
            return $true
        }
    } else {
        Write-Log "SignTool failed with exit code $exitCode." "error"
        if ($stderr.Trim()) { Write-Log "Error: $($stderr.Trim())" "error" }
        if ($stdout.Trim()) { Write-Log "Output: $($stdout.Trim())" "error" }
        
        # Delete the unsigned copy in Signed_Components so we don't leave bad files
        if ($signedFilePath -and (Test-Path $signedFilePath)) {
            try { Remove-Item $signedFilePath -Force } catch {}
        }
        return $false
    }
}

function Process-DroppedFiles {
    param(
        [string[]]$files
    )
    
    if ($files.Count -eq 0) { return }
    
    # Check if we have valid signing configurations first
    $pfx = $txtPfx.Text.Trim()
    $signtool = $txtSignTool.Text.Trim()
    
    if (-not $signtool -or -not (Test-Path $signtool)) {
        [System.Windows.Forms.MessageBox]::Show("SignTool path is invalid or empty. Please select signtool.exe before signing files.", "SignTool Not Found", [System.Windows.Forms.MessageBoxButtons]::OK, [System.Windows.Forms.MessageBoxIcon]::Error) | Out-Null
        return
    }
    
    if (-not $pfx -or -not (Test-Path $pfx)) {
        [System.Windows.Forms.MessageBox]::Show("PFX certificate path is invalid or empty. Please select a .pfx file before signing files.", "Certificate Not Found", [System.Windows.Forms.MessageBoxButtons]::OK, [System.Windows.Forms.MessageBoxIcon]::Error) | Out-Null
        return
    }
    
    $successCount = 0
    $failCount = 0
    
    # Disable controls briefly during operation
    $grpSettings.Enabled = $false
    $grpDropZone.Enabled = $false
    $btnClearLog.Enabled = $false
    
    try {
        foreach ($file in $files) {
            if ($file -and (Test-Path $file -PathType Container)) {
                Write-Log "Skipped folder: $file" "warning"
                continue
            }
            
            if ($file) {
                $res = Sign-File -filePath $file
                if ($res) {
                    $successCount++
                } else {
                    $failCount++
                }
            }
            
            # Allow UI to redraw
            [System.Windows.Forms.Application]::DoEvents()
        }
        
        if ($successCount -gt 0 -or $failCount -gt 0) {
            Write-Log "Batch Completed. Success: $successCount, Failed: $failCount" "info"
            [System.Windows.Forms.MessageBox]::Show("Batch signature process finished.`n`nSuccessfully Signed: $successCount`nFailed: $failCount", "Elite EasySigner - Finished", [System.Windows.Forms.MessageBoxButtons]::OK, [System.Windows.Forms.MessageBoxIcon]::Information) | Out-Null
        }
    } finally {
        $grpSettings.Enabled = $true
        $grpDropZone.Enabled = $true
        $btnClearLog.Enabled = $true
    }
}

# --- Event Handlers ---

# 1. Browse PFX
$btnBrowsePfx.Add_Click({
    $dialog = New-Object System.Windows.Forms.OpenFileDialog
    $dialog.Filter = "Personal Information Exchange (*.pfx)|*.pfx|All files (*.*)|*.*"
    $dialog.Title = "Select PFX Certificate"
    if ($txtPfx.Text -and (Test-Path $txtPfx.Text)) {
        $dialog.InitialDirectory = [System.IO.Path]::GetDirectoryName($txtPfx.Text)
    } else {
        $dialog.InitialDirectory = $scriptDir
    }
    
    if ($dialog.ShowDialog() -eq [System.Windows.Forms.DialogResult]::OK) {
        $txtPfx.Text = $dialog.FileName
        $lblStatusSetting.Text = "✓ Custom PFX loaded"
        $lblStatusSetting.ForeColor = [System.Drawing.Color]::DarkGreen
        Write-Log "PFX Certificate changed to: $($dialog.FileName)" "info"
    }
})

# 2. Browse SignTool
$btnBrowseSignTool.Add_Click({
    $dialog = New-Object System.Windows.Forms.OpenFileDialog
    $dialog.Filter = "SignTool Executable (signtool.exe)|signtool.exe|Executables (*.exe)|*.exe|All files (*.*)|*.*"
    $dialog.Title = "Select signtool.exe Path"
    if ($txtSignTool.Text -and (Test-Path $txtSignTool.Text)) {
        $dialog.InitialDirectory = [System.IO.Path]::GetDirectoryName($txtSignTool.Text)
    }
    
    if ($dialog.ShowDialog() -eq [System.Windows.Forms.DialogResult]::OK) {
        $txtSignTool.Text = $dialog.FileName
        Write-Log "SignTool path changed to: $($dialog.FileName)" "info"
    }
})

# 3. Show/Hide Password
$chkShowPassword.Add_Click({
    $txtPassword.UseSystemPasswordChar = -not $chkShowPassword.Checked
})

# 4. Clear Log
$btnClearLog.Add_Click({
    $rtbLog.Clear()
    Write-Log "Ready" "info"
})

# 5. Drag and Drop events
$dragEnterHandler = {
    param($sender, $e)
    if ($e.Data.GetDataPresent([System.Windows.Forms.DataFormats]::FileDrop)) {
        $e.Effect = [System.Windows.Forms.DragDropEffects]::Copy
        $lblDropPrompt.ForeColor = [System.Drawing.Color]::SteelBlue
        $grpDropZone.BackColor = [System.Drawing.Color]::FromArgb(235, 245, 255)
    } else {
        $e.Effect = [System.Windows.Forms.DragDropEffects]::None
    }
}

$dragLeaveHandler = {
    param($sender, $e)
    $lblDropPrompt.ForeColor = [System.Drawing.Color]::DimGray
    $grpDropZone.BackColor = [System.Drawing.SystemColors]::Control
}

$dragDropHandler = {
    param($sender, $e)
    $lblDropPrompt.ForeColor = [System.Drawing.Color]::DimGray
    $grpDropZone.BackColor = [System.Drawing.SystemColors]::Control
    $files = $e.Data.GetData([System.Windows.Forms.DataFormats]::FileDrop)
    if ($files) {
        Process-DroppedFiles -files $files
    }
}

$grpDropZone.Add_DragEnter($dragEnterHandler)
$grpDropZone.Add_DragLeave($dragLeaveHandler)
$grpDropZone.Add_DragDrop($dragDropHandler)

$lblDropPrompt.Add_DragEnter($dragEnterHandler)
$lblDropPrompt.Add_DragLeave($dragLeaveHandler)
$lblDropPrompt.Add_DragDrop($dragDropHandler)

# Also allow dropping directly onto the form background
$form.Add_DragEnter($dragEnterHandler)
$form.Add_DragLeave($dragLeaveHandler)
$form.Add_DragDrop($dragDropHandler)

# Show startup logs
Write-Log "Elite EasySigner - v1.0.42.2 initialized successfully." "info"
if ($txtSignTool.Text) {
    Write-Log "Auto-detected SignTool: $($txtSignTool.Text)" "info"
} else {
    Write-Log "Warning: signtool.exe was not found automatically. Please browse and select it." "warning"
}

if ($defaultPfx -and (Test-Path $defaultPfx)) {
    Write-Log "Auto-loaded EliteSoftware Special PFX certificate." "info"
}

# --- Show Form ---
$null = $form.ShowDialog()

# Clean up Resources
if ($formIcon) { $formIcon.Dispose() }
$form.Dispose()
