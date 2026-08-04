import os

filepath = r"C:\Users\Administrator\Desktop\Local_APK_Store\Manager_App\main.cpp"
with open(filepath, "r") as f:
    code = f.read()

# 1. Add Subclass procedure before WindowProc
subclass_code = '''
WNDPROC OldTabProc;
LRESULT CALLBACK TabProc(HWND hwnd, UINT msg, WPARAM wp, LPARAM lp) {
    if (msg == WM_COMMAND || msg == WM_NOTIFY) {
        return SendMessage(GetParent(hwnd), msg, wp, lp);
    }
    return CallWindowProc(OldTabProc, hwnd, msg, wp, lp);
}
'''
code = code.replace("void UpdateTabVisibility() {", subclass_code + "\nvoid UpdateTabVisibility() {")


# 2. In WM_CREATE, modify the creation of inner controls to use hwndTab instead of hwnd, and subclass hwndTab
# Find hwndTab creation:
old_tab_create = 'hwndTab = CreateWindowEx(0, WC_TABCONTROL, "", WS_CHILD | WS_VISIBLE | WS_CLIPSIBLINGS | WS_CLIPSIBLINGS, 10, 50, 810, 450, hwnd, (HMENU)100, NULL, NULL);'
new_tab_create = 'hwndTab = CreateWindowEx(0, WC_TABCONTROL, "", WS_CHILD | WS_VISIBLE | WS_CLIPSIBLINGS, 10, 50, 810, 450, hwnd, (HMENU)100, NULL, NULL);\n          OldTabProc = (WNDPROC)SetWindowLongPtr(hwndTab, GWLP_WNDPROC, (LONG_PTR)TabProc);'
code = code.replace(old_tab_create, new_tab_create)

