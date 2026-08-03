#define _WIN32_WINNT 0x0A00
#include <winsock2.h>
#include <windows.h>
#include <commctrl.h>
#include <string>
#include <vector>
#include <iostream>
#include <thread>
#include <fstream>
#include <filesystem>
#include "httplib.h"
#include "json.hpp"

#pragma comment(lib, "comctl32.lib")
#pragma comment(lib, "ws2_32.lib")

using json = nlohmann::json;
namespace fs = std::filesystem;

// UI Elements
HWND hwndApps, hwndName, hwndPackage, hwndVersion, hwndDesc, hwndCat, hwndTags, hwndStatus;
HWND btnBrowse, btnApply, btnExit, btnDelete, btnClearForm;
HWND btnAddScreenshot, btnClearScreenshots, lstScreenshots;
char filePath[MAX_PATH] = "";
std::vector<std::string> screenshots;
json dbCache;
int selectedAppIndex = -1;

std::string dbFile = "db.json";
std::string apkDir = "apks";
std::string imgDir = "images";

json loadDb() {
    if (!fs::exists(dbFile)) {
        json j;
        j["apps"] = json::array();
        return j;
    }
    std::ifstream i(dbFile);
    json j;
    try {
        i >> j;
    } catch (...) {
        j["apps"] = json::array();
    }
    return j;
}

void saveDb(const json& j) {
    std::ofstream o(dbFile);
    o << j.dump(4);
    dbCache = j;
}

void RefreshAppList() {
    dbCache = loadDb();
    SendMessage(hwndApps, LB_RESETCONTENT, 0, 0);
    for (size_t i = 0; i < dbCache["apps"].size(); i++) {
        std::string name = dbCache["apps"][i].value("name", "Unknown");
        std::string pkg = dbCache["apps"][i].value("package_name", "unknown.pkg");
        std::string display = name + " (" + pkg + ")";
        SendMessage(hwndApps, LB_ADDSTRING, 0, (LPARAM)display.c_str());
    }
}

void LoadAppIntoForm(int index) {
    if (index < 0 || index >= dbCache["apps"].size()) return;
    auto& app = dbCache["apps"][index];
    
    SetWindowText(hwndName, app.value("name", "").c_str());
    SetWindowText(hwndPackage, app.value("package_name", "").c_str());
    
    if (app.contains("versions") && app["versions"].size() > 0) {
        SetWindowText(hwndVersion, app["versions"].back().value("version", "").c_str());
    } else {
        SetWindowText(hwndVersion, "");
    }
    
    SetWindowText(hwndCat, app.value("category", "").c_str());
    SetWindowText(hwndDesc, app.value("description", "").c_str());
    
    std::string tagsStr = "";
    if (app.contains("tags")) {
        for (size_t i = 0; i < app["tags"].size(); i++) {
            tagsStr += app["tags"][i].get<std::string>();
            if (i < app["tags"].size() - 1) tagsStr += ", ";
        }
    }
    SetWindowText(hwndTags, tagsStr.c_str());
    
    SendMessage(lstScreenshots, LB_RESETCONTENT, 0, 0);
    screenshots.clear();
    if (app.contains("screenshots")) {
        for (auto& s : app["screenshots"]) {
            std::string sPath = imgDir + "\\" + s.get<std::string>();
            screenshots.push_back(sPath);
            SendMessage(lstScreenshots, LB_ADDSTRING, 0, (LPARAM)s.get<std::string>().c_str());
        }
    }
    
    filePath[0] = '\0';
    SetWindowText(hwndStatus, "No new APK selected (Editing Metadata)");
}

void ClearForm() {
    selectedAppIndex = -1;
    SendMessage(hwndApps, LB_SETCURSEL, (WPARAM)-1, 0);
    SetWindowText(hwndName, "");
    SetWindowText(hwndPackage, "");
    SetWindowText(hwndVersion, "");
    SetWindowText(hwndCat, "");
    SetWindowText(hwndDesc, "");
    SetWindowText(hwndTags, "");
    SendMessage(lstScreenshots, LB_RESETCONTENT, 0, 0);
    screenshots.clear();
    filePath[0] = '\0';
    SetWindowText(hwndStatus, "No APK selected");
}

