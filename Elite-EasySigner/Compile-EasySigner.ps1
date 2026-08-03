# Compile-EasySigner.ps1
# EliteSoftware Automated Build & Signing Script
# Est. 2006, Updated for 2026
#
# Synthesizes x86 and x64 executables of Elite-EasySigner and signs them.
# Wraps execution in a Legacy WinForms GUI with precision Aero Glass margins and Custom Painted Text.

$ErrorActionPreference = "Stop"

# --- Initialization & Paths ---
$scriptPath = if ($MyInvocation.MyCommand.Path) { $MyInvocation.MyCommand.Path } else { [System.Diagnostics.Process]::GetCurrentProcess().MainModule.FileName }
$scriptDir = [System.IO.Path]::GetDirectoryName($scriptPath)
$logFilePath = Join-Path $scriptDir "Elite-EasySigner_CompilerLog.txt"

$inputFile = Join-Path $scriptDir "Elite-EasySigner.ps1"
$iconFile = Join-Path $scriptDir "Elite-EasySigner.ico"
$ps2exeScript = Join-Path $scriptDir "PS2EXE\ps2exe.ps1"
$pfxPath = Join-Path $scriptDir "EliteSoftware_Special.pfx"
$password = "Minecraft145!!"

$outputX86 = Join-Path $scriptDir "Elite-EasySigner_x86.exe"
$outputX64 = Join-Path $scriptDir "Elite-EasySigner_x64.exe"
$outputSelf = Join-Path $scriptDir "Compile-EasySigner.exe"
$outputCompiler = Join-Path $scriptDir "Elite-EasyScriptCompiler.exe"

$compilerSource = Join-Path $scriptDir "Elite-EasyScriptCompiler.ps1"
$compilerIcon = Join-Path $scriptDir "Elite-EasyScriptCompiler.ico"
if (-not (Test-Path $compilerIcon)) { $compilerIcon = $iconFile }

# --- Registry & DWM Glass Logic ---
$RegPath = "HKCU:\Software\EliteSoftware\CompileEasySigner"
if (-not (Test-Path $RegPath)) { New-Item -Path $RegPath -Force | Out-Null }
$GlassEnabled = (Get-ItemProperty -Path $RegPath -Name "AeroGlass" -ErrorAction SilentlyContinue).AeroGlass -eq 1

Add-Type -AssemblyName System.Windows.Forms
Add-Type -AssemblyName System.Drawing
[System.Windows.Forms.Application]::EnableVisualStyles()

$DwmSignature = @"
using System;
using System.Runtime.InteropServices;
public class DWM {
    [StructLayout(LayoutKind.Sequential)]
    public struct MARGINS {
        public int cxLeftWidth;
        public int cxRightWidth;
        public int cyTopHeight;
        public int cyBottomHeight;
    }
    [DllImport("dwmapi.dll", PreserveSig = false)]
    public static extern void DwmExtendFrameIntoClientArea(IntPtr hwnd, ref MARGINS margins);
    [DllImport("dwmapi.dll", PreserveSig = false)]
    public static extern bool DwmIsCompositionEnabled();
}
"@
try { Add-Type -TypeDefinition $DwmSignature -ErrorAction SilentlyContinue } catch {}

# --- GUI Setup ---
$mainForm = New-Object System.Windows.Forms.Form
$mainForm.Text = "Elite EasySigner - Automated Compiler"
$mainForm.ClientSize = New-Object System.Drawing.Size(684, 461)
$mainForm.StartPosition = "CenterScreen"
$mainForm.FormBorderStyle = "FixedDialog"
$mainForm.MaximizeBox = $false

$shieldPanel = New-Object System.Windows.Forms.Panel
$shieldPanel.Size = New-Object System.Drawing.Size(660, 370)
$shieldPanel.Location = New-Object System.Drawing.Point(12, 12)
$shieldPanel.BackColor = [System.Drawing.Color]::FromArgb(15, 15, 15)
$shieldPanel.BorderStyle = "Fixed3D"