# Replace parents
# But wait, what if I just replace , hwnd,  with , hwndTab,  for the controls that belong inside?
# Let's target the exact lines:
controls_to_reparent = [
    ('hwndApps = CreateWindowEx(WS_EX_CLIENTEDGE, "LISTBOX", "", WS_CHILD | WS_VISIBLE | WS_CLIPSIBLINGS | WS_VSCROLL | LBS_NOTIFY, 0, 0, 0, 0, hwnd, (HMENU)101, NULL, NULL);',
     'hwndApps = CreateWindowEx(WS_EX_CLIENTEDGE, "LISTBOX", "", WS_CHILD | WS_VISIBLE | WS_VSCROLL | LBS_NOTIFY, 0, 0, 0, 0, hwndTab, (HMENU)101, NULL, NULL);'),
    
    ('hwndName = CreateWindowEx(WS_EX_CLIENTEDGE, "EDIT", "", WS_CHILD | WS_VISIBLE | WS_CLIPSIBLINGS | ES_AUTOHSCROLL, 0, 0, 0, 0, hwnd, NULL, NULL, NULL);',
     'hwndName = CreateWindowEx(WS_EX_CLIENTEDGE, "EDIT", "", WS_CHILD | WS_VISIBLE | ES_AUTOHSCROLL, 0, 0, 0, 0, hwndTab, NULL, NULL, NULL);'),
     
    ('hwndPackage = CreateWindowEx(WS_EX_CLIENTEDGE, "EDIT", "", WS_CHILD | WS_VISIBLE | WS_CLIPSIBLINGS | ES_AUTOHSCROLL, 0, 0, 0, 0, hwnd, NULL, NULL, NULL);',
     'hwndPackage = CreateWindowEx(WS_EX_CLIENTEDGE, "EDIT", "", WS_CHILD | WS_VISIBLE | ES_AUTOHSCROLL, 0, 0, 0, 0, hwndTab, NULL, NULL, NULL);'),
     
    ('hwndVersion = CreateWindowEx(WS_EX_CLIENTEDGE, "EDIT", "", WS_CHILD | WS_VISIBLE | WS_CLIPSIBLINGS | ES_AUTOHSCROLL, 0, 0, 0, 0, hwnd, NULL, NULL, NULL);',
     'hwndVersion = CreateWindowEx(WS_EX_CLIENTEDGE, "EDIT", "", WS_CHILD | WS_VISIBLE | ES_AUTOHSCROLL, 0, 0, 0, 0, hwndTab, NULL, NULL, NULL);'),
     
    ('hwndCat = CreateWindowEx(WS_EX_CLIENTEDGE, "COMBOBOX", "", WS_CHILD | WS_VISIBLE | WS_CLIPSIBLINGS | CBS_DROPDOWN | WS_VSCROLL, 0, 0, 0, 0, hwnd, NULL, NULL, NULL);',
     'hwndCat = CreateWindowEx(WS_EX_CLIENTEDGE, "COMBOBOX", "", WS_CHILD | WS_VISIBLE | CBS_DROPDOWN | WS_VSCROLL, 0, 0, 0, 0, hwndTab, NULL, NULL, NULL);'),
     
    ('hwndTags = CreateWindowEx(WS_EX_CLIENTEDGE, "EDIT", "", WS_CHILD | WS_VISIBLE | WS_CLIPSIBLINGS | ES_AUTOHSCROLL, 0, 0, 0, 0, hwnd, NULL, NULL, NULL);',
     'hwndTags = CreateWindowEx(WS_EX_CLIENTEDGE, "EDIT", "", WS_CHILD | WS_VISIBLE | ES_AUTOHSCROLL, 0, 0, 0, 0, hwndTab, NULL, NULL, NULL);'),
     
    ('hwndDesc = CreateWindowEx(WS_EX_CLIENTEDGE, "EDIT", "", WS_CHILD | WS_VISIBLE | WS_CLIPSIBLINGS | ES_MULTILINE | WS_VSCROLL | ES_AUTOVSCROLL, 0, 0, 0, 0, hwnd, NULL, NULL, NULL);',
     'hwndDesc = CreateWindowEx(WS_EX_CLIENTEDGE, "EDIT", "", WS_CHILD | WS_VISIBLE | ES_MULTILINE | WS_VSCROLL | ES_AUTOVSCROLL, 0, 0, 0, 0, hwndTab, NULL, NULL, NULL);'),
     
    ('lstScreenshots = CreateWindowEx(WS_EX_CLIENTEDGE, "LISTBOX", "", WS_CHILD | WS_VISIBLE | WS_CLIPSIBLINGS | WS_VSCROLL | LBS_NOTIFY, 0, 0, 0, 0, hwnd, (HMENU)102, NULL, NULL);',
     'lstScreenshots = CreateWindowEx(WS_EX_CLIENTEDGE, "LISTBOX", "", WS_CHILD | WS_VISIBLE | WS_VSCROLL | LBS_NOTIFY, 0, 0, 0, 0, hwndTab, (HMENU)102, NULL, NULL);'),
     
    ('hwndPreview = CreateWindowEx(WS_EX_CLIENTEDGE, "STATIC", "", WS_CHILD | WS_VISIBLE | WS_CLIPSIBLINGS | SS_BITMAP | SS_CENTERIMAGE, 0, 0, 0, 0, hwnd, NULL, NULL, NULL);',
     'hwndPreview = CreateWindowEx(WS_EX_CLIENTEDGE, "STATIC", "", WS_CHILD | WS_VISIBLE | SS_BITMAP | SS_CENTERIMAGE, 0, 0, 0, 0, hwndTab, NULL, NULL, NULL);'),
     
    ('btnAddScreenshot = CreateWindow("BUTTON", "Add", WS_CHILD | WS_VISIBLE | WS_CLIPSIBLINGS | BS_PUSHBUTTON, 0, 0, 0, 0, hwnd, (HMENU)103, NULL, NULL);',
     'btnAddScreenshot = CreateWindow("BUTTON", "Add", WS_CHILD | WS_VISIBLE | BS_PUSHBUTTON, 0, 0, 0, 0, hwndTab, (HMENU)103, NULL, NULL);'),
     
    ('btnClearScreenshots = CreateWindow("BUTTON", "Clear All", WS_CHILD | WS_VISIBLE | WS_CLIPSIBLINGS | BS_PUSHBUTTON, 0, 0, 0, 0, hwnd, (HMENU)104, NULL, NULL);',
     'btnClearScreenshots = CreateWindow("BUTTON", "Clear All", WS_CHILD | WS_VISIBLE | BS_PUSHBUTTON, 0, 0, 0, 0, hwndTab, (HMENU)104, NULL, NULL);'),
     
    ('hwndApkLabel = CreateWindowEx(WS_EX_CLIENTEDGE, "STATIC", "No APK selected", WS_CHILD | WS_VISIBLE | WS_CLIPSIBLINGS, 0, 0, 0, 0, hwnd, NULL, NULL, NULL);',
     'hwndApkLabel = CreateWindowEx(WS_EX_CLIENTEDGE, "STATIC", "No APK selected", WS_CHILD | WS_VISIBLE | SS_LEFTNOWORDWRAP, 0, 0, 0, 0, hwndTab, NULL, NULL, NULL);'),
     
    ('btnBrowse = CreateWindow("BUTTON", "Browse APK...", WS_CHILD | WS_VISIBLE | WS_CLIPSIBLINGS | BS_PUSHBUTTON, 0, 0, 0, 0, hwnd, (HMENU)105, NULL, NULL);',
     'btnBrowse = CreateWindow("BUTTON", "Browse APK...", WS_CHILD | WS_VISIBLE | BS_PUSHBUTTON, 0, 0, 0, 0, hwndTab, (HMENU)105, NULL, NULL);'),
     
    ('btnDelete = CreateWindow("BUTTON", "Delete Selected", WS_CHILD | WS_VISIBLE | WS_CLIPSIBLINGS | BS_PUSHBUTTON, 0, 0, 0, 0, hwnd, (HMENU)106, NULL, NULL);',
     'btnDelete = CreateWindow("BUTTON", "Delete Selected", WS_CHILD | WS_VISIBLE | BS_PUSHBUTTON, 0, 0, 0, 0, hwndTab, (HMENU)106, NULL, NULL);'),
     
    ('btnApply = CreateWindow("BUTTON", "Apply", WS_CHILD | WS_VISIBLE | WS_CLIPSIBLINGS | BS_PUSHBUTTON, 0, 0, 0, 0, hwnd, (HMENU)107, NULL, NULL);',
     'btnApply = CreateWindow("BUTTON", "Apply", WS_CHILD | WS_VISIBLE | BS_PUSHBUTTON, 0, 0, 0, 0, hwndTab, (HMENU)107, NULL, NULL);'),
     
    ('btnClearForm = CreateWindow("BUTTON", "New App", WS_CHILD | WS_VISIBLE | WS_CLIPSIBLINGS | BS_PUSHBUTTON, 0, 0, 0, 0, hwnd, (HMENU)108, NULL, NULL);',
     'btnClearForm = CreateWindow("BUTTON", "New App", WS_CHILD | WS_VISIBLE | BS_PUSHBUTTON, 0, 0, 0, 0, hwndTab, (HMENU)108, NULL, NULL);'),
     
    ('btnExit = CreateWindow("BUTTON", "Hide to Tray", WS_CHILD | WS_VISIBLE | WS_CLIPSIBLINGS | BS_PUSHBUTTON, 0, 0, 0, 0, hwnd, (HMENU)109, NULL, NULL);',
     'btnExit = CreateWindow("BUTTON", "Hide to Tray", WS_CHILD | WS_VISIBLE | BS_PUSHBUTTON, 0, 0, 0, 0, hwndTab, (HMENU)109, NULL, NULL);'),
     
    ('hwndLog = CreateWindowEx(WS_EX_CLIENTEDGE, "EDIT", "", WS_CHILD | WS_CLIPSIBLINGS | ES_MULTILINE | WS_VSCROLL | ES_AUTOVSCROLL | ES_READONLY, 0, 0, 0, 0, hwnd, NULL, NULL, NULL);',
     'hwndLog = CreateWindowEx(WS_EX_CLIENTEDGE, "EDIT", "", WS_CHILD | ES_MULTILINE | WS_VSCROLL | ES_AUTOVSCROLL | ES_READONLY, 0, 0, 0, 0, hwndTab, NULL, NULL, NULL);'),
     
    ('hwndServerStatus = CreateWindow("STATIC", "Status: STOPPED", WS_CHILD, 20, 460, 200, 20, hwnd, NULL, NULL, NULL);',
     'hwndServerStatus = CreateWindow("STATIC", "Status: STOPPED", WS_CHILD, 20, 460, 200, 20, hwndTab, NULL, NULL, NULL);'),
     
    ('btnToggleServer = CreateWindow("BUTTON", "Start Server", WS_CHILD | BS_PUSHBUTTON, 690, 460, 120, 30, hwnd, (HMENU)200, NULL, NULL);',
     'btnToggleServer = CreateWindow("BUTTON", "Start Server", WS_CHILD | BS_PUSHBUTTON, 690, 460, 120, 30, hwndTab, (HMENU)200, NULL, NULL);')
]

