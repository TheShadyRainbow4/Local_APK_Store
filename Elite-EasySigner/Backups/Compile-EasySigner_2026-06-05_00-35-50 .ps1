# Compile-EasySigner.ps1
# EliteSoftware Automated Build & Signing Script
# Est. 2006, Updated for 2026
#
# Synthesizes x86 and x64 executables of Elite-EasySigner and signs them.
# Also compiles itself into a standalone "Any Architecture" EXE.

$ErrorActionPreference = "Stop"

# Determine path (handle script vs compiled exe)
$scriptPath = if ($MyInvocation.MyCommand.Path) { $MyInvocation.MyCommand.Path } else { [System.Diagnostics.Process]::GetCurrentProcess().MainModule.FileName }
$scriptDir = [System.IO.Path]::GetDirectoryName($scriptPath)

# Define Paths
$inputFile = Join-Path $scriptDir "Elite-EasySigner.ps1"
$iconFile = Join-Path $scriptDir "Elite-EasySigner.ico"
$ps2exeScript = Join-Path $scriptDir "PS2EXE\ps2exe.ps1"
$pfxPath = Join-Path $scriptDir "EliteSoftware_Special.pfx"
$password = "Minecraft145!!"

# Compiled Executables
$outputX86 = Join-Path $scriptDir "Elite-EasySigner_x86.exe"
$outputX64 = Join-Path $scriptDir "Elite-EasySigner_x64.exe"
$outputSelf = Join-Path $scriptDir "Compile-EasySigner.exe"
$outputCompiler = Join-Path $scriptDir "Elite-EasyScriptCompiler.exe"

Write-Host "==========================================" -ForegroundColor Cyan
Write-Host "  Elite EasySigner - Automated Compiler   " -ForegroundColor Cyan
Write-Host "==========================================" -ForegroundColor Cyan

# 1. Validate Prerequisites
$compilerSource = Join-Path $scriptDir "Elite-EasyScriptCompiler.ps1"
$compilerIcon = Join-Path $scriptDir "Elite-EasyScriptCompiler.ico"
if (-not (Test-Path $compilerIcon)) { $compilerIcon = $iconFile } # Fallback

if (-not (Test-Path $inputFile)) {
    Write-Error "Source file not found: $inputFile"
}
if (-not (Test-Path $ps2exeScript)) {
    Write-Error "PS2EXE compiler script not found: $ps2exeScript"
}
if (-not (Test-Path $iconFile)) {
    Write-Host "Warning: Icon file not found: $iconFile (Will proceed without custom icon)" -ForegroundColor Yellow
}

# 2. Extract Version dynamically from source code
$version = "1.0.0.0"
try {
    $content = Get-Content $inputFile -Raw
    if ($content -match '# Elite EasySigner - v([\d\.]+)') {
        $version = $Matches[1]
        Write-Host "Detected EasySigner version: $version" -ForegroundColor Green
    } else {
        Write-Host "Warning: Could not extract version dynamically from source. Defaulting to $version" -ForegroundColor Yellow
    }
} catch {
    Write-Host "Warning: Error reading source file version: $_. Defaulting to $version" -ForegroundColor Yellow
}

# Helper to find signtool.exe
function Find-SignTool {
    # 1. Check local directory (only if it doesn't have sxstrace issues - but we'll try others first)
    # Actually, let's check SDK paths first as they are more reliable
    
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
                    if (Test-Path $p) { return $p }
                }
            }
        }
    }

    $localPaths = @(
        (Join-Path $scriptDir "signtool.exe")
    )
    foreach ($p in $localPaths) {
        if ($p -and (Test-Path $p)) { return $p }
    }

    $pathTool = Get-Command "signtool.exe" -ErrorAction SilentlyContinue
    if ($pathTool) { return $pathTool.Source }

    return ""
}

# 3. Locate SignTool
$signtool = Find-SignTool
if (-not $signtool) {
    Write-Host "Warning: signtool.exe was not automatically located. Code signing will be skipped if not resolved." -ForegroundColor Yellow
} else {
    Write-Host "Located SignTool: $signtool" -ForegroundColor Green
}

# Cleanup existing builds
foreach ($f in @($outputX86, $outputX64, $outputSelf)) {
    if (Test-Path $f) {
        try { Remove-Item $f -Force } catch { Write-Host "Could not clean up $f (In use?)" -ForegroundColor Yellow }
    }
}

