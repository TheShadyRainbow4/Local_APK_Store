# PowerShell Empirical Test for Win32 SysListView32 & ImageList in LocalAPKStore.exe

$code = @"
using System;
using System.Runtime.InteropServices;
using System.Text;
using System.Collections.Generic;

public class Win32UI {
    [DllImport("user32.dll", SetLastError = true, CharSet = CharSet.Auto)]
    public static extern IntPtr FindWindow(string lpClassName, string lpWindowName);

    [DllImport("user32.dll", SetLastError = true, CharSet = CharSet.Auto)]
    public static extern IntPtr FindWindowEx(IntPtr hwndParent, IntPtr hwndChildAfter, string lpszClass, string lpszWindow);

    [DllImport("user32.dll", CharSet = CharSet.Auto)]
    public static extern IntPtr SendMessage(IntPtr hWnd, uint Msg, IntPtr wParam, IntPtr lParam);

    [DllImport("user32.dll", CharSet = CharSet.Auto)]
    public static extern bool PostMessage(IntPtr hWnd, uint Msg, IntPtr wParam, IntPtr lParam);

    public delegate bool EnumWindowsProc(IntPtr hWnd, IntPtr lParam);

    [DllImport("user32.dll")]
    [return: MarshalAs(UnmanagedType.Bool)]
    public static extern bool EnumChildWindows(IntPtr hwndParent, EnumWindowsProc lpEnumFunc, IntPtr lParam);

    [DllImport("user32.dll", CharSet = CharSet.Auto, SetLastError = true)]
    public static extern int GetClassName(IntPtr hWnd, StringBuilder lpClassName, int nMaxCount);

    [DllImport("user32.dll")]
    public static extern bool SetFocus(IntPtr hWnd);

    [DllImport("user32.dll")]
    public static extern bool IsWindow(IntPtr hWnd);

    public const uint LVM_GETITEMCOUNT = 0x1004;
    public const uint LVM_GETIMAGELIST = 0x1002;
    public const uint LVM_GETNEXTITEM = 0x100C;
    public const int LVSIL_NORMAL = 0;
    public const int LVSIL_SMALL = 1;
    public const int LVSIL_STATE = 2;
    public const int LVNI_SELECTED = 0x0002;

    public const uint WM_KEYDOWN = 0x0100;
    public const uint WM_KEYUP = 0x0101;
    public const int VK_DOWN = 0x28;
    public const int VK_UP = 0x26;
    public const int VK_HOME = 0x24;

    private static List<IntPtr> foundListViews = new List<IntPtr>();

    private static bool EnumChildCallback(IntPtr hWnd, IntPtr lParam) {
        StringBuilder sb = new StringBuilder(256);
        GetClassName(hWnd, sb, sb.Capacity);
        if (sb.ToString().Equals("SysListView32", StringComparison.OrdinalIgnoreCase)) {
            foundListViews.Add(hWnd);
        }
        return true;
    }

    public static IntPtr GetAppListView() {
        foundListViews.Clear();
        IntPtr hwndMain = FindWindow("EliteAppMarketplaceServer", null);
        if (hwndMain == IntPtr.Zero) return IntPtr.Zero;
        EnumChildWindows(hwndMain, EnumChildCallback, IntPtr.Zero);
        if (foundListViews.Count > 0) return foundListViews[0];
        return IntPtr.Zero;
    }

    public static string Inspect() {
        IntPtr hwndMain = FindWindow("EliteAppMarketplaceServer", null);
        if (hwndMain == IntPtr.Zero) return "ERROR: Main window not found.";

        IntPtr hwndListView = GetAppListView();
        if (hwndListView == IntPtr.Zero) return "ERROR: SysListView32 control not found.";

        int itemCount = (int)SendMessage(hwndListView, LVM_GETITEMCOUNT, IntPtr.Zero, IntPtr.Zero);
        IntPtr hSmallImageList = SendMessage(hwndListView, LVM_GETIMAGELIST, (IntPtr)LVSIL_SMALL, IntPtr.Zero);
        int selectedIndex = (int)SendMessage(hwndListView, LVM_GETNEXTITEM, (IntPtr)(-1), (IntPtr)LVNI_SELECTED);

        return String.Format("SUCCESS|HWndMain=0x{0:X}|HWndLV=0x{1:X}|ItemCount={2}|HImageList=0x{3:X}|SelectedIndex={4}", 
            hwndMain.ToInt64(), hwndListView.ToInt64(), itemCount, hSmallImageList.ToInt64(), selectedIndex);
    }

    public static string NavigateList(string direction) {
        IntPtr hwndMain = FindWindow("EliteAppMarketplaceServer", null);
        if (hwndMain == IntPtr.Zero) return "ERROR: Main window not found.";
        IntPtr hwndListView = GetAppListView();
        if (hwndListView == IntPtr.Zero) return "ERROR: SysListView32 not found.";

        SetFocus(hwndListView);
        int key = VK_DOWN;
        if (direction == "UP") key = VK_UP;
        else if (direction == "HOME") key = VK_HOME;

        SendMessage(hwndListView, WM_KEYDOWN, (IntPtr)key, IntPtr.Zero);
        SendMessage(hwndListView, WM_KEYUP, (IntPtr)key, IntPtr.Zero);

        bool alive = IsWindow(hwndMain);
        int selectedIndex = (int)SendMessage(hwndListView, LVM_GETNEXTITEM, (IntPtr)(-1), (IntPtr)LVNI_SELECTED);

        return String.Format("NAV_SUCCESS|Direction={0}|WindowAlive={1}|NewSelectedIndex={2}", direction, alive, selectedIndex);
    }
}
"@

Add-Type -TypeDefinition $code -Language CSharp

Write-Host "Starting LocalAPKStore.exe..."
$proc = Start-Process -FilePath "C:\Users\Administrator\Desktop\Local_APK_Store\Manager_App\LocalAPKStore.exe" -PassThru
Start-Sleep -Seconds 6

Write-Host "Inspecting SysListView32..."
$result = [Win32UI]::Inspect()
Write-Host "Inspect Result: $result"

Write-Host "Navigating list via VK_HOME then VK_DOWN..."
$navHome = [Win32UI]::NavigateList("HOME")
Write-Host "Home: $navHome"
Start-Sleep -Milliseconds 300

for ($i = 0; $i -lt 5; $i++) {
    $nav = [Win32UI]::NavigateList("DOWN")
    Write-Host "Nav Down ${i}: $nav"
    Start-Sleep -Milliseconds 300
}

Write-Host "Final inspection..."
$resultAfter = [Win32UI]::Inspect()
Write-Host "Post-Nav Result: $resultAfter"

Write-Host "Stopping process..."
if ($proc -and -not $proc.HasExited) {
    Stop-Process -Id $proc.Id -Force
}
Write-Host "Test complete."