void DeleteSelectedApp() {
    if (selectedAppIndex >= 0 && selectedAppIndex < dbCache["apps"].size()) {
        int res = MessageBox(NULL, "Are you sure you want to completely delete this app and all its versions from the store?", "Confirm Delete", MB_YESNO | MB_ICONWARNING);
        if (res == IDYES) {
            dbCache["apps"].erase(dbCache["apps"].begin() + selectedAppIndex);
            saveDb(dbCache);
            ClearForm();
            RefreshAppList();
        }
    } else {
        MessageBox(NULL, "Please select an app to delete.", "Error", MB_OK | MB_ICONERROR);
    }
}

void ServerThread() {
    httplib::Server svr;

    svr.Get("/api/apps", [](const httplib::Request& req, httplib::Response& res) {
        json db = loadDb();
        if (req.has_param("q")) {
            std::string q = req.get_param_value("q");
            std::transform(q.begin(), q.end(), q.begin(), ::tolower);
            json filtered = json::array();
            for (auto& app : db["apps"]) {
                std::string n = app.value("name", "");
                std::transform(n.begin(), n.end(), n.begin(), ::tolower);
                if (n.find(q) != std::string::npos) {
                    filtered.push_back(app);
                }
            }
            json out; out["apps"] = filtered;
            res.set_content(out.dump(), "application/json");
        } else {
            res.set_content(db.dump(), "application/json");
        }
    });

    svr.set_mount_point("/apks", apkDir.c_str());
    svr.set_mount_point("/images", imgDir.c_str());

    svr.Post(R"(/api/apps/(.*)/reviews)", [](const httplib::Request& req, httplib::Response& res) {
        std::string pkg = req.matches[1];
        json reqJson;
        try {
            reqJson = json::parse(req.body);
        } catch(...) {
            res.status = 400; return;
        }
        
        json db = loadDb();
        bool found = false;
        for (auto& app : db["apps"]) {
            if (app["package_name"] == pkg) {
                json review;
                review["user"] = reqJson.value("user", "Anonymous");
                review["rating"] = reqJson.value("rating", 5);
                review["comment"] = reqJson.value("comment", "");
                if (!app.contains("reviews")) app["reviews"] = json::array();
                app["reviews"].push_back(review);
                found = true;
                break;
            }
        }
        if (found) {
            saveDb(db);
            res.set_content("{\"status\":\"success\"}", "application/json");
        } else {
            res.status = 404;
        }
    });

    svr.listen("0.0.0.0", 8443);
}

void CopyFileLocal(std::string src, std::string dest) {
    try {
        fs::copy_file(src, dest, fs::copy_options::overwrite_existing);
    } catch (...) {}
}

void ProcessApp(std::string apk, std::string name, std::string pkg, std::string ver, std::string desc, std::string cat, std::string tagsStr) {
    fs::create_directory(apkDir);
    fs::create_directory(imgDir);

    std::string apkName = "";
    if (!apk.empty()) {
        apkName = fs::path(apk).filename().string();
        CopyFileLocal(apk, apkDir + "/" + apkName);
    }

    std::vector<std::string> copiedScreenshots;
    for (const auto& s : screenshots) {
        std::string sName = fs::path(s).filename().string();
        if (fs::exists(s) && s.find(imgDir) == std::string::npos) {
            CopyFileLocal(s, imgDir + "/" + sName);
        }
        copiedScreenshots.push_back(sName);
    }

    std::vector<std::string> tags;
    size_t pos = 0;
    std::string tCopy = tagsStr;
    while ((pos = tCopy.find(",")) != std::string::npos) {
        std::string token = tCopy.substr(0, pos);
        while(token.size() && token[0]==' ') token.erase(0,1);
        while(token.size() && token.back()==' ') token.pop_back();
        if(!token.empty()) tags.push_back(token);
        tCopy.erase(0, pos + 1);
    }
    while(tCopy.size() && tCopy[0]==' ') tCopy.erase(0,1);
    while(tCopy.size() && tCopy.back()==' ') tCopy.pop_back();
    if(!tCopy.empty()) tags.push_back(tCopy);

    json db = loadDb();
    bool exists = false;
    for (auto& app : db["apps"]) {
        if (app["package_name"] == pkg) {
            exists = true;
            if (!apkName.empty()) {
                bool vExists = false;
                for (auto& v : app["versions"]) {
                    if (v["version"] == ver) {
                        vExists = true;
                        v["file"] = apkName; // overwrite file if same version
                    }
                }
                if (!vExists) {
                    app["versions"].push_back({{"version", ver}, {"file", apkName}});
                }
            }
            app["name"] = name;
            app["description"] = desc;
            app["category"] = cat;
            app["tags"] = tags;
            app["screenshots"] = copiedScreenshots;
            break;
        }
    }

    if (!exists) {
        if (apkName.empty()) {
            MessageBox(NULL, "You must provide an APK file for a new app!", "Error", MB_OK | MB_ICONERROR);
            return;
        }
        json newApp;
        newApp["name"] = name;
        newApp["package_name"] = pkg;
        newApp["description"] = desc;
        newApp["category"] = cat;
        newApp["tags"] = tags;
        newApp["versions"] = json::array();
        newApp["versions"].push_back({{"version", ver}, {"file", apkName}});
        newApp["screenshots"] = copiedScreenshots;
        newApp["reviews"] = json::array();
        db["apps"].push_back(newApp);
    }
    saveDb(db);
    RefreshAppList();
    MessageBox(NULL, "App Processed & Applied to Store!", "Success", MB_OK | MB_ICONINFORMATION);
}

