import re

with open('Manager_App/main.cpp', 'r') as f:
    code = f.read()

# 1. Replace the APK copy logic in ProcessApp
old_apk_logic = '''    if (!apk.empty()) {
        apkName = fs::path(apk).filename().string();
        CopyFileLocal(apk, apkDir + "/" + apkName);
    }'''
new_apk_logic = '''    if (!apk.empty()) {
        std::string safeName = name;
        std::replace(safeName.begin(), safeName.end(), ' ', '_');
        apkName = safeName + "-" + ver + ".apk";
        CopyFileLocal(apk, apkDir + "/" + apkName);
    }'''
code = code.replace(old_apk_logic, new_apk_logic)

# 2. Update Preview Image to Scale perfectly
old_preview = '''            bmp->GetHBITMAP(Color(255, 255, 255), &hPreviewBitmap);
            delete bmp;'''
new_preview = '''            int w = bmp->GetWidth();
            int h = bmp->GetHeight();
            int maxDim = 100;
            float scale = min((float)maxDim/w, (float)maxDim/h);
            int newW = max(1, (int)(w * scale));
            int newH = max(1, (int)(h * scale));
            Bitmap* resized = new Bitmap(newW, newH, PixelFormat32bppARGB);
            Graphics g(resized);
            g.SetInterpolationMode(InterpolationModeHighQualityBicubic);
            g.DrawImage(bmp, 0, 0, newW, newH);
            resized->GetHBITMAP(Color(255, 255, 255), &hPreviewBitmap);
            delete resized;
            delete bmp;'''
code = code.replace(old_preview, new_preview)

# 3. Add HWND for StatusBar and ApkLabel
code = code.replace('HWND hwndApps, hwndName, hwndPackage, hwndVersion, hwndDesc, hwndCat, hwndTags, hwndStatus;',
                    'HWND hwndApps, hwndName, hwndPackage, hwndVersion, hwndDesc, hwndCat, hwndTags, hwndApkLabel, hwndStatusBar;')
code = code.replace('SetWindowText(hwndStatus,', 'SetWindowText(hwndApkLabel,')
code = code.replace('hwndStatus = CreateWindowEx(WS_EX_CLIENTEDGE, "STATIC", " No APK selected", WS_CHILD | WS_VISIBLE | SS_LEFT, 330, 410, 350, 22, hwnd, NULL, NULL, NULL);',
                    'hwndApkLabel = CreateWindowEx(WS_EX_CLIENTEDGE, "STATIC", " No APK selected", WS_CHILD | WS_VISIBLE | SS_LEFT, 330, 450, 250, 22, hwnd, NULL, NULL, NULL);')
code = code.replace('hwndStatus', 'hwndApkLabel')

# 4. Modify Window style and add StatusBar
code = code.replace('WS_OVERLAPPED | WS_CAPTION | WS_SYSMENU | WS_MINIMIZEBOX', 'WS_OVERLAPPEDWINDOW')

# 5. Add StatusBar creation in WM_CREATE
create_sb = '''        hwndStatusBar = CreateWindowEx(0, STATUSCLASSNAME, NULL, WS_CHILD | WS_VISIBLE | SBARS_SIZEGRIP, 0, 0, 0, 0, hwnd, NULL, NULL, NULL);
        SendMessage(hwndStatusBar, SB_SETTEXT, 0, (LPARAM)"Ready");
'''
code = code.replace('RefreshAppList();', create_sb + '        RefreshAppList();')

# 6. Add WM_SIZE handler
wm_size = '''    case WM_SIZE: {
        int w = LOWORD(lParam);
        int h = HIWORD(lParam);

        SendMessage(hwndStatusBar, WM_SIZE, 0, 0);
        RECT statusRect;
        GetWindowRect(hwndStatusBar, &statusRect);
        int sh = statusRect.bottom - statusRect.top;
        
        MoveWindow(hwndApps, 15, 70, 200, h - 70 - sh - 15, TRUE);

        int editW = max(100, w - 330 - 20);
        MoveWindow(hwndName, 330, 70, editW, 20, TRUE);
        MoveWindow(hwndPackage, 330, 100, editW, 20, TRUE);
        MoveWindow(hwndVersion, 330, 130, editW, 20, TRUE);
        MoveWindow(hwndCat, 330, 160, editW, 150, TRUE);
        MoveWindow(hwndTags, 330, 190, editW, 20, TRUE);
        MoveWindow(hwndDesc, 330, 220, editW, 90, TRUE);

        MoveWindow(lstScreenshots, 330, 340, 150, 70, TRUE);
        MoveWindow(hwndPreview, 490, 340, 100, 100, TRUE);
        
        MoveWindow(btnAddScreenshot, w - 140, 340, 120, 30, TRUE);
        MoveWindow(btnClearScreenshots, w - 140, 380, 120, 30, TRUE);

        MoveWindow(hwndApkLabel, 330, 450, editW - 130, 22, TRUE);
        MoveWindow(btnBrowse, w - 140, 445, 120, 30, TRUE);
        
        MoveWindow(btnDelete, 330, 485, 130, 30, TRUE);
        MoveWindow(btnClearForm, 470, 485, 130, 30, TRUE);

        MoveWindow(btnApply, w - 240, h - sh - 40, 100, 30, TRUE);
        MoveWindow(btnExit, w - 120, h - sh - 40, 100, 30, TRUE);

        return 0;
    }
'''
code = code.replace('case WM_CREATE:', wm_size + '    case WM_CREATE:')

with open('Manager_App/main.cpp', 'w') as f:
    f.write(code)

with open('publish_release.ps1', 'r') as f:
    pub = f.read()
pub = pub.replace('-lws2_32', '-lws2_32 -lgdiplus')
with open('publish_release.ps1', 'w') as f:
    f.write(pub)

