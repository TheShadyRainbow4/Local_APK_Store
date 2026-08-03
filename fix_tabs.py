import os

cpp_code = '''
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
#include <algorithm>
#include "httplib.h"
#include "json.hpp"
#include <gdiplus.h>

#pragma comment(linker,"\\"/manifestdependency:type='win32' name='Microsoft.Windows.Common-Controls' version='6.0.0.0' processorArchitecture='*' publicKeyToken='6595b64144ccf1df' language='*'\\"")
#pragma comment(lib, "gdiplus.lib")
#pragma comment(lib, "comctl32.lib")
#pragma comment(lib, "ws2_32.lib")

using namespace Gdiplus;
using json = nlohmann::json;
namespace fs = std::filesystem;

#define WM_TRAYICON (WM_USER + 1)
#define ID_TRAY_APP_ICON 1001
#define ID_TRAY_EXIT_CONTEXT_MENU_ITEM 3000
#define ID_TRAY_OPEN_CONTEXT_MENU_ITEM 3001

HWND hwndTab;
HWND hwndApps, hwndName, hwndPackage, hwndVersion, hwndDesc, hwndCat, hwndTags, hwndApkLabel, hwndStatusBar;
HWND btnBrowse, btnApply, btnExit, btnDelete, btnClearForm;
HWND btnAddScreenshot, btnClearScreenshots, lstScreenshots;
HWND hwndPreview;
std::vector<HWND> invLabels;

HWND hwndLog, btnToggleServer, hwndServerStatus;

char filePath[MAX_PATH] = "";
std::vector<std::string> screenshots;
json dbCache;
int selectedAppIndex = -1;
int serverPort = 8552;

bool serverRunning = false;
httplib::Server* svrPtr = nullptr;
SOCKET udpSock = INVALID_SOCKET;
std::thread* tServer = nullptr;
std::thread* tUdp = nullptr;

HBITMAP hPreviewBitmap = NULL;
ULONG_PTR gdiplusToken;

std::string dbFile = "db.json";
std::string apkDir = "apks";
std::string imgDir = "images";
std::string configFile = "config.json";

void LogMessage(std::string msg) {
    if (!hwndLog) return;
    std::string timestamp = "[Log] " + msg + "\\r\\n";
    int len = GetWindowTextLength(hwndLog);
    SendMessage(hwndLog, EM_SETSEL, (WPARAM)len, (LPARAM)len);
    SendMessage(hwndLog, EM_REPLACESEL, 0, (LPARAM)timestamp.c_str());
}

void UpdatePreviewImage(std::string path) {
    if (hPreviewBitmap) { DeleteObject(hPreviewBitmap); hPreviewBitmap = NULL; }
    if (fs::exists(path)) {
        std::wstring wpath(path.begin(), path.end());
        Bitmap* bmp = Bitmap::FromFile(wpath.c_str());
        if (bmp && bmp->GetLastStatus() == Ok) {
            int w = bmp->GetWidth();
            int h = bmp->GetHeight();
            int maxDim = 100;
            float scale = std::min((float)maxDim/w, (float)maxDim/h);
            int newW = std::max(1, (int)(w * scale));
            int newH = std::max(1, (int)(h * scale));
            Bitmap* resized = new Bitmap(newW, newH, PixelFormat32bppARGB);
            Graphics g(resized);
            g.SetInterpolationMode(InterpolationModeHighQualityBicubic);
            g.DrawImage(bmp, 0, 0, newW, newH);
            resized->GetHBITMAP(Color(255, 255, 255), &hPreviewBitmap);
            delete resized;
            delete bmp;
        }
    }
    SendMessage(hwndPreview, STM_SETIMAGE, IMAGE_BITMAP, (LPARAM)hPreviewBitmap);
}

void InitTrayIcon(HWND hwnd) {
    NOTIFYICONDATA nid = {};
    nid.cbSize = sizeof(NOTIFYICONDATA);
    nid.hWnd = hwnd;
    nid.uID = ID_TRAY_APP_ICON;
    nid.uFlags = NIF_ICON | NIF_MESSAGE | NIF_TIP;
    nid.uCallbackMessage = WM_TRAYICON;
    nid.hIcon = LoadIcon((HINSTANCE)GetWindowLongPtr(hwnd, GWLP_HINSTANCE), MAKEINTRESOURCE(101));
    strcpy(nid.szTip, "Elite App Marketplace Server");
    Shell_NotifyIcon(NIM_ADD, &nid);
}

void RemoveTrayIcon(HWND hwnd) {
    NOTIFYICONDATA nid = {};
    nid.cbSize = sizeof(NOTIFYICONDATA);
    nid.hWnd = hwnd;
    nid.uID = ID_TRAY_APP_ICON;
    Shell_NotifyIcon(NIM_DELETE, &nid);
}

void LoadConfig() {
    if (fs::exists(configFile)) {
        try {
            std::ifstream i(configFile);
            json j; i >> j;
            serverPort = j.value("server_port", 8552);
        } catch(...) {}
    } else {
        json j; j["server_port"] = 8552;
        std::ofstream o(configFile); o << j.dump(4);
    }
}

json loadDb() {
    if (!fs::exists(dbFile)) {
        json j; j["apps"] = json::array(); return j;
    }
    std::ifstream i(dbFile);
    json j;
    try { i >> j; } catch (...) { j["apps"] = json::array(); }
    return j;
}

void saveDb(const json& j) {
    std::ofstream o(dbFile); o << j.dump(4);
    dbCache = j;
}

void RefreshAppList() {
    dbCache = loadDb();
    bool dbUpdated = false;
    if (fs::exists(apkDir)) {
        for (const auto& entry : fs::directory_iterator(apkDir)) {
            if (entry.path().extension() == ".apk") {
                std::string apkName = entry.path().filename().string();
                bool found = false;
                for (auto& app : dbCache["apps"]) {
                    if (app.contains("versions")) {
                        for (auto& v : app["versions"]) {
                            if (v.value("file", "") == apkName) found = true;
                        }
                    }
                }
                if (!found) {
                    json newApp;
                    newApp["name"] = apkName;
                    newApp["package_name"] = "unknown.package." + apkName;
                    newApp["description"] = "Auto-discovered APK.";
                    newApp["category"] = "Unknown";
                    newApp["tags"] = json::array();
                    newApp["versions"] = json::array();
                    newApp["versions"].push_back({{"version", "1.0"}, {"file", apkName}});
                    newApp["screenshots"] = json::array();
                    newApp["reviews"] = json::array();
                    dbCache["apps"].push_back(newApp);
                    dbUpdated = true;
                }
            }
        }
    }
    if (dbUpdated) saveDb(dbCache);

    SendMessage(hwndApps, LB_RESETCONTENT, 0, 0);
    SendMessage(hwndCat, CB_RESETCONTENT, 0, 0);
    std::vector<std::string> cats;
    for (auto& app : dbCache["apps"]) {
        std::string c = app.value("category", "");
        if (std::find(cats.begin(), cats.end(), c) == cats.end() && c != "") {
            cats.push_back(c);
            SendMessage(hwndCat, CB_ADDSTRING, 0, (LPARAM)c.c_str());
        }
    }
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
    } else { SetWindowText(hwndVersion, ""); }
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
            std::string sPath = imgDir + "\\\\" + s.get<std::string>();
            screenshots.push_back(sPath);
            SendMessage(lstScreenshots, LB_ADDSTRING, 0, (LPARAM)s.get<std::string>().c_str());
        }
    }
    filePath[0] = '\\0';
    SetWindowText(hwndApkLabel, "No new APK selected");
    if (screenshots.size() > 0) UpdatePreviewImage(screenshots[0]);
    else UpdatePreviewImage("");
}

void ClearForm() {
    selectedAppIndex = -1;
    SendMessage(hwndApps, LB_SETCURSEL, (WPARAM)-1, 0);
    SetWindowText(hwndName, ""); SetWindowText(hwndPackage, "");
    SetWindowText(hwndVersion, ""); SetWindowText(hwndCat, "");
    SetWindowText(hwndDesc, ""); SetWindowText(hwndTags, "");
    SendMessage(lstScreenshots, LB_RESETCONTENT, 0, 0);
    screenshots.clear(); filePath[0] = '\\0';
    SetWindowText(hwndApkLabel, "No APK selected");
    UpdatePreviewImage("");
}

void DeleteSelectedApp() {
    if (selectedAppIndex >= 0 && selectedAppIndex < dbCache["apps"].size()) {
        if (MessageBox(NULL, "Delete app?", "Confirm", MB_YESNO) == IDYES) {
            dbCache["apps"].erase(dbCache["apps"].begin() + selectedAppIndex);
            saveDb(dbCache); ClearForm(); RefreshAppList();
        }
    }
}

void UDPDiscoveryThread() {
    udpSock = socket(AF_INET, SOCK_DGRAM, 0);
    sockaddr_in addr = {};
    addr.sin_family = AF_INET;
    addr.sin_addr.s_addr = INADDR_ANY;
    addr.sin_port = htons(serverPort);
    bind(udpSock, (sockaddr*)&addr, sizeof(addr));
    char buffer[256];
    sockaddr_in clientAddr;
    int clientLen = sizeof(clientAddr);
    while (serverRunning) {
        int bytes = recvfrom(udpSock, buffer, 255, 0, (sockaddr*)&clientAddr, &clientLen);
        if (bytes > 0) {
            buffer[bytes] = '\\0';
            if (strcmp(buffer, "ELITE_MARKET_DISCOVER") == 0) {
                LogMessage("UDP Broadcast Received: Replying ELITE_MARKET_HERE");
                const char* reply = "ELITE_MARKET_HERE";
                sendto(udpSock, reply, strlen(reply), 0, (sockaddr*)&clientAddr, clientLen);
            }
        } else {
            break; 
        }
    }
}

void ServerThread() {
    svrPtr = new httplib::Server();
    svrPtr->set_logger([](const httplib::Request& req, const httplib::Response& res) {
        LogMessage(req.method + " " + req.path + " -> " + std::to_string(res.status));
    });
    svrPtr->Get("/api/apps", [](const httplib::Request& req, httplib::Response& res) {
        json db = loadDb();
        if (req.has_param("q")) {
            std::string q = req.get_param_value("q");
            std::transform(q.begin(), q.end(), q.begin(), ::tolower);
            json filtered = json::array();
            for (auto& app : db["apps"]) {
                std::string n = app.value("name", "");
                std::transform(n.begin(), n.end(), n.begin(), ::tolower);
                if (n.find(q) != std::string::npos) filtered.push_back(app);
            }
            json out; out["apps"] = filtered;
            res.set_content(out.dump(), "application/json");
        } else { res.set_content(db.dump(), "application/json"); }
    });
    svrPtr->set_mount_point("/apks", apkDir.c_str());
    svrPtr->set_mount_point("/images", imgDir.c_str());
    LogMessage("HTTP API Listening on port " + std::to_string(serverPort));
    svrPtr->listen("0.0.0.0", serverPort);
}

void StartServer() {
    if (serverRunning) return;
    serverRunning = true;
    LogMessage("Starting Elite Marketplace Server...");
    tServer = new std::thread(ServerThread);
    tUdp = new std::thread(UDPDiscoveryThread);
    SetWindowText(hwndServerStatus, "Status: RUNNING");
    SetWindowText(btnToggleServer, "Stop Server");
}

void StopServer() {
    if (!serverRunning) return;
    serverRunning = false;
    LogMessage("Stopping Elite Marketplace Server...");
    if (svrPtr) { svrPtr->stop(); }
    if (udpSock != INVALID_SOCKET) { closesocket(udpSock); udpSock = INVALID_SOCKET; }
    if (tServer && tServer->joinable()) { tServer->join(); delete tServer; tServer = nullptr; }
    if (tUdp && tUdp->joinable()) { tUdp->join(); delete tUdp; tUdp = nullptr; }
    if (svrPtr) { delete svrPtr; svrPtr = nullptr; }
    SetWindowText(hwndServerStatus, "Status: STOPPED");
    SetWindowText(btnToggleServer, "Start Server");
}

void CopyFileLocal(std::string src, std::string dest) {
    try { fs::copy_file(src, dest, fs::copy_options::overwrite_existing); } catch (...) {}
}

void ProcessApp(std::string apk, std::string name, std::string pkg, std::string ver, std::string desc, std::string cat, std::string tagsStr) {
    fs::create_directory(apkDir); fs::create_directory(imgDir);
    std::string apkName = "";
    if (!apk.empty()) {
        std::string safeName = name;
        std::replace(safeName.begin(), safeName.end(), ' ', '_');
        apkName = safeName + "-" + ver + ".apk";
        CopyFileLocal(apk, apkDir + "/" + apkName);
    }
    std::vector<std::string> copiedScreenshots;
    for (const auto& s : screenshots) {
        std::string sName = fs::path(s).filename().string();
        if (fs::exists(s) && s.find(imgDir) == std::string::npos) CopyFileLocal(s, imgDir + "/" + sName);
        copiedScreenshots.push_back(sName);
    }
    std::vector<std::string> tags;
    size_t pos = 0; std::string tCopy = tagsStr;
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
                    if (v["version"] == ver) { vExists = true; v["file"] = apkName; }
                }
                if (!vExists) app["versions"].push_back({{"version", ver}, {"file", apkName}});
            }
            app["name"] = name; app["description"] = desc; app["category"] = cat;
            app["tags"] = tags; app["screenshots"] = copiedScreenshots;
            break;
        }
    }
    if (!exists) {
        if (apkName.empty()) { MessageBox(NULL, "APK file required!", "Error", MB_OK); return; }
        json newApp;
        newApp["name"] = name; newApp["package_name"] = pkg; newApp["description"] = desc;
        newApp["category"] = cat; newApp["tags"] = tags;
        newApp["versions"] = json::array(); newApp["versions"].push_back({{"version", ver}, {"file", apkName}});
        newApp["screenshots"] = copiedScreenshots; newApp["reviews"] = json::array();
        db["apps"].push_back(newApp);
    }
    saveDb(db); RefreshAppList();
    MessageBox(NULL, "App Processed!", "Success", MB_OK);
}

void UpdateTabVisibility() {
    int tab = SendMessage(hwndTab, TCM_GETCURSEL, 0, 0);
    int showInv = (tab == 0) ? SW_SHOW : SW_HIDE;
    int showMon = (tab == 1) ? SW_SHOW : SW_HIDE;
    
    HWND windows[] = { hwndApps, hwndName, hwndPackage, hwndVersion, hwndCat, hwndTags, hwndDesc, lstScreenshots, btnAddScreenshot, btnClearScreenshots, hwndApkLabel, btnBrowse, btnDelete, btnClearForm };
    for(HWND w : windows) ShowWindow(w, showInv);
    ShowWindow(hwndPreview, showInv);
    for(HWND lbl : invLabels) ShowWindow(lbl, showInv);

    ShowWindow(hwndLog, showMon);
    ShowWindow(hwndServerStatus, showMon);
    ShowWindow(btnToggleServer, showMon);
}

LRESULT CALLBACK WindowProc(HWND hwnd, UINT uMsg, WPARAM wParam, LPARAM lParam) {
    switch (uMsg) {
    case WM_SIZE: {
        int w = LOWORD(lParam);
        int h = HIWORD(lParam);

        SendMessage(hwndStatusBar, WM_SIZE, 0, 0);
        RECT statusRect;
        GetWindowRect(hwndStatusBar, &statusRect);
        int sh = statusRect.bottom - statusRect.top;

        MoveWindow(hwndTab, 10, 50, w - 20, h - 50 - sh - 50, TRUE);

        RECT tabRect;
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

        MoveWindow(btnApply, w - 240, h - sh - 40, 100, 30, TRUE);
        MoveWindow(btnExit, w - 120, h - sh - 40, 100, 30, TRUE);

        MoveWindow(hwndLog, tabRect.left, tabRect.top, tabRect.right - tabRect.left, tabRect.bottom - tabRect.top - 40, TRUE);
        MoveWindow(hwndServerStatus, tabRect.left, tabRect.bottom - 30, 200, 30, TRUE);
        MoveWindow(btnToggleServer, tabRect.right - 120, tabRect.bottom - 35, 120, 30, TRUE);

        return 0;
    }
    case WM_NOTIFY: {
        if (((LPNMHDR)lParam)->code == TCN_SELCHANGE) {
            UpdateTabVisibility();
        }
        break;
    }
    case WM_CREATE: {
        RegisterHotKey(hwnd, 1, MOD_CONTROL | MOD_ALT, 'M');
        HFONT hFont = (HFONT)GetStockObject(DEFAULT_GUI_FONT);
        HFONT hFontBold = CreateFont(16, 0, 0, 0, FW_BOLD, FALSE, FALSE, FALSE, DEFAULT_CHARSET, OUT_DEFAULT_PRECIS, CLIP_DEFAULT_PRECIS, DEFAULT_QUALITY, DEFAULT_PITCH | FF_SWISS, "Segoe UI");
        
        hwndStatusBar = CreateWindowEx(0, STATUSCLASSNAME, NULL, WS_CHILD | WS_VISIBLE | SBARS_SIZEGRIP, 0, 0, 0, 0, hwnd, NULL, NULL, NULL);
        SendMessage(hwndStatusBar, SB_SETTEXT, 0, (LPARAM)"Ready");

        HWND hBannerIcon = CreateWindow("STATIC", "", WS_CHILD | WS_VISIBLE | SS_ICON, 10, 4, 32, 32, hwnd, NULL, (HINSTANCE)GetWindowLongPtr(hwnd, GWLP_HINSTANCE), NULL);
        SendMessage(hBannerIcon, STM_SETICON, (WPARAM)LoadIcon((HINSTANCE)GetWindowLongPtr(hwnd, GWLP_HINSTANCE), MAKEINTRESOURCE(101)), 0);
        HWND hBanner = CreateWindow("STATIC", ("        Elite App Marketplace - Server Manager (Port " + std::to_string(serverPort) + ")").c_str(), WS_CHILD | WS_VISIBLE | SS_CENTERIMAGE, 0, 0, 850, 40, hwnd, NULL, NULL, NULL);
        SendMessage(hBanner, WM_SETFONT, (WPARAM)hFontBold, TRUE);
        CreateWindowEx(0, "STATIC", "", WS_CHILD | WS_VISIBLE | SS_ETCHEDHORZ, 0, 40, 850, 2, hwnd, NULL, NULL, NULL);

        hwndTab = CreateWindowEx(0, WC_TABCONTROL, "", WS_CHILD | WS_VISIBLE, 10, 50, 810, 450, hwnd, (HMENU)100, NULL, NULL);
        TCITEM tie; tie.mask = TCIF_TEXT; 
        tie.pszText = (LPSTR)"App Inventory"; SendMessage(hwndTab, TCM_INSERTITEM, 0, (LPARAM)&tie);
        tie.pszText = (LPSTR)"Server Monitor"; SendMessage(hwndTab, TCM_INSERTITEM, 1, (LPARAM)&tie);

        invLabels.push_back(CreateWindow("STATIC", "Store Inventory:", WS_CHILD | WS_VISIBLE, 15, 50, 200, 20, hwnd, NULL, NULL, NULL));
        hwndApps = CreateWindowEx(WS_EX_CLIENTEDGE, "LISTBOX", NULL, WS_CHILD | WS_VISIBLE | WS_BORDER | WS_VSCROLL | LBS_NOTIFY, 15, 70, 200, 390, hwnd, (HMENU)10, NULL, NULL);
        
        invLabels.push_back(CreateWindow("STATIC", "App Name:", WS_CHILD | WS_VISIBLE, 230, 70, 90, 20, hwnd, NULL, NULL, NULL));
        hwndName = CreateWindowEx(WS_EX_CLIENTEDGE, "EDIT", "", WS_CHILD | WS_VISIBLE | WS_BORDER, 330, 70, 480, 20, hwnd, NULL, NULL, NULL);
        
        invLabels.push_back(CreateWindow("STATIC", "Package:", WS_CHILD | WS_VISIBLE, 230, 100, 90, 20, hwnd, NULL, NULL, NULL));
        hwndPackage = CreateWindowEx(WS_EX_CLIENTEDGE, "EDIT", "", WS_CHILD | WS_VISIBLE | WS_BORDER, 330, 100, 480, 20, hwnd, NULL, NULL, NULL);
        
        invLabels.push_back(CreateWindow("STATIC", "Version:", WS_CHILD | WS_VISIBLE, 230, 130, 90, 20, hwnd, NULL, NULL, NULL));
        hwndVersion = CreateWindowEx(WS_EX_CLIENTEDGE, "EDIT", "", WS_CHILD | WS_VISIBLE | WS_BORDER, 330, 130, 480, 20, hwnd, NULL, NULL, NULL);
        
        invLabels.push_back(CreateWindow("STATIC", "Category:", WS_CHILD | WS_VISIBLE, 230, 160, 90, 20, hwnd, NULL, NULL, NULL));
        hwndCat = CreateWindowEx(WS_EX_CLIENTEDGE, "COMBOBOX", "", WS_CHILD | WS_VISIBLE | WS_BORDER | CBS_DROPDOWN | WS_VSCROLL, 330, 160, 480, 150, hwnd, NULL, NULL, NULL);
        
        invLabels.push_back(CreateWindow("STATIC", "Tags (CSV):", WS_CHILD | WS_VISIBLE, 230, 190, 90, 20, hwnd, NULL, NULL, NULL));
        hwndTags = CreateWindowEx(WS_EX_CLIENTEDGE, "EDIT", "", WS_CHILD | WS_VISIBLE | WS_BORDER, 330, 190, 480, 20, hwnd, NULL, NULL, NULL);
        
        invLabels.push_back(CreateWindow("STATIC", "Description:", WS_CHILD | WS_VISIBLE, 230, 220, 90, 20, hwnd, NULL, NULL, NULL));
        hwndDesc = CreateWindowEx(WS_EX_CLIENTEDGE, "EDIT", "", WS_CHILD | WS_VISIBLE | WS_BORDER | ES_MULTILINE | ES_AUTOVSCROLL | WS_VSCROLL, 330, 220, 480, 90, hwnd, NULL, NULL, NULL);
        
        invLabels.push_back(CreateWindow("STATIC", "Screenshots:", WS_CHILD | WS_VISIBLE, 230, 320, 90, 20, hwnd, NULL, NULL, NULL));
        lstScreenshots = CreateWindowEx(WS_EX_CLIENTEDGE, "LISTBOX", NULL, WS_CHILD | WS_VISIBLE | WS_BORDER | WS_VSCROLL | LBS_NOTIFY, 330, 320, 150, 70, hwnd, (HMENU)30, NULL, NULL);
        hwndPreview = CreateWindow("STATIC", "", WS_CHILD | WS_VISIBLE | SS_BITMAP | SS_REALSIZECONTROL, 490, 320, 190, 70, hwnd, NULL, NULL, NULL);
        btnAddScreenshot = CreateWindow("BUTTON", "Add", WS_CHILD | WS_VISIBLE | BS_PUSHBUTTON, 690, 320, 120, 30, hwnd, (HMENU)3, NULL, NULL);
        btnClearScreenshots = CreateWindow("BUTTON", "Clear All", WS_CHILD | WS_VISIBLE | BS_PUSHBUTTON, 690, 360, 120, 30, hwnd, (HMENU)4, NULL, NULL);
        
        invLabels.push_back(CreateWindow("STATIC", "APK File:", WS_CHILD | WS_VISIBLE, 230, 410, 90, 20, hwnd, NULL, NULL, NULL));
        hwndApkLabel = CreateWindowEx(WS_EX_CLIENTEDGE, "STATIC", " No APK selected", WS_CHILD | WS_VISIBLE | SS_LEFT, 330, 450, 250, 22, hwnd, NULL, NULL, NULL);
        btnBrowse = CreateWindow("BUTTON", "Browse APK...", WS_CHILD | WS_VISIBLE | BS_PUSHBUTTON, 690, 445, 120, 30, hwnd, (HMENU)1, NULL, NULL);
        btnDelete = CreateWindow("BUTTON", "Delete Selected", WS_CHILD | WS_VISIBLE | BS_PUSHBUTTON, 330, 485, 130, 30, hwnd, (HMENU)6, NULL, NULL);
        btnClearForm = CreateWindow("BUTTON", "New App", WS_CHILD | WS_VISIBLE | BS_PUSHBUTTON, 470, 485, 130, 30, hwnd, (HMENU)5, NULL, NULL);

        btnApply = CreateWindow("BUTTON", "Apply", WS_CHILD | WS_VISIBLE | BS_PUSHBUTTON, 590, 515, 100, 30, hwnd, (HMENU)2, NULL, NULL);
        btnExit = CreateWindow("BUTTON", "Hide to Tray", WS_CHILD | WS_VISIBLE | BS_PUSHBUTTON, 710, 515, 100, 30, hwnd, (HMENU)7, NULL, NULL);

        // Server Monitor Setup
        hwndLog = CreateWindowEx(WS_EX_CLIENTEDGE, "EDIT", "", WS_CHILD | WS_BORDER | WS_VSCROLL | ES_MULTILINE | ES_READONLY | ES_AUTOVSCROLL, 20, 80, 790, 370, hwnd, NULL, NULL, NULL);
        hwndServerStatus = CreateWindow("STATIC", "Status: STOPPED", WS_CHILD, 20, 460, 200, 20, hwnd, NULL, NULL, NULL);
        btnToggleServer = CreateWindow("BUTTON", "Start Server", WS_CHILD | BS_PUSHBUTTON, 690, 460, 120, 30, hwnd, (HMENU)200, NULL, NULL);

        HWND windows[] = { hwndApps, hwndName, hwndPackage, hwndVersion, hwndCat, hwndTags, hwndDesc, lstScreenshots, btnAddScreenshot, btnClearScreenshots, hwndApkLabel, btnBrowse, btnDelete, btnClearForm, btnApply, btnExit, hwndTab, hwndLog, hwndServerStatus, btnToggleServer };
        for (HWND w : windows) SendMessage(w, WM_SETFONT, (WPARAM)hFont, TRUE);
        for (HWND lbl : invLabels) SendMessage(lbl, WM_SETFONT, (WPARAM)hFont, TRUE);

        UpdateTabVisibility();
        RefreshAppList();
        InitTrayIcon(hwnd);
        StartServer();
        break;
    }
    case WM_HOTKEY: {
        if (wParam == 1) {
            if (IsWindowVisible(hwnd)) {
                ShowWindow(hwnd, SW_HIDE);
            } else {
                ShowWindow(hwnd, SW_RESTORE);
                SetForegroundWindow(hwnd);
            }
        }
        return 0;
    }
    case WM_TRAYICON: {
        if (lParam == WM_RBUTTONUP || lParam == WM_LBUTTONUP) {
            POINT pt; GetCursorPos(&pt);
            HMENU hMenu = CreatePopupMenu();
            InsertMenu(hMenu, 0, MF_BYPOSITION | MF_STRING, ID_TRAY_OPEN_CONTEXT_MENU_ITEM, "Open Manager");
            InsertMenu(hMenu, 1, MF_BYPOSITION | MF_STRING, ID_TRAY_EXIT_CONTEXT_MENU_ITEM, "Quit Server");
            SetForegroundWindow(hwnd);
            TrackPopupMenu(hMenu, TPM_BOTTOMALIGN | TPM_LEFTALIGN, pt.x, pt.y, 0, hwnd, NULL);
            DestroyMenu(hMenu);
        }
        break;
    }
    case WM_COMMAND: {
        int wmId = LOWORD(wParam);
        int wmEvent = HIWORD(wParam);
        if (wmId == 200) { // toggle server
            if (serverRunning) StopServer();
            else StartServer();
        }
        else if (wmId == ID_TRAY_OPEN_CONTEXT_MENU_ITEM) {
            ShowWindow(hwnd, SW_RESTORE);
            SetForegroundWindow(hwnd);
        } else if (wmId == ID_TRAY_EXIT_CONTEXT_MENU_ITEM) {
            RemoveTrayIcon(hwnd);
            PostQuitMessage(0);
        }
        else if (wmId == 10 && wmEvent == LBN_SELCHANGE) {
            selectedAppIndex = SendMessage(hwndApps, LB_GETCURSEL, 0, 0);
            LoadAppIntoForm(selectedAppIndex);
        }
        else if (wmId == 1) {
            OPENFILENAME ofn; ZeroMemory(&ofn, sizeof(ofn)); ofn.lStructSize = sizeof(ofn);
            ofn.hwndOwner = hwnd; ofn.lpstrFile = filePath; ofn.lpstrFile[0] = '\\0';
            ofn.nMaxFile = sizeof(filePath); ofn.lpstrFilter = "APK Files\\0*.apk\\0All Files\\0*.*\\0";
            ofn.Flags = OFN_PATHMUSTEXIST | OFN_FILEMUSTEXIST;
            if (GetOpenFileName(&ofn)) SetWindowText(hwndApkLabel, filePath);
        }
        else if (wmId == 30 && wmEvent == LBN_SELCHANGE) {
            int sIdx = SendMessage(lstScreenshots, LB_GETCURSEL, 0, 0);
            if (sIdx >= 0 && sIdx < screenshots.size()) UpdatePreviewImage(screenshots[sIdx]);
        }
        else if (wmId == 3) {
            char imgPath[MAX_PATH] = "";
            OPENFILENAME ofn; ZeroMemory(&ofn, sizeof(ofn)); ofn.lStructSize = sizeof(ofn);
            ofn.hwndOwner = hwnd; ofn.lpstrFile = imgPath; ofn.lpstrFile[0] = '\\0';
            ofn.nMaxFile = sizeof(imgPath); ofn.lpstrFilter = "Image Files\\0*.png;*.jpg;*.jpeg\\0All Files\\0*.*\\0";
            ofn.Flags = OFN_PATHMUSTEXIST | OFN_FILEMUSTEXIST;
            if (GetOpenFileName(&ofn)) {
                screenshots.push_back(imgPath);
                SendMessage(lstScreenshots, LB_ADDSTRING, 0, (LPARAM)fs::path(imgPath).filename().string().c_str());
                UpdatePreviewImage(screenshots.back());
            }
        }
        else if (wmId == 4) { screenshots.clear(); SendMessage(lstScreenshots, LB_RESETCONTENT, 0, 0); UpdatePreviewImage(""); }
        else if (wmId == 5) ClearForm();
        else if (wmId == 6) DeleteSelectedApp();
        else if (wmId == 7) ShowWindow(hwnd, SW_HIDE);
        else if (wmId == 2) {
            char n[256], p[256], v[256], d[4096], c[256], t[512];
            GetWindowText(hwndName, n, 256); GetWindowText(hwndPackage, p, 256);
            GetWindowText(hwndVersion, v, 256); GetWindowText(hwndDesc, d, 4096);
            GetWindowText(hwndCat, c, 256); GetWindowText(hwndTags, t, 512);
            if (strlen(n) == 0 || strlen(p) == 0 || strlen(v) == 0) { MessageBox(hwnd, "Required fields missing", "Error", MB_OK); break; }
            ProcessApp(filePath, n, p, v, d, c, t);
        }
        break;
    }
    case WM_CLOSE:
        ShowWindow(hwnd, SW_HIDE);
        return 0;
    case WM_CTLCOLORSTATIC: {
        HDC hdcStatic = (HDC)wParam;
        SetBkColor(hdcStatic, GetSysColor(COLOR_BTNFACE));
        return (INT_PTR)GetSysColorBrush(COLOR_BTNFACE);
    }
    case WM_DESTROY:
        StopServer();
        UnregisterHotKey(hwnd, 1);
        RemoveTrayIcon(hwnd);
        PostQuitMessage(0);
        return 0;
    }
    return DefWindowProc(hwnd, uMsg, wParam, lParam);
}

int WINAPI WinMain(HINSTANCE hInstance, HINSTANCE hPrevInstance, LPSTR lpCmdLine, int nCmdShow) {
    char path[MAX_PATH];
    GetModuleFileName(NULL, path, MAX_PATH);
    fs::path exePath = path;
    fs::current_path(exePath.parent_path());

    GdiplusStartupInput gdiplusStartupInput;
    GdiplusStartup(&gdiplusToken, &gdiplusStartupInput, NULL);
    LoadConfig();

    INITCOMMONCONTROLSEX icex; icex.dwSize = sizeof(INITCOMMONCONTROLSEX);
    icex.dwICC = ICC_WIN95_CLASSES | ICC_STANDARD_CLASSES | ICC_TAB_CLASSES; InitCommonControlsEx(&icex);

    WNDCLASS wc = { }; wc.lpfnWndProc = WindowProc; wc.hInstance = hInstance;
    wc.lpszClassName = "EliteAppMarketplaceServer"; wc.hbrBackground = (HBRUSH)(COLOR_BTNFACE + 1);
    wc.hIcon = LoadIcon(hInstance, MAKEINTRESOURCE(101)); RegisterClass(&wc);

    HWND hwnd = CreateWindowEx(0, "EliteAppMarketplaceServer", "Elite App Marketplace - Server & Manager",
        WS_OVERLAPPEDWINDOW, CW_USEDEFAULT, CW_USEDEFAULT, 850, 600, NULL, NULL, hInstance, NULL);

    if (hwnd == NULL) return 0;
    ShowWindow(hwnd, SW_SHOW);

    MSG msg = { };
    while (GetMessage(&msg, NULL, 0, 0)) { TranslateMessage(&msg); DispatchMessage(&msg); }
    GdiplusShutdown(gdiplusToken);
    return 0;
}
'''
with open('Manager_App/main.cpp', 'w') as f:
    f.write(cpp_code)
