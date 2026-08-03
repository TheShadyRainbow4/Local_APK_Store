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
HWND hwndName, hwndPackage, hwndVersion, hwndDesc, hwndCat, hwndTags, hwndStatus;
HWND btnBrowse, btnUpload, btnAddScreenshot, lstScreenshots;
char filePath[MAX_PATH] = "";
std::vector<std::string> screenshots;

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
}

void ServerThread() {
    httplib::Server svr;

    svr.Get("/api/apps", [](const httplib::Request& req, httplib::Response& res) {
        json db = loadDb();
        if (req.has_param("q")) {
            std::string q = req.get_param_value("q");
            // Basic lowercase search
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

    // We can mount the static directories
    svr.set_mount_point("/apks", apkDir.c_str());
    svr.set_mount_point("/images", imgDir.c_str());

    // API to post review
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

    std::string apkName = fs::path(apk).filename().string();
    CopyFileLocal(apk, apkDir + "/" + apkName);

    std::vector<std::string> copiedScreenshots;
    for (const auto& s : screenshots) {
        std::string sName = fs::path(s).filename().string();
        CopyFileLocal(s, imgDir + "/" + sName);
        copiedScreenshots.push_back(sName);
    }

    // Split tags by comma
    std::vector<std::string> tags;
    size_t pos = 0;
    while ((pos = tagsStr.find(",")) != std::string::npos) {
        std::string token = tagsStr.substr(0, pos);
        if(!token.empty()) tags.push_back(token);
        tagsStr.erase(0, pos + 1);
    }
    if(!tagsStr.empty()) tags.push_back(tagsStr);

    json db = loadDb();
    bool exists = false;
    for (auto& app : db["apps"]) {
        if (app["package_name"] == pkg) {
            exists = true;
            bool vExists = false;
            for (auto& v : app["versions"]) {
                if (v["version"] == ver) vExists = true;
            }
            if (!vExists) {
                app["versions"].push_back({{"version", ver}, {"file", apkName}});
            }
            app["description"] = desc;
            app["category"] = cat;
            if (app.contains("tags")) {
                for (auto t : tags) app["tags"].push_back(t);
            } else {
                app["tags"] = tags;
            }
            for (auto sc : copiedScreenshots) {
                app["screenshots"].push_back(sc);
            }
            break;
        }
    }

    if (!exists) {
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
    MessageBox(NULL, "App Processed & Added to Database!", "Success", MB_OK | MB_ICONINFORMATION);
}

LRESULT CALLBACK WindowProc(HWND hwnd, UINT uMsg, WPARAM wParam, LPARAM lParam) {
    switch (uMsg) {
    case WM_CREATE: {
        HFONT hFont = (HFONT)GetStockObject(DEFAULT_GUI_FONT);
        HWND hBanner = CreateWindow("STATIC", "Elite App Marketplace - Server & Manager", WS_CHILD | WS_VISIBLE | SS_CENTERIMAGE | SS_CENTER, 0, 0, 480, 50, hwnd, NULL, NULL, NULL);
        
        CreateWindow("STATIC", "App Name:", WS_CHILD | WS_VISIBLE, 20, 70, 100, 20, hwnd, NULL, NULL, NULL);
        hwndName = CreateWindowEx(WS_EX_CLIENTEDGE, "EDIT", "", WS_CHILD | WS_VISIBLE | WS_BORDER, 130, 70, 300, 20, hwnd, NULL, NULL, NULL);

        CreateWindow("STATIC", "Package:", WS_CHILD | WS_VISIBLE, 20, 100, 100, 20, hwnd, NULL, NULL, NULL);
        hwndPackage = CreateWindowEx(WS_EX_CLIENTEDGE, "EDIT", "com.elite.", WS_CHILD | WS_VISIBLE | WS_BORDER, 130, 100, 300, 20, hwnd, NULL, NULL, NULL);

        CreateWindow("STATIC", "Version:", WS_CHILD | WS_VISIBLE, 20, 130, 100, 20, hwnd, NULL, NULL, NULL);
        hwndVersion = CreateWindowEx(WS_EX_CLIENTEDGE, "EDIT", "1.0", WS_CHILD | WS_VISIBLE | WS_BORDER, 130, 130, 300, 20, hwnd, NULL, NULL, NULL);

        CreateWindow("STATIC", "Category:", WS_CHILD | WS_VISIBLE, 20, 160, 100, 20, hwnd, NULL, NULL, NULL);
        hwndCat = CreateWindowEx(WS_EX_CLIENTEDGE, "EDIT", "Apps", WS_CHILD | WS_VISIBLE | WS_BORDER, 130, 160, 300, 20, hwnd, NULL, NULL, NULL);

        CreateWindow("STATIC", "Tags (comma):", WS_CHILD | WS_VISIBLE, 20, 190, 100, 20, hwnd, NULL, NULL, NULL);
        hwndTags = CreateWindowEx(WS_EX_CLIENTEDGE, "EDIT", "", WS_CHILD | WS_VISIBLE | WS_BORDER, 130, 190, 300, 20, hwnd, NULL, NULL, NULL);

        CreateWindow("STATIC", "Description:", WS_CHILD | WS_VISIBLE, 20, 220, 100, 20, hwnd, NULL, NULL, NULL);
        hwndDesc = CreateWindowEx(WS_EX_CLIENTEDGE, "EDIT", "", WS_CHILD | WS_VISIBLE | WS_BORDER | ES_MULTILINE | ES_AUTOVSCROLL, 130, 220, 300, 60, hwnd, NULL, NULL, NULL);

        btnBrowse = CreateWindow("BUTTON", "Browse APK...", WS_CHILD | WS_VISIBLE | BS_PUSHBUTTON, 20, 290, 100, 30, hwnd, (HMENU)1, NULL, NULL);
        hwndStatus = CreateWindow("STATIC", "No APK selected", WS_CHILD | WS_VISIBLE, 130, 295, 300, 20, hwnd, NULL, NULL, NULL);

        btnAddScreenshot = CreateWindow("BUTTON", "Add Screenshot", WS_CHILD | WS_VISIBLE | BS_PUSHBUTTON, 20, 330, 120, 30, hwnd, (HMENU)3, NULL, NULL);
        lstScreenshots = CreateWindowEx(WS_EX_CLIENTEDGE, "LISTBOX", NULL, WS_CHILD | WS_VISIBLE | WS_BORDER | WS_VSCROLL, 150, 330, 280, 60, hwnd, NULL, NULL, NULL);

        btnUpload = CreateWindow("BUTTON", "Apply", WS_CHILD | WS_VISIBLE | BS_PUSHBUTTON, 330, 410, 100, 30, hwnd, (HMENU)2, NULL, NULL);

        SendMessage(hBanner, WM_SETFONT, (WPARAM)hFont, TRUE);
        SendMessage(hwndName, WM_SETFONT, (WPARAM)hFont, TRUE);
        SendMessage(hwndPackage, WM_SETFONT, (WPARAM)hFont, TRUE);
        SendMessage(hwndVersion, WM_SETFONT, (WPARAM)hFont, TRUE);
        SendMessage(hwndCat, WM_SETFONT, (WPARAM)hFont, TRUE);
        SendMessage(hwndTags, WM_SETFONT, (WPARAM)hFont, TRUE);
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
            ofn.Flags = OFN_PATHMUSTEXIST | OFN_FILEMUSTEXIST;
            if (GetOpenFileName(&ofn)) {
                SetWindowText(hwndStatus, filePath);
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
        else if (LOWORD(wParam) == 2) { // Apply
            if (strlen(filePath) == 0) {
                MessageBox(hwnd, "Please select an APK file first.", "Error", MB_OK | MB_ICONERROR);
                break;
            }
            char n[256], p[256], v[256], d[1024], c[256], t[256];
            GetWindowText(hwndName, n, 256);
            GetWindowText(hwndPackage, p, 256);
            GetWindowText(hwndVersion, v, 256);
            GetWindowText(hwndDesc, d, 1024);
            GetWindowText(hwndCat, c, 256);
            GetWindowText(hwndTags, t, 256);
            ProcessApp(filePath, n, p, v, d, c, t);
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
    // Start HTTP Server in background thread
    std::thread serverThread(ServerThread);
    serverThread.detach();

    INITCOMMONCONTROLSEX icex;
    icex.dwSize = sizeof(INITCOMMONCONTROLSEX);
    icex.dwICC = ICC_WIN95_CLASSES;
    InitCommonControlsEx(&icex);

    const char* CLASS_NAME = "EliteAppMarketplaceServer";
    WNDCLASS wc = { };
    wc.lpfnWndProc = WindowProc;
    wc.hInstance = hInstance;
    wc.lpszClassName = CLASS_NAME;
    wc.hbrBackground = (HBRUSH)(COLOR_BTNFACE + 1);

    RegisterClass(&wc);

    HWND hwnd = CreateWindowEx(
        0, CLASS_NAME, "Elite App Marketplace - Server",
        WS_OVERLAPPED | WS_CAPTION | WS_SYSMENU | WS_MINIMIZEBOX,
        CW_USEDEFAULT, CW_USEDEFAULT, 480, 500,
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
