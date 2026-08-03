# Elite EasySigner - v1.0.52.0
# EliteSoftware Professional Certificate Signing Utility
# Est. 2006, Updated for 2026

# Capture CLI arguments 
$global:scriptArgs = $args

# Load Assemblies
Add-Type -AssemblyName System.Windows.Forms
Add-Type -AssemblyName System.Drawing
Add-Type -AssemblyName System.Security

[System.Windows.Forms.Application]::EnableVisualStyles()

# --- Elite Legacy Drag & Drop & UIPI Bypass Framework ---
# Dynamically pull all loaded assemblies, strictly filtering for .dll to avoid PS2EXE host wrapper crashes
$eliteAssemblies = [AppDomain]::CurrentDomain.GetAssemblies() | Where-Object { 
    -not $_.IsDynamic -and 
    [string]::IsNullOrWhiteSpace($_.Location) -eq $false -and 
    $_.Location.EndsWith('.dll', [System.StringComparison]::OrdinalIgnoreCase) 
} | Select-Object -ExpandProperty Location

Add-Type -ReferencedAssemblies $eliteAssemblies -TypeDefinition @"
using System;
using System.Windows.Forms;
using System.Runtime.InteropServices;
using System.Text;

public class Win32 {
    [DllImport("dwmapi.dll")]
    public static extern int DwmExtendFrameIntoClientArea(IntPtr hWnd, ref MARGINS pMarInset);

    [StructLayout(LayoutKind.Sequential)]
    public struct MARGINS {
        public int cxLeftWidth;
        public int cxRightWidth;
        public int cyTopHeight;
        public int cyBottomHeight;
    }
    
    [DllImport("shell32.dll")] public static extern void DragAcceptFiles(IntPtr hwnd, bool fAccept);
    [DllImport("shell32.dll")] public static extern uint DragQueryFile(IntPtr hDrop, uint iFile, StringBuilder lpszFile, uint cch);
    [DllImport("shell32.dll")] public static extern void DragFinish(IntPtr hDrop);
    [DllImport("user32.dll", SetLastError = true)] public static extern bool ChangeWindowMessageFilterEx(IntPtr hWnd, uint msg, uint action, IntPtr changeFilterStruct);
    
    public static void EnableLegacyDragDrop(IntPtr handle) {
        ChangeWindowMessageFilterEx(handle, 0x0233, 1, IntPtr.Zero); // WM_DROPFILES
        ChangeWindowMessageFilterEx(handle, 0x0049, 1, IntPtr.Zero); // WM_COPYGLOBALDATA
        ChangeWindowMessageFilterEx(handle, 0x004A, 1, IntPtr.Zero); // WM_COPYDATA
        DragAcceptFiles(handle, true);
    }
    
    public static string[] GetDroppedFiles(IntPtr hDrop) {
        uint count = DragQueryFile(hDrop, 0xFFFFFFFF, null, 0);
        string[] files = new string[count];
        for (uint i = 0; i < count; i++) {
            StringBuilder sb = new StringBuilder(260);
            DragQueryFile(hDrop, i, sb, 260);
            files[i] = sb.ToString();
        }
        DragFinish(hDrop);
        return files;
    }
}

public class EliteForm : Form {
    public delegate void FilesDroppedHandler(string[] files);
    public event FilesDroppedHandler FilesDropped;
    protected override void OnHandleCreated(EventArgs e) {
        base.OnHandleCreated(e);
        Win32.EnableLegacyDragDrop(this.Handle);
    }
    protected override void WndProc(ref Message m) {
        if (m.Msg == 0x0233) {
            if (FilesDropped != null) FilesDropped(Win32.GetDroppedFiles(m.WParam));
            m.Result = IntPtr.Zero;
            return;
        }
        base.WndProc(ref m);
    }
}

public class EliteListBox : ListBox {
    public delegate void FilesDroppedHandler(string[] files);
    public event FilesDroppedHandler FilesDropped;
    protected override void OnHandleCreated(EventArgs e) {
        base.OnHandleCreated(e);
        Win32.EnableLegacyDragDrop(this.Handle);
    }
    protected override void WndProc(ref Message m) {
        if (m.Msg == 0x0233) {
            if (FilesDropped != null) FilesDropped(Win32.GetDroppedFiles(m.WParam));
            m.Result = IntPtr.Zero;
            return;
        }
        base.WndProc(ref m);
    }
}

