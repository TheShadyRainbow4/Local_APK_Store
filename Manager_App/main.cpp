#include <windows.h>
#include <commctrl.h>
#include <string>
#include <vector>
#include <iostream>

#pragma comment(lib, "comctl32.lib")

// UI Elements
HWND hwndName, hwndPackage, hwndVersion, hwndDesc, hwndStatus;
HWND btnBrowse, btnUpload, btnAddScreenshot, lstScreenshots;
char filePath[MAX_PATH] = "";
char iconPath[MAX_PATH] = "";
std::vector<std::string> screenshots;

void ParseApkMetadata(const char* path) {
    char cmd[MAX_PATH + 50];
    sprintf_s(cmd, "python apk_parser.py \"%s\"", path);
    FILE* pipe = _popen(cmd, "r");
    if (!pipe) return;
    
    char buffer[1024];
    std::string result = "";
    while (fgets(buffer, sizeof(buffer), pipe) != NULL) {
        result += buffer;
    }
    _pclose(pipe);

    // Simple hacky JSON parsing for scaffolding since we don't have nlohmann/json included
    auto extract = [&](std::string key) -> std::string {
        std::string search = "\"" + key + "\": \"";
        size_t pos = result.find(search);
        if (pos == std::string::npos) return "";
        pos += search.length();
        size_t end = result.find("\"", pos);
        return result.substr(pos, end - pos);
    };

    std::string name = extract("name");
    std::string pkg = extract("package");
    std::string ver = extract("version");
    std::string icon = extract("icon");

    if (!name.empty()) SetWindowText(hwndName, name.c_str());
    if (!pkg.empty()) SetWindowText(hwndPackage, pkg.c_str());
    if (!ver.empty()) SetWindowText(hwndVersion, ver.c_str());
    if (!icon.empty()) strcpy_s(iconPath, icon.c_str());
}

void UploadApp(std::string apk, std::string name, std::string pkg, std::string ver, std::string desc) {
    std::string curlCmd = "curl.exe -s -X POST -F \"apk=@" + apk + "\" " +
                          "-F \"name=" + name + "\" " +
                          "-F \"package_name=" + pkg + "\" " +
                          "-F \"version=" + ver + "\" " +
                          "-F \"description=" + desc + "\" ";
    
    if (strlen(iconPath) > 0) {
        curlCmd += "-F \"icon=@" + std::string(iconPath) + "\" ";
    }

    for (const auto& s : screenshots) {
        curlCmd += "-F \"screenshots=@" + s + "\" ";
    }

    curlCmd += "http://127.0.0.1:8443/api/upload";

    // Run curl silently
    int res = system(curlCmd.c_str());
    if (res == 0) {
        MessageBox(NULL, "App Uploaded Successfully!", "Upload Status", MB_OK | MB_ICONINFORMATION);
    } else {
        MessageBox(NULL, "Upload Failed! Is the server running?", "Upload Error", MB_OK | MB_ICONERROR);
    }
}

void RunCLI(int argc, char** argv) {
    std::string apk = "", desc = "CLI Upload";
    for (int i = 1; i < argc; i++) {
        if (strcmp(argv[i], "--upload") == 0 && i + 1 < argc) apk = argv[++i];
        else if (strcmp(argv[i], "--desc") == 0 && i + 1 < argc) desc = argv[++i];
        else if (strcmp(argv[i], "--screenshot") == 0 && i + 1 < argc) screenshots.push_back(argv[++i]);
    }
    
    if (apk.empty()) {
        std::cout << "Usage: ServerManager.exe --upload <file.apk> [--desc \"description\"] [--screenshot <file.png>]\n";
        return;
    }
    
    // Parse it first
    char cmd[MAX_PATH + 50];
    sprintf_s(cmd, "python apk_parser.py \"%s\"", apk.c_str());
    FILE* pipe = _popen(cmd, "r");
    char buffer[1024];
    std::string result = "";
    if (pipe) {
        while (fgets(buffer, sizeof(buffer), pipe) != NULL) result += buffer;
        _pclose(pipe);
    }

    auto extract = [&](std::string key) -> std::string {
        std::string search = "\"" + key + "\": \"";
        size_t pos = result.find(search);
        if (pos == std::string::npos) return "";
        pos += search.length();
        size_t end = result.find("\"", pos);
        return result.substr(pos, end - pos);
    };

    std::string name = extract("name");
    std::string pkg = extract("package");
    std::string ver = extract("version");
    std::string icon = extract("icon");
    if (!icon.empty()) strcpy_s(iconPath, icon.c_str());
    
    if (name.empty()) name = "Unknown App";
    if (pkg.empty()) pkg = "com.unknown";
    if (ver.empty()) ver = "1.0";

    std::cout << "Uploading " << name << " (" << pkg << ") v" << ver << "...\n";
    UploadApp(apk, name, pkg, ver, desc);
    std::cout << "Done.\n";
}