LRESULT CALLBACK WindowProc(HWND hwnd, UINT uMsg, WPARAM wParam, LPARAM lParam) {
    switch (uMsg) {
    case WM_CREATE: {
        HFONT hFont = (HFONT)GetStockObject(DEFAULT_GUI_FONT);
        HFONT hFontBold = CreateFont(16, 0, 0, 0, FW_BOLD, FALSE, FALSE, FALSE, DEFAULT_CHARSET, OUT_DEFAULT_PRECIS, CLIP_DEFAULT_PRECIS, DEFAULT_QUALITY, DEFAULT_PITCH | FF_SWISS, "Segoe UI");
        
        // Title Banner
        HWND hBannerIcon = CreateWindow("STATIC", "", WS_CHILD | WS_VISIBLE | SS_ICON, 10, 4, 32, 32, hwnd, NULL, (HINSTANCE)GetWindowLongPtr(hwnd, GWLP_HINSTANCE), NULL);
        SendMessage(hBannerIcon, STM_SETICON, (WPARAM)LoadIcon((HINSTANCE)GetWindowLongPtr(hwnd, GWLP_HINSTANCE), MAKEINTRESOURCE(101)), 0);
        HWND hBanner = CreateWindow("STATIC", "        Elite App Marketplace - Store Manager", WS_CHILD | WS_VISIBLE | SS_CENTERIMAGE, 0, 0, 850, 40, hwnd, NULL, NULL, NULL);
        SendMessage(hBanner, WM_SETFONT, (WPARAM)hFontBold, TRUE);

        // Separator below banner
        CreateWindowEx(0, "STATIC", "", WS_CHILD | WS_VISIBLE | SS_ETCHEDHORZ, 0, 40, 850, 2, hwnd, NULL, NULL, NULL);

        // Left ListBox for existing apps
        CreateWindow("STATIC", "Store Inventory:", WS_CHILD | WS_VISIBLE, 15, 50, 200, 20, hwnd, NULL, NULL, NULL);
        hwndApps = CreateWindowEx(WS_EX_CLIENTEDGE, "LISTBOX", NULL, WS_CHILD | WS_VISIBLE | WS_BORDER | WS_VSCROLL | LBS_NOTIFY, 15, 70, 200, 390, hwnd, (HMENU)10, NULL, NULL);

        // Right side form
        CreateWindow("STATIC", "App Name:", WS_CHILD | WS_VISIBLE, 230, 70, 90, 20, hwnd, NULL, NULL, NULL);
        hwndName = CreateWindowEx(WS_EX_CLIENTEDGE, "EDIT", "", WS_CHILD | WS_VISIBLE | WS_BORDER, 330, 70, 480, 20, hwnd, NULL, NULL, NULL);

        CreateWindow("STATIC", "Package:", WS_CHILD | WS_VISIBLE, 230, 100, 90, 20, hwnd, NULL, NULL, NULL);
        hwndPackage = CreateWindowEx(WS_EX_CLIENTEDGE, "EDIT", "", WS_CHILD | WS_VISIBLE | WS_BORDER, 330, 100, 480, 20, hwnd, NULL, NULL, NULL);

        CreateWindow("STATIC", "Version:", WS_CHILD | WS_VISIBLE, 230, 130, 90, 20, hwnd, NULL, NULL, NULL);
        hwndVersion = CreateWindowEx(WS_EX_CLIENTEDGE, "EDIT", "", WS_CHILD | WS_VISIBLE | WS_BORDER, 330, 130, 480, 20, hwnd, NULL, NULL, NULL);

        CreateWindow("STATIC", "Category:", WS_CHILD | WS_VISIBLE, 230, 160, 90, 20, hwnd, NULL, NULL, NULL);
        hwndCat = CreateWindowEx(WS_EX_CLIENTEDGE, "EDIT", "", WS_CHILD | WS_VISIBLE | WS_BORDER, 330, 160, 480, 20, hwnd, NULL, NULL, NULL);

        CreateWindow("STATIC", "Tags (CSV):", WS_CHILD | WS_VISIBLE, 230, 190, 90, 20, hwnd, NULL, NULL, NULL);
        hwndTags = CreateWindowEx(WS_EX_CLIENTEDGE, "EDIT", "", WS_CHILD | WS_VISIBLE | WS_BORDER, 330, 190, 480, 20, hwnd, NULL, NULL, NULL);

        CreateWindow("STATIC", "Description:", WS_CHILD | WS_VISIBLE, 230, 220, 90, 20, hwnd, NULL, NULL, NULL);
        hwndDesc = CreateWindowEx(WS_EX_CLIENTEDGE, "EDIT", "", WS_CHILD | WS_VISIBLE | WS_BORDER | ES_MULTILINE | ES_AUTOVSCROLL | WS_VSCROLL, 330, 220, 480, 90, hwnd, NULL, NULL, NULL);

        CreateWindow("STATIC", "Screenshots:", WS_CHILD | WS_VISIBLE, 230, 320, 90, 20, hwnd, NULL, NULL, NULL);
        lstScreenshots = CreateWindowEx(WS_EX_CLIENTEDGE, "LISTBOX", NULL, WS_CHILD | WS_VISIBLE | WS_BORDER | WS_VSCROLL, 330, 320, 350, 70, hwnd, NULL, NULL, NULL);
        btnAddScreenshot = CreateWindow("BUTTON", "Add", WS_CHILD | WS_VISIBLE | BS_PUSHBUTTON, 690, 320, 120, 30, hwnd, (HMENU)3, NULL, NULL);
        btnClearScreenshots = CreateWindow("BUTTON", "Clear All", WS_CHILD | WS_VISIBLE | BS_PUSHBUTTON, 690, 360, 120, 30, hwnd, (HMENU)4, NULL, NULL);

        CreateWindow("STATIC", "APK File:", WS_CHILD | WS_VISIBLE, 230, 410, 90, 20, hwnd, NULL, NULL, NULL);
        hwndStatus = CreateWindowEx(WS_EX_CLIENTEDGE, "STATIC", " No APK selected", WS_CHILD | WS_VISIBLE | SS_LEFT, 330, 410, 350, 22, hwnd, NULL, NULL, NULL);
        btnBrowse = CreateWindow("BUTTON", "Browse APK...", WS_CHILD | WS_VISIBLE | BS_PUSHBUTTON, 690, 405, 120, 30, hwnd, (HMENU)1, NULL, NULL);

        btnDelete = CreateWindow("BUTTON", "Delete Selected", WS_CHILD | WS_VISIBLE | BS_PUSHBUTTON, 230, 450, 130, 30, hwnd, (HMENU)6, NULL, NULL);
        btnClearForm = CreateWindow("BUTTON", "New App", WS_CHILD | WS_VISIBLE | BS_PUSHBUTTON, 370, 450, 130, 30, hwnd, (HMENU)5, NULL, NULL);

        // Chin separator
        CreateWindowEx(0, "STATIC", "", WS_CHILD | WS_VISIBLE | SS_ETCHEDHORZ, 0, 500, 850, 2, hwnd, NULL, NULL, NULL);
        
        // Chin background (simulated using standard controls)
        btnApply = CreateWindow("BUTTON", "Apply", WS_CHILD | WS_VISIBLE | BS_PUSHBUTTON, 590, 515, 100, 30, hwnd, (HMENU)2, NULL, NULL);
        btnExit = CreateWindow("BUTTON", "Exit", WS_CHILD | WS_VISIBLE | BS_PUSHBUTTON, 710, 515, 100, 30, hwnd, (HMENU)7, NULL, NULL);

        // Set Fonts
        HWND windows[] = { hwndApps, hwndName, hwndPackage, hwndVersion, hwndCat, hwndTags, hwndDesc, lstScreenshots, btnAddScreenshot, btnClearScreenshots, hwndStatus, btnBrowse, btnDelete, btnClearForm, btnApply, btnExit };
        for (HWND w : windows) {
            SendMessage(w, WM_SETFONT, (WPARAM)hFont, TRUE);
        }

        RefreshAppList();
        break;
    }
    case WM_COMMAND: {
        int wmId = LOWORD(wParam);
        int wmEvent = HIWORD(wParam);
        
        if (wmId == 10 && wmEvent == LBN_SELCHANGE) {
            selectedAppIndex = SendMessage(hwndApps, LB_GETCURSEL, 0, 0);
            LoadAppIntoForm(selectedAppIndex);
        }
        else if (wmId == 1) { // Browse APK
            OPENFILENAME ofn;
            ZeroMemory(&ofn, sizeof(ofn));
            ofn.lStructSize = sizeof(ofn);
            ofn.hwndOwner = hwnd;
            ofn.lpstrFile = filePath;
            ofn.lpstrFile[0] = '\0';
            ofn.nMaxFile = sizeof(filePath);
            ofn.lpstrFilter = "APK Files\0*.apk\0All Files\0*.*\0";
            ofn.Flags = OFN_PATHMUSTEXIST | OFN_FILEMUSTEXIST;
            if (GetOpenFileName(&ofn)) {
                SetWindowText(hwndStatus, filePath);
            }
        }
        else if (wmId == 3) { // Add Screenshot
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
                SendMessage(lstScreenshots, LB_ADDSTRING, 0, (LPARAM)fs::path(imgPath).filename().string().c_str());
            }
        }
        else if (wmId == 4) { // Clear Screenshots
            screenshots.clear();
            SendMessage(lstScreenshots, LB_RESETCONTENT, 0, 0);
        }
        else if (wmId == 5) { // New App
            ClearForm();
        }
        else if (wmId == 6) { // Delete
            DeleteSelectedApp();
        }
        else if (wmId == 7) { // Exit
            PostQuitMessage(0);
        }
        else if (wmId == 2) { // Apply
            char n[256], p[256], v[256], d[4096], c[256], t[512];
            GetWindowText(hwndName, n, 256);
            GetWindowText(hwndPackage, p, 256);
            GetWindowText(hwndVersion, v, 256);
            GetWindowText(hwndDesc, d, 4096);
            GetWindowText(hwndCat, c, 256);
            GetWindowText(hwndTags, t, 512);
            
            if (strlen(n) == 0 || strlen(p) == 0 || strlen(v) == 0) {
                MessageBox(hwnd, "Name, Package, and Version are required.", "Validation Error", MB_OK | MB_ICONERROR);
                break;
            }
            ProcessApp(filePath, n, p, v, d, c, t);
        }
        break;
    }
    case WM_CTLCOLORSTATIC: {
        HDC hdcStatic = (HDC)wParam;
        HWND hwndStatic = (HWND)lParam;
        // Make the chin and background look native grey instead of white
        SetBkColor(hdcStatic, GetSysColor(COLOR_BTNFACE));
        return (INT_PTR)GetSysColorBrush(COLOR_BTNFACE);
    }
    case WM_DESTROY:
        PostQuitMessage(0);
        return 0;
    }
    return DefWindowProc(hwnd, uMsg, wParam, lParam);
}

