# Elite EasyScriptCompiler - v1.0.42.26
# EliteSoftware Professional Script Compiler & Signer
# Copyright 2026 EliteSoftware Tech Co.

param(
    [Parameter(Position=0, Mandatory=$false)]
    [string]$DroppedFile = $null,
    
    [Parameter(Mandatory=$false)]
    [switch]$noConsole
)

# Catch un-named arguments passed by Windows Explorer Drag-and-Drop
if (-not $DroppedFile -and $args.Count -gt 0) {
    if ($args[0] -ne "-noConsole") {
        $DroppedFile = $args[0]
    }
}

# --- Bulletproof Global Crash Handler ---
$tempLog = "$env:TEMP\EliteCompiler_EmergencyDeathLog.txt"
try {

    # --- Core Path Resolution & Identity ---
    $processPath = [System.Diagnostics.Process]::GetCurrentProcess().MainModule.FileName
    $isCompiled = $processPath.EndsWith('.exe', [System.StringComparison]::OrdinalIgnoreCase)
    
    $scriptPath = if ($isCompiled) { $processPath } else { $PSCommandPath }
    if (-not $scriptPath) { $scriptPath = $processPath }
    
    $scriptDir = Split-Path $scriptPath
    $logDir = "C:\EliteSoftware\Logs"
    $logFile = Join-Path $logDir "EliteCompiler_ErrorLog.txt"

    if (-not (Test-Path $logDir)) {
        New-Item -Path $logDir -ItemType Directory -Force | Out-Null
    }

    # Load Assemblies Explicitly
    Add-Type -AssemblyName System.Windows.Forms
    Add-Type -AssemblyName System.Drawing
    [System.Windows.Forms.Application]::EnableVisualStyles()

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

    function Write-EliteLog {
        param([string]$Message, [string]$Type="INFO", [string]$ErrorCode="E000")
        $ts = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
        $logEntry = "[$ts] [$Type] [Code: $ErrorCode] $Message"
        try { $logEntry | Out-File -FilePath $logFile -Append -Encoding UTF8 } catch {}

        if ($global:lblProgressStatus) {
            $global:lblProgressStatus.Text = $Message
            [System.Windows.Forms.Application]::DoEvents()
        }
    }

    Write-EliteLog "Elite EasyScriptCompiler initialized. Running in standard user mode." "INFO" "E000"

    $ps2exeScript = Join-Path $scriptDir "PS2EXE\ps2exe.ps1"
    if (-not (Test-Path $ps2exeScript)) { 
        $ps2exeScript = Join-Path $PSScriptRoot "PS2EXE\ps2exe.ps1" 
    }

    # --- Dynamic Global Icon Resolution Cascade ---
    $global:formIcon = $null
    $baseName = "Elite-EasyScriptCompiler"
    
    $iconCascade = @(
        (Join-Path $scriptDir "$baseName.exe"),
        (Join-Path $scriptDir "$baseName.ico"),
        (Join-Path $scriptDir "EliteSoftware Logo 2026.ico"),
        "C:\Users\zwhiteman\Desktop\Elite-EasySigner\$baseName.exe",
        "C:\Users\zwhiteman\Desktop\Elite-EasySigner\$baseName.ico",
        "C:\Users\zwhiteman\Desktop\Elite-EasySigner\EliteSoftware Logo 2026.ico"
    )

    foreach ($iconPath in $iconCascade) {
        if (Test-Path $iconPath) {
            try {
                if ($iconPath.EndsWith(".exe", [System.StringComparison]::OrdinalIgnoreCase)) {
                    $global:formIcon = [System.Drawing.Icon]::ExtractAssociatedIcon($iconPath)
                } else {
                    $global:formIcon = New-Object System.Drawing.Icon($iconPath)
                }
                if ($global:formIcon) { 
                    Write-EliteLog "Successfully loaded application interface icon from: $iconPath" "INFO" "E010"
                    break 
                }
            } catch {}
        }
    }

    # --- Utility Functions ---
    function Get-VersionFromFileName {
        param([string]$FileName)
        $match = [regex]::Match($FileName, '\d+(\.\d+){1,3}')
        if ($match.Success) {
            $ver = $match.Value
            while (($ver.Split('.')).Count -lt 4) { $ver += ".0" }
            return $ver
        }
        return "1.0.0.0"
    }

    # --- Elite Native Signing Engine ---
    function Sign-File {
        param([string]$filePath)
        
        $pfxPath = [System.IO.Path]::Combine($scriptDir, "EliteSoftware_Special.pfx")
        if (-not (Test-Path $pfxPath)) {
            $pfxPath = "C:\Users\zwhiteman\Desktop\Elite-EasySigner\EliteSoftware_Special.pfx"
        }
        $pfxPass = "Minecraft145!!"
        
        if (-not (Test-Path $pfxPath)) { Write-EliteLog "Master PFX missing. Refusing to forge documents." "ERROR" "E403"; return $false }
        
        $fileDir = [System.IO.Path]::GetDirectoryName($filePath)
        $fileName = [System.IO.Path]::GetFileName($filePath)
        
        $fileInfo = Get-Item -LiteralPath $filePath -Force
        $wasReadOnly = $fileInfo.IsReadOnly
        if ($wasReadOnly) {
            try {
                $fileInfo.IsReadOnly = $false
                Write-EliteLog "Stripped Read-Only flag from $fileName." "INFO" "E110"
            } catch {}
        }

        $tempBak = [System.IO.Path]::GetTempFileName()
        try {
            Copy-Item -Path $filePath -Destination $tempBak -Force
        } catch {
            Write-EliteLog "Failed to secure backup for $fileName. Aborting." "ERROR" "E502"
            if ($wasReadOnly -and (Test-Path -LiteralPath $filePath)) { try { (Get-Item -LiteralPath $filePath -Force).IsReadOnly = $true } catch {} }
            return $false
        }
        
        $signSuccess = $false
        Write-EliteLog "Engaging native .NET Authenticode signing sequence." "INFO" "E108"
        
        # Retry loop to bypass PS2EXE compiler file locks
        $retry = 0
        while ($retry -lt 3 -and -not $signSuccess) {
            try {
                $cert = New-Object System.Security.Cryptography.X509Certificates.X509Certificate2($pfxPath, $pfxPass, [System.Security.Cryptography.X509Certificates.X509KeyStorageFlags]::DefaultKeySet)
                $signParams = @{
                    FilePath = $filePath
                    Certificate = $cert
                    HashAlgorithm = "SHA256"
                    TimestampServer = "http://timestamp.digicert.com"
                }
                $result = Set-AuthenticodeSignature @signParams -ErrorAction Stop
                
                if ($result.Status -eq 'Valid') { 
                    $signSuccess = $true 
                } else { 
                    Write-EliteLog "Native auth attempt $($retry + 1) failed for $($fileName): $($result.StatusMessage)" "WARN" "E503" 
                    Start-Sleep -Milliseconds 750
                }
            } catch {
                Write-EliteLog "File lock or cryptography collision: $($_.Exception.Message)" "WARN" "E504"
                Start-Sleep -Milliseconds 750
            }
            $retry++
        }

        if ($signSuccess) {
            $origDir = Join-Path $fileDir "Original_Unsigned-Components"
            if (-not (Test-Path $origDir)) { $null = New-Item -ItemType Directory -Path $origDir -Force }
            $bakPath = Join-Path $origDir "$fileName.bak"
            if (Test-Path $bakPath) { Remove-Item $bakPath -Force }
            Move-Item -Path $tempBak -Destination $bakPath -Force
            
            if ($wasReadOnly -and (Test-Path -LiteralPath $filePath)) { try { (Get-Item -LiteralPath $filePath -Force).IsReadOnly = $true } catch {} }
            
            Write-EliteLog "Successfully forged signature on $fileName." "SUCCESS" "E200"
            return $true
        } else {
            Copy-Item -Path $tempBak -Destination $filePath -Force
            Remove-Item -Path $tempBak -Force
            if ($wasReadOnly -and (Test-Path -LiteralPath $filePath)) { try { (Get-Item -LiteralPath $filePath -Force).IsReadOnly = $true } catch {} }
            Write-EliteLog "Restored $fileName to unsigned state. All signature attempts rejected." "WARN" "E400"
            return $false
        }
    }

    function Run-Compilation {
        param(
            [string]$src, 
            [string]$arch,
            [string]$customTitle = "",
            [string]$customVersion = "",
            [string]$customCompany = "",
            [string]$customCopyright = "",
            [string]$customProduct = "",
            [string]$customIcon = ""
        )
        
        $srcDir = Split-Path $src
        $compBase = [System.IO.Path]::GetFileNameWithoutExtension($src)
        $outName = $compBase + "_$arch.exe"
        $outPath = [System.IO.Path]::Combine($srcDir, $outName)
        
        $extractedVersion = if ($customVersion) { $customVersion } else { Get-VersionFromFileName -FileName $compBase }
        $currentYear = (Get-Date).Year

        $finalCompany = if ($customCompany) { $customCompany } else { "EliteSoftware Tech Co." }
        $finalCopyright = if ($customCopyright) { $customCopyright } else { "Copyright $currentYear EliteSoftware Tech Co." }
        $finalProduct = if ($customProduct) { $customProduct } else { "Elite Software Suite" }
        $finalTitle = if ($customTitle) { $customTitle } else { "$compBase ($arch)" }

        Write-EliteLog "Forging binary: $outName (Version: $extractedVersion)" "INFO" "E101"

        $params = @{
            inputFile    = $src
            outputFile   = $outPath
            noConsole    = $true
            noOutput     = $true
            noError      = $true
            requireAdmin = $true
            STA          = $true
            company      = $finalCompany
            copyright    = $finalCopyright
            version      = $extractedVersion
            product      = $finalProduct
            title        = $finalTitle
        }

        $targetIcon = $null

        # Priority 0: Explicit User UI Override
        if ($customIcon -and (Test-Path $customIcon)) {
            $targetIcon = $customIcon
            Write-EliteLog "User specified manual override icon: $targetIcon" "INFO" "E115"
        }

        $sameNameIco = Join-Path $srcDir "$compBase.ico"
        $globalIco = Join-Path $scriptDir "EliteSoftware Logo 2026.ico"
        if (-not (Test-Path $globalIco)) {
            $globalIco = "C:\Users\zwhiteman\Desktop\Elite-EasySigner\EliteSoftware Logo 2026.ico"
        }

        # Priority 1: Script Content Regex Parsing (Primary automated target)
        if (-not $targetIcon) {
            try {
                $scriptContent = Get-Content -Path $src -Raw -ErrorAction SilentlyContinue
                if ($scriptContent -match '([a-zA-Z0-9_\-\s]+\.ico)') {
                    $matchedName = [System.IO.Path]::GetFileName($matches[1])
                    $potentialPath = Join-Path $srcDir $matchedName
                    if (Test-Path $potentialPath) { 
                        $targetIcon = $potentialPath 
                        Write-EliteLog "Icon parsed directly from script code: $targetIcon" "INFO" "E105"
                    }
                }
            } catch {}
        }

        # Priority 2: Same Base Name in Target Directory
        if (-not $targetIcon -and (Test-Path $sameNameIco)) {
            $targetIcon = $sameNameIco
            Write-EliteLog "Found matching filename icon in script directory: $targetIcon" "INFO" "E106"
        }

        # Priority 3: Global EliteSoftware Logo Final Fallback
        if (-not $targetIcon -and (Test-Path $globalIco)) {
            $targetIcon = $globalIco
            Write-EliteLog "Using Global EliteSoftware icon: $targetIcon" "INFO" "E107"
        }

        if ($targetIcon) {
            $params["iconFile"] = $targetIcon
        }

        if ($arch -eq "x86") { $params["x86"] = $true } else { $params["x64"] = $true }

        try {
            if (-not (Test-Path $ps2exeScript)) { throw "PS2EXE backend script missing. A digital void was encountered." }
            . $ps2exeScript
            Invoke-ps2exe @params
            
            if (Test-Path $outPath) {
                Write-EliteLog "Successfully minted $arch architecture executable." "SUCCESS" "E200"
                Start-Sleep -Milliseconds 500
                Sign-File -filePath $outPath
                return $true
            } else {
                throw "PS2EXE finished but output file is missing in action."
            }
        } catch {
            Write-EliteLog "Compilation engine seized up for $($arch): $($_.Exception.Message)" "ERROR" "E505"
            return $false
        }
    }

    # --- Headless Mode (Drag & Drop / Shortcut Execution) ---
    if ($DroppedFile -and (Test-Path $DroppedFile)) {
        
        if ($noConsole) {
            Run-Compilation -src $DroppedFile -arch "x86" | Out-Null
            Run-Compilation -src $DroppedFile -arch "x64" | Out-Null
            Exit
        }

        $progForm = New-Object System.Windows.Forms.Form
        $progForm.Text = "Elite EasyScriptCompiler - Processing"
        $progForm.Size = New-Object System.Drawing.Size(400, 180)
        $progForm.FormBorderStyle = [System.Windows.Forms.FormBorderStyle]::FixedSingle
        $progForm.MaximizeBox = $false
        $progForm.MinimizeBox = $false
        $progForm.StartPosition = [System.Windows.Forms.FormStartPosition]::CenterScreen
        $progForm.TopMost = $true
        $progForm.Font = New-EliteFont -family "Montserrat" -size 9
        if ($global:formIcon) { $progForm.Icon = $global:formIcon }

        $lblTitle = New-Object System.Windows.Forms.Label
        $lblTitle.Text = "Automated Compilation in Progress..."
        $lblTitle.Font = New-EliteFont -family "Montserrat" -size 10 -style ([System.Drawing.FontStyle]::Bold)
        $lblTitle.Location = New-Object System.Drawing.Point(15, 15)
        $lblTitle.Size = New-Object System.Drawing.Size(350, 25)

        $pbStatus = New-Object System.Windows.Forms.ProgressBar
        $pbStatus.Location = New-Object System.Drawing.Point(15, 45)
        $pbStatus.Size = New-Object System.Drawing.Size(350, 20)
        $pbStatus.Style = [System.Windows.Forms.ProgressBarStyle]::Marquee

        $global:lblProgressStatus = New-Object System.Windows.Forms.Label
        $global:lblProgressStatus.Text = "Initializing the digital forge..."
        $global:lblProgressStatus.Location = New-Object System.Drawing.Point(15, 75)
        $global:lblProgressStatus.Size = New-Object System.Drawing.Size(350, 20)

        $lnkProgLog = New-Object System.Windows.Forms.LinkLabel
        $lnkProgLog.Text = "Open Operations Log"
        $lnkProgLog.Location = New-Object System.Drawing.Point(15, 105)
        $lnkProgLog.AutoSize = $true
        $lnkProgLog.Add_LinkClicked({
            if (Test-Path $logFile) { [System.Diagnostics.Process]::Start("notepad.exe", $logFile) | Out-Null }
        })

        $btnExitProg = New-Object System.Windows.Forms.Button
        $btnExitProg.Text = "Exit"
        $btnExitProg.Location = New-Object System.Drawing.Point(290, 100)
        $btnExitProg.Size = New-Object System.Drawing.Size(75, 25)
        $btnExitProg.Visible = $false
        $btnExitProg.Add_Click({ $progForm.Close() })

        $progForm.Controls.AddRange(@($lblTitle, $pbStatus, $global:lblProgressStatus, $lnkProgLog, $btnExitProg))

        $progForm.Add_Shown({
            Write-EliteLog "Headless drop detected. Processing payload: $DroppedFile" "INFO" "E100"
            
            $errorCount = 0
            $r1 = Run-Compilation -src $DroppedFile -arch "x86"
            if (-not $r1) { $errorCount++ }

            $r2 = Run-Compilation -src $DroppedFile -arch "x64"
            if (-not $r2) { $errorCount++ }

            $pbStatus.Style = [System.Windows.Forms.ProgressBarStyle]::Continuous
            $pbStatus.Value = 100

            if ($errorCount -gt 0) {
                $lblTitle.Text = "Operation Completed with Errors"
                $lblTitle.ForeColor = [System.Drawing.Color]::DarkRed
                $global:lblProgressStatus.Text = "The forge encountered critical failures. Check the log."
                $btnExitProg.Visible = $true
            } else {
                $lblTitle.Text = "Success!"
                $lblTitle.ForeColor = [System.Drawing.Color]::DarkGreen
                $global:lblProgressStatus.Text = "Target compiled and signed. Closing in 2 seconds..."
                [System.Windows.Forms.Application]::DoEvents()
                Start-Sleep -Seconds 2
                $progForm.Close()
            }
        })

        $null = $progForm.ShowDialog()
        $progForm.Dispose()
        Exit
    }

    # --- Standard GUI Mode ---
    $form = New-Object System.Windows.Forms.Form
    $form.Text = "Elite EasyScriptCompiler - Professional Edition"
    $form.Size = New-Object System.Drawing.Size(600, 420)
    $form.FormBorderStyle = [System.Windows.Forms.FormBorderStyle]::FixedSingle
    $form.MaximizeBox = $false
    $form.StartPosition = [System.Windows.Forms.FormStartPosition]::CenterScreen
    $form.AllowDrop = $true
    $form.Font = New-EliteFont -family "Montserrat" -size 9

    if ($global:formIcon) {
        $form.Icon = $global:formIcon
    }

    $lblInstructions = New-Object System.Windows.Forms.Label
    $lblInstructions.Text = "Drag & Drop a .ps1 file here, paste the path, or browse."
    $lblInstructions.Location = New-Object System.Drawing.Point(15, 15)
    $lblInstructions.Size = New-Object System.Drawing.Size(400, 20)

    $txtSource = New-Object System.Windows.Forms.TextBox
    $txtSource.Location = New-Object System.Drawing.Point(15, 35)
    $txtSource.Size = New-Object System.Drawing.Size(460, 23)
    $txtSource.AllowDrop = $true

    $btnBrowse = New-Object System.Windows.Forms.Button
    $btnBrowse.Text = "Browse..."
    $btnBrowse.Location = New-Object System.Drawing.Point(485, 33)
    $btnBrowse.Size = New-Object System.Drawing.Size(85, 27)

    # Custom Icon Field
    $lblIcon = New-Object System.Windows.Forms.Label
    $lblIcon.Text = "Custom Icon Path (.ico) [Optional]:"
    $lblIcon.Location = New-Object System.Drawing.Point(15, 70)
    $lblIcon.AutoSize = $true

    $txtIcon = New-Object System.Windows.Forms.TextBox
    $txtIcon.Location = New-Object System.Drawing.Point(15, 90)
    $txtIcon.Size = New-Object System.Drawing.Size(460, 23)
    $txtIcon.AllowDrop = $true

    $btnBrowseIcon = New-Object System.Windows.Forms.Button
    $btnBrowseIcon.Text = "Browse..."
    $btnBrowseIcon.Location = New-Object System.Drawing.Point(485, 88)
    $btnBrowseIcon.Size = New-Object System.Drawing.Size(85, 27)

    # Title & Version Fields
    $lblTitleText = New-Object System.Windows.Forms.Label
    $lblTitleText.Text = "Custom Title [Optional]:"
    $lblTitleText.Location = New-Object System.Drawing.Point(15, 125)
    $lblTitleText.AutoSize = $true

    $txtTitle = New-Object System.Windows.Forms.TextBox
    $txtTitle.Location = New-Object System.Drawing.Point(15, 145)
    $txtTitle.Size = New-Object System.Drawing.Size(260, 23)

    $lblVersion = New-Object System.Windows.Forms.Label
    $lblVersion.Text = "Custom Version (e.g., 1.0.0.0) [Optional]:"
    $lblVersion.Location = New-Object System.Drawing.Point(290, 125)
    $lblVersion.AutoSize = $true

    $txtVersion = New-Object System.Windows.Forms.TextBox
    $txtVersion.Location = New-Object System.Drawing.Point(290, 145)
    $txtVersion.Size = New-Object System.Drawing.Size(260, 23)

    # Company & Copyright Fields
    $lblCompany = New-Object System.Windows.Forms.Label
    $lblCompany.Text = "Company Name [Optional]:"
    $lblCompany.Location = New-Object System.Drawing.Point(15, 175)
    $lblCompany.AutoSize = $true

    $txtCompany = New-Object System.Windows.Forms.TextBox
    $txtCompany.Location = New-Object System.Drawing.Point(15, 195)
    $txtCompany.Size = New-Object System.Drawing.Size(260, 23)

    $lblCopyright = New-Object System.Windows.Forms.Label
    $lblCopyright.Text = "Copyright Information [Optional]:"
    $lblCopyright.Location = New-Object System.Drawing.Point(290, 175)
    $lblCopyright.AutoSize = $true

    $txtCopyright = New-Object System.Windows.Forms.TextBox
    $txtCopyright.Location = New-Object System.Drawing.Point(290, 195)
    $txtCopyright.Size = New-Object System.Drawing.Size(260, 23)

    # Product Name Field
    $lblProduct = New-Object System.Windows.Forms.Label
    $lblProduct.Text = "Product Name [Optional]:"
    $lblProduct.Location = New-Object System.Drawing.Point(15, 225)
    $lblProduct.AutoSize = $true

    $txtProduct = New-Object System.Windows.Forms.TextBox
    $txtProduct.Location = New-Object System.Drawing.Point(15, 245)
    $txtProduct.Size = New-Object System.Drawing.Size(555, 23)

    # Status Label
    $lblStatus = New-Object System.Windows.Forms.Label
    $lblStatus.Text = "Status: Awaiting orders."
    $lblStatus.Location = New-Object System.Drawing.Point(15, 285)
    $lblStatus.Size = New-Object System.Drawing.Size(550, 20)
    $lblStatus.ForeColor = [System.Drawing.Color]::DimGray

    $btnApply = New-Object System.Windows.Forms.Button
    $btnApply.Text = "Apply"
    $btnApply.Location = New-Object System.Drawing.Point(15, 320)
    $btnApply.Size = New-Object System.Drawing.Size(270, 40)

    $btnExit = New-Object System.Windows.Forms.Button
    $btnExit.Text = "Exit"
    $btnExit.Location = New-Object System.Drawing.Point(300, 320)
    $btnExit.Size = New-Object System.Drawing.Size(270, 40)

    $form.Controls.AddRange(@(
        $lblInstructions, $txtSource, $btnBrowse, 
        $lblIcon, $txtIcon, $btnBrowseIcon, 
        $lblTitleText, $txtTitle, 
        $lblVersion, $txtVersion, 
        $lblCompany, $txtCompany, 
        $lblCopyright, $txtCopyright, 
        $lblProduct, $txtProduct, 
        $lblStatus, $btnApply, $btnExit
    ))

    function Show-EliteError {
        param([string]$Message)
        $msgForm = New-Object System.Windows.Forms.Form
        $msgForm.Size = New-Object System.Drawing.Size(420, 160)
        $msgForm.StartPosition = [System.Windows.Forms.FormStartPosition]::CenterParent
        $msgForm.Text = "Elite Error Handler"
        $msgForm.FormBorderStyle = [System.Windows.Forms.FormBorderStyle]::FixedDialog
        $msgForm.MaximizeBox = $false
        $msgForm.MinimizeBox = $false
        $msgForm.Font = New-EliteFont -family "Montserrat" -size 9
        
        $msgLbl = New-Object System.Windows.Forms.Label
        $msgLbl.Text = $Message
        $msgLbl.Location = New-Object System.Drawing.Point(20, 20)
        $msgLbl.Size = New-Object System.Drawing.Size(360, 40)
        
        $msgBtn = New-Object System.Windows.Forms.Button
        $msgBtn.Text = "Okay"
        $msgBtn.Location = New-Object System.Drawing.Point(160, 70)
        $msgBtn.Size = New-Object System.Drawing.Size(80, 30)
        $msgBtn.Add_Click({ $msgForm.Close() })
        
        $msgForm.Controls.Add($msgLbl)
        $msgForm.Controls.Add($msgBtn)
        $msgForm.ShowDialog() | Out-Null
        $msgForm.Dispose()
    }

    $btnBrowse.Add_Click({
        $d = New-Object System.Windows.Forms.OpenFileDialog
        $d.Filter = "PowerShell Scripts (*.ps1)|*.ps1|All files (*.*)|*.*"
        if ($d.ShowDialog() -eq [System.Windows.Forms.DialogResult]::OK) { 
            $txtSource.Text = $d.FileName
        }
    })

    $btnBrowseIcon.Add_Click({
        $d = New-Object System.Windows.Forms.OpenFileDialog
        $d.Filter = "Icon Files (*.ico)|*.ico|All files (*.*)|*.*"
        if ($d.ShowDialog() -eq [System.Windows.Forms.DialogResult]::OK) { 
            $txtIcon.Text = $d.FileName
        }
    })

    $btnApply.Add_Click({
        if (-not $txtSource.Text -or -not (Test-Path $txtSource.Text)) { 
            Show-EliteError "Error E404: The target file pulled a Houdini. Give me a real path."
            return 
        }
        
        $btnApply.Enabled = $false
        $lblStatus.Text = "Status: Firing up the forge... Do not touch anything."
        $lblStatus.ForeColor = [System.Drawing.Color]::Blue
        $form.Refresh()
        
        $global:lblProgressStatus = $lblStatus

        $r1 = Run-Compilation -src $txtSource.Text -arch "x86" -customTitle $txtTitle.Text -customVersion $txtVersion.Text -customCompany $txtCompany.Text -customCopyright $txtCopyright.Text -customProduct $txtProduct.Text -customIcon $txtIcon.Text
        $r2 = Run-Compilation -src $txtSource.Text -arch "x64" -customTitle $txtTitle.Text -customVersion $txtVersion.Text -customCompany $txtCompany.Text -customCopyright $txtCopyright.Text -customProduct $txtProduct.Text -customIcon $txtIcon.Text
        
        if ($r1 -and $r2) { 
            $lblStatus.Text = "Status: Triumphant Success. Check source directory."
            $lblStatus.ForeColor = [System.Drawing.Color]::Green
        } else { 
            $lblStatus.Text = "Status: Complete disaster. Check EliteCompiler_ErrorLog.txt for the post-mortem."
            $lblStatus.ForeColor = [System.Drawing.Color]::Red
        }
        
        $global:lblProgressStatus = $null
        $btnApply.Enabled = $true
    })

    $btnExit.Add_Click({ $form.Close() })

    # --- Source Field Drag & Drop Handlers ---
    $txtSource.Add_DragEnter({
        param($s, $e)
        if ($e.Data.GetDataPresent([System.Windows.Forms.DataFormats]::FileDrop)) { 
            $e.Effect = [System.Windows.Forms.DragDropEffects]::Copy 
        }
    })

    $txtSource.Add_DragDrop({
        param($s, $e)
        $files = $e.Data.GetData([System.Windows.Forms.DataFormats]::FileDrop)
        if ($files[0].ToLower().EndsWith(".ps1")) {
            $txtSource.Text = $files[0]
            $lblStatus.Text = "Status: Source target locked. Ready to apply."
            $lblStatus.ForeColor = [System.Drawing.Color]::Black
        } else {
            $lblStatus.Text = "Status: Error E415. I only eat .ps1 files for the source."
            $lblStatus.ForeColor = [System.Drawing.Color]::Red
        }
    })

    # --- Icon Field Drag & Drop Handlers ---
    $txtIcon.Add_DragEnter({
        param($s, $e)
        if ($e.Data.GetDataPresent([System.Windows.Forms.DataFormats]::FileDrop)) { 
            $e.Effect = [System.Windows.Forms.DragDropEffects]::Copy 
        }
    })

    $txtIcon.Add_DragDrop({
        param($s, $e)
        $files = $e.Data.GetData([System.Windows.Forms.DataFormats]::FileDrop)
        if ($files[0].ToLower().EndsWith(".ico")) {
            $txtIcon.Text = $files[0]
            $lblStatus.Text = "Status: Custom icon loaded into memory."
            $lblStatus.ForeColor = [System.Drawing.Color]::Black
        } else {
            $lblStatus.Text = "Status: Error E416. Invalid icon format. Must be .ico."
            $lblStatus.ForeColor = [System.Drawing.Color]::Red
        }
    })

    # --- Global Form Drag & Drop Fallback ---
    $form.Add_DragEnter({
        param($s, $e)
        if ($e.Data.GetDataPresent([System.Windows.Forms.DataFormats]::FileDrop)) { 
            $e.Effect = [System.Windows.Forms.DragDropEffects]::Copy 
        }
    })

    $form.Add_DragDrop({
        param($s, $e)
        $files = $e.Data.GetData([System.Windows.Forms.DataFormats]::FileDrop)
        if ($files[0].ToLower().EndsWith(".ps1")) {
            $txtSource.Text = $files[0]
            $lblStatus.Text = "Status: Target locked. Ready to apply."
            $lblStatus.ForeColor = [System.Drawing.Color]::Black
        } elseif ($files[0].ToLower().EndsWith(".ico")) {
            $txtIcon.Text = $files[0]
            $lblStatus.Text = "Status: Icon targeted. Drop a script file next."
            $lblStatus.ForeColor = [System.Drawing.Color]::Black
        } else {
            $lblStatus.Text = "Status: Error E415. Unsupported file type dropped."
            $lblStatus.ForeColor = [System.Drawing.Color]::Red
        }
    })

    if (-not $noConsole) {
        [void]$form.ShowDialog()
    }
    $form.Dispose()

} catch {
    $ts = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
    $errMsg = "[$ts] [FATAL] [Code: E999] Catastrophic Engine Failure: $($_.Exception.Message)`r`nLine: $($_.InvocationInfo.ScriptLineNumber)`r`nPosition: $($_.InvocationInfo.PositionMessage)"
    $errMsg | Out-File -FilePath $tempLog -Encoding UTF8
    Start-Process "notepad.exe" $tempLog
    Exit
}