$outputBox = New-Object System.Windows.Forms.RichTextBox
$outputBox.Dock = "Fill"
$outputBox.ReadOnly = $true
$outputBox.BackColor = [System.Drawing.Color]::FromArgb(15, 15, 15)
$outputBox.ForeColor = [System.Drawing.Color]::WhiteSmoke
$outputBox.BorderStyle = "None"
$outputBox.Font = New-Object System.Drawing.Font("Consolas", 9.5, [System.Drawing.FontStyle]::Bold)
$shieldPanel.Controls.Add($outputBox)
$mainForm.Controls.Add($shieldPanel)

if ($GlassEnabled) {
    $mainForm.BackColor = [System.Drawing.Color]::Black
    $mainForm.Add_Shown({
        try {
            if ([DWM]::DwmIsCompositionEnabled()) {
                $margins = New-Object DWM+MARGINS
                $margins.cxLeftWidth = $shieldPanel.Left
                $margins.cxRightWidth = $mainForm.ClientSize.Width - $shieldPanel.Right
                $margins.cyTopHeight = $shieldPanel.Top
                $margins.cyBottomHeight = $mainForm.ClientSize.Height - $shieldPanel.Bottom
                [DWM]::DwmExtendFrameIntoClientArea($mainForm.Handle, [ref]$margins)
            }
        } catch {}
    })
} else {
    $mainForm.BackColor = [System.Drawing.SystemColors]::Control
}

$glassCheckbox = New-Object System.Windows.Forms.CheckBox
# Clear the text so standard WinForms rendering doesn't draw the ugly chunky text
$glassCheckbox.Text = "" 
$glassCheckbox.Size = New-Object System.Drawing.Size(350, 25)
$glassCheckbox.Location = New-Object System.Drawing.Point(12, 393)
$glassCheckbox.Checked = $GlassEnabled
$glassCheckbox.BackColor = [System.Drawing.Color]::Transparent
$glassCheckbox.Font = New-Object System.Drawing.Font("Segoe UI", 9, [System.Drawing.FontStyle]::Bold)

if ($GlassEnabled) { 
    $glassCheckbox.ForeColor = [System.Drawing.Color]::Black 
} else {
    $glassCheckbox.ForeColor = [System.Drawing.SystemColors]::ControlText
}

# THE FIX: Custom Paint Event to simulate native DrawThemeTextEx Composited Glow
$glassCheckbox.Add_Paint({
    param($sender, $e)
    $g = $e.Graphics
    $g.SmoothingMode = [System.Drawing.Drawing2D.SmoothingMode]::HighQuality
    $g.TextRenderingHint = [System.Drawing.Text.TextRenderingHint]::AntiAlias
    
    $displayText = "Extend Frame to Client Area (Aero Glass)"
    $font = $sender.Font
    $xOffset = 18 # Push text right to clear the physical checkbox graphic
    $yOffset = 3
    
    if ($GlassEnabled) {
        # Draw the soft white aura first (prevents DWM black-hole effect & ensures readability on dark wallpapers)
        $glowColor = [System.Drawing.Color]::FromArgb(180, 255, 255, 255)
        $glowBrush = New-Object System.Drawing.SolidBrush($glowColor)
        $g.DrawString($displayText, $font, $glowBrush, ($xOffset - 1), ($yOffset - 1))
        $g.DrawString($displayText, $font, $glowBrush, ($xOffset + 1), ($yOffset - 1))
        $g.DrawString($displayText, $font, $glowBrush, ($xOffset - 1), ($yOffset + 1))
        $g.DrawString($displayText, $font, $glowBrush, ($xOffset + 1), ($yOffset + 1))
        $glowBrush.Dispose()
    }
    
    # Draw the main sharp text over the aura
    $textBrush = New-Object System.Drawing.SolidBrush($sender.ForeColor)
    $g.DrawString($displayText, $font, $textBrush, $xOffset, $yOffset)
    $textBrush.Dispose()
})