int WINAPI WinMain(HINSTANCE hInstance, HINSTANCE hPrevInstance, LPSTR lpCmdLine, int nCmdShow) {
    std::thread serverThread(ServerThread);
    serverThread.detach();

    INITCOMMONCONTROLSEX icex;
    icex.dwSize = sizeof(INITCOMMONCONTROLSEX);
    icex.dwICC = ICC_WIN95_CLASSES | ICC_STANDARD_CLASSES;
    InitCommonControlsEx(&icex);

    const char* CLASS_NAME = "EliteAppMarketplaceServer";
    WNDCLASS wc = { };
    wc.lpfnWndProc = WindowProc;
    wc.hInstance = hInstance;
    wc.lpszClassName = CLASS_NAME;
    wc.hbrBackground = (HBRUSH)(COLOR_BTNFACE + 1);
    wc.hIcon = LoadIcon(hInstance, MAKEINTRESOURCE(101));

    RegisterClass(&wc);

    HWND hwnd = CreateWindowEx(
        0, CLASS_NAME, "Elite App Marketplace - Server & Manager",
        WS_OVERLAPPED | WS_CAPTION | WS_SYSMENU | WS_MINIMIZEBOX,
        CW_USEDEFAULT, CW_USEDEFAULT, 850, 600,
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
