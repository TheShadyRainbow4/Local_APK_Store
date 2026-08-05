# run_full_m3_harness.ps1 - Complete End-to-End Empirical Test Harness for Milestone 3

$ErrorActionPreference = 'Stop'
$workingDir = "C:\Users\Administrator\Desktop\Local_APK_Store\Manager_App"
$exePath = "$workingDir\Elite_App_Marketplace-Server.exe"
$logFilePath = "$env:SystemDrive\EliteSoftware\Logs\LocalAPKStore.log"

Write-Host "================================================================="
Write-Host " Milestone 3 Empirical Verification Suite"
Write-Host "================================================================="

# Step 1: Re-compile Manager_App via build.bat
Write-Host "`n[STEP 1] Re-compiling Manager_App..."
$buildProc = Start-Process -FilePath "cmd.exe" -ArgumentList "/c build.bat" -WorkingDirectory $workingDir -NoNewWindow -Wait -PassThru
if ($buildProc.ExitCode -ne 0) {
    Write-Error "Compilation failed with exit code $($buildProc.ExitCode)"
    exit 1
}
Write-Host "Compilation successful: Exit Code 0"

# Kill any lingering instances
Get-Process | Where-Object { $_.ProcessName -eq "Elite_App_Marketplace-Server" -or $_.ProcessName -eq "LocalAPKStore" } | Stop-Process -Force -ErrorAction SilentlyContinue
Start-Sleep -Seconds 1

# Step 2: Launch Elite_App_Marketplace-Server.exe
Write-Host "`n[STEP 2] Launching Elite_App_Marketplace-Server.exe..."
cmd.exe /c "cd /d C:\Users\Administrator\Desktop\Local_APK_Store\Manager_App && start Elite_App_Marketplace-Server.exe"
Start-Sleep -Seconds 2
$serverProc = Get-Process | Where-Object { $_.ProcessName -eq "Elite_App_Marketplace-Server" -or $_.ProcessName -eq "LocalAPKStore" } | Select-Object -First 1
Write-Host "Server process found under PID: $($serverProc.Id)"

# Poll until port 8552 is LISTENING
Write-Host "Waiting for server HTTP API to initialize and listen on port 8552..."
$listening = $false
$maxRetries = 120
for ($i = 1; $i -le $maxRetries; $i++) {
    $netstat = netstat -ano | Select-String "8552.*LISTENING"
    if ($netstat) {
        $listening = $true
        Write-Host "Port 8552 is LISTENING after $i seconds."
        break
    }
    Start-Sleep -Seconds 1
}

if (-not $listening) {
    Write-Error "Server failed to start listening on port 8552 within $maxRetries seconds!"
    $serverProc | Stop-Process -Force -ErrorAction SilentlyContinue
    exit 1
}

Add-Type -TypeDefinition @"
using System;
using System.Runtime.InteropServices;
using System.Text;
using System.Collections.Generic;

public class Win32UI {
    public delegate bool EnumWindowsProc(IntPtr hWnd, IntPtr lParam);

    [DllImport("user32.dll", SetLastError = true, CharSet = CharSet.Auto)]
    public static extern IntPtr FindWindow(string lpClassName, string lpWindowName);

    [DllImport("user32.dll", SetLastError = true, CharSet = CharSet.Auto)]
    public static extern bool EnumChildWindows(IntPtr hWndParent, EnumWindowsProc lpEnumFunc, IntPtr lParam);

    [DllImport("user32.dll", CharSet = CharSet.Auto)]
    public static extern int GetWindowText(IntPtr hWnd, StringBuilder lpString, int nMaxCount);

    [DllImport("user32.dll", CharSet = CharSet.Auto)]
    public static extern int GetClassName(IntPtr hWnd, StringBuilder lpString, int nMaxCount);

    [DllImport("user32.dll")]
    public static extern IntPtr SendMessage(IntPtr hWnd, uint Msg, IntPtr wParam, IntPtr lParam);

    public const uint LVM_GETITEMCOUNT = 0x1004;

    public static List<IntPtr> GetAllChildWindows(IntPtr parent) {
        List<IntPtr> result = new List<IntPtr>();
        GCHandle listHandle = GCHandle.Alloc(result);
        try {
            EnumChildWindows(parent, (hWnd, lParam) => {
                List<IntPtr> list = GCHandle.FromIntPtr(lParam).Target as List<IntPtr>;
                if (list != null) {
                    list.Add(hWnd);
                }
                return true;
            }, GCHandle.ToIntPtr(listHandle));
        } finally {
            if (listHandle.IsAllocated)
                listHandle.Free();
        }
        return result;
    }
}
"@

function Get-UIState {
    $mainHWnd = [Win32UI]::FindWindow("EliteAppMarketplaceServer", $null)
    if ($mainHWnd -eq [IntPtr]::Zero) {
        return @{ Found = $false; LabelText = "N/A"; ListViewCount = -1 }
    }

    $children = [Win32UI]::GetAllChildWindows($mainHWnd)
    $label = "N/A"
    $count = -1

    foreach ($child in $children) {
        $clsSb = New-Object System.Text.StringBuilder 256
        [Win32UI]::GetClassName($child, $clsSb, 256) | Out-Null
        $cls = $clsSb.ToString()

        $txtSb = New-Object System.Text.StringBuilder 256
        [Win32UI]::GetWindowText($child, $txtSb, 256) | Out-Null
        $txt = $txtSb.ToString()

        if ($cls -eq "STATIC" -and $txt -like "Connected Clients (*") {
            $label = $txt
        }
        if ($cls -eq "SysListView32") {
            $count = [Win32UI]::SendMessage($child, [Win32UI]::LVM_GETITEMCOUNT, [IntPtr]::Zero, [IntPtr]::Zero).ToInt32()
        }
    }

    return @{ Found = $true; MainHWnd = $mainHWnd; LabelText = $label; ListViewCount = $count }
}

