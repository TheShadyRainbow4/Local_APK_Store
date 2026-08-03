import re

with open('Manager_App/main.cpp', 'r') as f:
    code = f.read()

# 1. Includes and Pragmas
code = code.replace('#include "json.hpp"', '''#include "json.hpp"
#include <gdiplus.h>

#pragma comment(linker,"\"/manifestdependency:type='win32' name='Microsoft.Windows.Common-Controls' version='6.0.0.0' processorArchitecture='*' publicKeyToken='6595b64144ccf1df' language='*'\"")
#pragma comment(lib, "gdiplus.lib")

using namespace Gdiplus;''')

# 2. Globals
code = code.replace('int serverPort = 8552;', '''int serverPort = 8552;
HWND hwndPreview;
HBITMAP hPreviewBitmap = NULL;
ULONG_PTR gdiplusToken;

void UpdatePreviewImage(std::string path) {
    if (hPreviewBitmap) { DeleteObject(hPreviewBitmap); hPreviewBitmap = NULL; }
    if (fs::exists(path)) {
        std::wstring wpath(path.begin(), path.end());
        Bitmap* bmp = Bitmap::FromFile(wpath.c_str());
        if (bmp && bmp->GetLastStatus() == Ok) {
            bmp->GetHBITMAP(Color(255, 255, 255), &hPreviewBitmap);
            delete bmp;
        }
    }
    SendMessage(hwndPreview, STM_SETIMAGE, IMAGE_BITMAP, (LPARAM)hPreviewBitmap);
}''')

# 3. RefreshAppList - ComboBox Categories
code = code.replace('SendMessage(hwndApps, LB_RESETCONTENT, 0, 0);', '''SendMessage(hwndApps, LB_RESETCONTENT, 0, 0);
    SendMessage(hwndCat, CB_RESETCONTENT, 0, 0);
    std::vector<std::string> cats;
    for (auto& app : dbCache["apps"]) {
        std::string c = app.value("category", "");
        if (std::find(cats.begin(), cats.end(), c) == cats.end() && c != "") {
            cats.push_back(c);
            SendMessage(hwndCat, CB_ADDSTRING, 0, (LPARAM)c.c_str());
        }
    }''')

# 4. LoadAppIntoForm
code = code.replace('SetWindowText(hwndStatus, "No new APK selected");', '''SetWindowText(hwndStatus, "No new APK selected");
    if (screenshots.size() > 0) UpdatePreviewImage(screenshots[0]);
    else UpdatePreviewImage("");''')

code = code.replace('SetWindowText(hwndStatus, "No APK selected");', '''SetWindowText(hwndStatus, "No APK selected");
    UpdatePreviewImage("");''')

# 5. UI Elements
code = code.replace('hwndCat = CreateWindowEx(WS_EX_CLIENTEDGE, "EDIT", "", WS_CHILD | WS_VISIBLE | WS_BORDER, 330, 160, 480, 20, hwnd, NULL, NULL, NULL);', 
                    'hwndCat = CreateWindowEx(WS_EX_CLIENTEDGE, "COMBOBOX", "", WS_CHILD | WS_VISIBLE | WS_BORDER | CBS_DROPDOWN | WS_VSCROLL, 330, 160, 480, 150, hwnd, NULL, NULL, NULL);')

code = code.replace('lstScreenshots = CreateWindowEx(WS_EX_CLIENTEDGE, "LISTBOX", NULL, WS_CHILD | WS_VISIBLE | WS_BORDER | WS_VSCROLL, 330, 320, 350, 70, hwnd, NULL, NULL, NULL);',
                    'lstScreenshots = CreateWindowEx(WS_EX_CLIENTEDGE, "LISTBOX", NULL, WS_CHILD | WS_VISIBLE | WS_BORDER | WS_VSCROLL | LBS_NOTIFY, 330, 320, 150, 70, hwnd, (HMENU)30, NULL, NULL);\n        hwndPreview = CreateWindow("STATIC", "", WS_CHILD | WS_VISIBLE | SS_BITMAP | SS_REALSIZECONTROL, 490, 320, 190, 70, hwnd, NULL, NULL, NULL);')

code = code.replace('HWND windows[] = { hwndApps, hwndName, hwndPackage, hwndVersion, hwndCat, hwndTags, hwndDesc, lstScreenshots, btnAddScreenshot, btnClearScreenshots, hwndStatus, btnBrowse, btnDelete, btnClearForm, btnApply, btnExit };',
                    'HWND windows[] = { hwndApps, hwndName, hwndPackage, hwndVersion, hwndCat, hwndTags, hwndDesc, lstScreenshots, btnAddScreenshot, btnClearScreenshots, hwndStatus, btnBrowse, btnDelete, btnClearForm, btnApply, btnExit, hwndPreview };')

# 6. lstScreenshots click handler
code = code.replace('else if (wmId == 3) {', '''else if (wmId == 30 && wmEvent == LBN_SELCHANGE) {
            int sIdx = SendMessage(lstScreenshots, LB_GETCURSEL, 0, 0);
            if (sIdx >= 0 && sIdx < screenshots.size()) UpdatePreviewImage(screenshots[sIdx]);
        }
        else if (wmId == 3) {''')

# 7. WinMain Fixes
code = code.replace('int WINAPI WinMain(HINSTANCE hInstance, HINSTANCE hPrevInstance, LPSTR lpCmdLine, int nCmdShow) {', '''int WINAPI WinMain(HINSTANCE hInstance, HINSTANCE hPrevInstance, LPSTR lpCmdLine, int nCmdShow) {
    char path[MAX_PATH];
    GetModuleFileName(NULL, path, MAX_PATH);
    fs::path exePath = path;
    fs::current_path(exePath.parent_path());

    GdiplusStartupInput gdiplusStartupInput;
    GdiplusStartup(&gdiplusToken, &gdiplusStartupInput, NULL);''')

code = code.replace('return 0;\n}', '''GdiplusShutdown(gdiplusToken);
    return 0;
}''')

with open('Manager_App/main.cpp', 'w') as f:
    f.write(code)