for old, new in controls_to_reparent:
    code = code.replace(old, new)

# invLabels replacements (they use push_back, I will just replace hwnd with hwndTab in them)
code = code.replace('invLabels.push_back(CreateWindow("STATIC", "Store Inventory:", WS_CHILD | WS_VISIBLE | WS_CLIPSIBLINGS, 15, 50, 200, 20, hwnd, NULL, NULL, NULL));',
                    'invLabels.push_back(CreateWindow("STATIC", "Store Inventory:", WS_CHILD | WS_VISIBLE, 0, 0, 0, 0, hwndTab, NULL, NULL, NULL));')
code = code.replace('invLabels.push_back(CreateWindow("STATIC", "App Name:", WS_CHILD | WS_VISIBLE | WS_CLIPSIBLINGS, 0, 0, 0, 0, hwnd, NULL, NULL, NULL));',
                    'invLabels.push_back(CreateWindow("STATIC", "App Name:", WS_CHILD | WS_VISIBLE, 0, 0, 0, 0, hwndTab, NULL, NULL, NULL));')
code = code.replace('invLabels.push_back(CreateWindow("STATIC", "Package:", WS_CHILD | WS_VISIBLE | WS_CLIPSIBLINGS, 0, 0, 0, 0, hwnd, NULL, NULL, NULL));',
                    'invLabels.push_back(CreateWindow("STATIC", "Package:", WS_CHILD | WS_VISIBLE, 0, 0, 0, 0, hwndTab, NULL, NULL, NULL));')