public class EliteGroupBox : GroupBox {
    public delegate void FilesDroppedHandler(string[] files);
    public event FilesDroppedHandler FilesDropped;
    protected override void OnHandleCreated(EventArgs e) {
        base.OnHandleCreated(e);
        Win32.EnableLegacyDragDrop(this.Handle);
    }
    protected override void WndProc(ref Message m) {
        if (m.Msg == 0x0233) {
            if (FilesDropped != null) FilesDropped(Win32.GetDroppedFiles(m.WParam));
            m.Result = IntPtr.Zero;
            return;
        }
        base.WndProc(ref m);
    }
}
"@

# Global variables
$scriptPath = if ($MyInvocation.MyCommand.Path) { $MyInvocation.MyCommand.Path } else { [System.Diagnostics.Process]::GetCurrentProcess().MainModule.FileName }
$scriptDir = if ($scriptPath) { [System.IO.Path]::GetDirectoryName($scriptPath) } else { (Get-Location).Path }
if (-not $scriptDir) { $scriptDir = (Get-Location).Path }
$baseName = if ($scriptPath) { [System.IO.Path]::GetFileNameWithoutExtension($scriptPath) } else { "Elite-EasySigner" }
$logFilePath = Join-Path $scriptDir "Elite-EasySigner_Error.log"

