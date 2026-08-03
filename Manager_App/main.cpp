#include <windows.h>
#include <commctrl.h>
#include <string>

#pragma comment(lib, "comctl32.lib")

// UI Elements
HWND hwndName, hwndPackage, hwndVersion, hwndDesc, hwndStatus;
HWND btnBrowse, btnUpload;
char filePath[MAX_PATH] = "";

LRESULT CALLBACK WindowProc(HWND hwnd, UINT uMsg, WPARAM wParam, LPARAM lParam) {
    switch (uMsg) {
    case WM_CREATE: {
        // Apply System Font
        HFONT hFont = (HFONT)GetStockObject(DEFAULT_GUI_FONT);
        
        // Title Banner (Fake Banner for legacy aesthetic)
        HWND hBanner = CreateWindow("STATIC", "Local APK Store - Server Manager",
            WS_CHILD | WS_VISIBLE | SS_CENTERIMAGE | SS_CENTER,
            0, 0, 480, 50, hwnd, NULL, NULL, NULL);
        SendMessage(hBanner, WM_SETFONT, (WPARAM)hFont, TRUE);

        // Name
        CreateWindow("STATIC", "App Name:", WS_CHILD | WS_VISIBLE, 20, 70, 100, 20, hwnd, NULL, NULL, NULL);
        hwndName = CreateWindowEx(WS_EX_CLIENTEDGE, "EDIT", "", WS_CHILD | WS_VISIBLE | WS_BORDER, 130, 70, 300, 20, hwnd, NULL, NULL, NULL);

        // Package
        CreateWindow("STATIC", "Package Name:", WS_CHILD | WS_VISIBLE, 20, 100, 100, 20, hwnd, NULL, NULL, NULL);
        hwndPackage = CreateWindowEx(WS_EX_CLIENTEDGE, "EDIT", "com.example.app", WS_CHILD | WS_VISIBLE | WS_BORDER, 130, 100, 300, 20, hwnd, NULL, NULL, NULL);

        // Version
        CreateWindow("STATIC", "Version:", WS_CHILD | WS_VISIBLE, 20, 130, 100, 20, hwnd, NULL, NULL, NULL);
        hwndVersion = CreateWindowEx(WS_EX_CLIENTEDGE, "EDIT", "1.0", WS_CHILD | WS_VISIBLE | WS_BORDER, 130, 130, 300, 20, hwnd, NULL, NULL, NULL);

        // Description
        CreateWindow("STATIC", "Description:", WS_CHILD | WS_VISIBLE, 20, 160, 100, 20, hwnd, NULL, NULL, NULL);
        hwndDesc = CreateWindowEx(WS_EX_CLIENTEDGE, "EDIT", "", WS_CHILD | WS_VISIBLE | WS_BORDER | ES_MULTILINE | ES_AUTOVSCROLL, 130, 160, 300, 60, hwnd, NULL, NULL, NULL);

        // APK Select
        btnBrowse = CreateWindow("BUTTON", "Browse APK...", WS_CHILD | WS_VISIBLE | BS_PUSHBUTTON, 20, 240, 100, 30, hwnd, (HMENU)1, NULL, NULL);
        hwndStatus = CreateWindow("STATIC", "No APK selected", WS_CHILD | WS_VISIBLE, 130, 245, 300, 20, hwnd, NULL, NULL, NULL);

        // Chin / bottom area
        btnUpload = CreateWindow("BUTTON", "Apply", WS_CHILD | WS_VISIBLE | BS_PUSHBUTTON, 330, 300, 100, 30, hwnd, (HMENU)2, NULL, NULL);

        // Set Fonts
        SendMessage(hwndName, WM_SETFONT, (WPARAM)hFont, TRUE);
        SendMessage(hwndPackage, WM_SETFONT, (WPARAM)hFont, TRUE);
        SendMessage(hwndVersion, WM_SETFONT, (WPARAM)hFont, TRUE);
        SendMessage(hwndDesc, WM_SETFONT, (WPARAM)hFont, TRUE);
        SendMessage(btnBrowse, WM_SETFONT, (WPARAM)hFont, TRUE);
        SendMessage(hwndStatus, WM_SETFONT, (WPARAM)hFont, TRUE);
        SendMessage(btnUpload, WM_SETFONT, (WPARAM)hFont, TRUE);
        break;
    }
    case WM_COMMAND: {
        if (LOWORD(wParam) == 1) { // Browse
            OPENFILENAME ofn;
            ZeroMemory(&ofn, sizeof(ofn));
            ofn.lStructSize = sizeof(ofn);
            ofn.hwndOwner = hwnd;
            ofn.lpstrFile = filePath;
            ofn.lpstrFile[0] = '\0';
            ofn.nMaxFile = sizeof(filePath);
            ofn.lpstrFilter = "APK Files\0*.apk\0All Files\0*.*\0";
            ofn.nFilterIndex = 1;
            ofn.Flags = OFN_PATHMUSTEXIST | OFN_FILEMUSTEXIST;
            if (GetOpenFileName(&ofn)) {
                SetWindowText(hwndStatus, filePath);
            }
        }
        else if (LOWORD(wParam) == 2) { // Upload (Apply)
            // Implementation of HTTP POST upload to python server (127.0.0.1:8443) would go here.
            // Using libcurl or WinINet. For scaffolding, display a message.
            MessageBox(hwnd, "APK metadata prepared for upload (Network upload not fully implemented in stub).", "Upload Status", MB_OK | MB_ICONINFORMATION);
        }
        break;
    }
    case WM_DESTROY:
        PostQuitMessage(0);
        return 0;
    }
    return DefWindowProc(hwnd, uMsg, wParam, lParam);
}

int WINAPI WinMain(HINSTANCE hInstance, HINSTANCE hPrevInstance, LPSTR lpCmdLine, int nCmdShow) {
    INITCOMMONCONTROLSEX icex;
    icex.dwSize = sizeof(INITCOMMONCONTROLSEX);
    icex.dwICC = ICC_WIN95_CLASSES;
    InitCommonControlsEx(&icex);

    const char* CLASS_NAME = "ServerManagerClass";
    WNDCLASS wc = { };
    wc.lpfnWndProc = WindowProc;
    wc.hInstance = hInstance;
    wc.lpszClassName = CLASS_NAME;
    wc.hbrBackground = (HBRUSH)(COLOR_BTNFACE + 1); // Native legacy aesthetic

    RegisterClass(&wc);

    HWND hwnd = CreateWindowEx(
        0, CLASS_NAME, "EliteSoftware Server Manager",
        WS_OVERLAPPED | WS_CAPTION | WS_SYSMENU | WS_MINIMIZEBOX, // Strict frame, not fully resizable to maintain layout
        CW_USEDEFAULT, CW_USEDEFAULT, 480, 390,
        NULL, NULL, hInstance, NULL
    );

    if (hwnd == NULL) return 0;

    ShowWindow(hwnd, nCmdShow);

    MSG msg = { };
    while (GetMessage(&msg, NULL, 0, 0)) {
        TranslateMessage(&msg);
        DispatchMessage(&msg);
    }

    return 0;
}