code = code.replace('invLabels.push_back(CreateWindow("STATIC", "Version:", WS_CHILD | WS_VISIBLE | WS_CLIPSIBLINGS, 0, 0, 0, 0, hwnd, NULL, NULL, NULL));',
                    'invLabels.push_back(CreateWindow("STATIC", "Version:", WS_CHILD | WS_VISIBLE, 0, 0, 0, 0, hwndTab, NULL, NULL, NULL));')
code = code.replace('invLabels.push_back(CreateWindow("STATIC", "Category:", WS_CHILD | WS_VISIBLE | WS_CLIPSIBLINGS, 0, 0, 0, 0, hwnd, NULL, NULL, NULL));',
                    'invLabels.push_back(CreateWindow("STATIC", "Category:", WS_CHILD | WS_VISIBLE, 0, 0, 0, 0, hwndTab, NULL, NULL, NULL));')
code = code.replace('invLabels.push_back(CreateWindow("STATIC", "Tags (CSV):", WS_CHILD | WS_VISIBLE | WS_CLIPSIBLINGS, 0, 0, 0, 0, hwnd, NULL, NULL, NULL));',
                    'invLabels.push_back(CreateWindow("STATIC", "Tags (CSV):", WS_CHILD | WS_VISIBLE, 0, 0, 0, 0, hwndTab, NULL, NULL, NULL));')
code = code.replace('invLabels.push_back(CreateWindow("STATIC", "Description:", WS_CHILD | WS_VISIBLE | WS_CLIPSIBLINGS, 0, 0, 0, 0, hwnd, NULL, NULL, NULL));',
                    'invLabels.push_back(CreateWindow("STATIC", "Description:", WS_CHILD | WS_VISIBLE, 0, 0, 0, 0, hwndTab, NULL, NULL, NULL));')