$glassCheckbox.Add_CheckedChanged({
    $val = if ($glassCheckbox.Checked) { 1 } else { 0 }
    Set-ItemProperty -Path $RegPath -Name "AeroGlass" -Value $val
    
    $restartMsg = [System.Windows.Forms.MessageBox]::Show("Aero Glass setting updated. The matrix needs to reload for this visual majesty to take effect. Restart now?", "Visual Styles Update", [System.Windows.Forms.MessageBoxButtons]::YesNo)
    if ($restartMsg -eq "Yes") {
        Start-Process -FilePath $scriptPath
        [System.Windows.Forms.Application]::Exit()
        exit
    }
})
$mainForm.Controls.Add($glassCheckbox)

$exitButton = New-Object System.Windows.Forms.Button
$exitButton.Text = "Exit"
$exitButton.Size = New-Object System.Drawing.Size(100, 30)
$exitButton.Location = New-Object System.Drawing.Point(572, 390)
$exitButton.BackColor = [System.Drawing.SystemColors]::ButtonFace
$exitButton.UseVisualStyleBackColor = $true
$exitButton.Add_Click({ $mainForm.Close() })
$mainForm.Controls.Add($exitButton)

$runButton = New-Object System.Windows.Forms.Button
$runButton.Text = "Okay"
$runButton.Size = New-Object System.Drawing.Size(100, 30)
$runButton.Location = New-Object System.Drawing.Point(462, 390)
$runButton.BackColor = [System.Drawing.SystemColors]::ButtonFace
$runButton.UseVisualStyleBackColor = $true
$runButton.Add_Click({ 
    $runButton.Enabled = $false
    Start-BuildProcess 
    $runButton.Enabled = $true
})
$mainForm.Controls.Add($runButton)

# --- Core Functions ---

function Write-UILog {
    param(
        [string]$Message,
        $Color = [System.Drawing.Color]::WhiteSmoke
    )
    
    if ($Color -is [string]) {
        $colorName = $Color -replace '\[System.Drawing.Color\]::', ''
        $Color = [System.Drawing.Color]::FromName($colorName)
    }

    $timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
    $logLine = "[$timestamp] $Message"
    
    try {
        Add-Content -Path $logFilePath -Value $logLine
    } catch {
        # Silent fail on file lock to not crash the UI
    }

    $outputBox.SelectionStart = $outputBox.TextLength
    $outputBox.SelectionLength = 0
    $outputBox.SelectionColor = $Color
    $outputBox.AppendText("$Message`n")
    $outputBox.ScrollToCaret()
    [System.Windows.Forms.Application]::DoEvents()
}

function Find-SignTool {
    $sdkRoot = "C:\Program Files (x86)\Windows Kits"
    if (Test-Path $sdkRoot) {
        $win10Bin = Join-Path $sdkRoot "10\bin"
        if (Test-Path $win10Bin) {
            $versions = Get-ChildItem -Path $win10Bin -Directory -ErrorAction SilentlyContinue | Sort-Object Name -Descending
            foreach ($v in $versions) {
                $signtoolPaths = @(
                    (Join-Path $v.FullName "x64\signtool.exe"),
                    (Join-Path $v.FullName "x86\signtool.exe")
                )
                foreach ($p in $signtoolPaths) {
                    if (Test-Path $p) { return $p }
                }
            }
        }
    }
    $localPaths = @((Join-Path $scriptDir "signtool.exe"))
    foreach ($p in $localPaths) {
        if ($p -and (Test-Path $p)) { return $p }
    }
    $pathTool = Get-Command "signtool.exe" -ErrorAction SilentlyContinue
    if ($pathTool) { return $pathTool.Source }
    return ""
}

