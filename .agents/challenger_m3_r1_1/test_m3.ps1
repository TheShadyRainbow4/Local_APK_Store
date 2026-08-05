# test_m3.ps1 - Empirical Verification Script for Milestone 3

$ErrorActionPreference = 'Continue'
$serverExePath = "C:\Users\Administrator\Desktop\Local_APK_Store\Manager_App\Elite_App_Marketplace-Server.exe"
$logFilePath = "$env:SystemDrive\EliteSoftware\Logs\LocalAPKStore.log"

Write-Host "===================================================="
Write-Host " Starting Empirical Test Suite for Milestone 3"
Write-Host "===================================================="

Add-Type -TypeDefinition @"
using System;
using System.Runtime.InteropServices;
using System.Text;
using System.Collections.Generic;

public class Win32Helper {
    public delegate bool EnumWindowsProc(IntPtr hWnd, IntPtr lParam);

    [DllImport("user32.dll", SetLastError = true, CharSet = CharSet.Auto)]
    public static extern bool EnumWindows(EnumWindowsProc lpEnumFunc, IntPtr lParam);

    [DllImport("user32.dll", SetLastError = true, CharSet = CharSet.Auto)]
    public static extern bool EnumChildWindows(IntPtr hWndParent, EnumWindowsProc lpEnumFunc, IntPtr lParam);

    [DllImport("user32.dll", CharSet = CharSet.Auto)]
    public static extern int GetWindowText(IntPtr hWnd, StringBuilder lpString, int nMaxCount);

    [DllImport("user32.dll", CharSet = CharSet.Auto)]
    public static extern int GetClassName(IntPtr hWnd, StringBuilder lpString, int nMaxCount);

    [DllImport("user32.dll")]
    public static extern IntPtr SendMessage(IntPtr hWnd, uint Msg, IntPtr wParam, IntPtr lParam);

    public const uint LVM_GETITEMCOUNT = 0x1004;

    public static IntPtr FindMainWindow(int processId) {
        IntPtr foundHWnd = IntPtr.Zero;
        EnumWindows((hWnd, lParam) => {
            uint pid;
            GetWindowThreadProcessId(hWnd, out pid);
            if (pid == processId) {
                StringBuilder sb = new StringBuilder(256);
                GetWindowText(hWnd, sb, 256);
                if (sb.ToString().Contains("Local APK Store")) {
                    foundHWnd = hWnd;
                    return false;
                }
            }
            return true;
        }, IntPtr.Zero);
        return foundHWnd;
    }

    [DllImport("user32.dll")]
    public static extern uint GetWindowThreadProcessId(IntPtr hWnd, out uint lpdwProcessId);