LRESULT CALLBACK WindowProc(HWND hwnd, UINT uMsg, WPARAM wParam, LPARAM lParam) {
    switch (uMsg) {
    case WM_CREATE: {
        HFONT hFont = (HFONT)GetStockObject(DEFAULT_GUI_FONT);
        
        HWND hBanner = CreateWindow("STATIC", "Local APK Store - Server Manager",
            WS_CHILD | WS_VISIBLE | SS_CENTERIMAGE | SS_CENTER,
            0, 0, 480, 50, hwnd, NULL, NULL, NULL);
        
        CreateWindow("STATIC", "App Name:", WS_CHILD | WS_VISIBLE, 20, 70, 100, 20, hwnd, NULL, NULL, NULL);
        hwndName = CreateWindowEx(WS_EX_CLIENTEDGE, "EDIT", "", WS_CHILD | WS_VISIBLE | WS_BORDER, 130, 70, 300, 20, hwnd, NULL, NULL, NULL);

        CreateWindow("STATIC", "Package Name:", WS_CHILD | WS_VISIBLE, 20, 100, 100, 20, hwnd, NULL, NULL, NULL);
        hwndPackage = CreateWindowEx(WS_EX_CLIENTEDGE, "EDIT", "", WS_CHILD | WS_VISIBLE | WS_BORDER, 130, 100, 300, 20, hwnd, NULL, NULL, NULL);

        CreateWindow("STATIC", "Version:", WS_CHILD | WS_VISIBLE, 20, 130, 100, 20, hwnd, NULL, NULL, NULL);
        hwndVersion = CreateWindowEx(WS_EX_CLIENTEDGE, "EDIT", "", WS_CHILD | WS_VISIBLE | WS_BORDER, 130, 130, 300, 20, hwnd, NULL, NULL, NULL);

        CreateWindow("STATIC", "Description:", WS_CHILD | WS_VISIBLE, 20, 160, 100, 20, hwnd, NULL, NULL, NULL);
        hwndDesc = CreateWindowEx(WS_EX_CLIENTEDGE, "EDIT", "", WS_CHILD | WS_VISIBLE | WS_BORDER | ES_MULTILINE | ES_AUTOVSCROLL, 130, 160, 300, 60, hwnd, NULL, NULL, NULL);

        btnBrowse = CreateWindow("BUTTON", "Browse APK...", WS_CHILD | WS_VISIBLE | BS_PUSHBUTTON, 20, 240, 100, 30, hwnd, (HMENU)1, NULL, NULL);
        hwndStatus = CreateWindow("STATIC", "No APK selected", WS_CHILD | WS_VISIBLE, 130, 245, 300, 20, hwnd, NULL, NULL, NULL);

        btnAddScreenshot = CreateWindow("BUTTON", "Add Screenshot", WS_CHILD | WS_VISIBLE | BS_PUSHBUTTON, 20, 280, 120, 30, hwnd, (HMENU)3, NULL, NULL);
        lstScreenshots = CreateWindowEx(WS_EX_CLIENTEDGE, "LISTBOX", NULL, WS_CHILD | WS_VISIBLE | WS_BORDER | WS_VSCROLL, 150, 280, 280, 60, hwnd, NULL, NULL, NULL);

        btnUpload = CreateWindow("BUTTON", "Apply", WS_CHILD | WS_VISIBLE | BS_PUSHBUTTON, 330, 360, 100, 30, hwnd, (HMENU)2, NULL, NULL);

        SendMessage(hBanner, WM_SETFONT, (WPARAM)hFont, TRUE);
        SendMessage(hwndName, WM_SETFONT, (WPARAM)hFont, TRUE);
        SendMessage(hwndPackage, WM_SETFONT, (WPARAM)hFont, TRUE);
        SendMessage(hwndVersion, WM_SETFONT, (WPARAM)hFont, TRUE);
        SendMessage(hwndDesc, WM_SETFONT, (WPARAM)hFont, TRUE);
        SendMessage(btnBrowse, WM_SETFONT, (WPARAM)hFont, TRUE);
        SendMessage(hwndStatus, WM_SETFONT, (WPARAM)hFont, TRUE);
        SendMessage(btnAddScreenshot, WM_SETFONT, (WPARAM)hFont, TRUE);
        SendMessage(lstScreenshots, WM_SETFONT, (WPARAM)hFont, TRUE);
        SendMessage(btnUpload, WM_SETFONT, (WPARAM)hFont, TRUE);
        break;
    }
    case WM_COMMAND: {
        if (LOWORD(wParam) == 1) { // Browse APK
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
                ParseApkMetadata(filePath);
            }
        }
        else if (LOWORD(wParam) == 3) { // Add Screenshot
            char imgPath[MAX_PATH] = "";
            OPENFILENAME ofn;
            ZeroMemory(&ofn, sizeof(ofn));
            ofn.lStructSize = sizeof(ofn);
            ofn.hwndOwner = hwnd;
            ofn.lpstrFile = imgPath;
            ofn.lpstrFile[0] = '\0';
            ofn.nMaxFile = sizeof(imgPath);
            ofn.lpstrFilter = "Image Files\0*.png;*.jpg;*.jpeg\0All Files\0*.*\0";
            ofn.Flags = OFN_PATHMUSTEXIST | OFN_FILEMUSTEXIST;
            if (GetOpenFileName(&ofn)) {
                screenshots.push_back(imgPath);
                SendMessage(lstScreenshots, LB_ADDSTRING, 0, (LPARAM)imgPath);
            }
        }
        else if (LOWORD(wParam) == 2) { // Upload (Apply)
            if (strlen(filePath) == 0) {
                MessageBox(hwnd, "Please select an APK file first.", "Error", MB_OK | MB_ICONERROR);
                break;
            }
            char n[256], p[256], v[256], d[1024];
            GetWindowText(hwndName, n, 256);
            GetWindowText(hwndPackage, p, 256);
            GetWindowText(hwndVersion, v, 256);
            GetWindowText(hwndDesc, d, 1024);
            UploadApp(filePath, n, p, v, d);
        }
        break;
    }
    case WM_DESTROY:
        PostQuitMessage(0);
        return 0;
    }
    return DefWindowProc(hwnd, uMsg, wParam, lParam);
}