$isAdmin = ([Security.Principal.WindowsPrincipal][Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)

# Registry for UI Config
$regPath = "HKCU:\Software\EliteSoftware\EasySigner"
if (-not (Test-Path $regPath)) { New-Item -Path $regPath -Force | Out-Null }
$glassEnabled = (Get-ItemProperty -Path $regPath -Name "EnableGlass" -ErrorAction SilentlyContinue).EnableGlass -eq 1
$useSignToolConfig = (Get-ItemProperty -Path $regPath -Name "UseSignTool" -ErrorAction SilentlyContinue).UseSignTool -eq 1

# Supported Extensions
$supportedExts = @('.dll', '.mui', '.mun', '.cpl', '.exe', '.ocx', '.ps1', '.msi', '.cab', '.sys')

# 1. Determine local certificate path
$defaultPfx = if ($scriptDir) { [System.IO.Path]::Combine($scriptDir, "EliteSoftware_Special.pfx") } else { "EliteSoftware_Special.pfx" }
$defaultPassword = "Minecraft145!!"

# --- Helper Functions ---

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

function Resolve-Shortcut {
    param([string]$Path)
    if ($Path -match '\.lnk$') {
        try {
            $wshell = New-Object -ComObject WScript.Shell
            $shortcut = $wshell.CreateShortcut($Path)
            if ($shortcut.TargetPath) { return $shortcut.TargetPath }
        } catch {
            Write-Log "Failed to parse shortcut. The digital ghost in the machine said no: $($_.Exception.Message)" "warning"
        }
    }
    return $Path
}

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

function Write-Log {
    param([string]$message, [string]$type = "info")
    $color = [System.Drawing.Color]::Black
    switch ($type.ToLower()) {
        "success" { $color = [System.Drawing.Color]::DarkGreen }
        "error"   { $color = [System.Drawing.Color]::DarkRed }
        "warning" { $color = [System.Drawing.Color]::DarkOrange }
        "worker"  { $color = [System.Drawing.Color]::Purple }
    }
    $timestamp = "[$([DateTime]::Now.ToString('yyyy-MM-dd HH:mm:ss'))]"
    $logLine = "$timestamp [$($type.ToUpper())] $message"
    
    if ($global:rtbLog -and $global:lblStatusText) {
        $global:rtbLog.SelectionStart = $global:rtbLog.TextLength
        $global:rtbLog.SelectionColor = $color
        $global:rtbLog.AppendText("$logLine`r`n")
        $global:rtbLog.ScrollToCaret()
        $global:lblStatusText.Text = $message
        [System.Windows.Forms.Application]::DoEvents()
    }
    
    if ($global:lblProgressStatus) {
        $global:lblProgressStatus.Text = $message
        [System.Windows.Forms.Application]::DoEvents()
    }
    
    try { Add-Content -Path $logFilePath -Value $logLine -ErrorAction SilentlyContinue } catch {}
}

function Sign-File {
    param(
        [string]$filePath,
        [string]$pfxPath,
        [string]$pfxPass,
        [string]$signToolPath,
        [bool]$useSignTool
    )
    if (-not $filePath -or -not (Test-Path $filePath)) { return $false }
    
    $fileExt = [System.IO.Path]::GetExtension($filePath).ToLower()
    if ($supportedExts -notcontains $fileExt) {
        Write-Log "Ignored $filePath. Extension $fileExt is not elite enough." "warning"
        return $false
    }

    if (-not $pfxPath -or -not (Test-Path $pfxPath)) { Write-Log "Master PFX missing. Refusing to forge documents." "error"; return $false }
    
    $fileDir = [System.IO.Path]::GetDirectoryName($filePath)
    $fileName = [System.IO.Path]::GetFileName($filePath)
    
    # Strip Read-Only Attribute if present to prevent Access Denied errors
    $fileInfo = Get-Item -LiteralPath $filePath -Force
    $wasReadOnly = $fileInfo.IsReadOnly
    if ($wasReadOnly) {
        try {
            $fileInfo.IsReadOnly = $false
            Write-Log "Stripped Read-Only attribute from $fileName for digital ink application." "info"
        } catch {
            Write-Log "Failed to strip Read-Only flag from $fileName. Access might still be denied." "warning"
        }
    }

    $tempBak = [System.IO.Path]::GetTempFileName()
    try {
        Copy-Item -Path $filePath -Destination $tempBak -Force
    } catch {
        Write-Log "Failed to secure a temporary backup for $($fileName). Aborting to save your bits. Is the file locked or running?" "error"
        if ($wasReadOnly -and (Test-Path -LiteralPath $filePath)) { try { (Get-Item -LiteralPath $filePath -Force).IsReadOnly = $true } catch {} }
        return $false
    }
    
    $signSuccess = $false

    if ($useSignTool) {
        if (-not $signToolPath -or -not (Test-Path $signToolPath)) { Write-Log "SignTool.exe is MIA." "error"; return $false }
        try {
            $argsSign = @("sign", "/f", $pfxPath, "/p", $pfxPass, "/fd", "SHA256", "/t", "http://timestamp.digicert.com", "/v", $filePath)
            $p = Start-Process -FilePath $signToolPath -ArgumentList $argsSign -NoNewWindow -PassThru -Wait
            if ($p.ExitCode -eq 0) { $signSuccess = $true } 
            else { Write-Log "SignTool vehemently rejected $fileName (Exit code: $($p.ExitCode))." "error" }
        } catch {
            Write-Log "SignTool crashed harder than a Vista machine on 512MB of RAM: $($_.Exception.Message)" "error"
        }
    } else {
        try {
            $cert = New-Object System.Security.Cryptography.X509Certificates.X509Certificate2($pfxPath, $pfxPass, [System.Security.Cryptography.X509Certificates.X509KeyStorageFlags]::DefaultKeySet)
            $signParams = @{
                FilePath = $filePath
                Certificate = $cert
                HashAlgorithm = "SHA256"
                TimestampServer = "http://timestamp.digicert.com"
            }
            $result = Set-AuthenticodeSignature @signParams
            if ($result.Status -eq 'Valid') { 
                $signSuccess = $true 
            } else { 
                Write-Log "Native auth failed for $fileName. Reason: $($result.StatusMessage). The cryptography gods say no." "error" 
            }
        } catch {
            Write-Log "Native signing blew up unexpectedly. Access Denied or file lock?: $($_.Exception.Message)" "error"
        }
    }

    if ($signSuccess) {
        $origDir = Join-Path $fileDir "Original_Unsigned-Components"
        if (-not (Test-Path $origDir)) { $null = New-Item -ItemType Directory -Path $origDir -Force }
        $bakPath = Join-Path $origDir "$fileName.bak"
        if (Test-Path $bakPath) { Remove-Item $bakPath -Force }
        Move-Item -Path $tempBak -Destination $bakPath -Force
        
        # Restore Read-Only attribute on the newly signed file if it had it originally
        if ($wasReadOnly -and (Test-Path -LiteralPath $filePath)) { try { (Get-Item -LiteralPath $filePath -Force).IsReadOnly = $true } catch {} }
        
        Write-Log "Successfully signed $fileName. Pristine original backed up." "success"
        return $true
    } else {
        Copy-Item -Path $tempBak -Destination $filePath -Force
        Remove-Item -Path $tempBak -Force
        
        if ($wasReadOnly -and (Test-Path -LiteralPath $filePath)) { try { (Get-Item -LiteralPath $filePath -Force).IsReadOnly = $true } catch {} }
        
        Write-Log "Restored $fileName to its original unsigned state. No backup created." "warning"
        return $false
    }
}

try {
    # --- Worker Mode Interception (Headless Elevated Action) ---
    $workerIndex = [array]::IndexOf($global:scriptArgs, "-EliteWorker")
    if ($workerIndex -ge 0 -and $workerIndex -lt ($global:scriptArgs.Count - 1)) {
        $payloadFile = $global:scriptArgs[$workerIndex + 1]
        if (Test-Path $payloadFile) {
            Write-Log "Elevated Elite Worker injected successfully. Processing payload..." "worker"
            $payload = Import-Clixml -Path $payloadFile
            foreach ($file in $payload.Files) {
                $null = Sign-File -filePath $file -pfxPath $payload.PfxPath -pfxPass $payload.PfxPass -signToolPath $payload.SignToolPath -useSignTool $payload.UseSignTool
            }
            Remove-Item $payloadFile -Force
            Write-Log "Elite Worker execution complete. Dissolving..." "worker"
        }
        exit
    }

    # Determine Run Mode
    $isCompiled = $scriptPath -match "\.exe$"
    $autoRunMode = ($isCompiled -and $global:scriptArgs -and $global:scriptArgs.Count -gt 0)

    # Load Form Icon globally
    $icoPath = if ($scriptDir -and $baseName) { [System.IO.Path]::Combine($scriptDir, "$baseName.ico") } else { "" }
    $global:formIcon = $null
    if ($icoPath -and (Test-Path $icoPath)) { try { $global:formIcon = New-Object System.Drawing.Icon($icoPath) } catch {} }
    if ($null -eq $global:formIcon -and $isCompiled -and (Test-Path $scriptPath)) { try { $global:formIcon = [System.Drawing.Icon]::ExtractAssociatedIcon($scriptPath) } catch {} }

    if ($autoRunMode) {
        # --- HEADLESS / AUTO-SIGN PROGRESS UI ---
        $progForm = New-Object EliteForm
        $progForm.Text = "Elite EasySigner - Processing"
        $progForm.Size = New-Object System.Drawing.Size(400, 180)
        $progForm.FormBorderStyle = [System.Windows.Forms.FormBorderStyle]::FixedSingle
        $progForm.MaximizeBox = $false
        $progForm.MinimizeBox = $false
        $progForm.StartPosition = [System.Windows.Forms.FormStartPosition]::CenterScreen
        $progForm.TopMost = $true
        $progForm.Font = New-EliteFont -family "Montserrat" -size 9
        if ($global:formIcon) { $progForm.Icon = $global:formIcon }

        $lblTitle = New-Object System.Windows.Forms.Label
        $lblTitle.Text = "Automated Signing in Progress..."
        $lblTitle.Font = New-EliteFont -family "Montserrat" -size 10 -style ([System.Drawing.FontStyle]::Bold)
        $lblTitle.Location = New-Object System.Drawing.Point(15, 15)
        $lblTitle.Size = New-Object System.Drawing.Size(350, 25)

        $pbStatus = New-Object System.Windows.Forms.ProgressBar
        $pbStatus.Location = New-Object System.Drawing.Point(15, 45)
        $pbStatus.Size = New-Object System.Drawing.Size(350, 20)
        $pbStatus.Style = [System.Windows.Forms.ProgressBarStyle]::Marquee

        $global:lblProgressStatus = New-Object System.Windows.Forms.Label
        $global:lblProgressStatus.Text = "Initializing the digital pens..."
        $global:lblProgressStatus.Location = New-Object System.Drawing.Point(15, 75)
        $global:lblProgressStatus.Size = New-Object System.Drawing.Size(350, 20)

        $lnkProgLog = New-Object System.Windows.Forms.LinkLabel
        $lnkProgLog.Text = "Open Operations Log"
        $lnkProgLog.Location = New-Object System.Drawing.Point(15, 105)
        $lnkProgLog.AutoSize = $true
        $lnkProgLog.Add_LinkClicked({
            if (Test-Path $logFilePath) { [System.Diagnostics.Process]::Start($logFilePath) | Out-Null }
        })

        $btnExitProg = New-Object System.Windows.Forms.Button
        $btnExitProg.Text = "Exit"
        $btnExitProg.Location = New-Object System.Drawing.Point(290, 100)
        $btnExitProg.Size = New-Object System.Drawing.Size(75, 25)
        $btnExitProg.Visible = $false
        $btnExitProg.Add_Click({ $progForm.Close() })

        $progForm.Controls.AddRange(@($lblTitle, $pbStatus, $global:lblProgressStatus, $lnkProgLog, $btnExitProg))

        $progForm.Add_Shown({
            if (-not $isAdmin) {
                $global:lblProgressStatus.Text = "Requesting UIPI override..."
                [System.Windows.Forms.Application]::DoEvents()
                
                $exeArgs = @()
                foreach ($a in $global:scriptArgs) { $exeArgs += "`"$a`"" }
                
                Start-Process -FilePath $scriptPath -ArgumentList $exeArgs -Verb RunAs -Wait -ErrorAction SilentlyContinue
                $progForm.Close()
                return
            }

            $errorCount = 0
            $signToolP = Find-SignTool
            foreach ($file in $global:scriptArgs) {
                $targetPath = Resolve-Shortcut -Path $file
                if ($targetPath -and (Test-Path $targetPath -PathType Leaf)) {
                    $res = Sign-File -filePath $targetPath -pfxPath $defaultPfx -pfxPass $defaultPassword -signToolPath $signToolP -useSignTool $useSignToolConfig
                    if (-not $res) { $errorCount++ }
                }
            }

            $pbStatus.Style = [System.Windows.Forms.ProgressBarStyle]::Continuous
            $pbStatus.Value = 100

            if ($errorCount -gt 0) {
                $lblTitle.Text = "Operation Completed with Errors"
                $lblTitle.ForeColor = [System.Drawing.Color]::DarkRed
                $global:lblProgressStatus.Text = "$errorCount files stubbornly refused their signatures."
                $btnExitProg.Visible = $true
            } else {
                $lblTitle.Text = "Success!"
                $lblTitle.ForeColor = [System.Drawing.Color]::DarkGreen
                $global:lblProgressStatus.Text = "All files elegantly signed. Closing in 2 seconds..."
                [System.Windows.Forms.Application]::DoEvents()
                Start-Sleep -Seconds 2
                $progForm.Close()
            }
        })

        Write-Log "Headless mode invoked via CLI arguments." "info"
        $null = $progForm.ShowDialog()
        $progForm.Dispose()
        exit
    }

    # --- MAIN GUI ---
    # Using Custom EliteForm to bypass UIPI Drag/Drop limitations
    $form = New-Object EliteForm
    $form.Text = "Elite EasySigner - v1.0.52.0"
    $form.Size = New-Object System.Drawing.Size(620, 770)
    $form.FormBorderStyle = [System.Windows.Forms.FormBorderStyle]::FixedDialog
    $form.MaximizeBox = $false
    $form.MinimizeBox = $true
    $form.StartPosition = [System.Windows.Forms.FormStartPosition]::CenterScreen
    $form.Font = New-EliteFont -family "Montserrat" -size 9
    if ($global:formIcon) { $form.Icon = $global:formIcon }

    if ($glassEnabled) {
        $form.BackColor = [System.Drawing.Color]::Black
    } else {
        $form.BackColor = [System.Drawing.SystemColors]::Control
    }

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
    $lblHeaderSub.Text = "v1.0.52.0 - EliteSoftware Certificate Signing Utility"
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
    if ($global:formIcon) { $picHeaderIcon.Image = $global:formIcon.ToBitmap() }

    $pnlHeader.Controls.AddRange(@($lblHeaderTitle, $lblHeaderSub, $chkGlass, $picHeaderIcon))

    # --- Client Area ---
    $pnlClient = New-Object System.Windows.Forms.Panel
    $pnlClient.Dock = [System.Windows.Forms.DockStyle]::Fill
    $pnlClient.BackColor = if ($glassEnabled) { [System.Drawing.Color]::Transparent } else { [System.Drawing.SystemColors]::Control }

    # 1. Configuration
    $grpSettings = New-Object EliteGroupBox
    $grpSettings.Text = "Signing Configuration"
    $grpSettings.Font = New-EliteFont -family "Montserrat" -size 9 -style ([System.Drawing.FontStyle]::Bold)
    $grpSettings.Location = New-Object System.Drawing.Point(12, 10)
    $grpSettings.Size = New-Object System.Drawing.Size(580, 185)
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

    $chkUseSignTool = New-Object System.Windows.Forms.CheckBox
    $chkUseSignTool.Text = "Use Legacy SignTool.exe (Default: Native PowerShell)"
    $chkUseSignTool.Location = New-Object System.Drawing.Point(130, 82)
    $chkUseSignTool.Size = New-Object System.Drawing.Size(400, 20)
    $chkUseSignTool.Checked = $useSignToolConfig

    $txtSignTool = New-Object System.Windows.Forms.TextBox
    $txtSignTool.Text = Find-SignTool
    $txtSignTool.Location = New-Object System.Drawing.Point(130, 112)
    $txtSignTool.Size = New-Object System.Drawing.Size(360, 23)
    $txtSignTool.Enabled = $useSignToolConfig

    $lblSignTool = New-Object System.Windows.Forms.Label
    $lblSignTool.Text = "SignTool Path:"
    $lblSignTool.Location = New-Object System.Drawing.Point(15, 115)
    $lblSignTool.Size = New-Object System.Drawing.Size(110, 20)

    $btnBrowseSignTool = New-Object System.Windows.Forms.Button
    $btnBrowseSignTool.Text = "..."
    $btnBrowseSignTool.Location = New-Object System.Drawing.Point(500, 111)
    $btnBrowseSignTool.Size = New-Object System.Drawing.Size(65, 24)
    $btnBrowseSignTool.ForeColor = [System.Drawing.Color]::Black
    $btnBrowseSignTool.Enabled = $useSignToolConfig

    $lblStatusSetting = New-Object System.Windows.Forms.Label
    $pfxExists = ($defaultPfx -and (Test-Path $defaultPfx))
    $lblStatusSetting.Text = if ($pfxExists) { "✓ Master PFX locked and loaded." } else { "⚠ Master PFX missing in action." }
    $lblStatusSetting.ForeColor = if ($pfxExists) { [System.Drawing.Color]::LimeGreen } else { [System.Drawing.Color]::Orange }
    $lblStatusSetting.Location = New-Object System.Drawing.Point(130, 145)
    $lblStatusSetting.Size = New-Object System.Drawing.Size(400, 20)

    $grpSettings.Controls.AddRange(@($lblPfx, $txtPfx, $btnBrowsePfx, $lblPassword, $txtPassword, $chkShowPassword, $chkUseSignTool, $lblSignTool, $txtSignTool, $btnBrowseSignTool, $lblStatusSetting))

    # 2. File Queue Zone
    $grpDropZone = New-Object EliteGroupBox
    $grpDropZone.Text = "File Queue (Drag & Drop Here)"
    $grpDropZone.Font = New-EliteFont -family "Montserrat" -size 9 -style ([System.Drawing.FontStyle]::Bold)
    $grpDropZone.Location = New-Object System.Drawing.Point(12, 205)
    $grpDropZone.Size = New-Object System.Drawing.Size(580, 200)
    $grpDropZone.ForeColor = if ($glassEnabled) { [System.Drawing.Color]::White } else { [System.Drawing.Color]::Black }

    $lbFiles = New-Object EliteListBox
    $lbFiles.Location = New-Object System.Drawing.Point(15, 25)
    $lbFiles.Size = New-Object System.Drawing.Size(550, 120)
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
    $grpLogs = New-Object EliteGroupBox
    $grpLogs.Text = "Operations Log"
    $grpLogs.Font = New-EliteFont -family "Montserrat" -size 9 -style ([System.Drawing.FontStyle]::Bold)
    $grpLogs.Location = New-Object System.Drawing.Point(12, 415)
    $grpLogs.Size = New-Object System.Drawing.Size(580, 180)
    $grpLogs.ForeColor = if ($glassEnabled) { [System.Drawing.Color]::White } else { [System.Drawing.Color]::Black }

    $global:rtbLog = New-Object System.Windows.Forms.RichTextBox
    $global:rtbLog.Location = New-Object System.Drawing.Point(15, 25)
    $global:rtbLog.Size = New-Object System.Drawing.Size(550, 115)
    $global:rtbLog.ReadOnly = $true
    $global:rtbLog.Font = New-Object System.Drawing.Font("Consolas", 8.5)
    $global:rtbLog.BackColor = [System.Drawing.Color]::White

    $btnClearLog = New-Object System.Windows.Forms.Button
    $btnClearLog.Text = "Clear Log"
    $btnClearLog.Location = New-Object System.Drawing.Point(480, 146)
    $btnClearLog.Size = New-Object System.Drawing.Size(85, 24)
    $btnClearLog.ForeColor = [System.Drawing.Color]::Black

    $global:lblStatusText = New-Object System.Windows.Forms.Label
    $global:lblStatusText.Text = "Ready for input."
    $global:lblStatusText.Location = New-Object System.Drawing.Point(15, 149)
    $global:lblStatusText.Size = New-Object System.Drawing.Size(350, 20)

    $lnkMainLog = New-Object System.Windows.Forms.LinkLabel
    $lnkMainLog.Text = "Open Error Log"
    $lnkMainLog.Location = New-Object System.Drawing.Point(375, 150)
    $lnkMainLog.AutoSize = $true
    $lnkMainLog.Add_LinkClicked({
        if (Test-Path $logFilePath) { [System.Diagnostics.Process]::Start($logFilePath) | Out-Null }
    })

    $grpLogs.Controls.AddRange(@($global:rtbLog, $btnClearLog, $global:lblStatusText, $lnkMainLog))

    $btnExit = New-Object System.Windows.Forms.Button
    $btnExit.Text = "Exit"
    $btnExit.Location = New-Object System.Drawing.Point(507, 610)
    $btnExit.Size = New-Object System.Drawing.Size(85, 30)
    $btnExit.ForeColor = [System.Drawing.Color]::Black

    $pnlClient.Controls.AddRange(@($grpSettings, $grpDropZone, $grpLogs, $btnExit))
    $form.Controls.AddRange(@($pnlClient, $pnlHeader))

    # --- Functions (UI Tied) ---
    function Process-DroppedFiles {
        param([string[]]$files)
        $added = 0
        foreach ($file in $files) {
            $targetPath = Resolve-Shortcut -Path $file
            if ($targetPath -and (Test-Path $targetPath -PathType Leaf)) {
                $ext = [System.IO.Path]::GetExtension($targetPath).ToLower()
                if ($supportedExts -contains $ext) {
                    if (-not $lbFiles.Items.Contains($targetPath)) {
                        $null = $lbFiles.Items.Add($targetPath)
                        $added++
                    }
                } else {
                    Write-Log "File ignored: $targetPath (Unsupported extension)" "warning"
                }
            }
        }
        if ($added -gt 0) { Write-Log "Added $added file(s) to the queue." "info" }
    }

    # --- Events ---
    $form.Add_Load({
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
        
        $ans = [System.Windows.Forms.MessageBox]::Show("Frame extension requires an application restart to avoid visual glitching. Restart now?", "Elite EasySigner", [System.Windows.Forms.MessageBoxButtons]::YesNo, [System.Windows.Forms.MessageBoxIcon]::Question)
        if ($ans -eq [System.Windows.Forms.DialogResult]::Yes) {
            Start-Process -FilePath "powershell.exe" -ArgumentList "-ExecutionPolicy Bypass -File `"$scriptPath`""
            $form.Close()
        }
    })

    $chkUseSignTool.Add_CheckedChanged({
        $val = if ($chkUseSignTool.Checked) { 1 } else { 0 }
        Set-ItemProperty -Path $regPath -Name "UseSignTool" -Value $val -Force
        $txtSignTool.Enabled = $chkUseSignTool.Checked
        $btnBrowseSignTool.Enabled = $chkUseSignTool.Checked
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
        $d.Filter = "Elite Supported Files|*.exe;*.dll;*.cpl;*.mui;*.mun;*.ocx|All files (*.*)|*.*"
        $d.Multiselect = $true
        if ($d.ShowDialog() -eq [System.Windows.Forms.DialogResult]::OK) { Process-DroppedFiles -files $d.FileNames }
    })

    $btnClearFiles.Add_Click({ $lbFiles.Items.Clear(); Write-Log "Queue completely cleared." "info" })

    $btnSignFiles.Add_Click({
        if ($lbFiles.Items.Count -eq 0) { Write-Log "Queue is empty. Feed me bits to sign." "warning"; return }
        $btnSignFiles.Enabled = $false
        
        if (-not $isAdmin) {
            Write-Log "Standard privileges detected. Summoning elevated digital proxy to bypass UIPI constraints..." "warning"
            
            $payload = @{
                Files = @($lbFiles.Items | ForEach-Object { $_ })
                PfxPath = $txtPfx.Text.Trim()
                PfxPass = $txtPassword.Text
                SignToolPath = $txtSignTool.Text.Trim()
                UseSignTool = $chkUseSignTool.Checked
            }
            $payloadFile = Join-Path $env:TEMP "EliteSignQueue_$([guid]::NewGuid()).xml"
            $payload | Export-Clixml -Path $payloadFile
            
            $logSizeBefore = if (Test-Path $logFilePath) { (Get-Item $logFilePath).Length } else { 0 }
            
            $exeArgs = @("-EliteWorker", "`"$payloadFile`"")
            if ($scriptPath -match "\.exe$") {
                $process = Start-Process -FilePath $scriptPath -ArgumentList $exeArgs -Verb RunAs -PassThru -Wait -ErrorAction SilentlyContinue
            } else {
                $psArgs = @("-ExecutionPolicy", "Bypass", "-File", "`"$scriptPath`"") + $exeArgs
                $process = Start-Process -FilePath "powershell.exe" -ArgumentList $psArgs -Verb RunAs -PassThru -Wait -ErrorAction SilentlyContinue
            }
            
            if (Test-Path $logFilePath) {
                try {
                    $logFileStream = [System.IO.File]::Open($logFilePath, [System.IO.FileMode]::Open, [System.IO.FileAccess]::Read, [System.IO.FileShare]::ReadWrite)
                    $logFileReader = New-Object System.IO.StreamReader($logFileStream)
                    $logFileReader.BaseStream.Seek($logSizeBefore, [System.IO.SeekOrigin]::Begin) | Out-Null
                    $newLogs = $logFileReader.ReadToEnd()
                    $logFileReader.Close()
                    
                    if ($newLogs) {
                        $global:rtbLog.SelectionStart = $global:rtbLog.TextLength
                        $global:rtbLog.SelectionColor = [System.Drawing.Color]::Purple
                        $global:rtbLog.AppendText($newLogs)
                        $global:rtbLog.ScrollToCaret()
                    }
                } catch { Write-Log "Worker finished, but couldn't parse the log tail." "warning" }
            }
            
        } else {
            Write-Log "Processing $($lbFiles.Items.Count) file(s) with local Admin power..." "info"
            foreach ($item in $lbFiles.Items) {
                $null = Sign-File -filePath $item -pfxPath $txtPfx.Text.Trim() -pfxPass $txtPassword.Text -signToolPath $txtSignTool.Text.Trim() -useSignTool $chkUseSignTool.Checked
            }
        }

        $lbFiles.Items.Clear()
        Write-Log "Batch run complete. Queue emptied." "info"
        $btnSignFiles.Enabled = $true
    })

    $chkShowPassword.Add_Click({ $txtPassword.UseSystemPasswordChar = -not $chkShowPassword.Checked })
    $btnClearLog.Add_Click({ $global:rtbLog.Clear() })
    $btnExit.Add_Click({ $form.Close() })

    # Elite C# Drop Handlers 
    $dropHandler = {
        param($files)
        if ($files) { Process-DroppedFiles -files $files }
    }

    $form.add_FilesDropped($dropHandler)
    $grpDropZone.add_FilesDropped($dropHandler)
    $lbFiles.add_FilesDropped($dropHandler)
    $grpSettings.add_FilesDropped($dropHandler)
    $grpLogs.add_FilesDropped($dropHandler)

    Write-Log "Elite EasySigner UI Initialized. Awaiting payloads." "info"
    $null = $form.ShowDialog()
    $form.Dispose()

} catch {
    $err = "FATAL ERROR in the matrix:`n`n$($_.Exception.Message)`n`nStack Trace:`n$($_.ScriptStackTrace)"
    try { Add-Content -Path $logFilePath -Value "[$([DateTime]::Now.ToString('yyyy-MM-dd HH:mm:ss'))] [FATAL] $err" -ErrorAction SilentlyContinue } catch {}
    [System.Windows.Forms.MessageBox]::Show($err, "Elite EasySigner - Unrecoverable Crash", [System.Windows.Forms.MessageBoxButtons]::OK, [System.Windows.Forms.MessageBoxIcon]::Error) | Out-Null
}