code = code.replace('invLabels.push_back(CreateWindow("STATIC", "Screenshots:", WS_CHILD | WS_VISIBLE | WS_CLIPSIBLINGS, 0, 0, 0, 0, hwnd, NULL, NULL, NULL));',
                    'invLabels.push_back(CreateWindow("STATIC", "Screenshots:", WS_CHILD | WS_VISIBLE, 0, 0, 0, 0, hwndTab, NULL, NULL, NULL));')
code = code.replace('invLabels.push_back(CreateWindow("STATIC", "APK File:", WS_CHILD | WS_VISIBLE | WS_CLIPSIBLINGS, 0, 0, 0, 0, hwnd, NULL, NULL, NULL));',
                    'invLabels.push_back(CreateWindow("STATIC", "APK File:", WS_CHILD | WS_VISIBLE, 0, 0, 0, 0, hwndTab, NULL, NULL, NULL));')


# 3. Update WM_SIZE. Since they are children of hwndTab, their coordinates must be relative to hwndTab's 0,0!
# And they should be inside the Display Area (tabRect after TCM_ADJUSTRECT).
# The current code MapsWindowPoints to hwnd, we should remove that!
wm_size_old = '''          RECT tabRect;
          GetWindowRect(hwndTab, &tabRect);
          MapWindowPoints(HWND_DESKTOP, hwnd, (LPPOINT)&tabRect, 2);
          SendMessage(hwndTab, TCM_ADJUSTRECT, FALSE, (LPARAM)&tabRect);
          
          MoveWindow(hwndApps, tabRect.left, tabRect.top, 200, tabRect.bottom - tabRect.top - 50, TRUE);
          MoveWindow(invLabels[0], tabRect.left, tabRect.top - 20, 200, 20, TRUE); // Store Inventory Label
  
          int editW = std::max(100, (int)(tabRect.right - tabRect.left - 230));
          
          MoveWindow(invLabels[1], tabRect.left + 220, tabRect.top, 90, 20, TRUE);
          MoveWindow(hwndName, tabRect.left + 320, tabRect.top, editW - 100, 20, TRUE);
          
          MoveWindow(invLabels[2], tabRect.left + 220, tabRect.top + 30, 90, 20, TRUE);
          MoveWindow(hwndPackage, tabRect.left + 320, tabRect.top + 30, editW - 100, 20, TRUE);
          
          MoveWindow(invLabels[3], tabRect.left + 220, tabRect.top + 60, 90, 20, TRUE);
          MoveWindow(hwndVersion, tabRect.left + 320, tabRect.top + 60, editW - 100, 20, TRUE);
          
          MoveWindow(invLabels[4], tabRect.left + 220, tabRect.top + 90, 90, 20, TRUE);
          MoveWindow(hwndCat, tabRect.left + 320, tabRect.top + 90, editW - 100, 150, TRUE);
          
          MoveWindow(invLabels[5], tabRect.left + 220, tabRect.top + 120, 90, 20, TRUE);
          MoveWindow(hwndTags, tabRect.left + 320, tabRect.top + 120, editW - 100, 20, TRUE);
          
          MoveWindow(invLabels[6], tabRect.left + 220, tabRect.top + 150, 90, 20, TRUE);
          MoveWindow(hwndDesc, tabRect.left + 320, tabRect.top + 150, editW - 100, 90, TRUE);
  
          MoveWindow(invLabels[7], tabRect.left + 220, tabRect.top + 250, 90, 20, TRUE);
          MoveWindow(lstScreenshots, tabRect.left + 320, tabRect.top + 250, 150, 70, TRUE);
          MoveWindow(hwndPreview, tabRect.left + 480, tabRect.top + 250, 100, 100, TRUE);
          
          MoveWindow(btnAddScreenshot, tabRect.right - 130, tabRect.top + 250, 120, 30, TRUE);
          MoveWindow(btnClearScreenshots, tabRect.right - 130, tabRect.top + 290, 120, 30, TRUE);
  
          MoveWindow(invLabels[8], tabRect.left + 220, tabRect.top + 360, 90, 20, TRUE);
          MoveWindow(hwndApkLabel, tabRect.left + 320, tabRect.top + 360, editW - 240, 22, TRUE);
          MoveWindow(btnBrowse, tabRect.right - 130, tabRect.top + 355, 120, 30, TRUE);
          
          MoveWindow(btnDelete, tabRect.left, tabRect.bottom - 40, 130, 30, TRUE);
          MoveWindow(btnClearForm, tabRect.left + 140, tabRect.bottom - 40, 130, 30, TRUE);
          MoveWindow(btnApply, tabRect.right - 220, tabRect.bottom + 10, 100, 30, TRUE);
          MoveWindow(btnExit, tabRect.right - 110, tabRect.bottom + 10, 100, 30, TRUE);

          MoveWindow(hwndLog, tabRect.left, tabRect.top, tabRect.right - tabRect.left, tabRect.bottom - tabRect.top, TRUE);
          MoveWindow(hwndServerStatus, tabRect.left, tabRect.bottom + 10, 200, 20, TRUE);
          MoveWindow(btnToggleServer, tabRect.right - 130, tabRect.bottom + 5, 120, 30, TRUE);'''