int main(int argc, char** argv) {
    if (argc > 1) {
        RunCLI(argc, argv);
        return 0;
    }

    HINSTANCE hInstance = GetModuleHandle(NULL);
    INITCOMMONCONTROLSEX icex;
    icex.dwSize = sizeof(INITCOMMONCONTROLSEX);
    icex.dwICC = ICC_WIN95_CLASSES;
    InitCommonControlsEx(&icex);

    const char* CLASS_NAME = "ServerManagerClass";
    WNDCLASS wc = { };
    wc.lpfnWndProc = WindowProc;
    wc.hInstance = hInstance;
    wc.lpszClassName = CLASS_NAME;
    wc.hbrBackground = (HBRUSH)(COLOR_BTNFACE + 1);

    RegisterClass(&wc);

    HWND hwnd = CreateWindowEx(
        0, CLASS_NAME, "EliteSoftware Server Manager",
        WS_OVERLAPPED | WS_CAPTION | WS_SYSMENU | WS_MINIMIZEBOX,
        CW_USEDEFAULT, CW_USEDEFAULT, 480, 450,
        NULL, NULL, hInstance, NULL
    );

    if (hwnd == NULL) return 0;
    ShowWindow(hwnd, SW_SHOW);

    MSG msg = { };
    while (GetMessage(&msg, NULL, 0, 0)) {
        TranslateMessage(&msg);
        DispatchMessage(&msg);
    }
    return 0;
}