$baseUrl = "http://127.0.0.1:8552"

# Initial UI State
Start-Sleep -Seconds 2
$ui = Get-UIState
Write-Host "`nInitial UI State: Label='$($ui.LabelText)', ListViewCount=$($ui.ListViewCount)"

# Step 3: Test /api/heartbeat
Write-Host "`n[STEP 3] Testing /api/heartbeat with multiple client IDs..."
$c1 = @{ client_id = "client_alpha"; device_name = "Google Pixel 8" } | ConvertTo-Json
$res1 = Invoke-RestMethod -Uri "$baseUrl/api/heartbeat" -Method Post -Body $c1 -ContentType "application/json"
Write-Host "Client 1 Heartbeat Response: $($res1 | ConvertTo-Json -Compress)"

$c2 = @{ client_id = "client_beta"; device_name = "Samsung Galaxy S24" } | ConvertTo-Json
$res2 = Invoke-RestMethod -Uri "$baseUrl/api/heartbeat" -Method Post -Body $c2 -ContentType "application/json"
Write-Host "Client 2 Heartbeat Response: $($res2 | ConvertTo-Json -Compress)"

$c3 = @{ device_name = "Anonymous Tablet" } | ConvertTo-Json
$res3 = Invoke-RestMethod -Uri "$baseUrl/api/heartbeat" -Method Post -Body $c3 -ContentType "application/json"
Write-Host "Client 3 (fallback client_id) Response: $($res3 | ConvertTo-Json -Compress)"

# Test malformed JSON
try {
    $errRes = Invoke-RestMethod -Uri "$baseUrl/api/heartbeat" -Method Post -Body "{bad_json" -ContentType "application/json"
    Write-Host "ERROR: Expected 400 bad request, got success!"
} catch {
    Write-Host "Malformed JSON correctly rejected with 400 Bad Request: $($_.Exception.Message)"
}

Start-Sleep -Seconds 2
$ui = Get-UIState
Write-Host "UI State after 3 clients connected: Label='$($ui.LabelText)', ListViewCount=$($ui.ListViewCount)"

# Step 4: Test /api/disconnect
Write-Host "`n[STEP 4] Testing /api/disconnect..."
$dc1 = @{ client_id = "client_alpha" } | ConvertTo-Json
$resDc1 = Invoke-RestMethod -Uri "$baseUrl/api/disconnect" -Method Post -Body $dc1 -ContentType "application/json"
Write-Host "Client 1 Disconnect Response: $($resDc1 | ConvertTo-Json -Compress)"

Start-Sleep -Seconds 2
$ui = Get-UIState
Write-Host "UI State after disconnecting client_alpha: Label='$($ui.LabelText)', ListViewCount=$($ui.ListViewCount)"

# Clean up remaining clients before timeout test
$dc2 = @{ client_id = "client_beta" } | ConvertTo-Json
Invoke-RestMethod -Uri "$baseUrl/api/disconnect" -Method Post -Body $dc2 -ContentType "application/json" | Out-Null
$dc3 = @{ client_id = "127.0.0.1" } | ConvertTo-Json
Invoke-RestMethod -Uri "$baseUrl/api/disconnect" -Method Post -Body $dc3 -ContentType "application/json" | Out-Null
Start-Sleep -Seconds 2

$ui = Get-UIState
Write-Host "UI State after disconnecting all clients: Label='$($ui.LabelText)', ListViewCount=$($ui.ListViewCount)"

# Step 5: Ungraceful disconnect timeout test (15 seconds)
Write-Host "`n[STEP 5] Testing Ungraceful Disconnect Timeout (15 seconds limit)..."
$hbTimeout = @{ client_id = "timeout_client_xyz"; device_name = "Transient Phone" } | ConvertTo-Json
Invoke-RestMethod -Uri "$baseUrl/api/heartbeat" -Method Post -Body $hbTimeout -ContentType "application/json" | Out-Null

Start-Sleep -Seconds 2
$ui = Get-UIState
Write-Host "T=2s UI State (Client Active): Label='$($ui.LabelText)', ListViewCount=$($ui.ListViewCount)"

Write-Host "Waiting 16 seconds for ClientCleanupThread (15s limit) to auto-purge..."
Start-Sleep -Seconds 16

$ui = Get-UIState
Write-Host "T=18s UI State after timeout: Label='$($ui.LabelText)', ListViewCount=$($ui.ListViewCount)"

# Step 6: Server Log Inspection
Write-Host "`n[STEP 6] Inspecting Server Log ($logFilePath)..."
if (Test-Path $logFilePath) {
    Get-Content $logFilePath -Tail 25
} else {
    Write-Host "Log file not found at $logFilePath"
}

# Stop server process
$serverProc | Stop-Process -Force -ErrorAction SilentlyContinue
Write-Host "`n================================================================="
Write-Host " Empirical Test Harness Complete!"
Write-Host "================================================================="