    public static List<IntPtr> GetChildWindows(IntPtr parent) {
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

# Helper to inspect server UI elements
function Get-ServerUIState($procId) {
    $mainWnd = [Win32Helper]::FindMainWindow($procId)
    if ($mainWnd -eq [IntPtr]::Zero) {
        return @{ Found = $false; Error = "Main window not found for PID $procId" }
    }
    
    $children = [Win32Helper]::GetChildWindows($mainWnd)
    $labelWnd = [IntPtr]::Zero
    $labelCountText = ""
    $listViewWnd = [IntPtr]::Zero
    $listViewItemCount = -1

    foreach ($child in $children) {
        $clsSb = New-Object System.Text.StringBuilder 256
        [Win32Helper]::GetClassName($child, $clsSb, 256) | Out-Null
        $clsName = $clsSb.ToString()

        $txtSb = New-Object System.Text.StringBuilder 256
        [Win32Helper]::GetWindowText($child, $txtSb, 256) | Out-Null
        $txt = $txtSb.ToString()

        if ($clsName -eq "STATIC" -and $txt -like "Connected Clients (*") {
            $labelWnd = $child
            $labelCountText = $txt
        }
        if ($clsName -eq "SysListView32") {
            $listViewWnd = $child
            $listViewItemCount = [Win32Helper]::SendMessage($child, [Win32Helper]::LVM_GETITEMCOUNT, [IntPtr]::Zero, [IntPtr]::Zero).ToInt32()
        }
    }

    return @{
        Found = $true
        MainWnd = $mainWnd
        LabelWnd = $labelWnd
        LabelText = $labelCountText
        ListViewWnd = $listViewWnd
        ListViewItemCount = $listViewItemCount
    }
}

# Ensure any existing running server is terminated before test
Get-Process -Name "Elite_App_Marketplace-Server" -ErrorAction SilentlyContinue | Stop-Process -Force
Start-Sleep -Seconds 1

# Launch Server
Write-Host "[TEST STEP 2] Launching Elite_App_Marketplace-Server.exe..."
$serverProc = Start-Process -FilePath $serverExePath -PassThru
Start-Sleep -Seconds 2

if ($serverProc.HasExited) {
    Write-Error "Server process failed to start or exited immediately!"
    exit 1
}

Write-Host "Server running under PID $($serverProc.Id)"

# Check initial UI State
$uiState = Get-ServerUIState $serverProc.Id
Write-Host "Initial UI State: LabelText='$($uiState.LabelText)', ListViewItemCount=$($uiState.ListViewItemCount)"

# Test 1: POST /api/heartbeat with multiple clients
Write-Host "`n[TEST STEP 3] Testing /api/heartbeat..."
$baseUrl = "http://127.0.0.1:8552"

$hb1 = @{ client_id = "test_client_001"; device_name = "Pixel 8 Pro" } | ConvertTo-Json
$res1 = Invoke-RestMethod -Uri "$baseUrl/api/heartbeat" -Method Post -Body $hb1 -ContentType "application/json"
Write-Host "Client 1 Heartbeat Response: $($res1 | ConvertTo-Json -Compress)"

$hb2 = @{ client_id = "test_client_002"; device_name = "Galaxy S24 Ultra" } | ConvertTo-Json
$res2 = Invoke-RestMethod -Uri "$baseUrl/api/heartbeat" -Method Post -Body $hb2 -ContentType "application/json"
Write-Host "Client 2 Heartbeat Response: $($res2 | ConvertTo-Json -Compress)"

# Test heartbeat fallback without client_id
$hb3 = @{ device_name = "Anonymous Tablet" } | ConvertTo-Json
$res3 = Invoke-RestMethod -Uri "$baseUrl/api/heartbeat" -Method Post -Body $hb3 -ContentType "application/json"
Write-Host "Client 3 (fallback) Heartbeat Response: $($res3 | ConvertTo-Json -Compress)"

# Test malformed JSON
try {
    $resErr = Invoke-RestMethod -Uri "$baseUrl/api/heartbeat" -Method Post -Body "{invalid_json" -ContentType "application/json"
    Write-Host "ERROR: Expected 400 bad request for malformed json, got success!"
} catch {
    Write-Host "Malformed JSON caught as expected: $($_.Exception.Message)"
}

Start-Sleep -Seconds 2
$uiState = Get-ServerUIState $serverProc.Id
Write-Host "After 3 heartbeats: LabelText='$($uiState.LabelText)', ListViewItemCount=$($uiState.ListViewItemCount)"

# Test 2: POST /api/disconnect
Write-Host "`n[TEST STEP 4] Testing /api/disconnect..."
$dc1 = @{ client_id = "test_client_001" } | ConvertTo-Json
$resDc1 = Invoke-RestMethod -Uri "$baseUrl/api/disconnect" -Method Post -Body $dc1 -ContentType "application/json"
Write-Host "Client 1 Disconnect Response: $($resDc1 | ConvertTo-Json -Compress)"

Start-Sleep -Seconds 2
$uiState = Get-ServerUIState $serverProc.Id
Write-Host "After disconnecting Client 1: LabelText='$($uiState.LabelText)', ListViewItemCount=$($uiState.ListViewItemCount)"

# Clean up client 2 and 3 before timeout test
$dc2 = @{ client_id = "test_client_002" } | ConvertTo-Json
Invoke-RestMethod -Uri "$baseUrl/api/disconnect" -Method Post -Body $dc2 -ContentType "application/json" | Out-Null
$dc3 = @{ client_id = "127.0.0.1" } | ConvertTo-Json
Invoke-RestMethod -Uri "$baseUrl/api/disconnect" -Method Post -Body $dc3 -ContentType "application/json" | Out-Null
Start-Sleep -Seconds 1

# Test 3: Timeout Cleanup Thread (15s timeout)
Write-Host "`n[TEST STEP 5] Testing Ungraceful Disconnect Timeout (15 seconds)..."
$hbTimeout = @{ client_id = "timeout_client_999"; device_name = "Vanishing Tablet" } | ConvertTo-Json
Invoke-RestMethod -Uri "$baseUrl/api/heartbeat" -Method Post -Body $hbTimeout -ContentType "application/json" | Out-Null

$uiState = Get-ServerUIState $serverProc.Id
Write-Host "At T=0s: LabelText='$($uiState.LabelText)', ListViewItemCount=$($uiState.ListViewItemCount)"

Write-Host "Waiting 16 seconds to allow ClientCleanupThread (15s limit) to purge client..."
Start-Sleep -Seconds 16

$uiState = Get-ServerUIState $serverProc.Id
Write-Host "At T=16s: LabelText='$($uiState.LabelText)', ListViewItemCount=$($uiState.ListViewItemCount)"

# Check Log output
if (Test-Path $logFilePath) {
    Write-Host "`nServer Log Entries:"
    Get-Content $logFilePath -Tail 15
} else {
    Write-Host "Log file not found at $logFilePath"
}

# Stop server process
$serverProc | Stop-Process -Force
Write-Host "`nEmpirical Test Suite Completed."
