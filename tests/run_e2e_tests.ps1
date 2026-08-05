# Local APK Store - PowerShell E2E Test Suite Runner
param(
    [switch]$VerboseOutput = $false
)

$ErrorActionPreference = 'Stop'

Write-Host "========================================================================" -ForegroundColor Cyan
Write-Host "          LOCAL APK STORE - POWERSHELL E2E TEST SUITE RUNNER            " -ForegroundColor Cyan
Write-Host "========================================================================" -ForegroundColor Cyan

$scriptPath = $MyInvocation.MyCommand.Path
$testsDir = Split-Path -Parent $scriptPath
$projectDir = Split-Path -Parent $testsDir

Set-Location $projectDir

Write-Host "Project Directory: $projectDir"
Write-Host "Invoking Python E2E Test Runner..." -ForegroundColor Yellow

$pythonCmd = "python"
$runnerScript = Join-Path $testsDir "run_e2e_tests.py"

& $pythonCmd $runnerScript

$exitCode = $LASTEXITCODE

if ($exitCode -eq 0) {
    Write-Host "`n[SUCCESS] E2E Test Suite completed with 0 failures!" -ForegroundColor Green
    Exit 0
} else {
    Write-Host "`n[FAILURE] E2E Test Suite reported failures. Exit code: $exitCode" -ForegroundColor Red
    Exit $exitCode
}