wm_size_new = '''          RECT tabRect;
          GetWindowRect(hwndTab, &tabRect);
          MapWindowPoints(HWND_DESKTOP, hwndTab, (LPPOINT)&tabRect, 2); // Map to hwndTab's own client area!
          SendMessage(hwndTab, TCM_ADJUSTRECT, FALSE, (LPARAM)&tabRect);
          
          MoveWindow(invLabels[0], tabRect.left, tabRect.top, 200, 20, TRUE); // Store Inventory Label
          MoveWindow(hwndApps, tabRect.left, tabRect.top + 20, 200, tabRect.bottom - tabRect.top - 70, TRUE);
  
          int editW = std::max(100, (int)(tabRect.right - tabRect.left - 230));
          
          MoveWindow(invLabels[1], tabRect.left + 220, tabRect.top, 90, 20, TRUE);
          MoveWindow(hwndName, tabRect.left + 320, tabRect.top, editW - 100, 20, TRUE);
          
          MoveWindow(invLabels[2], tabRect.left + 220, tabRect.top + 30, 90, 20, TRUE);
          MoveWindow(hwndPackage, tabRect.left + 320, tabRect.top + 30, editW - 100, 20, TRUE);
          
          MoveWindow(invLabels[3], tabRect.left + 220, tabRect.top + 60, 90, 20, TRUE);
          MoveWindow(hwndVersion, tabRect.left + 320, tabRect.top + 60, editW - 100, 20, TRUE);
          
          MoveWindow(invLabels[4], tabRect.left + 220, tabRect.top + 90, 90, 20, TRUE);
          MoveWindow(hwndCat, tabRect.left + 320, tabRect.top + 90, editW - 100, 150, TRUE);
          
          MoveWindow(invLabels[5], tabRect.left + 220, tabRect.top + 120, 90, 20, TRUE);
          MoveWindow(hwndTags, tabRect.left + 320, tabRect.top + 120, editW - 100, 20, TRUE);
          
          MoveWindow(invLabels[6], tabRect.left + 220, tabRect.top + 150, 90, 20, TRUE);
          MoveWindow(hwndDesc, tabRect.left + 320, tabRect.top + 150, editW - 100, 90, TRUE);
  
          MoveWindow(invLabels[7], tabRect.left + 220, tabRect.top + 250, 90, 20, TRUE);
          MoveWindow(lstScreenshots, tabRect.left + 320, tabRect.top + 250, 150, 70, TRUE);
          MoveWindow(hwndPreview, tabRect.left + 480, tabRect.top + 250, 100, 100, TRUE);
          
          MoveWindow(btnAddScreenshot, tabRect.right - 130, tabRect.top + 250, 120, 30, TRUE);
          MoveWindow(btnClearScreenshots, tabRect.right - 130, tabRect.top + 290, 120, 30, TRUE);
  
          MoveWindow(invLabels[8], tabRect.left + 220, tabRect.top + 360, 90, 20, TRUE);
          MoveWindow(hwndApkLabel, tabRect.left + 320, tabRect.top + 360, editW - 240, 22, TRUE);
          MoveWindow(btnBrowse, tabRect.right - 130, tabRect.top + 355, 120, 30, TRUE);
          
          MoveWindow(btnDelete, tabRect.left, tabRect.bottom - 40, 130, 30, TRUE);
          MoveWindow(btnClearForm, tabRect.left + 140, tabRect.bottom - 40, 130, 30, TRUE);
          MoveWindow(btnApply, tabRect.right - 220, tabRect.bottom - 40, 100, 30, TRUE);
          MoveWindow(btnExit, tabRect.right - 110, tabRect.bottom - 40, 100, 30, TRUE);

          MoveWindow(hwndLog, tabRect.left, tabRect.top, tabRect.right - tabRect.left, tabRect.bottom - tabRect.top - 40, TRUE);
          MoveWindow(hwndServerStatus, tabRect.left, tabRect.bottom - 30, 200, 20, TRUE);
          MoveWindow(btnToggleServer, tabRect.right - 130, tabRect.bottom - 35, 120, 30, TRUE);'''

