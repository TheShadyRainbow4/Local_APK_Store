# Elite EasyScriptCompiler - v1.0.42.12
# EliteSoftware Professional Script Compiler & Signer
# Copyright 2026 EliteSoftware Tech Co.

param(
    [Parameter(Position=0, Mandatory=$false)]
    [string]$DroppedFile = $null
)

# Catch un-named arguments passed by Windows Explorer Drag-and-Drop
if (-not $DroppedFile -and $args.Count -gt 0) {
    $DroppedFile = $args[0]
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

    # --- Self-Elevation Protocol (Pre-GUI) ---
    $isAdmin = ([Security.Principal.WindowsPrincipal][Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)
    if (-not $isAdmin) {
        $exe = if ($isCompiled) { $scriptPath } else { "pwsh.exe" }
        $argsList = if ($isCompiled) {
            if ($DroppedFile) { "`"$DroppedFile`"" } else { "" }
        } else {
            # CRITICAL: -STA MUST BE PASSED OR WINFORMS WILL DETONATE IN PS7
            $str = "-STA -NoProfile -ExecutionPolicy Bypass -File `"$scriptPath`""
            if ($DroppedFile) { $str += " `"$DroppedFile`"" }
            $str
        }
        
        Start-Process -FilePath $exe -ArgumentList $argsList -Verb RunAs -ErrorAction Stop
        Exit
    }

    # IF WE ARE HERE, WE HAVE FULL ADMINISTRATOR PRIVILEGES.
    
    if (-not (Test-Path $logDir)) {
        New-Item -Path $logDir -ItemType Directory -Force | Out-Null
    }

    function Write-EliteLog {
        param([string]$Message, [string]$Type="INFO", [string]$ErrorCode="E000")
        $ts = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
        $logEntry = "[$ts] [$Type] [Code: $ErrorCode] $Message"
        try { $logEntry | Out-File -FilePath $logFile -Append -Encoding UTF8 } catch {}
    }

    Write-EliteLog "Elite EasyScriptCompiler initialized. Administrator Privileges: CONFIRMED." "INFO" "E000"

    # Load Assemblies Explicitly
    Add-Type -AssemblyName System.Windows.Forms
    Add-Type -AssemblyName System.Drawing
    [System.Windows.Forms.Application]::EnableVisualStyles()

    # --- Backend Dependencies ---
    $ps2exeScript = Join-Path $scriptDir "PS2EXE\ps2exe.ps1"
    if (-not (Test-Path $ps2exeScript)) { 
        $ps2exeScript = Join-Path $PSScriptRoot "PS2EXE\ps2exe.ps1" 
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

    function Find-SignTool {
        $localPaths = @((Join-Path $scriptDir "signtool.exe"), (Join-Path $PSScriptRoot "signtool.exe"))
        foreach ($p in $localPaths) { if ($p -and (Test-Path $p)) { return $p } }
        
        $pathTool = Get-Command "signtool.exe" -ErrorAction SilentlyContinue
        if ($pathTool) { return $pathTool.Source }

        $sdkRoot = "C:\Program Files (x86)\Windows Kits"
        if (Test-Path $sdkRoot) {
            $win10Bin = Join-Path $sdkRoot "10\bin"
            if (Test-Path $win10Bin) {
                $versions = Get-ChildItem -Path $win10Bin -Directory | Sort-Object Name -Descending
                foreach ($v in $versions) {
                    foreach ($arch in @("x64", "x86")) {
                        $p = Join-Path $v.FullName "$arch\signtool.exe"
                        if (Test-Path $p) { return $p }
                    }
                }
            }
        }
        return ""
    }

    function Sign-File {
        param([string]$file)
        $defaultPfx = [System.IO.Path]::Combine($scriptDir, "EliteSoftware_Special.pfx")
        $signtool = Find-SignTool
        
        if (-not $signtool) { Write-EliteLog "SignTool MIA. Bypassing cryptographic signature." "WARN" "E404"; return $false }
        if (-not (Test-Path $defaultPfx)) { Write-EliteLog "PFX not found. The digital bouncer won't let us sign." "WARN" "E403"; return $false }
        
        try {
            $args = @("sign", "/f", $defaultPfx, "/p", "Minecraft145!!", "/fd", "SHA256", "/t", "http://timestamp.digicert.com", "/v", $file)
            $p = Start-Process -FilePath $signtool -ArgumentList $args -NoNewWindow -PassThru -Wait
            if ($p.ExitCode -eq 0) { Write-EliteLog "Binary securely signed: $(Split-Path $file -Leaf)" "SUCCESS" "E200"; return $true }
            Write-EliteLog "SignTool rejected the file with exit code $($p.ExitCode)." "ERROR" "E500"
        } catch {
            Write-EliteLog "Signing threw an unexpected tantrum: $($_.Exception.Message)" "ERROR" "E501"
        }
        return $false
    }

    function Run-Compilation {
        param([string]$src, [string]$arch)
        
        $srcDir = Split-Path $src
        $baseName = [System.IO.Path]::GetFileNameWithoutExtension($src)
        $outName = $baseName + "_$arch.exe"
        $outPath = [System.IO.Path]::Combine($srcDir, $outName)
        $extractedVersion = Get-VersionFromFileName -FileName $baseName
        $currentYear = (Get-Date).Year

        Write-EliteLog "Forging binary: $outName (Version: $extractedVersion) in $srcDir" "INFO" "E101"

        $params = @{
            inputFile    = $src
            outputFile   = $outPath
            noConsole    = $true
            noOutput     = $true
            noError      = $true
            requireAdmin = $true
            STA          = $true
            company      = "EliteSoftware Tech Co."
            copyright    = "Copyright $currentYear EliteSoftware Tech Co."
            version      = $extractedVersion
            product      = "Elite Software Suite"
            title        = "$baseName ($arch)"
        }

        if ($arch -eq "x86") { $params["x86"] = $true } else { $params["x64"] = $true }

        try {
            if (-not (Test-Path $ps2exeScript)) { throw "PS2EXE backend script missing. A digital void was encountered." }
            . $ps2exeScript
            Invoke-ps2exe @params
            
            if (Test-Path $outPath) {
                Write-EliteLog "Successfully minted $arch architecture executable." "SUCCESS" "E200"
                Sign-File $outPath
                return $true
            } else {
                throw "PS2EXE finished but output file is missing in action."
            }
        } catch {
            # THE FIX IS RIGHT HERE
            Write-EliteLog "Compilation engine seized up for $($arch): $($_.Exception.Message)" "ERROR" "E505"
            return $false
        }
    }

    # --- Headless Mode (Drag & Drop execution) ---
    if ($DroppedFile -and (Test-Path $DroppedFile)) {
        Write-EliteLog "Headless drop detected. Engaging silent auto-compile for: $DroppedFile" "INFO" "E100"
        Run-Compilation -src $DroppedFile -arch "x86" | Out-Null
        Run-Compilation -src $DroppedFile -arch "x64" | Out-Null
        Write-EliteLog "Headless operations concluded." "INFO" "E200"
        Exit
    }

    # --- GUI Mode ---
    $form = New-Object System.Windows.Forms.Form
    $form.Text = "Elite EasyScriptCompiler - Professional Edition"
    $form.Size = New-Object System.Drawing.Size(600, 220)
    $form.FormBorderStyle = [System.Windows.Forms.FormBorderStyle]::FixedSingle
    $form.MaximizeBox = $false
    $form.StartPosition = [System.Windows.Forms.FormStartPosition]::CenterScreen
    $form.AllowDrop = $true

    $lblInstructions = New-Object System.Windows.Forms.Label
    $lblInstructions.Text = "Drag & Drop a .ps1 file here, paste the path, or browse."
    $lblInstructions.Location = New-Object System.Drawing.Point(15, 15)
    $lblInstructions.Size = New-Object System.Drawing.Size(400, 20)

    $txtSource = New-Object System.Windows.Forms.TextBox
    $txtSource.Location = New-Object System.Drawing.Point(15, 40)
    $txtSource.Size = New-Object System.Drawing.Size(460, 23)

    $btnBrowse = New-Object System.Windows.Forms.Button
    $btnBrowse.Text = "Browse..."
    $btnBrowse.Location = New-Object System.Drawing.Point(485, 38)
    $btnBrowse.Size = New-Object System.Drawing.Size(85, 27)

    $lblStatus = New-Object System.Windows.Forms.Label
    $lblStatus.Text = "Status: Awaiting orders."
    $lblStatus.Location = New-Object System.Drawing.Point(15, 80)
    $lblStatus.Size = New-Object System.Drawing.Size(550, 20)
    $lblStatus.ForeColor = [System.Drawing.Color]::DimGray

    $btnApply = New-Object System.Windows.Forms.Button
    $btnApply.Text = "Apply"
    $btnApply.Location = New-Object System.Drawing.Point(15, 120)
    $btnApply.Size = New-Object System.Drawing.Size(270, 40)

    $btnExit = New-Object System.Windows.Forms.Button
    $btnExit.Text = "Exit"
    $btnExit.Location = New-Object System.Drawing.Point(300, 120)
    $btnExit.Size = New-Object System.Drawing.Size(270, 40)

    $form.Controls.AddRange(@($lblInstructions, $txtSource, $btnBrowse, $lblStatus, $btnApply, $btnExit))

    # --- Custom Error Popup ---
    function Show-EliteError {
        param([string]$Message)
        $msgForm = New-Object System.Windows.Forms.Form
        $msgForm.Size = New-Object System.Drawing.Size(420, 160)
        $msgForm.StartPosition = [System.Windows.Forms.FormStartPosition]::CenterParent
        $msgForm.Text = "Elite Error Handler"
        $msgForm.FormBorderStyle = [System.Windows.Forms.FormBorderStyle]::FixedDialog
        $msgForm.MaximizeBox = $false
        $msgForm.MinimizeBox = $false
        
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

    # --- GUI Events ---
    $btnBrowse.Add_Click({
        $d = New-Object System.Windows.Forms.OpenFileDialog
        $d.Filter = "PowerShell Scripts (*.ps1)|*.ps1|All files (*.*)|*.*"
        if ($d.ShowDialog() -eq [System.Windows.Forms.DialogResult]::OK) { 
            $txtSource.Text = $d.FileName
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
        
        $r1 = Run-Compilation -src $txtSource.Text -arch "x86"
        $r2 = Run-Compilation -src $txtSource.Text -arch "x64"
        
        if ($r1 -and $r2) { 
            $lblStatus.Text = "Status: Triumphant Success. Check source directory."
            $lblStatus.ForeColor = [System.Drawing.Color]::Green
        } else { 
            $lblStatus.Text = "Status: Complete disaster. Check EliteCompiler_ErrorLog.txt for the post-mortem."
            $lblStatus.ForeColor = [System.Drawing.Color]::Red
        }
        $btnApply.Enabled = $true
    })

    $btnExit.Add_Click({ $form.Close() })

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
        } else {
            $lblStatus.Text = "Status: Error E415. I only eat .ps1 files, what is this garbage?"
            $lblStatus.ForeColor = [System.Drawing.Color]::Red
        }
    })

    [void]$form.ShowDialog()
    $form.Dispose()

} catch {
    $ts = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
    $errMsg = "[$ts] [FATAL] [Code: E999] Catastrophic Engine Failure: $($_.Exception.Message)`r`nLine: $($_.InvocationInfo.ScriptLineNumber)`r`nPosition: $($_.InvocationInfo.PositionMessage)"
    $errMsg | Out-File -FilePath $tempLog -Encoding UTF8
    Start-Process "notepad.exe" $tempLog
    Exit
}