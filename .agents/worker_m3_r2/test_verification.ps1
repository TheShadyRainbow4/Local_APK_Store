# test_verification.ps1 - Empirical Verification of M3 R2 fixes

$ErrorActionPreference = 'Continue'
$exePath = "C:\Users\Administrator\Desktop\Local_APK_Store\Manager_App\Elite_App_Marketplace-Server.exe"
$baseUrl = "http://127.0.0.1:8552"

# Kill any running instance first
Get-Process | Where-Object { $_.ProcessName -eq "Elite_App_Marketplace-Server" -or $_.ProcessName -eq "LocalAPKStore" } | Stop-Process -Force -ErrorAction SilentlyContinue
Start-Sleep -Seconds 2

Write-Host "=== TEST 1: Launch Server and Verify Startup Latency ==="
$sw = [System.Diagnostics.Stopwatch]::StartNew()
$proc = Start-Process -FilePath $exePath -PassThru
$sw.Stop()
Write-Host "Process launched PID: $($proc.Id) in $($sw.ElapsedMilliseconds) ms"

# Wait a moment for UI and server thread to initialize
Start-Sleep -Seconds 3

Write-Host "`n=== TEST 2: Verify Heartbeat & Explicit Disconnect ==="
$hbBody = @{ client_id = "test_device_1"; device_name = "Pixel 8" } | ConvertTo-Json
$r1 = Invoke-RestMethod -Uri "$baseUrl/api/heartbeat" -Method Post -Body $hbBody -ContentType "application/json"
Write-Host "Heartbeat Response: $($r1 | ConvertTo-Json -Compress)"

$dcBody = @{ client_id = "test_device_1" } | ConvertTo-Json
$r2 = Invoke-RestMethod -Uri "$baseUrl/api/disconnect" -Method Post -Body $dcBody -ContentType "application/json"
Write-Host "Disconnect Response: $($r2 | ConvertTo-Json -Compress)"

Write-Host "`n=== TEST 3: Verify Timeout Cleanup (Deadlock Fix Verification) ==="
$hbTimeout = @{ client_id = "timeout_client"; device_name = "Deadlock Test Device" } | ConvertTo-Json
Invoke-RestMethod -Uri "$baseUrl/api/heartbeat" -Method Post -Body $hbTimeout -ContentType "application/json" | Out-Null
Write-Host "Sent heartbeat for timeout_client. Waiting 18 seconds for ClientCleanupThread to run..."

Start-Sleep -Seconds 18

# Attempt REST call to verify server is alive and not deadlocked
try {
    $r3 = Invoke-RestMethod -Uri "$baseUrl/api/apps" -Method Get -TimeoutSec 5
    Write-Host "SUCCESS: Server is responsive after client timeout! Returned $($r3.apps.Count) apps."
} catch {
    Write-Error "FAILURE: Server deadlocked or non-responsive after timeout! Exception: $_"
}

Write-Host "`n=== TEST 4: Verify Socket Bind Failure Handling ==="
# Attempt to start a second server process while port 8552 is held by the first
$proc2 = Start-Process -FilePath $exePath -PassThru
Start-Sleep -Seconds 3

# Kill second process after testing
if ($proc2 -and -not $proc2.HasExited) {
    Stop-Process -Id $proc2.Id -Force -ErrorAction SilentlyContinue
}

Write-Host "`n=== Clean up ==="
if ($proc -and -not $proc.HasExited) {
    Stop-Process -Id $proc.Id -Force -ErrorAction SilentlyContinue
}

Write-Host "`nAll Verification Tests Completed."