code = code.replace(wm_size_old, wm_size_new)

# 4. Remove SetWindowPos HWND_BOTTOM
code = code.replace('SetWindowPos(hwndTab, HWND_BOTTOM, 0, 0, 0, 0, SWP_NOMOVE | SWP_NOSIZE);', '')

# 5. Fix Banner
code = code.replace('HWND hBanner = CreateWindow("STATIC", ("        Elite App Marketplace - Server Manager (Port " + std::to_string(serverPort) + ")").c_str(), WS_CHILD | WS_VISIBLE | WS_CLIPSIBLINGS | SS_CENTERIMAGE, 0, 0, 850, 40, hwnd, NULL, NULL, NULL);',
                    'HWND hBanner = CreateWindow("STATIC", ("Elite App Marketplace - Server Manager (Port " + std::to_string(serverPort) + ")").c_str(), WS_CHILD | WS_VISIBLE | SS_CENTERIMAGE, 50, 0, 800, 40, hwnd, NULL, NULL, NULL);')
code = code.replace('HWND hBannerIcon = CreateWindow("STATIC", "", WS_CHILD | WS_VISIBLE | WS_CLIPSIBLINGS | SS_ICON, 10, 4, 32, 32, hwnd, NULL, (HINSTANCE)GetWindowLongPtr(hwnd, GWLP_HINSTANCE), NULL);',
                    'HWND hBannerIcon = CreateWindow("STATIC", "", WS_CHILD | WS_VISIBLE | SS_ICON, 10, 4, 32, 32, hwnd, NULL, (HINSTANCE)GetWindowLongPtr(hwnd, GWLP_HINSTANCE), NULL);')

# 6. Fix background colors
# Since all inner controls are now children of hwndTab, they will send WM_CTLCOLORSTATIC to hwndTab!
# We MUST handle WM_CTLCOLORSTATIC inside TabProc for the labels to be transparent!
# Let's add that to TabProc!
tab_proc_new = '''
LRESULT CALLBACK TabProc(HWND hwnd, UINT msg, WPARAM wp, LPARAM lp) {
    if (msg == WM_COMMAND || msg == WM_NOTIFY) {
        return SendMessage(GetParent(hwnd), msg, wp, lp);
    }
    if (msg == WM_CTLCOLORSTATIC) {
        HDC hdc = (HDC)wp;
        SetBkMode(hdc, TRANSPARENT);
        return (LRESULT)GetSysColorBrush(COLOR_WINDOW); // Match the tab control client area (usually window color/white)
    }
    return CallWindowProc(OldTabProc, hwnd, msg, wp, lp);
}
'''
code = code.replace('''LRESULT CALLBACK TabProc(HWND hwnd, UINT msg, WPARAM wp, LPARAM lp) {
    if (msg == WM_COMMAND || msg == WM_NOTIFY) {
        return SendMessage(GetParent(hwnd), msg, wp, lp);
    }
    return CallWindowProc(OldTabProc, hwnd, msg, wp, lp);
}''', tab_proc_new)

with open(filepath, "w") as f:
    f.write(code)