# 4. Compilation Function
function Compile-App {
    param(
        [string]$arch, # "x86", "x64", or "Any"
        [string]$source,
        [string]$outputPath,
        [string]$titleSuffix = "",
        [string]$customIcon = $null
    )
    
    $archText = if ($arch -eq "Any") { "Any Architecture" } else { "$arch Architecture" }
    Write-Host "`n------------------------------------------" -ForegroundColor Gray
    Write-Host "Compiling $archText..." -ForegroundColor Blue
    
    $params = @{
        inputFile   = $source
        outputFile  = $outputPath
        noConsole   = $true
        title       = "Elite EasySigner $titleSuffix ($archText)"
        description = "EliteSoftware Professional Certificate Utility ($archText)"
        company     = "EliteSoftwareTech Co."
        product     = "Elite EasySigner Suite"
        copyright   = "Copyright 2006-2026 EliteSoftware"
        version     = $version
        supportOS   = $true
        requireAdmin = $true
    }
    
    if ($customIcon -and (Test-Path $customIcon)) {
        $params["iconFile"] = $customIcon
    } elseif (Test-Path $iconFile) {
        $params["iconFile"] = $iconFile
    }
    
    if ($arch -eq "x86") {
        $params["x86"] = $true
    } elseif ($arch -eq "x64") {
        $params["x64"] = $true
    }
    # "Any" skips x86/x64 flags
    
    # Execute ps2exe by dot-sourcing and calling the function
    $compileSuccess = $false
    try {
        . $ps2exeScript
        Invoke-ps2exe @params -Verbose
        $compileSuccess = Test-Path $outputPath
    } catch {
        Write-Host "Exception during compilation: $_" -ForegroundColor Red
    }
    
    if ($compileSuccess) {
        Write-Host "Compilation of $arch succeeded: $outputPath" -ForegroundColor Green
        return $true
    } else {
        Write-Host "Compilation of $arch failed." -ForegroundColor Red
        return $false
    }
}

# 5. Signing Function
function Sign-App {
    param(
        [string]$targetFile
    )
    
    if (-not $signtool) {
        Write-Host "Skipping signing for $targetFile (SignTool not found)" -ForegroundColor Yellow
        return $false
    }
    
    if (-not (Test-Path $pfxPath)) {
        Write-Host "Skipping signing for $targetFile (PFX not found: $pfxPath)" -ForegroundColor Yellow
        return $false
    }
    
    Write-Host "Signing $targetFile..." -ForegroundColor Blue
    
    # Execute signtool
    $argsList = @("sign", "/f", $pfxPath, "/p", $password, "/fd", "SHA256", "/t", "http://timestamp.digicert.com", "/v", $targetFile)
    $process = Start-Process -FilePath $signtool -ArgumentList $argsList -NoNewWindow -PassThru -Wait
    
    if ($process.ExitCode -eq 0) {
        Write-Host "Successfully signed $targetFile" -ForegroundColor Green
        return $true
    } else {
        Write-Host "Failed to sign $targetFile (Exit code $($process.ExitCode))" -ForegroundColor Red
        return $false
    }
}

# Perform Compilations for Signer
$x86Success = Compile-App -arch "x86" -source $inputFile -outputPath $outputX86
$x64Success = Compile-App -arch "x64" -source $inputFile -outputPath $outputX64

# Perform Compilation for Compiler itself
$selfSuccess = Compile-App -arch "Any" -source $scriptPath -outputPath $outputSelf -titleSuffix "Automated Compiler"

# Perform Compilation for Script Compiler utility
$compilerSuccess = Compile-App -arch "Any" -source $compilerSource -outputPath $outputCompiler -titleSuffix "Script Compiler Utility" -customIcon $compilerIcon

# Perform Signings if successful
if ($x86Success) { $null = Sign-App -targetFile $outputX86 }
if ($x64Success) { $null = Sign-App -targetFile $outputX64 }
if ($selfSuccess) { $null = Sign-App -targetFile $outputSelf }
if ($compilerSuccess) { $null = Sign-App -targetFile $outputCompiler }

Write-Host "`n==========================================" -ForegroundColor Cyan
Write-Host "               BUILD SUMMARY              " -ForegroundColor Cyan
Write-Host "==========================================" -ForegroundColor Cyan

function Show-Summary {
    param($label, $path)
    Write-Host "$label Build: " -NoNewline
    if (Test-Path $path) {
        $sig = Get-AuthenticodeSignature $path -ErrorAction SilentlyContinue
        if ($sig -and $sig.Status -eq "Valid") {
            Write-Host "SUCCESS & SIGNED (CN=$($sig.SignerCertificate.Subject))" -ForegroundColor Green
        } else {
            Write-Host "SUCCESS (UNSIGNED / INVALID SIGNATURE)" -ForegroundColor Yellow
        }
    } else {
        Write-Host "FAILED" -ForegroundColor Red
    }
}

Show-Summary -label "Signer x86" -path $outputX86
Show-Summary -label "Signer x64" -path $outputX64
Show-Summary -label "Compiler EXE" -path $outputSelf
Show-Summary -label "Script Compiler Utility" -path $outputCompiler

Write-Host "==========================================" -ForegroundColor Cyan