function Compile-App {
    param([string]$arch, [string]$source, [string]$outputPath, [string]$titleSuffix = "", [string]$customIcon = $null)
    
    $archText = if ($arch -eq "Any") { "Any Architecture" } else { "$arch Architecture" }
    Write-UILog "------------------------------------------" [System.Drawing.Color]::DarkGray
    Write-UILog "Compiling $archText..." [System.Drawing.Color]::Cyan
    
    $params = @{
        inputFile    = $source
        outputFile   = $outputPath
        noConsole    = $true
        title        = "Elite EasySigner $titleSuffix ($archText)"
        description  = "EliteSoftware Professional Certificate Utility ($archText)"
        company      = "EliteSoftwareTech Co."
        product      = "Elite EasySigner Suite"
        copyright    = "Copyright 2006-2026 EliteSoftware"
        version      = $script:version
        supportOS    = $true
        requireAdmin = $true
    }
    
    if ($customIcon -and (Test-Path $customIcon)) { $params["iconFile"] = $customIcon } 
    elseif (Test-Path $iconFile) { $params["iconFile"] = $iconFile }
    
    if ($arch -eq "x86") { $params["x86"] = $true } 
    elseif ($arch -eq "x64") { $params["x64"] = $true }
    
    $compileSuccess = $false
    try {
        . $ps2exeScript
        Invoke-ps2exe @params -WarningAction SilentlyContinue | Out-Null
        $compileSuccess = Test-Path $outputPath
    } catch {
        Write-UILog "Exception during compilation: Looks like the code monkeys threw a wrench in the gears. Details: $_" [System.Drawing.Color]::Red
    }
    
    if ($compileSuccess) {
        Write-UILog "Compilation of $arch succeeded: $outputPath" [System.Drawing.Color]::LimeGreen
        return $true
    } else {
        Write-UILog "Compilation of $arch failed. The digital ether has rejected your binaries." [System.Drawing.Color]::Red
        return $false
    }
}

function Sign-App {
    param([string]$targetFile)
    if (-not $script:signtool) {
        Write-UILog "Skipping signing for $targetFile (SignTool evaporated into the void)" [System.Drawing.Color]::Yellow
        return $false
    }
    if (-not (Test-Path $pfxPath)) {
        Write-UILog "Skipping signing for $targetFile (Your PFX file is playing hide and seek: $pfxPath)" [System.Drawing.Color]::Yellow
        return $false
    }
    
    Write-UILog "Signing $targetFile..." [System.Drawing.Color]::Cyan
    try {
        $argsList = @("sign", "/f", $pfxPath, "/p", $password, "/fd", "SHA256", "/t", "http://timestamp.digicert.com", "/v", $targetFile)
        $process = Start-Process -FilePath $script:signtool -ArgumentList $argsList -NoNewWindow -PassThru -Wait
        
        if ($process.ExitCode -eq 0) {
            Write-UILog "Successfully stamped $targetFile with Elite authority." [System.Drawing.Color]::LimeGreen
            return $true
        } else {
            Write-UILog "Failed to sign $targetFile. The cryptography gods demand a sacrifice (Exit code $($process.ExitCode))" [System.Drawing.Color]::Red
            return $false
        }
    } catch {
        Write-UILog "Signing process threw a tantrum: $_" [System.Drawing.Color]::Red
        return $false
    }
}

# --- Main Execution Block ---

