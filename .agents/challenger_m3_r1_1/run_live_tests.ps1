# run_live_tests.ps1 - Empirical Verification of Milestone 3 on running server process

$ErrorActionPreference = 'Continue'
$baseUrl = "http://127.0.0.1:8552"
$logFilePath = "$env:SystemDrive\EliteSoftware\Logs\LocalAPKStore.log"

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

    [DllImport("user32.dll")]
    public static extern uint GetWindowThreadProcessId(IntPtr hWnd, out uint lpdwProcessId);

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

# Find running server PID
$serverProc = Get-Process | Where-Object { $_.ProcessName -eq "Elite_App_Marketplace-Server" -or $_.ProcessName -eq "LocalAPKStore" } | Select-Object -First 1
if (-not $serverProc) {
    Write-Error "Server process not found!"
    exit 1
}

Write-Host "Targeting Server Process PID: $($serverProc.Id)"

# Check Initial State
$uiState = Get-ServerUIState $serverProc.Id
Write-Host "Initial UI State: LabelText='$($uiState.LabelText)', ListViewItemCount=$($uiState.ListViewItemCount)"

# STEP 3: Test /api/heartbeat
Write-Host "`n--- [STEP 3] Testing /api/heartbeat POST requests ---"
$hb1 = @{ client_id = "client_alpha"; device_name = "Pixel 8 Pro" } | ConvertTo-Json
$r1 = Invoke-RestMethod -Uri "$baseUrl/api/heartbeat" -Method Post -Body $hb1 -ContentType "application/json"
Write-Host "Heartbeat 1 Response: $($r1 | ConvertTo-Json -Compress)"

$hb2 = @{ client_id = "client_beta"; device_name = "Galaxy S24 Ultra" } | ConvertTo-Json
$r2 = Invoke-RestMethod -Uri "$baseUrl/api/heartbeat" -Method Post -Body $hb2 -ContentType "application/json"
Write-Host "Heartbeat 2 Response: $($r2 | ConvertTo-Json -Compress)"

$hb3 = @{ device_name = "Anonymous Tablet" } | ConvertTo-Json
$r3 = Invoke-RestMethod -Uri "$baseUrl/api/heartbeat" -Method Post -Body $hb3 -ContentType "application/json"
Write-Host "Heartbeat 3 (fallback client_id) Response: $($r3 | ConvertTo-Json -Compress)"

Start-Sleep -Seconds 2
$uiState = Get-ServerUIState $serverProc.Id
Write-Host "UI State after 3 heartbeats: LabelText='$($uiState.LabelText)', ListViewItemCount=$($uiState.ListViewItemCount)"

# STEP 4: Test /api/disconnect
Write-Host "`n--- [STEP 4] Testing /api/disconnect POST request ---"
$dc1 = @{ client_id = "client_alpha" } | ConvertTo-Json
$rDc1 = Invoke-RestMethod -Uri "$baseUrl/api/disconnect" -Method Post -Body $dc1 -ContentType "application/json"
Write-Host "Disconnect Response: $($rDc1 | ConvertTo-Json -Compress)"

Start-Sleep -Seconds 2
$uiState = Get-ServerUIState $serverProc.Id
Write-Host "UI State after disconnecting client_alpha: LabelText='$($uiState.LabelText)', ListViewItemCount=$($uiState.ListViewItemCount)"

# Clean up client_beta and fallback client
$dc2 = @{ client_id = "client_beta" } | ConvertTo-Json
Invoke-RestMethod -Uri "$baseUrl/api/disconnect" -Method Post -Body $dc2 -ContentType "application/json" | Out-Null
$dc3 = @{ client_id = "127.0.0.1" } | ConvertTo-Json
Invoke-RestMethod -Uri "$baseUrl/api/disconnect" -Method Post -Body $dc3 -ContentType "application/json" | Out-Null
Start-Sleep -Seconds 2

$uiState = Get-ServerUIState $serverProc.Id
Write-Host "UI State after cleaning up all clients: LabelText='$($uiState.LabelText)', ListViewItemCount=$($uiState.ListViewItemCount)"

# STEP 5: Test Ungraceful Disconnect Timeout (15s limit)
Write-Host "`n--- [STEP 5] Testing Ungraceful Disconnect Timeout (15 seconds) ---"
$hbTimeout = @{ client_id = "client_timeout_test"; device_name = "Timeout Test Phone" } | ConvertTo-Json
Invoke-RestMethod -Uri "$baseUrl/api/heartbeat" -Method Post -Body $hbTimeout -ContentType "application/json" | Out-Null

Start-Sleep -Seconds 1
$uiState = Get-ServerUIState $serverProc.Id
Write-Host "T=1s UI State: LabelText='$($uiState.LabelText)', ListViewItemCount=$($uiState.ListViewItemCount)"

Write-Host "Waiting 16 seconds (no heartbeats sent)..."
Start-Sleep -Seconds 16

$uiState = Get-ServerUIState $serverProc.Id
Write-Host "T=17s UI State after timeout: LabelText='$($uiState.LabelText)', ListViewItemCount=$($uiState.ListViewItemCount)"

# STEP 6: UI Verification & Log Inspection
Write-Host "`n--- [STEP 6] Inspecting Server Logs ---"
if (Test-Path $logFilePath) {
    Get-Content $logFilePath -Tail 20
} else {
    Write-Host "Log file not found at $logFilePath"
}

Write-Host "`nLive Test Verification Complete."