function Start-BuildProcess {
    Write-UILog "==========================================" [System.Drawing.Color]::Cyan
    Write-UILog "  Elite EasySigner - Automated Compiler   " [System.Drawing.Color]::Cyan
    Write-UILog "==========================================" [System.Drawing.Color]::Cyan

    try {
        if (-not (Test-Path $inputFile)) { throw "Source file took a vacation: $inputFile" }
        if (-not (Test-Path $ps2exeScript)) { throw "PS2EXE compiler script vanished: $ps2exeScript" }
        if (-not (Test-Path $iconFile)) { Write-UILog "Warning: Icon file missing. Operating without aesthetic flavor." [System.Drawing.Color]::Yellow }

        $script:version = "1.0.0.0"
        try {
            $content = Get-Content $inputFile -Raw
            if ($content -match '# Elite EasySigner - v([\d\.]+)') {
                $script:version = $Matches[1]
                Write-UILog "Detected EasySigner version: $script:version" [System.Drawing.Color]::LimeGreen
            } else {
                Write-UILog "Warning: Could not dynamically extract version. Defaulting to legacy standard $script:version" [System.Drawing.Color]::Yellow
            }
        } catch {
            Write-UILog "Warning: Error reading source file version. Defaulting to $script:version" [System.Drawing.Color]::Yellow
        }

        $script:signtool = Find-SignTool
        if (-not $script:signtool) {
            Write-UILog "Warning: signtool.exe was not located. Signatures will be suspiciously absent." [System.Drawing.Color]::Yellow
        } else {
            Write-UILog "Located SignTool: $script:signtool" [System.Drawing.Color]::LimeGreen
        }

        foreach ($f in @($outputX86, $outputX64, $outputSelf)) {
            if (Test-Path $f) {
                try { Remove-Item $f -Force } catch { Write-UILog "Could not sanitize old build $f (Is it running?)" [System.Drawing.Color]::Yellow }
            }
        }

        $x86Success = Compile-App -arch "x86" -source $inputFile -outputPath $outputX86
        $x64Success = Compile-App -arch "x64" -source $inputFile -outputPath $outputX64
        $selfSuccess = Compile-App -arch "Any" -source $scriptPath -outputPath $outputSelf -titleSuffix "Automated Compiler"
        $compilerSuccess = Compile-App -arch "Any" -source $compilerSource -outputPath $outputCompiler -titleSuffix "Script Compiler Utility" -customIcon $compilerIcon

        if ($x86Success) { $null = Sign-App -targetFile $outputX86 }
        if ($x64Success) { $null = Sign-App -targetFile $outputX64 }
        if ($selfSuccess) { $null = Sign-App -targetFile $outputSelf }
        if ($compilerSuccess) { $null = Sign-App -targetFile $outputCompiler }

        Write-UILog "`n==========================================" [System.Drawing.Color]::Cyan
        Write-UILog "               BUILD SUMMARY              " [System.Drawing.Color]::Cyan
        Write-UILog "==========================================" [System.Drawing.Color]::Cyan

        function Show-Summary {
            param($label, $path)
            $msg = "$label Build: "
            if (Test-Path $path) {
                $sig = Get-AuthenticodeSignature $path -ErrorAction SilentlyContinue
                if ($sig -and $sig.Status -eq "Valid") {
                    Write-UILog "$msg SUCCESS & SIGNED (CN=$($sig.SignerCertificate.Subject))" [System.Drawing.Color]::LimeGreen
                } else {
                    Write-UILog "$msg SUCCESS (UNSIGNED / INVALID SIGNATURE)" [System.Drawing.Color]::Yellow
                }
            } else {
                Write-UILog "$msg FAILED MISERABLY" [System.Drawing.Color]::Red
            }
        }

        Show-Summary -label "Signer x86" -path $outputX86
        Show-Summary -label "Signer x64" -path $outputX64
        Show-Summary -label "Compiler EXE" -path $outputSelf
        Show-Summary -label "Script Compiler Utility" -path $outputCompiler

        Write-UILog "==========================================" [System.Drawing.Color]::Cyan
        Write-UILog "Ready." [System.Drawing.Color]::WhiteSmoke

    } catch {
        Write-UILog "CRITICAL MALFUNCTION: $_" [System.Drawing.Color]::Red
        Write-UILog "The build process has flatlined. Check the logs and try not to panic." [System.Drawing.Color]::Red
    }
}

$mainForm.ShowDialog() | Out-Null