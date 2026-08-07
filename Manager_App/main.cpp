#define _WIN32_WINNT 0x0A00
#include <winsock2.h>
#include <windows.h>
#include <commctrl.h>
#include <shellapi.h>
#include <string>
#include <vector>
#include <iostream>
#include <thread>
#include <fstream>
#include <filesystem>
#include <algorithm>
#include "httplib.h"
#include "json.hpp"
#include "miniz.h"
#include <gdiplus.h>
#include <memory>
#include <array>

#pragma comment(linker,"\"/manifestdependency:type='win32' name='Microsoft.Windows.Common-Controls' version='6.0.0.0' processorArchitecture='*' publicKeyToken='6595b64144ccf1df' language='*'\"")
#pragma comment(lib, "gdiplus.lib")
#pragma comment(lib, "comctl32.lib")
#pragma comment(lib, "ws2_32.lib")

using namespace Gdiplus;
using json = nlohmann::json;
namespace fs = std::filesystem;

#define WM_TRAYICON (WM_USER + 1)
#define WM_LOG_MESSAGE (WM_APP + 101)
#define ID_TRAY_APP_ICON 1001
#define ID_TRAY_EXIT_CONTEXT_MENU_ITEM 3000
#define ID_TRAY_OPEN_CONTEXT_MENU_ITEM 3001

#define ID_FILE_SETTINGS       2001
#define ID_FILE_VIEWLOG        2002
#define ID_FILE_EXIT           2003
#define ID_TOOLS_SCAN          2004
#define ID_TOOLS_TOGGLE        2005
#define ID_HELP_GUIDANCE       2006
#define ID_HELP_ABOUT          2007

#define ID_TOOLBAR_BROWSE      3001
#define ID_TOOLBAR_REFRESH     3002
#define ID_TOOLBAR_TOGGLE      3003
#define ID_TOOLBAR_SETTINGS    3004
#define ID_TOOLBAR_HELP        3005

HFONT hFontSegoeNormal = NULL;
HFONT hFontSegoeBold = NULL;

HWND hwndMain = NULL;
extern bool g_serverError;
void UpdateServerStatusUI();
HWND hwndTab = NULL;
HWND hwndApps = NULL; // SysListView32
HIMAGELIST hSmallIcons = NULL;
std::string g_aaptPath = "NOT_FOUND";
HWND hwndName = NULL;
HWND hwndPackage = NULL;
HWND hwndVersion = NULL;
HWND hwndDesc = NULL;
HWND hwndCat = NULL;
HWND hwndTags = NULL;
HWND hwndApkLabel = NULL;
HWND hwndStatusBar = NULL;

HWND btnBrowse = NULL;
HWND btnApply = NULL;
HWND btnExit = NULL;
HWND btnDelete = NULL;
HWND btnClearForm = NULL;
HWND btnAddScreenshot = NULL;
HWND btnClearScreenshots = NULL;
HWND lstScreenshots = NULL;
HIMAGELIST g_hImgListSS = NULL;
HWND hwndPreview = NULL;

std::vector<HWND> invLabels;

HWND hwndLog = NULL;
HWND btnToggleServer = NULL;
HWND hwndServerStatus = NULL;
HWND lblConnectedClients = NULL;
HWND hwndClientList = NULL;

struct ClientInfo {
    std::string client_id;
    std::string ip_address;
    std::string device_name;
    std::chrono::steady_clock::time_point last_seen;
};

std::mutex g_clientMutex;
std::map<std::string, ClientInfo> g_connectedClients;
std::thread* tCleanup = nullptr;

HWND hwndChin = NULL;
HWND hwndLogLink = NULL;
HWND hwndToolbar = NULL;
HWND hwndRebar = NULL;
HWND hwndTT = NULL;
HICON g_hAppIcon = NULL;
HBRUSH hbrBanner = NULL;

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
int g_windowWidth = 1000;
int g_windowHeight = 700;
int g_windowX = CW_USEDEFAULT;
int g_windowY = CW_USEDEFAULT;
bool g_windowMaximized = false;
int g_listWidth = 350;
std::vector<int> g_listCols = {110, 130, 55, 60, 70};
bool g_isDraggingSplitter = false;
HWND hwndSplitter = NULL;
WNDPROC oldSplitterProc = NULL;

void SaveConfig(HWND hwnd = NULL);

LRESULT CALLBACK SplitterProc(HWND hwnd, UINT uMsg, WPARAM wParam, LPARAM lParam) {
    switch (uMsg) {
    case WM_SETCURSOR:
        SetCursor(LoadCursor(NULL, IDC_SIZEWE));
        return TRUE;
    case WM_LBUTTONDOWN:
        SetCapture(hwnd);
        g_isDraggingSplitter = true;
        return 0;
    case WM_MOUSEMOVE:
        if (g_isDraggingSplitter) {
            POINT pt;
            GetCursorPos(&pt);
            HWND hParent = GetParent(GetParent(hwnd));
            ScreenToClient(GetParent(hwnd), &pt);
            int newWidth = pt.x - 10;
            if (newWidth < 240) newWidth = 240;
            g_listWidth = newWidth;
            RECT rc; GetClientRect(hParent, &rc);
            SendMessageA(hParent, WM_SIZE, 0, MAKELPARAM(rc.right, rc.bottom));
        }
        return 0;
    case WM_LBUTTONUP:
        if (g_isDraggingSplitter) {
            ReleaseCapture();
            g_isDraggingSplitter = false;
            HWND hParent = GetParent(GetParent(hwnd));
            SaveConfig(hParent);
        }
        return 0;
    }
    return CallWindowProcA(oldSplitterProc, hwnd, uMsg, wParam, lParam);
}


void LogToFileAndUI(const std::string& msg) {
    char sysDrive[MAX_PATH] = "C:";
    DWORD len = GetEnvironmentVariableA("SystemDrive", sysDrive, MAX_PATH);
    if (len == 0 || len >= MAX_PATH) {
        strcpy(sysDrive, "C:");
    }
    std::string logDir = std::string(sysDrive) + "\\EliteSoftware\\Logs";
    std::string logFilePath = logDir + "\\LocalAPKStore.log";
    
    try {
        fs::create_directories(logDir);
        std::ofstream logFile(logFilePath, std::ios::app);
        if (logFile.is_open()) {
            SYSTEMTIME st;
            GetLocalTime(&st);
            char timeBuf[64];
            sprintf(timeBuf, "[%04d-%02d-%02d %02d:%02d:%02d] ", st.wYear, st.wMonth, st.wDay, st.wHour, st.wMinute, st.wSecond);
            logFile << timeBuf << msg << std::endl;
        }
    } catch (...) {}

    std::string formattedTimestampMsg = "[Log] " + msg + "\r\n";
    if (hwndMain && IsWindow(hwndMain)) {
        std::string* pStr = new std::string(formattedTimestampMsg);
        if (!PostMessageA(hwndMain, WM_LOG_MESSAGE, 0, (LPARAM)pStr)) {
            delete pStr;
        }
    }
}

void LogMessage(std::string msg) {
    LogToFileAndUI(msg);
}

void OpenLogFile() {
    char sysDrive[MAX_PATH] = "C:";
    DWORD len = GetEnvironmentVariableA("SystemDrive", sysDrive, MAX_PATH);
    if (len == 0 || len >= MAX_PATH) {
        strcpy(sysDrive, "C:");
    }
    std::string logDir = std::string(sysDrive) + "\\EliteSoftware\\Logs";
    std::string logFilePath = logDir + "\\LocalAPKStore.log";
    
    try {
        fs::create_directories(logDir);
        if (!fs::exists(logFilePath)) {
            std::ofstream o(logFilePath);
            o << "[Log File Initialized]\n";
        }
    } catch(...) {}

    ShellExecuteA(NULL, "open", "notepad.exe", logFilePath.c_str(), NULL, SW_SHOWNORMAL);
}

HBITMAP LoadIconAsHBitmap(HINSTANCE hInstance, int resourceId, int width, int height) {
    HICON hIcon = (HICON)LoadImage(hInstance, MAKEINTRESOURCE(resourceId), IMAGE_ICON, width, height, LR_DEFAULTCOLOR);
    if (!hIcon) return NULL;

    BITMAPINFO bmi = {0};
    bmi.bmiHeader.biSize = sizeof(BITMAPINFOHEADER);
    bmi.bmiHeader.biWidth = width;
    bmi.bmiHeader.biHeight = -height;
    bmi.bmiHeader.biPlanes = 1;
    bmi.bmiHeader.biBitCount = 32;
    bmi.bmiHeader.biCompression = BI_RGB;

    void* pBits = NULL;
    HDC hdcScreen = GetDC(NULL);
    HBITMAP hBmp = CreateDIBSection(hdcScreen, &bmi, DIB_RGB_COLORS, &pBits, NULL, 0);
    if (hBmp && pBits) {
        HDC hdcMem = CreateCompatibleDC(hdcScreen);
        HBITMAP hBmpOld = (HBITMAP)SelectObject(hdcMem, hBmp);
        memset(pBits, 0, width * height * 4);
        DrawIconEx(hdcMem, 0, 0, hIcon, width, height, 0, NULL, DI_NORMAL);
        SelectObject(hdcMem, hBmpOld);
        DeleteDC(hdcMem);
    }
    ReleaseDC(NULL, hdcScreen);
    DestroyIcon(hIcon);
    return hBmp;
}

HBITMAP LoadPngAsHBitmap(HINSTANCE hInstance, int resourceId) {
    HRSRC hRes = FindResource(hInstance, MAKEINTRESOURCE(resourceId), RT_RCDATA);
    if (!hRes) return NULL;
    DWORD size = SizeofResource(hInstance, hRes);
    HGLOBAL hMem = LoadResource(hInstance, hRes);
    if (!hMem) return NULL;
    void* pData = LockResource(hMem);
    HGLOBAL hBuffer = GlobalAlloc(GMEM_MOVEABLE, size);
    if (hBuffer) {
        void* pBuffer = GlobalLock(hBuffer);
        memcpy(pBuffer, pData, size);
        GlobalUnlock(hBuffer);
        IStream* pStream = NULL;
        if (CreateStreamOnHGlobal(hBuffer, TRUE, &pStream) == S_OK) {
            Gdiplus::Bitmap* bmp = Gdiplus::Bitmap::FromStream(pStream);
            HBITMAP hBmp = NULL;
            if (bmp && bmp->GetLastStatus() == Gdiplus::Ok) {
                bmp->GetHBITMAP(Gdiplus::Color::Transparent, &hBmp);
            }
            if (bmp) delete bmp;
            pStream->Release();
            return hBmp;
        }
        GlobalFree(hBuffer);
    }
    return NULL;
}

HBITMAP LoadPngAsHBitmap32(HINSTANCE hInstance, int resourceId, int width, int height) {
    HRSRC hRes = FindResource(hInstance, MAKEINTRESOURCE(resourceId), RT_RCDATA);
    if (!hRes) return NULL;
    DWORD size = SizeofResource(hInstance, hRes);
    HGLOBAL hMem = LoadResource(hInstance, hRes);
    if (!hMem) return NULL;
    void* pData = LockResource(hMem);
    HGLOBAL hBuffer = GlobalAlloc(GMEM_MOVEABLE, size);
    if (hBuffer) {
        void* pBuffer = GlobalLock(hBuffer);
        memcpy(pBuffer, pData, size);
        GlobalUnlock(hBuffer);
        IStream* pStream = NULL;
        HBITMAP hBmp = NULL;
        if (CreateStreamOnHGlobal(hBuffer, TRUE, &pStream) == S_OK) {
            Gdiplus::Bitmap* bmp = Gdiplus::Bitmap::FromStream(pStream);
            if (bmp && bmp->GetLastStatus() == Gdiplus::Ok) {
                Gdiplus::Bitmap* finalBmp = bmp;
                Gdiplus::Bitmap* resized = NULL;
                if (width > 0 && height > 0) {
                    resized = new Gdiplus::Bitmap(width, height, PixelFormat32bppARGB);
                    Gdiplus::Graphics g(resized);
                    g.SetInterpolationMode(Gdiplus::InterpolationModeHighQualityBicubic);
                    g.DrawImage(bmp, 0, 0, width, height);
                    finalBmp = resized;
                }
                
                BITMAPINFO bmi = {0};
                bmi.bmiHeader.biSize = sizeof(BITMAPINFOHEADER);
                bmi.bmiHeader.biWidth = finalBmp->GetWidth();
                bmi.bmiHeader.biHeight = -(INT)finalBmp->GetHeight();
                bmi.bmiHeader.biPlanes = 1;
                bmi.bmiHeader.biBitCount = 32;
                bmi.bmiHeader.biCompression = BI_RGB;
                
                void* pBits = NULL;
                HDC hdcScreen = GetDC(NULL);
                hBmp = CreateDIBSection(hdcScreen, &bmi, DIB_RGB_COLORS, &pBits, NULL, 0);
                ReleaseDC(NULL, hdcScreen);
                
                if (hBmp && pBits) {
                    Gdiplus::BitmapData bmpData;
                    Gdiplus::Rect rect(0, 0, finalBmp->GetWidth(), finalBmp->GetHeight());
                    finalBmp->LockBits(&rect, Gdiplus::ImageLockModeRead, PixelFormat32bppPARGB, &bmpData);
                    memcpy(pBits, bmpData.Scan0, bmpData.Stride * finalBmp->GetHeight());
                    finalBmp->UnlockBits(&bmpData);
                }
                
                if (resized) delete resized;
            }
            if (bmp) delete bmp;
            pStream->Release();
        }
        GlobalFree(hBuffer);
        return hBmp;
    }
    return NULL;
}

HICON GetDynamicAppIcon(HINSTANCE hInstance) {
    char exePath[MAX_PATH];
    GetModuleFileNameA(NULL, exePath, MAX_PATH);
    fs::path p(exePath);
    fs::path icoPath = p.parent_path() / (p.stem().string() + ".ico");
    
    HICON hIcon = NULL;
    if (fs::exists(icoPath)) {
        hIcon = (HICON)LoadImageA(NULL, icoPath.string().c_str(), IMAGE_ICON, 32, 32, LR_LOADFROMFILE);
    }
    if (!hIcon) {
        hIcon = LoadIcon(hInstance, MAKEINTRESOURCE(101));
    }
    if (!hIcon) {
        hIcon = LoadIcon(NULL, IDI_APPLICATION);
    }
    return hIcon;
}

std::string ExecCmd(const char* cmd) {
    std::array<char, 512> buffer;
    std::string result;
    std::unique_ptr<FILE, decltype(&_pclose)> pipe(_popen(cmd, "r"), _pclose);
    if (!pipe) return "";
    while (fgets(buffer.data(), buffer.size(), pipe.get()) != nullptr) {
        result += buffer.data();
    }
    return result;
}

std::string GetAaptPath() {
    if (g_aaptPath == "NOT_FOUND") {
        return "";
    }
    if (!g_aaptPath.empty() && fs::exists(g_aaptPath)) {
        return g_aaptPath;
    }
    std::vector<std::string> candidatePaths = {
        "aapt.exe",
        ".\\aapt.exe",
        "C:\\AndroidBuildTools\\android-sdk\\build-tools\\33.0.1\\aapt.exe",
        "C:\\AndroidBuildTools\\aapt.exe"
    };
    for (const auto& path : candidatePaths) {
        if (fs::exists(path)) {
            g_aaptPath = path;
            return g_aaptPath;
        }
    }
    g_aaptPath = "NOT_FOUND";
    return "";
}

std::string PsEscape(const std::string& str) {
    std::string res;
    for (char c : str) {
        if (c == '\'') res += "''";
        else res += c;
    }
    return res;
}

std::string RunAaptBadging(const std::string& aaptPath, const std::string& apkPath) {
    SECURITY_ATTRIBUTES saAttr;
    saAttr.nLength = sizeof(SECURITY_ATTRIBUTES);
    saAttr.bInheritHandle = TRUE;
    saAttr.lpSecurityDescriptor = NULL;

    HANDLE hRead, hWrite;
    if (!CreatePipe(&hRead, &hWrite, &saAttr, 0)) return "";
    SetHandleInformation(hRead, HANDLE_FLAG_INHERIT, 0);

    STARTUPINFOA si;
    PROCESS_INFORMATION pi;
    ZeroMemory(&si, sizeof(si));
    si.cb = sizeof(si);
    si.hStdError = hWrite;
    si.hStdOutput = hWrite;
    si.dwFlags |= STARTF_USESTDHANDLES | STARTF_USESHOWWINDOW;
    si.wShowWindow = SW_HIDE;

    ZeroMemory(&pi, sizeof(pi));

    std::string cmd = "\"" + aaptPath + "\" dump badging \"" + apkPath + "\"";
    char* cmdStr = _strdup(cmd.c_str());

    std::string result = "";
    if (CreateProcessA(aaptPath.c_str(), cmdStr, NULL, NULL, TRUE, 0, NULL, NULL, &si, &pi)) {
        CloseHandle(hWrite);
        char buffer[1024];
        DWORD bytesRead;
        while (ReadFile(hRead, buffer, sizeof(buffer) - 1, &bytesRead, NULL) && bytesRead > 0) {
            buffer[bytesRead] = '\0';
            result += buffer;
        }
        WaitForSingleObject(pi.hProcess, 5000);
        CloseHandle(pi.hProcess);
        CloseHandle(pi.hThread);
    } else {
        CloseHandle(hWrite);
    }
    CloseHandle(hRead);
    free(cmdStr);
    return result;
}

void ExtractApkMetadataAndIcon(const std::string& apkPath, json& appNode) {
    if (!fs::exists(apkPath)) return;

    std::string aaptPath = GetAaptPath();
    if (aaptPath.empty()) return;

    std::string absApkPath = fs::absolute(apkPath).string();
    std::string dump = RunAaptBadging(aaptPath, absApkPath);

    std::string pkg = "";
    size_t pkgPos = dump.find("package: name='");
    if (pkgPos != std::string::npos) {
        pkgPos += 15;
        size_t end = dump.find("'", pkgPos);
        if (end != std::string::npos) {
            pkg = dump.substr(pkgPos, end - pkgPos);
        }
    }

    std::string vName = "";
    size_t vNamePos = dump.find("versionName='");
    if (vNamePos != std::string::npos) {
        vNamePos += 13;
        size_t end = dump.find("'", vNamePos);
        if (end != std::string::npos) {
            vName = dump.substr(vNamePos, end - vNamePos);
        }
    }

    std::string label = "";
    size_t labelPos = dump.find("application-label:'");
    if (labelPos == std::string::npos) labelPos = dump.find("application: label='");
    if (labelPos != std::string::npos) {
        labelPos = dump.find("'", labelPos) + 1;
        size_t end = dump.find("'", labelPos);
        if (end != std::string::npos) {
            label = dump.substr(labelPos, end - labelPos);
        }
    }

    if (!pkg.empty()) {
        appNode["package_name"] = pkg;
    }
    if (!label.empty()) {
        std::string currentName = appNode.value("name", "");
        if (currentName.empty() || currentName.rfind("unknown", 0) == 0 || currentName.find(".apk") != std::string::npos) {
            appNode["name"] = label;
        }
    }
    if (!vName.empty() && appNode.contains("versions") && !appNode["versions"].empty()) {
        if (appNode["versions"][0].value("version", "") == "1.0") {
            appNode["versions"][0]["version"] = vName;
        }
    }

    std::string pkgNameStr = appNode.value("package_name", "");
    if (pkgNameStr.empty() || pkgNameStr.rfind("unknown.package", 0) == 0) {
        pkgNameStr = fs::path(apkPath).stem().string();
    }

    std::string candidatePng = "";
    std::vector<std::string> keys = {"application-icon-640:'", "application-icon-480:'", "application-icon-320:'", "application-icon-240:'", "application-icon-160:'", "icon='"};
    for (const auto& k : keys) {
        size_t pos = dump.find(k);
        if (pos != std::string::npos) {
            pos += k.length();
            size_t end = dump.find("'", pos);
            if (end != std::string::npos) {
                std::string pathInApk = dump.substr(pos, end - pos);
                if (pathInApk.length() >= 4 && pathInApk.substr(pathInApk.length() - 4) == ".png") {
                    candidatePng = pathInApk;
                    break;
                }
            }
        }
    }

    fs::create_directories(imgDir);
    std::string outIconName = pkgNameStr + "_icon.png";
    std::string outIconPath = imgDir + "\\" + outIconName;
    std::string absOutIconPath = fs::absolute(outIconPath).string();

    mz_zip_archive zip_archive;
    memset(&zip_archive, 0, sizeof(zip_archive));
    if (mz_zip_reader_init_file(&zip_archive, absApkPath.c_str(), 0)) {
        int target_index = -1;
        if (!candidatePng.empty()) {
            target_index = mz_zip_reader_locate_file(&zip_archive, candidatePng.c_str(), NULL, 0);
        }
        if (target_index < 0) {
            std::vector<std::string> priorities = {
                "res/mipmap-xxxhdpi-v4/ic_launcher.png", "res/mipmap-xxhdpi-v4/ic_launcher.png",
                "res/mipmap-xhdpi-v4/ic_launcher.png", "res/mipmap-hdpi-v4/ic_launcher.png",
                "res/mipmap-mdpi-v4/ic_launcher.png", "res/drawable-xxhdpi-v4/ic_launcher.png",
                "res/drawable-xhdpi-v4/ic_launcher.png", "res/drawable-hdpi-v4/ic_launcher.png"
            };
            for (const auto& p : priorities) {
                target_index = mz_zip_reader_locate_file(&zip_archive, p.c_str(), NULL, 0);
                if (target_index >= 0) break;
            }
            if (target_index < 0) {
                mz_uint num_files = mz_zip_reader_get_num_files(&zip_archive);
                mz_uint64 max_size = 0;
                int best_icon = -1;
                for (mz_uint i = 0; i < num_files; i++) {
                    mz_zip_archive_file_stat file_stat;
                    if (mz_zip_reader_file_stat(&zip_archive, i, &file_stat)) {
                        std::string name = file_stat.m_filename;
                        if (name.length() >= 4 && name.substr(name.length()-4) == ".png" && name.find(".9.png") == std::string::npos) {
                            if (name.find("ic_launcher") != std::string::npos || name.find("icon") != std::string::npos || name.find("res/") != std::string::npos) {
                                if (file_stat.m_uncomp_size > max_size) {
                                    max_size = file_stat.m_uncomp_size;
                                    best_icon = i;
                                }
                            }
                        }
                    }
                }
                if (best_icon >= 0) target_index = best_icon;
            }
        }
        if (target_index >= 0) {
            mz_zip_reader_extract_to_file(&zip_archive, target_index, absOutIconPath.c_str(), 0);
        }
        mz_zip_reader_end(&zip_archive);
    }

    if (fs::exists(outIconPath)) {
        appNode["icon"] = outIconName;
    }
}

void ParseApkMetadata(std::string apkPath) {
    json tempApp;
    tempApp["name"] = "";
    tempApp["package_name"] = "";
    ExtractApkMetadataAndIcon(apkPath, tempApp);

    if (tempApp.contains("name") && !tempApp["name"].get<std::string>().empty()) {
        SetWindowTextA(hwndName, tempApp["name"].get<std::string>().c_str());
    }
    if (tempApp.contains("package_name") && !tempApp["package_name"].get<std::string>().empty()) {
        SetWindowTextA(hwndPackage, tempApp["package_name"].get<std::string>().c_str());
    }
    if (tempApp.contains("versions") && !tempApp["versions"].empty()) {
        SetWindowTextA(hwndVersion, tempApp["versions"][0].value("version", "").c_str());
    }

    LogMessage("Extracted metadata and icon from " + apkPath);
}


int AddImageToImageList(HIMAGELIST hIml, const std::string& path) {
    if (!fs::exists(path)) return -1;
    std::wstring wpath(path.begin(), path.end());
    Gdiplus::Bitmap* bmp = Gdiplus::Bitmap::FromFile(wpath.c_str());
    int idx = -1;
    if (bmp && bmp->GetLastStatus() == Gdiplus::Ok) {
        int w = bmp->GetWidth();
        int h = bmp->GetHeight();
        float scale = std::min((float)100/w, (float)100/h);
        int newW = std::max(1, (int)(w * scale));
        int newH = std::max(1, (int)(h * scale));
        Gdiplus::Bitmap* resized = new Gdiplus::Bitmap(100, 100, PixelFormat32bppARGB);
        Gdiplus::Graphics g(resized);
        g.Clear(Gdiplus::Color(255,255,255,255));
        g.SetInterpolationMode(Gdiplus::InterpolationModeHighQualityBicubic);
        g.DrawImage(bmp, (100-newW)/2, (100-newH)/2, newW, newH);
        HBITMAP hBmp = NULL;
        resized->GetHBITMAP(Gdiplus::Color(255, 255, 255), &hBmp);
        if (hBmp) {
            idx = ImageList_Add(hIml, hBmp, NULL);
            DeleteObject(hBmp);
        }
        delete resized;
        delete bmp;
    }
    return idx;
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
    SendMessageA(hwndPreview, STM_SETIMAGE, IMAGE_BITMAP, (LPARAM)hPreviewBitmap);
}

void InitTrayIcon(HWND hwnd) {
    NOTIFYICONDATAA nid = {};
    nid.cbSize = sizeof(NOTIFYICONDATAA);
    nid.hWnd = hwnd;
    nid.uID = ID_TRAY_APP_ICON;
    nid.uFlags = NIF_ICON | NIF_MESSAGE | NIF_TIP;
    nid.uCallbackMessage = WM_TRAYICON;
    nid.hIcon = GetDynamicAppIcon((HINSTANCE)GetWindowLongPtr(hwnd, GWLP_HINSTANCE));
    strcpy(nid.szTip, "Local APK Store Server");
    Shell_NotifyIconA(NIM_ADD, &nid);
}

void RemoveTrayIcon(HWND hwnd) {
    NOTIFYICONDATAA nid = {};
    nid.cbSize = sizeof(NOTIFYICONDATAA);
    nid.hWnd = hwnd;
    nid.uID = ID_TRAY_APP_ICON;
    Shell_NotifyIconA(NIM_DELETE, &nid);
}

void SaveConfig(HWND hwnd) {
    json j;
    j["server_port"] = serverPort;
    j["apk_dir"] = apkDir;
    j["img_dir"] = imgDir;
    
    WINDOWPLACEMENT wp;
    wp.length = sizeof(WINDOWPLACEMENT);
    if (hwnd && GetWindowPlacement(hwnd, &wp)) {
        j["window_maximized"] = (wp.showCmd == SW_SHOWMAXIMIZED);
        int normW = wp.rcNormalPosition.right - wp.rcNormalPosition.left;
        j["window_width"] = normW;
        j["window_height"] = wp.rcNormalPosition.bottom - wp.rcNormalPosition.top;
        j["window_x"] = wp.rcNormalPosition.left;
        j["window_y"] = wp.rcNormalPosition.top;
        
        if (wp.showCmd == SW_SHOWMAXIMIZED) {
            RECT rc; GetClientRect(hwnd, &rc);
            int curW = rc.right;
            j["listview_width"] = g_listWidth - (curW - normW);
        } else {
            j["listview_width"] = g_listWidth;
        }
    } else {
        j["window_width"] = g_windowWidth;
        j["window_height"] = g_windowHeight;
        j["window_maximized"] = g_windowMaximized;
        j["listview_width"] = g_listWidth;
        j["window_x"] = -1;
        j["window_y"] = -1;
    }
    
    if (hwndApps && IsWindow(hwndApps)) {
        json cols = json::array();
        for (int i = 0; i < 5; i++) {
            cols.push_back(ListView_GetColumnWidth(hwndApps, i));
        }
        j["list_cols"] = cols;
    }
    
    std::ofstream o(configFile);
    o << j.dump(4);
}

void LoadConfig() {
    if (fs::exists(configFile)) {
        try {
            std::ifstream i(configFile);
            json j; i >> j;
            serverPort = j.value("server_port", 8552);
            apkDir = j.value("apk_dir", "apks");
            imgDir = j.value("img_dir", "images");
            g_windowWidth = j.value("window_width", 1000);
            g_windowHeight = j.value("window_height", 700);
            g_windowX = j.value("window_x", CW_USEDEFAULT);
            g_windowY = j.value("window_y", CW_USEDEFAULT);
            g_windowMaximized = j.value("window_maximized", false);
            g_listWidth = j.value("listview_width", 350);
            if (j.contains("list_cols") && j["list_cols"].is_array()) {
                auto cols = j["list_cols"];
                for (size_t i = 0; i < cols.size() && i < g_listCols.size(); i++) {
                    g_listCols[i] = cols[i].get<int>();
                }
            }
        } catch(...) {}
    } else {
        SaveConfig(NULL);
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

    // Auto extract metadata and icon for any apps missing an icon or unknown package
    for (auto& app : dbCache["apps"]) {
        std::string pkg = app.value("package_name", "");
        std::string iconVal = app.value("icon", "");
        if (iconVal.empty() || pkg.empty() || pkg.find("unknown.package") == 0 || !fs::exists(fs::path(imgDir) / iconVal)) {
            std::string apkFile = "";
            if (app.contains("versions") && !app["versions"].empty()) {
                apkFile = app["versions"][0].value("file", "");
            }
            if (!apkFile.empty()) {
                std::string fullApkPath = apkDir + "/" + apkFile;
                if (fs::exists(fullApkPath)) {
                    ExtractApkMetadataAndIcon(fullApkPath, app);
                    dbUpdated = true;
                }
            }
        }
    }

    if (dbUpdated) saveDb(dbCache);

    // Refresh Category Combobox
    SendMessageA(hwndCat, CB_RESETCONTENT, 0, 0);
    const char* defaultCats[] = {"Games", "Productivity", "Social", "Tools", "Entertainment", "Education", "Other"};
    for (const char* c : defaultCats) SendMessageA(hwndCat, CB_ADDSTRING, 0, (LPARAM)c);

    std::vector<std::string> cats;
    for (auto& app : dbCache["apps"]) {
        std::string c = app.value("category", "");
        if (!c.empty() && std::find(cats.begin(), cats.end(), c) == cats.end()) {
            cats.push_back(c);
            if (SendMessageA(hwndCat, CB_FINDSTRINGEXACT, -1, (LPARAM)c.c_str()) == CB_ERR) {
                SendMessageA(hwndCat, CB_ADDSTRING, 0, (LPARAM)c.c_str());
            }
        }
    }

    // Refresh ListView Items and ImageList
    if (!hSmallIcons) {
        hSmallIcons = ImageList_Create(32, 32, ILC_COLOR32 | ILC_MASK, 10, 100);
        if (hwndApps) ListView_SetImageList(hwndApps, hSmallIcons, LVSIL_SMALL);
    } else {
        ImageList_RemoveAll(hSmallIcons);
    }

    HICON hDefaultIcon = (HICON)LoadImageA(GetModuleHandle(NULL), MAKEINTRESOURCE(111), IMAGE_ICON, 32, 32, LR_DEFAULTCOLOR);
    if (hDefaultIcon) {
        ImageList_AddIcon(hSmallIcons, hDefaultIcon);
        DestroyIcon(hDefaultIcon);
    }

    ListView_DeleteAllItems(hwndApps);
    for (size_t i = 0; i < dbCache["apps"].size(); i++) {
        auto& app = dbCache["apps"][i];
        std::string name = app.value("name", "Unknown");
        std::string pkg = app.value("package_name", "unknown.pkg");
        std::string version = app.contains("versions") && !app["versions"].empty() ? app["versions"].back().value("version", "1.0") : "1.0";
        std::string apkFile = app.contains("versions") && !app["versions"].empty() ? app["versions"].back().value("file", "") : "";
        std::string sizeStr = "N/A";
        if (!apkFile.empty()) {
            std::string fullPath = apkDir + "/" + apkFile;
            if (fs::exists(fullPath)) {
                try {
                    auto sz = fs::file_size(fullPath);
                    char buf[32];
                    sprintf(buf, "%.1f MB", (double)sz / (1024.0 * 1024.0));
                    sizeStr = buf;
                } catch(...) {}
            }
        }

        std::string iconFile = app.value("icon", "");
        int imgIndex = 0; // Default icon is now always at index 0
        if (!iconFile.empty()) {
            std::string fullIconPath = imgDir + "/" + iconFile;
            if (fs::exists(fullIconPath)) {
                std::wstring wpath(fullIconPath.begin(), fullIconPath.end());
                Bitmap* bmp = Bitmap::FromFile(wpath.c_str());
                if (bmp && bmp->GetLastStatus() == Ok) {
                    HICON hIcon = NULL;
                    bmp->GetHICON(&hIcon);
                    if (hIcon) {
                        imgIndex = ImageList_AddIcon(hSmallIcons, hIcon);
                        DestroyIcon(hIcon);
                    }
                    delete bmp;
                }
            }
        }

        LVITEMA lvi = {0};
        lvi.mask = LVIF_TEXT | LVIF_IMAGE | LVIF_PARAM;
        lvi.iItem = (int)i;
        lvi.iSubItem = 0;
        lvi.pszText = (LPSTR)name.c_str();
        lvi.iImage = imgIndex;
        lvi.lParam = (LPARAM)i;
        int idx = ListView_InsertItem(hwndApps, &lvi);

        ListView_SetItemText(hwndApps, idx, 1, (LPSTR)pkg.c_str());
        ListView_SetItemText(hwndApps, idx, 2, (LPSTR)version.c_str());
        ListView_SetItemText(hwndApps, idx, 3, (LPSTR)sizeStr.c_str());
        ListView_SetItemText(hwndApps, idx, 4, (LPSTR)"Available");
    }
}

void LoadAppIntoForm(int index) {
    if (index < 0 || index >= (int)dbCache["apps"].size()) return;
    auto& app = dbCache["apps"][index];
    SetWindowTextA(hwndName, app.value("name", "").c_str());
    SetWindowTextA(hwndPackage, app.value("package_name", "").c_str());
    if (app.contains("versions") && app["versions"].size() > 0) {
        SetWindowTextA(hwndVersion, app["versions"].back().value("version", "").c_str());
    } else { SetWindowTextA(hwndVersion, ""); }
    SetWindowTextA(hwndCat, app.value("category", "").c_str());
    SetWindowTextA(hwndDesc, app.value("description", "").c_str());
    std::string tagsStr = "";
    if (app.contains("tags")) {
        for (size_t i = 0; i < app["tags"].size(); i++) {
            tagsStr += app["tags"][i].get<std::string>();
            if (i < app["tags"].size() - 1) tagsStr += ", ";
        }
    }
    SetWindowTextA(hwndTags, tagsStr.c_str());
    ListView_DeleteAllItems(lstScreenshots); ImageList_RemoveAll(g_hImgListSS);
    screenshots.clear();
    if (app.contains("screenshots")) {
        for (auto& s : app["screenshots"]) {
            std::string sPath = imgDir + "\\" + s.get<std::string>();
            screenshots.push_back(sPath);
            int imgIdx = AddImageToImageList(g_hImgListSS, sPath);
            LVITEMA lvi = {0};
            lvi.mask = LVIF_TEXT | LVIF_IMAGE;
            lvi.iItem = ListView_GetItemCount(lstScreenshots);
            lvi.iImage = imgIdx;
            lvi.pszText = (LPSTR)s.get<std::string>().c_str();
            ListView_InsertItem(lstScreenshots, &lvi);
        }
    }
    filePath[0] = '\0';
    SetWindowTextA(hwndApkLabel, "No new APK selected");
    if (screenshots.size() > 0) {
        UpdatePreviewImage(screenshots[0]);
    } else {
        std::string iconP = app.value("icon", "");
        if (!iconP.empty() && fs::exists(imgDir + "\\" + iconP)) {
            UpdatePreviewImage(imgDir + "\\" + iconP);
        } else {
            UpdatePreviewImage("");
        }
    }
}

void ClearForm() {
    selectedAppIndex = -1;
    if (hwndApps) {
        ListView_SetItemState(hwndApps, -1, 0, LVIS_SELECTED);
    }
    SetWindowTextA(hwndName, ""); SetWindowTextA(hwndPackage, "");
    SetWindowTextA(hwndVersion, ""); SetWindowTextA(hwndCat, "");
    SetWindowTextA(hwndDesc, ""); SetWindowTextA(hwndTags, "");
    ListView_DeleteAllItems(lstScreenshots); ImageList_RemoveAll(g_hImgListSS);
    screenshots.clear(); filePath[0] = '\0';
    SetWindowTextA(hwndApkLabel, "No APK selected");
    UpdatePreviewImage("");
}

void DeleteSelectedApp() {
    if (selectedAppIndex >= 0 && selectedAppIndex < (int)dbCache["apps"].size()) {
        if (MessageBoxA(hwndMain, "Are you sure you want to delete the selected application entry?", "Confirm Delete", MB_YESNO | MB_ICONQUESTION) == IDYES) {
            dbCache["apps"].erase(dbCache["apps"].begin() + selectedAppIndex);
            saveDb(dbCache);
            ClearForm();
            RefreshAppList();
            LogToFileAndUI("Deleted application entry at index " + std::to_string(selectedAppIndex));
        }
    } else {
        MessageBoxA(hwndMain, "Please select an application to delete.", "No Selection", MB_OK | MB_ICONINFORMATION);
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
    while (serverRunning) {
        int clientLen = sizeof(clientAddr);
        int bytes = recvfrom(udpSock, buffer, 255, 0, (sockaddr*)&clientAddr, &clientLen);
        if (bytes > 0) {
            buffer[bytes] = '\0';
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

void ClientCleanupThread() {
    const int CLIENT_TIMEOUT_SECONDS = 15;
    while (serverRunning) {
        std::this_thread::sleep_for(std::chrono::seconds(3));
        if (!serverRunning) break;
        auto now = std::chrono::steady_clock::now();
        std::vector<std::string> timedOutLogs;
        {
            std::lock_guard<std::mutex> lock(g_clientMutex);
            for (auto it = g_connectedClients.begin(); it != g_connectedClients.end(); ) {
                auto elapsed = std::chrono::duration_cast<std::chrono::seconds>(now - it->second.last_seen).count();
                if (elapsed > CLIENT_TIMEOUT_SECONDS) {
                    timedOutLogs.push_back("Client disconnected (timeout): " + it->second.device_name + " (" + it->second.ip_address + ")");
                    it = g_connectedClients.erase(it);
                } else {
                    ++it;
                }
            }
        }
        for (const auto& logMsg : timedOutLogs) {
            LogMessage(logMsg);
        }
        if (!timedOutLogs.empty() && hwndMain) {
            PostMessageA(hwndMain, WM_COMMAND, 5001, 0);
        }
    }
}

void RefreshClientListView() {
    if (!hwndClientList || !IsWindow(hwndClientList)) return;

    std::lock_guard<std::mutex> lock(g_clientMutex);

    SendMessageA(hwndClientList, WM_SETREDRAW, FALSE, 0);
    ListView_DeleteAllItems(hwndClientList);

    int index = 0;
    auto now = std::chrono::steady_clock::now();
    for (const auto& pair : g_connectedClients) {
        const auto& client = pair.second;
        LVITEMA lvi = {0};
        lvi.mask = LVIF_TEXT;
        lvi.iItem = index;
        lvi.iSubItem = 0;
        lvi.pszText = (LPSTR)client.ip_address.c_str();
        ListView_InsertItem(hwndClientList, &lvi);

        ListView_SetItemText(hwndClientList, index, 1, (LPSTR)client.device_name.c_str());

        auto secAgo = std::chrono::duration_cast<std::chrono::seconds>(now - client.last_seen).count();
        std::string statusStr = std::to_string(secAgo) + "s ago";
        ListView_SetItemText(hwndClientList, index, 2, (LPSTR)statusStr.c_str());

        index++;
    }

    SendMessageA(hwndClientList, WM_SETREDRAW, TRUE, 0);
    InvalidateRect(hwndClientList, NULL, TRUE);

    if (lblConnectedClients && IsWindow(lblConnectedClients)) {
        std::string countStr = "Connected Clients (" + std::to_string(g_connectedClients.size()) + "):";
        SetWindowTextA(lblConnectedClients, countStr.c_str());
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
                std::string d = app.value("description", "");
                std::transform(n.begin(), n.end(), n.begin(), ::tolower);
                std::transform(d.begin(), d.end(), d.begin(), ::tolower);
                if (n.find(q) != std::string::npos || d.find(q) != std::string::npos) filtered.push_back(app);
            }
            json out; out["apps"] = filtered;
            res.set_content(out.dump(), "application/json");
        } else { res.set_content(db.dump(), "application/json"); }
    });
    svrPtr->Post("/api/heartbeat", [](const httplib::Request& req, httplib::Response& res) {
        try {
            json j = json::parse(req.body);
            std::string clientId = j.value("client_id", req.remote_addr);
            std::string deviceName = j.value("device_name", "Android Device");
            std::string ip = req.remote_addr;

            {
                std::lock_guard<std::mutex> lock(g_clientMutex);
                g_connectedClients[clientId] = ClientInfo{
                    clientId, ip, deviceName, std::chrono::steady_clock::now()
                };
            }
            if (hwndMain) PostMessageA(hwndMain, WM_COMMAND, 5001, 0);
            res.set_content("{\"status\":\"ok\"}", "application/json");
        } catch (...) {
            res.status = 400;
            res.set_content("{\"error\":\"invalid json\"}", "application/json");
        }
    });

    
    svrPtr->Post("/api/upload_apk", [](const httplib::Request& req, httplib::Response& res, const httplib::ContentReader& content_reader) {
        if (!req.has_header("X-File-Name")) {
            res.status = 400;
            res.set_content("{\"error\":\"Missing X-File-Name header\"}", "application/json");
            return;
        }
        std::string filename = req.get_header_value("X-File-Name");
        std::string path = "apks/" + filename;
        std::ofstream ofs(path, std::ios::binary);
        if (ofs) {
            content_reader([&](const char* data, size_t data_length) {
                ofs.write(data, data_length);
                return true;
            });
            ofs.close();
            res.set_content("{\"status\":\"ok\"}", "application/json");
        } else {
            res.status = 500;
            res.set_content("{\"error\":\"Could not open file for writing\"}", "application/json");
        }
    });

    svrPtr->Post("/api/upload_image", [](const httplib::Request& req, httplib::Response& res, const httplib::ContentReader& content_reader) {
        if (!req.has_header("X-File-Name")) {
            res.status = 400;
            res.set_content("{\"error\":\"Missing X-File-Name header\"}", "application/json");
            return;
        }
        std::string filename = req.get_header_value("X-File-Name");
        std::string path = "images/" + filename;
        std::ofstream ofs(path, std::ios::binary);
        if (ofs) {
            content_reader([&](const char* data, size_t data_length) {
                ofs.write(data, data_length);
                return true;
            });
            ofs.close();
            res.set_content("{\"status\":\"ok\"}", "application/json");
        } else {
            res.status = 500;
            res.set_content("{\"error\":\"Could not open file for writing\"}", "application/json");
        }
    });

    svrPtr->Post("/api/update_app", [](const httplib::Request& req, httplib::Response& res) {
        try {
            json j = json::parse(req.body);
            std::string pkg = j.value("package_name", "");
            if (pkg.empty()) {
                res.status = 400;
                res.set_content("{\"error\":\"missing package_name\"}", "application/json");
                return;
            }

            json db = loadDb();
            bool found = false;
            for (auto& app : db["apps"]) {
                if (app["package_name"] == pkg) {
                    // Update existing app
                    if (j.contains("name")) app["name"] = j["name"];
                    if (j.contains("description")) app["description"] = j["description"];
                    if (j.contains("category")) app["category"] = j["category"];
                    if (j.contains("icon")) app["icon"] = j["icon"];
                    
                    if (j.contains("tags") && j["tags"].is_array()) {
                        app["tags"] = j["tags"];
                    }
                    if (j.contains("screenshots") && j["screenshots"].is_array()) {
                        app["screenshots"] = j["screenshots"];
                    }
                    if (j.contains("versions") && j["versions"].is_array()) {
                        // Merge versions
                        for (auto& newV : j["versions"]) {
                            std::string newVerName = newV.value("version", "");
                            bool vFound = false;
                            for (auto& oldV : app["versions"]) {
                                if (oldV["version"] == newVerName) {
                                    vFound = true;
                                    break;
                                }
                            }
                            if (!vFound) {
                                app["versions"].push_back(newV);
                            }
                        }
                    }
                    found = true;
                    break;
                }
            }

            if (!found) {
                // Insert as new app
                db["apps"].push_back(j);
            }

            saveDb(db);
            
            // Trigger UI refresh
            PostMessageA(hwndMain, WM_COMMAND, 5000, 0);

            res.set_content("{\"status\":\"ok\"}", "application/json");
        } catch (...) {
            res.status = 400;
            res.set_content("{\"error\":\"invalid json\"}", "application/json");
        }
    });

svrPtr->Post("/api/disconnect", [](const httplib::Request& req, httplib::Response& res) {
        try {
            json j = json::parse(req.body);
            std::string clientId = j.value("client_id", req.remote_addr);
            std::string deviceName = "";
            bool found = false;
            {
                std::lock_guard<std::mutex> lock(g_clientMutex);
                auto it = g_connectedClients.find(clientId);
                if (it != g_connectedClients.end()) {
                    deviceName = it->second.device_name;
                    g_connectedClients.erase(it);
                    found = true;
                }
            }
            if (found) {
                LogMessage("Client disconnected (explicit): " + deviceName + " (" + req.remote_addr + ")");
                if (hwndMain) PostMessageA(hwndMain, WM_COMMAND, 5001, 0);
            }
            res.set_content("{\"status\":\"disconnected\"}", "application/json");
        } catch (...) {
            res.status = 400;
            res.set_content("{\"error\":\"invalid json\"}", "application/json");
        }
    });
    svrPtr->set_mount_point("/apks", apkDir.c_str());
    svrPtr->set_mount_point("/images", imgDir.c_str());

    // Removed testSock check to avoid TIME_WAIT blocking the port for httplib
    LogMessage("HTTP API Listening on port " + std::to_string(serverPort));
    bool success = svrPtr->listen("0.0.0.0", serverPort);
    if (!success) {
        LogMessage("ERROR: HTTP Server failed to bind to port " + std::to_string(serverPort));
        serverRunning = false;
        if (hwndServerStatus && IsWindow(hwndServerStatus)) {
            SetWindowTextA(hwndServerStatus, "Status: STOPPED (Port Error)");
        }
        if (btnToggleServer && IsWindow(btnToggleServer)) {
            SetWindowTextA(btnToggleServer, "Start Server");
        }
        g_serverError = true;
        UpdateServerStatusUI();
    }
}

DWORD g_timeServerStopped = 0;
bool g_serverError = false;
HIMAGELIST g_hTabImageList = NULL;

void UpdateServerStatusUI() {
    if (!hwndMain) return;
    HMENU hMenuMain = GetMenu(hwndMain);
    if (!hMenuMain) return;
    
    int statusIconId = 107;
    std::string statusText = "Status: OFF";
    std::string toggleText = "Toggle Server: Enable";
    
    if (serverRunning) {
        statusIconId = 108;
        statusText = "Status: RUNNING";
        toggleText = "Toggle Server: Disable";
    } else {
        if (g_serverError) {
            statusIconId = 110;
            statusText = "Status: ERROR";
        } else if (g_timeServerStopped != 0 && (GetTickCount() - g_timeServerStopped) > 30000) {
            statusIconId = 107;
        } else {
            statusIconId = 109;
        }
    }
    
    static HBITMAP hBmpOn = LoadIconAsHBitmap(GetModuleHandle(NULL), 108, 16, 16);
    static HBITMAP hBmpOff = LoadIconAsHBitmap(GetModuleHandle(NULL), 109, 16, 16);
    static HBITMAP hBmpIdle = LoadIconAsHBitmap(GetModuleHandle(NULL), 107, 16, 16);
    static HBITMAP hBmpErr = LoadIconAsHBitmap(GetModuleHandle(NULL), 110, 16, 16);
    
    HBITMAP hBmpCurrent = hBmpIdle;
    if (statusIconId == 108) hBmpCurrent = hBmpOn;
    else if (statusIconId == 109) hBmpCurrent = hBmpOff;
    else if (statusIconId == 110) hBmpCurrent = hBmpErr;
    
    MENUITEMINFOA mii = {0};
    mii.cbSize = sizeof(MENUITEMINFOA);
    mii.fMask = MIIM_STRING | MIIM_BITMAP;
    mii.dwTypeData = (LPSTR)statusText.c_str();
    mii.hbmpItem = hBmpCurrent;
    SetMenuItemInfoA(hMenuMain, 2008, FALSE, &mii);
    
    MENUITEMINFOA miiToggle = {0};
    miiToggle.cbSize = sizeof(MENUITEMINFOA);
    miiToggle.fMask = MIIM_STRING | MIIM_STATE | MIIM_BITMAP;
    miiToggle.fState = serverRunning ? MFS_CHECKED : MFS_UNCHECKED;
    miiToggle.dwTypeData = (LPSTR)toggleText.c_str();
    miiToggle.hbmpItem = hBmpCurrent;
    SetMenuItemInfoA(hMenuMain, 2005, FALSE, &miiToggle);
    CheckMenuRadioItem(hMenuMain, 2005, 2005, 2005, MF_BYCOMMAND);
    
    DrawMenuBar(hwndMain);
}

void StartServer() {
    if (serverRunning) return;
    if (tServer && tServer->joinable()) { tServer->join(); delete tServer; tServer = nullptr; }
    if (tUdp && tUdp->joinable()) { tUdp->join(); delete tUdp; tUdp = nullptr; }
    if (tCleanup && tCleanup->joinable()) { tCleanup->join(); delete tCleanup; tCleanup = nullptr; }
    if (svrPtr) { delete svrPtr; svrPtr = nullptr; }
    serverRunning = true;
    LogMessage("Starting Elite Marketplace Server...");
    tServer = new std::thread(ServerThread);
    tUdp = new std::thread(UDPDiscoveryThread);
    tCleanup = new std::thread(ClientCleanupThread);
    SetWindowTextA(hwndServerStatus, "Status: RUNNING");
    SetWindowTextA(btnToggleServer, "Stop Server");
    g_serverError = false;
    UpdateServerStatusUI();
}

void StopServer() {
    if (!serverRunning) return;
    serverRunning = false;
    LogMessage("Stopping Elite Marketplace Server...");
    if (svrPtr) { svrPtr->stop(); }
    if (udpSock != INVALID_SOCKET) { closesocket(udpSock); udpSock = INVALID_SOCKET; }
    if (tServer && tServer->joinable()) { tServer->join(); delete tServer; tServer = nullptr; }
    if (tUdp && tUdp->joinable()) { tUdp->join(); delete tUdp; tUdp = nullptr; }
    if (tCleanup && tCleanup->joinable()) { tCleanup->join(); delete tCleanup; tCleanup = nullptr; }
    if (svrPtr) { delete svrPtr; svrPtr = nullptr; }
    {
        std::lock_guard<std::mutex> lock(g_clientMutex);
        g_connectedClients.clear();
    }
    SetWindowTextA(hwndServerStatus, "Status: STOPPED");
    SetWindowTextA(btnToggleServer, "Start Server");
    g_timeServerStopped = GetTickCount();
    g_serverError = false;
    UpdateServerStatusUI();
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
            std::string iconP = imgDir + "/" + pkg + "_icon.png";
            if (fs::exists(iconP)) app["icon"] = pkg + "_icon.png";
            break;
        }
    }
    if (!exists) {
        if (apkName.empty()) {
            MessageBoxA(hwndMain, "An APK file is required for new applications!", "Validation Error", MB_OK | MB_ICONWARNING);
            return;
        }
        json newApp;
        newApp["name"] = name; newApp["package_name"] = pkg; newApp["description"] = desc;
        newApp["category"] = cat; newApp["tags"] = tags;
        newApp["versions"] = json::array(); newApp["versions"].push_back({{"version", ver}, {"file", apkName}});
        newApp["screenshots"] = copiedScreenshots; newApp["reviews"] = json::array();
        std::string iconP = imgDir + "/" + pkg + "_icon.png";
        if (fs::exists(iconP)) newApp["icon"] = pkg + "_icon.png";
        db["apps"].push_back(newApp);
    }
    saveDb(db); RefreshAppList();
    MessageBoxA(hwndMain, "Application entry processed and saved successfully!", "Success", MB_OK | MB_ICONINFORMATION);
}

// Dialog Procedures
LRESULT CALLBACK AboutDialogProc(HWND hwnd, UINT uMsg, WPARAM wParam, LPARAM lParam) {
    static bool expanded = false;
    static HWND hBtnDetails = NULL;
    static HWND hTxtDetails = NULL;
    static HFONT hBoldFont = NULL;
    static HFONT hNormalFont = NULL;

    switch (uMsg) {
    case WM_PAINT: {
        PAINTSTRUCT ps;
        HDC hdc = BeginPaint(hwnd, &ps);
        RECT clientRect; GetClientRect(hwnd, &clientRect);
        
        RECT bannerRect = {0, 0, clientRect.right, 42};
        HBRUSH hbrBanner = CreateSolidBrush(RGB(255, 255, 255));
        FillRect(hdc, &bannerRect, hbrBanner);
        DeleteObject(hbrBanner);
        
        DrawIconEx(hdc, 15, 5, LoadIcon(NULL, IDI_INFORMATION), 32, 32, 0, NULL, DI_NORMAL | DI_COMPAT);
        
        EndPaint(hwnd, &ps);
        return 0;
    }
    case WM_CREATE: {
        expanded = false;
        hNormalFont = CreateFontA(14, 0, 0, 0, FW_NORMAL, FALSE, FALSE, FALSE, DEFAULT_CHARSET, OUT_DEFAULT_PRECIS, CLIP_DEFAULT_PRECIS, CLEARTYPE_QUALITY, DEFAULT_PITCH | FF_SWISS, "Segoe UI");
        hBoldFont = CreateFontA(16, 0, 0, 0, FW_BOLD, FALSE, FALSE, FALSE, DEFAULT_CHARSET, OUT_DEFAULT_PRECIS, CLIP_DEFAULT_PRECIS, CLEARTYPE_QUALITY, DEFAULT_PITCH | FF_SWISS, "Segoe UI");

        // Icon drawn in WM_PAINT instead for transparency over banner

        HWND hTitle = CreateWindowA("STATIC", "Local APK Store Manager v1.2.0.0", WS_CHILD | WS_VISIBLE, 60, 12, 360, 24, hwnd, NULL, NULL, NULL);
        SendMessageA(hTitle, WM_SETFONT, (WPARAM)hBoldFont, TRUE);

        HWND hDesc = CreateWindowA("STATIC", "EliteSoftwareTech Co. Win32 Store & Server Manager.\r\nDesigned with classic Win32/WinForms aesthetics and native visual styles.\r\n(c) 2026 EliteSoftwareTech Co. All Rights Reserved.", WS_CHILD | WS_VISIBLE, 60, 40, 360, 55, hwnd, NULL, NULL, NULL);
        SendMessageA(hDesc, WM_SETFONT, (WPARAM)hNormalFont, TRUE);

        CreateWindowExA(0, "STATIC", "", WS_CHILD | WS_VISIBLE | SS_ETCHEDHORZ, 15, 105, 410, 2, hwnd, NULL, NULL, NULL);

        hBtnDetails = CreateWindowA("BUTTON", "Details >>", WS_CHILD | WS_VISIBLE | BS_PUSHBUTTON, 15, 120, 100, 28, hwnd, (HMENU)101, NULL, NULL);
        HWND hBtnOkay = CreateWindowA("BUTTON", "Okay", WS_CHILD | WS_VISIBLE | BS_PUSHBUTTON, 325, 120, 100, 28, hwnd, (HMENU)IDOK, NULL, NULL);

        SendMessageA(hBtnDetails, WM_SETFONT, (WPARAM)hNormalFont, TRUE);
        SendMessageA(hBtnOkay, WM_SETFONT, (WPARAM)hNormalFont, TRUE);

        hTxtDetails = CreateWindowExA(WS_EX_CLIENTEDGE, "EDIT",
            "Technical Details:\r\n"
            "- Architecture: Win32 API / C++17 (GDI+, httplib, nlohmann_json)\r\n"
            "- Framework Target: Win32 Native Visual Styles (Legacy Aesthetic)\r\n"
            "- Default Port: 8552\r\n"
            "- Log Path: %SystemDrive%\\EliteSoftware\\Logs\\LocalAPKStore.log\r\n"
            "- Minimum OS: Windows Vista / 7\r\n"
            "- Authors: Zachary Whiteman, Susan Gemm, TheShadyRainbow4, EliteSoftwareTech Co.",
            WS_CHILD | WS_VSCROLL | ES_MULTILINE | ES_READONLY,
            15, 160, 410, 120, hwnd, (HMENU)102, NULL, NULL);
        SendMessageA(hTxtDetails, WM_SETFONT, (WPARAM)hNormalFont, TRUE);

        RECT parentRc, rc;
        GetWindowRect(GetParent(hwnd), &parentRc);
        GetWindowRect(hwnd, &rc);
        int x = parentRc.left + (parentRc.right - parentRc.left - 450) / 2;
        int y = parentRc.top + (parentRc.bottom - parentRc.top - 200) / 2;
        SetWindowPos(hwnd, NULL, x, y, 450, 200, SWP_NOZORDER);
        break;
    }
    case WM_CTLCOLORSTATIC:
    case WM_CTLCOLORBTN: {
        HDC hdcStatic = (HDC)wParam;
        SetBkMode(hdcStatic, TRANSPARENT);
        return (LRESULT)GetStockObject(HOLLOW_BRUSH);
    }
    case WM_COMMAND: {
        int id = LOWORD(wParam);
        if (id == IDOK || id == IDCANCEL) {
            DestroyWindow(hwnd);
        } else if (id == 101) {
            expanded = !expanded;
            if (expanded) {
                SetWindowTextA(hBtnDetails, "<< Details");
                ShowWindow(hTxtDetails, SW_SHOW);
                RECT rc; GetWindowRect(hwnd, &rc);
                SetWindowPos(hwnd, NULL, rc.left, rc.top, 450, 330, SWP_NOMOVE | SWP_NOZORDER);
            } else {
                SetWindowTextA(hBtnDetails, "Details >>");
                ShowWindow(hTxtDetails, SW_HIDE);
                RECT rc; GetWindowRect(hwnd, &rc);
                SetWindowPos(hwnd, NULL, rc.left, rc.top, 450, 200, SWP_NOMOVE | SWP_NOZORDER);
            }
        }
        break;
    }
    case WM_DESTROY:
        if (hNormalFont) DeleteObject(hNormalFont);
        if (hBoldFont) DeleteObject(hBoldFont);
        EnableWindow(GetParent(hwnd), TRUE);
        SetForegroundWindow(GetParent(hwnd));
        break;
    }
    return DefWindowProcA(hwnd, uMsg, wParam, lParam);
}

void ShowAboutDialog(HWND hwndParent) {
    static bool registered = false;
    HINSTANCE hInst = (HINSTANCE)GetWindowLongPtr(hwndParent, GWLP_HINSTANCE);
    if (!registered) {
        WNDCLASSA wc = {0};
        wc.lpfnWndProc = AboutDialogProc;
        wc.hInstance = hInst;
        wc.hIcon = LoadIcon(NULL, IDI_INFORMATION);
        wc.hbrBackground = (HBRUSH)(COLOR_BTNFACE + 1);
        wc.lpszClassName = "EliteAboutDialog";
        RegisterClassA(&wc);
        registered = true;
    }
    EnableWindow(hwndParent, FALSE);
    CreateWindowExA(WS_EX_DLGMODALFRAME, "EliteAboutDialog", "About Local APK Store",
        WS_POPUP | WS_CAPTION | WS_SYSMENU | WS_VISIBLE,
        CW_USEDEFAULT, CW_USEDEFAULT, 450, 200, hwndParent, NULL, hInst, NULL);
}

LRESULT CALLBACK HelpDialogProc(HWND hwnd, UINT uMsg, WPARAM wParam, LPARAM lParam) {
    static HFONT hNormalFont = NULL;
    static HFONT hBoldFont = NULL;

    switch (uMsg) {
    case WM_PAINT: {
        PAINTSTRUCT ps;
        HDC hdc = BeginPaint(hwnd, &ps);
        RECT clientRect; GetClientRect(hwnd, &clientRect);
        
        RECT bannerRect = {0, 0, clientRect.right, 42};
        HBRUSH hbrBanner = CreateSolidBrush(RGB(255, 255, 255));
        FillRect(hdc, &bannerRect, hbrBanner);
        DeleteObject(hbrBanner);
        
        HICON hHelpIcon = LoadIconA(GetModuleHandle(NULL), MAKEINTRESOURCE(102));
        if (hHelpIcon) DrawIconEx(hdc, 15, 5, hHelpIcon, 32, 32, 0, NULL, DI_NORMAL | DI_COMPAT);
        
        EndPaint(hwnd, &ps);
        return 0;
    }
    case WM_CREATE: {
        hNormalFont = CreateFontA(14, 0, 0, 0, FW_NORMAL, FALSE, FALSE, FALSE, DEFAULT_CHARSET, OUT_DEFAULT_PRECIS, CLIP_DEFAULT_PRECIS, CLEARTYPE_QUALITY, DEFAULT_PITCH | FF_SWISS, "Segoe UI");
        hBoldFont = CreateFontA(16, 0, 0, 0, FW_BOLD, FALSE, FALSE, FALSE, DEFAULT_CHARSET, OUT_DEFAULT_PRECIS, CLIP_DEFAULT_PRECIS, CLEARTYPE_QUALITY, DEFAULT_PITCH | FF_SWISS, "Segoe UI");

        HICON hHelpIcon = LoadIconA(GetModuleHandle(NULL), MAKEINTRESOURCE(102));
        SendMessageA(hwnd, WM_SETICON, ICON_BIG, (LPARAM)hHelpIcon);
        SendMessageA(hwnd, WM_SETICON, ICON_SMALL, (LPARAM)hHelpIcon);
        
        // Icon drawn in WM_PAINT instead for transparency over banner

        HWND hTitle = CreateWindowA("STATIC", "Local APK Store User Manual & Help Guidance", WS_CHILD | WS_VISIBLE, 60, 20, 420, 24, hwnd, NULL, NULL, NULL);
        SendMessageA(hTitle, WM_SETFONT, (WPARAM)hBoldFont, TRUE);

        CreateWindowExA(0, "STATIC", "", WS_CHILD | WS_VISIBLE | SS_ETCHEDHORZ, 15, 55, 470, 2, hwnd, NULL, NULL, NULL);

        HWND hHelpText = CreateWindowExA(WS_EX_CLIENTEDGE, "EDIT",
            "WELCOME TO LOCAL APK STORE MANAGER\r\n\r\n"
            "1. APP INVENTORY TAB:\r\n"
            "   - View all registered Android packages in the SysListView32 store index.\r\n"
            "   - Select an app from the list to populate its name, package, version, category, tags, and description.\r\n"
            "   - Click 'Browse APK...' to locate a local .apk file. The system will automatically attempt metadata extraction via aapt.exe.\r\n"
            "   - Click 'Add Screenshot' to attach PNG/JPG preview images.\r\n"
            "   - Click 'Apply' to save changes to the local db.json repository.\r\n"
            "   - Click 'Delete Selected' to remove an application entry.\r\n\r\n"
            "2. SERVER MONITOR TAB:\r\n"
            "   - Embedded HTTP server listens on port 8552 (or custom configured port).\r\n"
            "   - View real-time HTTP API logs and server activity.\r\n"
            "   - Click 'Start Server' / 'Stop Server' to toggle server state.\r\n\r\n"
            "3. LOG FILE INTEGRATION:\r\n"
            "   - All events are logged to %SystemDrive%\\EliteSoftware\\Logs\\LocalAPKStore.log.\r\n"
            "   - Click 'View LocalAPKStore Logs' at the bottom chin to view complete log history in Notepad.\r\n",
            WS_CHILD | WS_VISIBLE | WS_VSCROLL | ES_MULTILINE | ES_READONLY,
            15, 65, 470, 280, hwnd, NULL, NULL, NULL);
        SendMessageA(hHelpText, WM_SETFONT, (WPARAM)hNormalFont, TRUE);

        CreateWindowExA(0, "STATIC", "", WS_CHILD | WS_VISIBLE | SS_ETCHEDHORZ, 15, 355, 470, 2, hwnd, NULL, NULL, NULL);

        HWND hBtnOkay = CreateWindowA("BUTTON", "Okay", WS_CHILD | WS_VISIBLE | BS_PUSHBUTTON, 385, 365, 100, 28, hwnd, (HMENU)IDOK, NULL, NULL);
        SendMessageA(hBtnOkay, WM_SETFONT, (WPARAM)hNormalFont, TRUE);

        RECT parentRc, rc;
        GetWindowRect(GetParent(hwnd), &parentRc);
        GetWindowRect(hwnd, &rc);
        int x = parentRc.left + (parentRc.right - parentRc.left - 510) / 2;
        int y = parentRc.top + (parentRc.bottom - parentRc.top - 440) / 2;
        SetWindowPos(hwnd, NULL, x, y, 510, 440, SWP_NOZORDER);
        break;
    }
    case WM_CTLCOLORSTATIC:
    case WM_CTLCOLORBTN: {
        HDC hdcStatic = (HDC)wParam;
        SetBkMode(hdcStatic, TRANSPARENT);
        return (LRESULT)GetStockObject(HOLLOW_BRUSH);
    }
    case WM_COMMAND: {
        if (LOWORD(wParam) == IDOK || LOWORD(wParam) == IDCANCEL) {
            DestroyWindow(hwnd);
        }
        break;
    }
    case WM_DESTROY:
        if (hNormalFont) DeleteObject(hNormalFont);
        if (hBoldFont) DeleteObject(hBoldFont);
        EnableWindow(GetParent(hwnd), TRUE);
        SetForegroundWindow(GetParent(hwnd));
        break;
    }
    return DefWindowProcA(hwnd, uMsg, wParam, lParam);
}

void ShowHelpDialog(HWND hwndParent) {
    static bool registered = false;
    HINSTANCE hInst = (HINSTANCE)GetWindowLongPtr(hwndParent, GWLP_HINSTANCE);
    if (!registered) {
        WNDCLASSA wc = {0};
        wc.lpfnWndProc = HelpDialogProc;
        wc.hInstance = hInst;
        wc.hIcon = LoadIcon(NULL, IDI_QUESTION);
        wc.hbrBackground = (HBRUSH)(COLOR_BTNFACE + 1);
        wc.lpszClassName = "EliteHelpDialog";
        RegisterClassA(&wc);
        registered = true;
    }
    EnableWindow(hwndParent, FALSE);
    CreateWindowExA(WS_EX_DLGMODALFRAME, "EliteHelpDialog", "Local APK Store Help & Guidance",
        WS_POPUP | WS_CAPTION | WS_SYSMENU | WS_VISIBLE,
        CW_USEDEFAULT, CW_USEDEFAULT, 510, 440, hwndParent, NULL, hInst, NULL);
}

LRESULT CALLBACK SettingsDialogProc(HWND hwnd, UINT uMsg, WPARAM wParam, LPARAM lParam) {
    static HFONT hNormalFont = NULL;
    static HFONT hBoldFont = NULL;
    static HWND hTxtPort = NULL;
    static HWND hTxtApkDir = NULL;
    static HWND hTxtImgDir = NULL;

    switch (uMsg) {
    case WM_PAINT: {
        PAINTSTRUCT ps;
        HDC hdc = BeginPaint(hwnd, &ps);
        RECT rc;
        GetClientRect(hwnd, &rc);
        
        RECT bannerRc = { 0, 0, rc.right, 40 };
        FillRect(hdc, &bannerRc, (HBRUSH)GetStockObject(WHITE_BRUSH));

        HICON hSettingsIcon = LoadIconA(GetModuleHandle(NULL), MAKEINTRESOURCE(103));
        DrawIconEx(hdc, 15, 4, hSettingsIcon, 32, 32, 0, NULL, DI_NORMAL | DI_COMPAT);
        
        EndPaint(hwnd, &ps);
        return 0;
    }
    case WM_CREATE: {
        hNormalFont = CreateFontA(14, 0, 0, 0, FW_NORMAL, FALSE, FALSE, FALSE, DEFAULT_CHARSET, OUT_DEFAULT_PRECIS, CLIP_DEFAULT_PRECIS, CLEARTYPE_QUALITY, DEFAULT_PITCH | FF_SWISS, "Segoe UI");
        hBoldFont = CreateFontA(16, 0, 0, 0, FW_BOLD, FALSE, FALSE, FALSE, DEFAULT_CHARSET, OUT_DEFAULT_PRECIS, CLIP_DEFAULT_PRECIS, CLEARTYPE_QUALITY, DEFAULT_PITCH | FF_SWISS, "Segoe UI");

        HICON hSettingsIcon = LoadIconA(GetModuleHandle(NULL), MAKEINTRESOURCE(103));
        SendMessageA(hwnd, WM_SETICON, ICON_BIG, (LPARAM)hSettingsIcon);
        SendMessageA(hwnd, WM_SETICON, ICON_SMALL, (LPARAM)hSettingsIcon);

        // Icon drawn in WM_PAINT instead for transparency over banner

        HWND hTitle = CreateWindowA("STATIC", "Application & Server Settings", WS_CHILD | WS_VISIBLE, 60, 12, 300, 24, hwnd, NULL, NULL, NULL);
        SendMessageA(hTitle, WM_SETFONT, (WPARAM)hBoldFont, TRUE);

        CreateWindowExA(0, "STATIC", "", WS_CHILD | WS_VISIBLE | SS_ETCHEDHORZ, 0, 40, 500, 2, hwnd, NULL, NULL, NULL);

        HWND lblPort = CreateWindowA("STATIC", "HTTP Server Port:", WS_CHILD | WS_VISIBLE, 15, 55, 130, 20, hwnd, NULL, NULL, NULL);
        hTxtPort = CreateWindowExA(WS_EX_CLIENTEDGE, "EDIT", std::to_string(serverPort).c_str(), WS_CHILD | WS_VISIBLE | ES_NUMBER, 150, 53, 100, 22, hwnd, NULL, NULL, NULL);

        HWND lblApkDir = CreateWindowA("STATIC", "APK Repository Path:", WS_CHILD | WS_VISIBLE, 15, 90, 130, 20, hwnd, NULL, NULL, NULL);
        hTxtApkDir = CreateWindowExA(WS_EX_CLIENTEDGE, "EDIT", apkDir.c_str(), WS_CHILD | WS_VISIBLE, 150, 88, 255, 22, hwnd, NULL, NULL, NULL);

        HWND lblImgDir = CreateWindowA("STATIC", "Image Storage Path:", WS_CHILD | WS_VISIBLE, 15, 125, 130, 20, hwnd, NULL, NULL, NULL);
        hTxtImgDir = CreateWindowExA(WS_EX_CLIENTEDGE, "EDIT", imgDir.c_str(), WS_CHILD | WS_VISIBLE, 150, 123, 255, 22, hwnd, NULL, NULL, NULL);

        CreateWindowExA(0, "STATIC", "", WS_CHILD | WS_VISIBLE | SS_ETCHEDHORZ, 15, 160, 390, 2, hwnd, NULL, NULL, NULL);

        HWND hBtnOkay = CreateWindowA("BUTTON", "Okay", WS_CHILD | WS_VISIBLE | BS_PUSHBUTTON, 195, 172, 100, 28, hwnd, (HMENU)IDOK, NULL, NULL);
        HWND hBtnCancel = CreateWindowA("BUTTON", "Cancel", WS_CHILD | WS_VISIBLE | BS_PUSHBUTTON, 305, 172, 100, 28, hwnd, (HMENU)IDCANCEL, NULL, NULL);

        SendMessageA(lblPort, WM_SETFONT, (WPARAM)hNormalFont, TRUE);
        SendMessageA(hTxtPort, WM_SETFONT, (WPARAM)hNormalFont, TRUE);
        SendMessageA(lblApkDir, WM_SETFONT, (WPARAM)hNormalFont, TRUE);
        SendMessageA(hTxtApkDir, WM_SETFONT, (WPARAM)hNormalFont, TRUE);
        SendMessageA(lblImgDir, WM_SETFONT, (WPARAM)hNormalFont, TRUE);
        SendMessageA(hTxtImgDir, WM_SETFONT, (WPARAM)hNormalFont, TRUE);
        SendMessageA(hBtnOkay, WM_SETFONT, (WPARAM)hNormalFont, TRUE);
        SendMessageA(hBtnCancel, WM_SETFONT, (WPARAM)hNormalFont, TRUE);

        RECT parentRc, rc;
        GetWindowRect(GetParent(hwnd), &parentRc);
        GetWindowRect(hwnd, &rc);
        int x = parentRc.left + (parentRc.right - parentRc.left - 430) / 2;
        int y = parentRc.top + (parentRc.bottom - parentRc.top - 240) / 2;
        SetWindowPos(hwnd, NULL, x, y, 430, 240, SWP_NOZORDER);
        break;
    }
    case WM_CTLCOLORSTATIC:
    case WM_CTLCOLORBTN: {
        HDC hdcStatic = (HDC)wParam;
        SetBkMode(hdcStatic, TRANSPARENT);
        return (LRESULT)GetStockObject(HOLLOW_BRUSH);
    }
    case WM_COMMAND: {
        int id = LOWORD(wParam);
        if (id == IDOK) {
            char pBuf[32], aBuf[MAX_PATH], iBuf[MAX_PATH];
            GetWindowTextA(hTxtPort, pBuf, 32);
            GetWindowTextA(hTxtApkDir, aBuf, MAX_PATH);
            GetWindowTextA(hTxtImgDir, iBuf, MAX_PATH);

            int newPort = atoi(pBuf);
            if (newPort > 0 && newPort < 65535) {
                serverPort = newPort;
            }
            if (strlen(aBuf) > 0) apkDir = aBuf;
            if (strlen(iBuf) > 0) imgDir = iBuf;

            SaveConfig(hwndMain);
            LogToFileAndUI("Settings updated. Server Port: " + std::to_string(serverPort));
            DestroyWindow(hwnd);
        } else if (id == IDCANCEL) {
            DestroyWindow(hwnd);
        }
        break;
    }
    case WM_DESTROY:
        if (hNormalFont) DeleteObject(hNormalFont);
        if (hBoldFont) DeleteObject(hBoldFont);
        EnableWindow(GetParent(hwnd), TRUE);
        SetForegroundWindow(GetParent(hwnd));
        break;
    }
    return DefWindowProcA(hwnd, uMsg, wParam, lParam);
}

void ShowSettingsDialog(HWND hwndParent) {
    static bool registered = false;
    HINSTANCE hInst = (HINSTANCE)GetWindowLongPtr(hwndParent, GWLP_HINSTANCE);
    if (!registered) {
        WNDCLASSA wc = {0};
        wc.lpfnWndProc = SettingsDialogProc;
        wc.hInstance = hInst;
        wc.hIcon = LoadIcon(NULL, IDI_APPLICATION);
        wc.hbrBackground = (HBRUSH)(COLOR_BTNFACE + 1);
        wc.lpszClassName = "EliteSettingsDialog";
        RegisterClassA(&wc);
        registered = true;
    }
    EnableWindow(hwndParent, FALSE);
    CreateWindowExA(WS_EX_DLGMODALFRAME, "EliteSettingsDialog", "Local APK Store Settings",
        WS_POPUP | WS_CAPTION | WS_SYSMENU | WS_VISIBLE,
        CW_USEDEFAULT, CW_USEDEFAULT, 430, 240, hwndParent, NULL, hInst, NULL);
}

void InitTooltips(HWND hwndParent) {
    HINSTANCE hInst = (HINSTANCE)GetWindowLongPtr(hwndParent, GWLP_HINSTANCE);
    hwndTT = CreateWindowExA(WS_EX_TOPMOST, TOOLTIPS_CLASS, NULL,
        WS_POPUP | TTS_NOPREFIX | TTS_ALWAYSTIP,
        CW_USEDEFAULT, CW_USEDEFAULT, CW_USEDEFAULT, CW_USEDEFAULT,
        hwndParent, NULL, hInst, NULL);

    SetWindowPos(hwndTT, HWND_TOPMOST, 0, 0, 0, 0, SWP_NOMOVE | SWP_NOSIZE | SWP_NOACTIVATE);

    auto AddTT = [&](HWND ctrl, const char* text) {
        if (!ctrl) return;
        TOOLINFOA ti = {0};
        ti.cbSize = sizeof(TOOLINFOA);
        ti.uFlags = TTF_SUBCLASS | TTF_IDISHWND;
        ti.hwnd = GetParent(ctrl);
        ti.uId = (UINT_PTR)ctrl;
        ti.lpszText = (LPSTR)text;
        SendMessageA(hwndTT, TTM_ADDTOOL, 0, (LPARAM)&ti);
    };

    AddTT(hwndApps, "Displays all APK packages registered in your local store repository. Click one to view details.");
    AddTT(hwndName, "The human-readable name of the application. Make it snappy!");
    AddTT(hwndPackage, "Unique Android package identifier (e.g. com.example.app). Don't mess this up or Android will throw a fit.");
    AddTT(hwndVersion, "Semantic version string. Increment this unless you enjoy user confusion.");
    AddTT(hwndCat, "Select a classification category for the store index.");
    AddTT(hwndTags, "Comma-separated search keywords for easy discoverability.");
    AddTT(hwndDesc, "Detailed narrative explaining why users should download this masterwork.");
    AddTT(lstScreenshots, "Registered screenshot images showcasing the application UI.");
    AddTT(hwndPreview, "Visual preview of selected screenshot or application media.");
    AddTT(btnAddScreenshot, "Browse local storage to attach promotional screenshot images.");
    AddTT(btnClearScreenshots, "Wipe all attached screenshot references for this entry.");
    AddTT(hwndApkLabel, "Current local filesystem path to the selected .apk archive.");
    AddTT(btnBrowse, "Locate an .apk file on disk. Auto-populates metadata if aapt is feeling cooperative.");
    AddTT(btnDelete, "Permanently erase the selected app entry from the store database. No undo, so tread carefully!");
    AddTT(btnClearForm, "Reset all input fields to construct a brand new app package entry.");
    AddTT(btnApply, "Commit and save current application details to the database catalog.");
    AddTT(btnExit, "Minimizes application window to system notification area while keeping server active.");
    AddTT(btnToggleServer, "Toggles the embedded HTTP API server and UDP broadcast service.");
    AddTT(hwndLog, "Real-time activity log showing HTTP API calls, client requests, and server events.");
    AddTT(hwndClientList, "Real-time list of connected devices displaying IP address, model name, and active status.");
    AddTT(hwndLogLink, "Opens the complete persistent log file (%SystemDrive%\\EliteSoftware\\Logs\\LocalAPKStore.log) in Notepad.");
}

void CreateAppMenu(HWND hwnd) {
    HMENU hMenuMain = CreateMenu();
    HMENU hMenuFile = CreatePopupMenu();
    AppendMenuA(hMenuFile, MF_STRING, ID_FILE_SETTINGS, "Settings...\tCtrl+S");
    AppendMenuA(hMenuFile, MF_STRING, ID_FILE_VIEWLOG, "View LocalAPKStore Logs");
    AppendMenuA(hMenuFile, MF_SEPARATOR, 0, NULL);
    AppendMenuA(hMenuFile, MF_STRING, ID_FILE_EXIT, "Exit");
    AppendMenuA(hMenuMain, MF_POPUP, (UINT_PTR)hMenuFile, "&File");

    HMENU hMenuTools = CreatePopupMenu();
    AppendMenuA(hMenuTools, MF_STRING, ID_TOOLS_SCAN, "Scan APK Directory");
    AppendMenuA(hMenuTools, MF_STRING, ID_TOOLS_TOGGLE, "Toggle Server");
    AppendMenuA(hMenuMain, MF_POPUP, (UINT_PTR)hMenuTools, "&Tools");

    HMENU hMenuHelp = CreatePopupMenu();
    AppendMenuA(hMenuHelp, MF_STRING, ID_HELP_GUIDANCE, "User Manual & Help...");
    AppendMenuA(hMenuHelp, MF_STRING, ID_HELP_ABOUT, "About Local APK Store...");
    AppendMenuA(hMenuMain, MF_POPUP, (UINT_PTR)hMenuHelp, "&Help");

    AppendMenuA(hMenuMain, MF_STRING | MFT_RIGHTJUSTIFY, 2008, "Status: OFF");

    SetMenu(hwnd, hMenuMain);

    HBITMAP hBmpSettings = LoadPngAsHBitmap32(GetModuleHandle(NULL), 113, 16, 16);
    if (hBmpSettings) {
        MENUITEMINFOA mii = { sizeof(MENUITEMINFOA) };
        mii.fMask = MIIM_BITMAP;
        mii.hbmpItem = hBmpSettings;
        SetMenuItemInfoA(hMenuMain, ID_FILE_SETTINGS, FALSE, &mii);
    }
    
    HBITMAP hBmpHelp = LoadPngAsHBitmap32(GetModuleHandle(NULL), 112, 16, 16);
    if (hBmpHelp) {
        MENUITEMINFOA mii = { sizeof(MENUITEMINFOA) };
        mii.fMask = MIIM_BITMAP;
        mii.hbmpItem = hBmpHelp;
        SetMenuItemInfoA(hMenuMain, ID_HELP_GUIDANCE, FALSE, &mii);
    }

    UpdateServerStatusUI();
}

void CreateAppToolbar(HWND hwndParent) {
    HINSTANCE hInst = (HINSTANCE)GetWindowLongPtr(hwndParent, GWLP_HINSTANCE);
    hwndRebar = CreateWindowExA(WS_EX_TOOLWINDOW, REBARCLASSNAMEA, NULL,
        WS_CHILD | WS_VISIBLE | WS_CLIPSIBLINGS | WS_CLIPCHILDREN | RBS_VARHEIGHT | CCS_NODIVIDER | CCS_NOPARENTALIGN,
        0, 0, 0, 0, hwndParent, (HMENU)501, hInst, NULL);

    hwndToolbar = CreateWindowExA(0, TOOLBARCLASSNAME, NULL,
        WS_CHILD | WS_VISIBLE | TBSTYLE_FLAT | TBSTYLE_TOOLTIPS | CCS_NORESIZE | CCS_NODIVIDER,
        0, 0, 0, 0, hwndParent, (HMENU)500, hInst, NULL);

    SendMessageA(hwndToolbar, TB_BUTTONSTRUCTSIZE, (WPARAM)sizeof(TBBUTTON), 0);

    HIMAGELIST hToolbarImageList = ImageList_Create(24, 24, ILC_COLOR32 | ILC_MASK, 5, 1);
    
    HBITMAP hBrowse = LoadPngAsHBitmap32(hInst, 114, 24, 24);
    HICON hRefresh = (HICON)LoadImageA(hInst, MAKEINTRESOURCE(101), IMAGE_ICON, 24, 24, LR_DEFAULTCOLOR); // using main app icon for refresh
    HBITMAP hToggle = LoadPngAsHBitmap32(hInst, 115, 24, 24);
    HICON hSettings = (HICON)LoadImageA(hInst, MAKEINTRESOURCE(103), IMAGE_ICON, 24, 24, LR_DEFAULTCOLOR);
    HBITMAP hHelp = LoadPngAsHBitmap32(hInst, 116, 24, 24);
    
    ImageList_Add(hToolbarImageList, hBrowse, NULL);
    ImageList_AddIcon(hToolbarImageList, hRefresh);
    ImageList_Add(hToolbarImageList, hToggle, NULL);
    ImageList_AddIcon(hToolbarImageList, hSettings);
    ImageList_Add(hToolbarImageList, hHelp, NULL);
    
    DeleteObject(hBrowse); DestroyIcon(hRefresh); DeleteObject(hToggle); DestroyIcon(hSettings); DeleteObject(hHelp);
    
    SendMessageA(hwndToolbar, TB_SETIMAGELIST, 0, (LPARAM)hToolbarImageList);

    TBBUTTON tbb[7];
    ZeroMemory(tbb, sizeof(tbb));

    tbb[0].iBitmap = 0;
    tbb[0].idCommand = ID_TOOLBAR_BROWSE;
    tbb[0].fsState = TBSTATE_ENABLED;
    tbb[0].fsStyle = BTNS_BUTTON;
    tbb[0].iString = (INT_PTR)"Browse APK";

    tbb[1].iBitmap = 1;
    tbb[1].idCommand = ID_TOOLBAR_REFRESH;
    tbb[1].fsState = TBSTATE_ENABLED;
    tbb[1].fsStyle = BTNS_BUTTON;
    tbb[1].iString = (INT_PTR)"Refresh";

    tbb[2].fsStyle = BTNS_SEP;

    tbb[3].iBitmap = 2;
    tbb[3].idCommand = ID_TOOLBAR_TOGGLE;
    tbb[3].fsState = TBSTATE_ENABLED;
    tbb[3].fsStyle = BTNS_BUTTON;
    tbb[3].iString = (INT_PTR)"Toggle Server";

    tbb[4].iBitmap = 3;
    tbb[4].idCommand = ID_TOOLBAR_SETTINGS;
    tbb[4].fsState = TBSTATE_ENABLED;
    tbb[4].fsStyle = BTNS_BUTTON;
    tbb[4].iString = (INT_PTR)"Settings";

    tbb[5].fsStyle = BTNS_SEP;

    tbb[6].iBitmap = 4;
    tbb[6].idCommand = ID_TOOLBAR_HELP;
    tbb[6].fsState = TBSTATE_ENABLED;
    tbb[6].fsStyle = BTNS_BUTTON;
    tbb[6].iString = (INT_PTR)"Help";

    SendMessageA(hwndToolbar, TB_ADDBUTTONS, 7, (LPARAM)&tbb);
    SendMessageA(hwndToolbar, TB_AUTOSIZE, 0, 0);

    REBARBANDINFOA rbBand;
    ZeroMemory(&rbBand, sizeof(rbBand));
    rbBand.cbSize = sizeof(REBARBANDINFOA);
    rbBand.fMask = RBBIM_STYLE | RBBIM_CHILD | RBBIM_CHILDSIZE | RBBIM_SIZE;
    rbBand.fStyle = RBBS_CHILDEDGE | RBBS_GRIPPERALWAYS;
    rbBand.hwndChild = hwndToolbar;
    
    DWORD dwBtnSize = (DWORD)SendMessageA(hwndToolbar, TB_GETBUTTONSIZE, 0, 0);
    rbBand.cyChild = HIWORD(dwBtnSize);
    rbBand.cxMinChild = 7 * LOWORD(dwBtnSize);
    rbBand.cyMinChild = HIWORD(dwBtnSize);
    
    SendMessageA(hwndRebar, RB_INSERTBANDA, (WPARAM)-1, (LPARAM)&rbBand);
}

WNDPROC OldTabProc = NULL;

LRESULT CALLBACK TabProc(HWND hwnd, UINT msg, WPARAM wp, LPARAM lp) {
    if (msg == WM_COMMAND || msg == WM_NOTIFY || msg == WM_DROPFILES) {
        return SendMessageA(GetParent(hwnd), msg, wp, lp);
    }
    if (msg == WM_CTLCOLORSTATIC) {
        if ((HWND)lp == hwndLog || (HWND)lp == hwndClientList) {
            return CallWindowProcA(OldTabProc, hwnd, msg, wp, lp);
        }
        HDC hdc = (HDC)wp;
        SetBkMode(hdc, TRANSPARENT);
        return (LRESULT)GetStockObject(HOLLOW_BRUSH);
    }
    if (msg == WM_CTLCOLORBTN) {
        HDC hdc = (HDC)wp;
        SetBkMode(hdc, TRANSPARENT);
        return (LRESULT)GetStockObject(HOLLOW_BRUSH);
    }
    return CallWindowProcA(OldTabProc, hwnd, msg, wp, lp);
}

void UpdateTabVisibility() {
    int tab = SendMessageA(hwndTab, TCM_GETCURSEL, 0, 0);
    int showInv = (tab == 0) ? SW_SHOW : SW_HIDE;
    int showMon = (tab == 1) ? SW_SHOW : SW_HIDE;
    
    HWND windows[] = { hwndApps, hwndName, hwndPackage, hwndVersion, hwndCat, hwndTags, hwndDesc, lstScreenshots, btnAddScreenshot, btnClearScreenshots, hwndApkLabel, btnBrowse, btnDelete, btnClearForm, btnApply };
    for(HWND w : windows) { if (w) { ShowWindow(w, showInv); if (showInv == SW_SHOW) BringWindowToTop(w); } }
    if (hwndPreview) { ShowWindow(hwndPreview, showInv); if (showInv == SW_SHOW) BringWindowToTop(hwndPreview); }
    for(HWND lbl : invLabels) { if (lbl) { ShowWindow(lbl, showInv); if (showInv == SW_SHOW) BringWindowToTop(lbl); } }

    if (hwndLog) { ShowWindow(hwndLog, showMon); if (showMon == SW_SHOW) BringWindowToTop(hwndLog); }
    if (lblConnectedClients) { ShowWindow(lblConnectedClients, showMon); if (showMon == SW_SHOW) BringWindowToTop(lblConnectedClients); }
    if (hwndClientList) { ShowWindow(hwndClientList, showMon); if (showMon == SW_SHOW) BringWindowToTop(hwndClientList); }
    if (hwndServerStatus) { ShowWindow(hwndServerStatus, showMon); if (showMon == SW_SHOW) BringWindowToTop(hwndServerStatus); }
    if (btnToggleServer) { ShowWindow(btnToggleServer, showMon); if (showMon == SW_SHOW) BringWindowToTop(btnToggleServer); }
}

LRESULT CALLBACK WindowProc(HWND hwnd, UINT uMsg, WPARAM wParam, LPARAM lParam) {
    switch (uMsg) {
    case WM_PAINT: {
        PAINTSTRUCT ps;
        HDC hdc = BeginPaint(hwnd, &ps);
        RECT clientRect; GetClientRect(hwnd, &clientRect);
        
        RECT bannerRect = {0, 0, clientRect.right, 42};
        if (!hbrBanner) hbrBanner = CreateSolidBrush(RGB(164, 198, 57));
        FillRect(hdc, &bannerRect, hbrBanner);

        if (!g_hAppIcon) g_hAppIcon = GetDynamicAppIcon((HINSTANCE)GetWindowLongPtr(hwnd, GWLP_HINSTANCE));
        if (g_hAppIcon) DrawIconEx(hdc, 10, 5, g_hAppIcon, 32, 32, 0, NULL, DI_NORMAL);

        SetBkMode(hdc, TRANSPARENT);
        SelectObject(hdc, hFontSegoeBold);
        
        RECT textRect = {50, 0, clientRect.right, 40};
        std::string titleText = "Local APK Store - Server Manager (Port " + std::to_string(serverPort) + ")";
        
        SetTextColor(hdc, RGB(50, 50, 50));
        RECT shadowRect = textRect; OffsetRect(&shadowRect, 1, 1);
        DrawTextA(hdc, titleText.c_str(), -1, &shadowRect, DT_LEFT | DT_VCENTER | DT_SINGLELINE);
        
        SetTextColor(hdc, RGB(255, 255, 255));
        DrawTextA(hdc, titleText.c_str(), -1, &textRect, DT_LEFT | DT_VCENTER | DT_SINGLELINE);

        EndPaint(hwnd, &ps);
        return 0;
    }
    case WM_LOG_MESSAGE: {
        std::string* pStr = (std::string*)lParam;
        if (pStr) {
            if (hwndLog && IsWindow(hwndLog)) {
                int len = GetWindowTextLengthA(hwndLog);
                SendMessageA(hwndLog, EM_SETSEL, (WPARAM)len, (LPARAM)len);
                SendMessageA(hwndLog, EM_REPLACESEL, 0, (LPARAM)pStr->c_str());
            }
            delete pStr;
        }
        return 0;
    }
    case WM_DROPFILES: {
        HDROP hDrop = (HDROP)wParam;
        UINT numFiles = DragQueryFileA(hDrop, 0xFFFFFFFF, NULL, 0);
        bool addedScreenshot = false;
        for (UINT i = 0; i < numFiles; ++i) {
            char path[MAX_PATH];
            DragQueryFileA(hDrop, i, path, MAX_PATH);
            std::string p = path;
            std::string ext = "";
            size_t dot = p.find_last_of('.');
            if (dot != std::string::npos) {
                ext = p.substr(dot);
                std::transform(ext.begin(), ext.end(), ext.begin(), ::tolower);
            }
            if (ext == ".png" || ext == ".jpg" || ext == ".jpeg") {
                screenshots.push_back(path);
                int imgIdx = AddImageToImageList(g_hImgListSS, path);
                LVITEMA lvi = {0};
                lvi.mask = LVIF_TEXT | LVIF_IMAGE;
                lvi.iItem = ListView_GetItemCount(lstScreenshots);
                lvi.iImage = imgIdx;
                std::string fname = fs::path(path).filename().string();
                lvi.pszText = (LPSTR)fname.c_str();
                ListView_InsertItem(lstScreenshots, &lvi);
                UpdatePreviewImage(screenshots.back());
                addedScreenshot = true;
            } else if (ext == ".apk") {
                SetWindowTextA(hwndApkLabel, path);
                ParseApkMetadata(path);
            }
        }
        DragFinish(hDrop);
        
        if (addedScreenshot) {
            char pkg[256];
            GetWindowTextA(hwndPackage, pkg, 256);
            if (strlen(pkg) > 0) {
                SendMessageA(hwnd, WM_COMMAND, 2, 0);
            }
        }
        return 0;
    }
    case WM_EXITSIZEMOVE: {
        SaveConfig(hwnd);
        return 0;
    }
    case WM_SIZE: {
        if (wParam == SIZE_MINIMIZED) return DefWindowProcA(hwnd, uMsg, wParam, lParam);
        int w = LOWORD(lParam);
        int h = HIWORD(lParam);
        static int prevW = 0;
        if (prevW != 0 && w != prevW) {
            g_listWidth += (w - prevW);
        }
        prevW = w;
        
        int sh = 0;
        if (hwndStatusBar && IsWindow(hwndStatusBar)) {
            SendMessageA(hwndStatusBar, WM_SIZE, 0, 0);
            RECT statusRect; GetWindowRect(hwndStatusBar, &statusRect);
            sh = statusRect.bottom - statusRect.top;
        }

        int bannerH = 42;
        int toolbarH = 0;
        if (hwndRebar && IsWindow(hwndRebar)) {
            SendMessageA(hwndRebar, WM_SIZE, 0, 0);
            RECT tbRect; GetWindowRect(hwndRebar, &tbRect);
            toolbarH = tbRect.bottom - tbRect.top;
            MoveWindow(hwndRebar, 0, bannerH, w, toolbarH, TRUE);
        } else if (hwndToolbar && IsWindow(hwndToolbar)) {
            SendMessageA(hwndToolbar, WM_SIZE, 0, 0);
            RECT tbRect; GetWindowRect(hwndToolbar, &tbRect);
            toolbarH = tbRect.bottom - tbRect.top;
            MoveWindow(hwndToolbar, 0, bannerH, w, toolbarH, TRUE);
        }

        int topOffset = bannerH + toolbarH;

        int chinH = 42;
        int chinY = h - sh - chinH;

        if (hwndChin && IsWindow(hwndChin)) {
            MoveWindow(hwndChin, 0, chinY, w, 2, TRUE);
        }
        if (hwndLogLink && IsWindow(hwndLogLink)) {
            MoveWindow(hwndLogLink, 15, chinY + 10, 180, 22, TRUE);
        }
        if (btnExit && IsWindow(btnExit)) {
            MoveWindow(btnExit, w - 120, chinY + 6, 100, 30, TRUE);
        }
        if (btnApply && IsWindow(btnApply)) {
            MoveWindow(btnApply, w - 240, chinY + 6, 110, 30, TRUE);
        }

        int tabY = topOffset + 4;
        int tabH = chinY - tabY - 6;
        if (hwndTab && IsWindow(hwndTab)) {
            MoveWindow(hwndTab, 10, tabY, w - 20, tabH, TRUE);

            RECT tabRect;
            GetClientRect(hwndTab, &tabRect);
            SendMessageA(hwndTab, TCM_ADJUSTRECT, FALSE, (LPARAM)&tabRect);

            // Tab 0 controls
            int leftWidth = g_listWidth;
            if (leftWidth < 240) leftWidth = 240;
            if (leftWidth > tabRect.right - tabRect.left - 300) leftWidth = std::max(240L, tabRect.right - tabRect.left - 300);
            
            if (invLabels.size() > 0 && invLabels[0]) {
                MoveWindow(invLabels[0], tabRect.left + 5, tabRect.top + 5, 200, 18, TRUE);
            }
            if (hwndApps) MoveWindow(hwndApps, tabRect.left + 5, tabRect.top + 26, leftWidth, tabRect.bottom - tabRect.top - 70, TRUE);
            if (btnDelete) MoveWindow(btnDelete, tabRect.left + 5, tabRect.bottom - 38, 115, 30, TRUE);
            if (btnClearForm) MoveWindow(btnClearForm, tabRect.left + 125, tabRect.bottom - 38, 115, 30, TRUE);
            
            if (hwndSplitter) {
                MoveWindow(hwndSplitter, tabRect.left + 5 + leftWidth, tabRect.top + 26, 8, tabRect.bottom - tabRect.top - 70, TRUE);
                SetWindowPos(hwndSplitter, HWND_TOP, 0,0,0,0, SWP_NOMOVE | SWP_NOSIZE);
            }

            int formX = tabRect.left + leftWidth + 15;
            int rightPanelW = 160;
            int rightPanelX = tabRect.right - rightPanelW - 5;
            int editW = std::max(120, (int)(rightPanelX - (formX + 90) - 15));

            if (invLabels.size() > 1 && invLabels[1]) MoveWindow(invLabels[1], formX, tabRect.top + 5, 85, 20, TRUE);
            if (hwndName) MoveWindow(hwndName, formX + 90, tabRect.top + 5, editW, 22, TRUE);

            if (invLabels.size() > 2 && invLabels[2]) MoveWindow(invLabels[2], formX, tabRect.top + 35, 85, 20, TRUE);
            if (hwndPackage) MoveWindow(hwndPackage, formX + 90, tabRect.top + 35, editW, 22, TRUE);

            if (invLabels.size() > 3 && invLabels[3]) MoveWindow(invLabels[3], formX, tabRect.top + 65, 85, 20, TRUE);
            if (hwndVersion) MoveWindow(hwndVersion, formX + 90, tabRect.top + 65, editW, 22, TRUE);

            if (invLabels.size() > 4 && invLabels[4]) MoveWindow(invLabels[4], formX, tabRect.top + 95, 85, 20, TRUE);
            if (hwndCat) MoveWindow(hwndCat, formX + 90, tabRect.top + 95, editW, 110, TRUE);

            if (invLabels.size() > 5 && invLabels[5]) MoveWindow(invLabels[5], formX, tabRect.top + 215, 85, 20, TRUE);
            if (hwndTags) MoveWindow(hwndTags, formX + 90, tabRect.top + 215, editW, 22, TRUE);

            if (invLabels.size() > 6 && invLabels[6]) MoveWindow(invLabels[6], formX, tabRect.top + 245, 85, 20, TRUE);
            if (hwndDesc) MoveWindow(hwndDesc, formX + 90, tabRect.top + 245, editW, 100, TRUE);

            if (invLabels.size() > 8 && invLabels[8]) MoveWindow(invLabels[8], formX, tabRect.top + 355, 85, 20, TRUE);
            int apkLabelW = std::max(50, editW - 90);
            if (hwndApkLabel) MoveWindow(hwndApkLabel, formX + 90, tabRect.top + 355, apkLabelW, 24, TRUE);
            if (btnBrowse) MoveWindow(btnBrowse, formX + 90 + apkLabelW + 5, tabRect.top + 353, 85, 28, TRUE);

            if (invLabels.size() > 7 && invLabels[7]) MoveWindow(invLabels[7], rightPanelX, tabRect.top + 5, rightPanelW, 20, TRUE);
            if (lstScreenshots) MoveWindow(lstScreenshots, rightPanelX, tabRect.top + 25, rightPanelW, tabRect.bottom - tabRect.top - 210, TRUE);
            if (hwndPreview) MoveWindow(hwndPreview, rightPanelX, tabRect.bottom - 180, rightPanelW, 140, TRUE);

            if (btnAddScreenshot) MoveWindow(btnAddScreenshot, rightPanelX, tabRect.bottom - 38, rightPanelW/2 - 2, 28, TRUE);
            if (btnClearScreenshots) MoveWindow(btnClearScreenshots, rightPanelX + rightPanelW/2 + 2, tabRect.bottom - 38, rightPanelW/2 - 2, 28, TRUE);


            // Tab 1 controls
            int monW = tabRect.right - tabRect.left - 10;
            int totalMonH = tabRect.bottom - tabRect.top - 50;
            int logH = 180;
            if (totalMonH < 300) logH = std::max(80, totalMonH / 2);

            if (hwndLog) MoveWindow(hwndLog, tabRect.left + 5, tabRect.top + 5, monW, logH, TRUE);

            int lblY = tabRect.top + logH + 12;
            if (lblConnectedClients) MoveWindow(lblConnectedClients, tabRect.left + 5, lblY, monW, 20, TRUE);

            int listY = lblY + 22;
            int listH = (tabRect.bottom - 45) - listY;
            if (listH < 50) listH = 50;
            if (hwndClientList) MoveWindow(hwndClientList, tabRect.left + 5, listY, monW, listH, TRUE);

            if (hwndServerStatus) MoveWindow(hwndServerStatus, tabRect.left + 10, tabRect.bottom - 38, 200, 24, TRUE);
            if (btnToggleServer) MoveWindow(btnToggleServer, tabRect.right - 130, tabRect.bottom - 38, 120, 30, TRUE);
        }

        return 0;
    }
    case WM_NOTIFY: {
        LPNMHDR pnmh = (LPNMHDR)lParam;
        if (pnmh->hwndFrom == hwndTab && pnmh->code == TCN_SELCHANGE) {
            UpdateTabVisibility();
        }
        else if (pnmh->hwndFrom == hwndApps && (pnmh->code == LVN_ITEMCHANGED || pnmh->code == NM_CLICK)) {
            if (pnmh->code == LVN_ITEMCHANGED) {
                LPNMLISTVIEW pnlv = (LPNMLISTVIEW)lParam;
                if ((pnlv->uChanged & LVIF_STATE) && (pnlv->uNewState & LVIS_SELECTED)) {
                    selectedAppIndex = pnlv->iItem;
                    LoadAppIntoForm(selectedAppIndex);
                }
            } else if (pnmh->code == NM_CLICK) {
                int selected = ListView_GetNextItem(hwndApps, -1, LVNI_SELECTED);
                if (selected >= 0) {
                    selectedAppIndex = selected;
                    LoadAppIntoForm(selectedAppIndex);
                }
            }
        }
        else if (pnmh->hwndFrom == lstScreenshots && (pnmh->code == LVN_ITEMCHANGED || pnmh->code == NM_CLICK)) {
            int sIdx = ListView_GetNextItem(lstScreenshots, -1, LVNI_SELECTED);
            if (sIdx >= 0 && sIdx < (int)screenshots.size()) UpdatePreviewImage(screenshots[sIdx]);
        }
        break;
    }
    case WM_CREATE: {
        hwndMain = hwnd;
        RegisterHotKey(hwnd, 1, MOD_CONTROL | MOD_ALT, 'M');
        
        hFontSegoeNormal = CreateFontA(14, 0, 0, 0, FW_NORMAL, FALSE, FALSE, FALSE, DEFAULT_CHARSET, OUT_DEFAULT_PRECIS, CLIP_DEFAULT_PRECIS, CLEARTYPE_QUALITY, DEFAULT_PITCH | FF_SWISS, "Segoe UI");
        hFontSegoeBold = CreateFontA(16, 0, 0, 0, FW_BOLD, FALSE, FALSE, FALSE, DEFAULT_CHARSET, OUT_DEFAULT_PRECIS, CLIP_DEFAULT_PRECIS, CLEARTYPE_QUALITY, DEFAULT_PITCH | FF_SWISS, "Segoe UI");
        
        CreateAppMenu(hwnd);
        CreateAppToolbar(hwnd);

        hwndStatusBar = CreateWindowExA(0, STATUSCLASSNAME, NULL, WS_CHILD | WS_VISIBLE | WS_CLIPSIBLINGS | SBARS_SIZEGRIP, 0, 0, 0, 0, hwnd, NULL, (HINSTANCE)GetWindowLongPtr(hwnd, GWLP_HINSTANCE), NULL);
        SendMessageA(hwndStatusBar, SB_SETTEXT, 0, (LPARAM)"Ready");
        SendMessageA(hwndStatusBar, WM_SETFONT, (WPARAM)hFontSegoeNormal, TRUE);

        HINSTANCE hInstance = (HINSTANCE)GetWindowLongPtr(hwnd, GWLP_HINSTANCE);
        if (!g_hAppIcon) g_hAppIcon = GetDynamicAppIcon(hInstance);
        SendMessageA(hwnd, WM_SETICON, ICON_BIG, (LPARAM)g_hAppIcon);
        SendMessageA(hwnd, WM_SETICON, ICON_SMALL, (LPARAM)g_hAppIcon);

        CreateWindowExA(0, "STATIC", "", WS_CHILD | WS_VISIBLE | WS_CLIPSIBLINGS | SS_ETCHEDHORZ, 0, 41, 2000, 2, hwnd, NULL, NULL, NULL);

        hwndTab = CreateWindowExA(0, WC_TABCONTROL, "", WS_CHILD | WS_VISIBLE | WS_CLIPSIBLINGS, 10, 50, 810, 450, hwnd, (HMENU)100, hInstance, NULL);
        OldTabProc = (WNDPROC)SetWindowLongPtrA(hwndTab, GWLP_WNDPROC, (LONG_PTR)TabProc);
        DragAcceptFiles(hwnd, TRUE);
        DragAcceptFiles(hwndTab, TRUE);
        SendMessageA(hwndTab, WM_SETFONT, (WPARAM)hFontSegoeNormal, TRUE);
        
        g_hTabImageList = ImageList_Create(16, 16, ILC_COLOR32 | ILC_MASK, 1, 1);
        HICON hIconServer = (HICON)LoadImageA(hInstance, MAKEINTRESOURCE(107), IMAGE_ICON, 16, 16, LR_DEFAULTCOLOR);
        ImageList_AddIcon(g_hTabImageList, hIconServer);
        DestroyIcon(hIconServer);
        SendMessageA(hwndTab, TCM_SETIMAGELIST, 0, (LPARAM)g_hTabImageList);

        TCITEMA tie; tie.mask = TCIF_TEXT | TCIF_IMAGE; 
        tie.iImage = -1;
        tie.pszText = (LPSTR)"App Inventory"; SendMessageA(hwndTab, TCM_INSERTITEM, 0, (LPARAM)&tie);
        tie.iImage = 0;
        tie.pszText = (LPSTR)"Server Monitor"; SendMessageA(hwndTab, TCM_INSERTITEM, 1, (LPARAM)&tie);

        hwndApps = CreateWindowExA(WS_EX_CLIENTEDGE, WC_LISTVIEWA, "",
            WS_CHILD | WS_VISIBLE | LVS_REPORT | LVS_SINGLESEL | LVS_SHOWSELALWAYS,
            20, 90, 240, 360, hwndTab, (HMENU)10, hInstance, NULL);
        ListView_SetExtendedListViewStyle(hwndApps, LVS_EX_FULLROWSELECT | LVS_EX_GRIDLINES | LVS_EX_DOUBLEBUFFER);

        LVCOLUMNA lvc = {0};
        lvc.mask = LVCF_TEXT | LVCF_WIDTH | LVCF_SUBITEM;

        lvc.iSubItem = 0; lvc.pszText = (LPSTR)"Name"; lvc.cx = g_listCols[0]; ListView_InsertColumn(hwndApps, 0, &lvc);
        lvc.iSubItem = 1; lvc.pszText = (LPSTR)"Package"; lvc.cx = g_listCols[1]; ListView_InsertColumn(hwndApps, 1, &lvc);
        lvc.iSubItem = 2; lvc.pszText = (LPSTR)"Version"; lvc.cx = g_listCols[2]; ListView_InsertColumn(hwndApps, 2, &lvc);
        lvc.iSubItem = 3; lvc.pszText = (LPSTR)"Size"; lvc.cx = g_listCols[3]; ListView_InsertColumn(hwndApps, 3, &lvc);
        lvc.iSubItem = 4; lvc.pszText = (LPSTR)"Status"; lvc.cx = g_listCols[4]; ListView_InsertColumn(hwndApps, 4, &lvc);

        HIMAGELIST hSmallState = ImageList_Create(32, 32, ILC_COLOR32 | ILC_MASK, 10, 10);
        ListView_SetImageList(hwndApps, hSmallState, LVSIL_SMALL);
        
        invLabels.push_back(CreateWindowA("STATIC", "Store Inventory:", WS_CHILD | WS_VISIBLE, 0, 0, 0, 0, hwndTab, NULL, hInstance, NULL));
        invLabels.push_back(CreateWindowA("STATIC", "App Name:", WS_CHILD | WS_VISIBLE, 0, 0, 0, 0, hwndTab, NULL, hInstance, NULL));
        hwndName = CreateWindowExA(WS_EX_CLIENTEDGE, "EDIT", "", WS_CHILD | WS_VISIBLE | ES_AUTOHSCROLL, 0, 0, 0, 0, hwndTab, NULL, hInstance, NULL);
        
        invLabels.push_back(CreateWindowA("STATIC", "Package:", WS_CHILD | WS_VISIBLE, 0, 0, 0, 0, hwndTab, NULL, hInstance, NULL));
        hwndPackage = CreateWindowExA(WS_EX_CLIENTEDGE, "EDIT", "", WS_CHILD | WS_VISIBLE | ES_AUTOHSCROLL, 0, 0, 0, 0, hwndTab, NULL, hInstance, NULL);
        
        invLabels.push_back(CreateWindowA("STATIC", "Version:", WS_CHILD | WS_VISIBLE, 0, 0, 0, 0, hwndTab, NULL, hInstance, NULL));
        hwndVersion = CreateWindowExA(WS_EX_CLIENTEDGE, "EDIT", "", WS_CHILD | WS_VISIBLE | ES_AUTOHSCROLL, 0, 0, 0, 0, hwndTab, NULL, hInstance, NULL);
        
        invLabels.push_back(CreateWindowA("STATIC", "Category:", WS_CHILD | WS_VISIBLE, 0, 0, 0, 0, hwndTab, NULL, hInstance, NULL));
        hwndCat = CreateWindowExA(WS_EX_CLIENTEDGE, "COMBOBOX", "", WS_CHILD | WS_VISIBLE | CBS_DROPDOWNLIST, 0, 0, 0, 0, hwndTab, NULL, hInstance, NULL);
        const char* cats[] = {"Games", "Productivity", "Social", "Tools", "Entertainment", "Education", "Other"};
        for (const char* c : cats) SendMessageA(hwndCat, CB_ADDSTRING, 0, (LPARAM)c);
        SendMessageA(hwndCat, CB_SETCURSEL, 0, 0);

        invLabels.push_back(CreateWindowA("STATIC", "Tags (csv):", WS_CHILD | WS_VISIBLE, 0, 0, 0, 0, hwndTab, NULL, hInstance, NULL));
        hwndTags = CreateWindowExA(WS_EX_CLIENTEDGE, "EDIT", "", WS_CHILD | WS_VISIBLE | ES_AUTOHSCROLL, 0, 0, 0, 0, hwndTab, NULL, hInstance, NULL);
        
        invLabels.push_back(CreateWindowA("STATIC", "Description:", WS_CHILD | WS_VISIBLE, 0, 0, 0, 0, hwndTab, NULL, hInstance, NULL));
        hwndDesc = CreateWindowExA(WS_EX_CLIENTEDGE, "EDIT", "", WS_CHILD | WS_VISIBLE | WS_VSCROLL | ES_MULTILINE | ES_AUTOVSCROLL | ES_WANTRETURN, 0, 0, 0, 0, hwndTab, NULL, hInstance, NULL);

        invLabels.push_back(CreateWindowA("STATIC", "Screenshots:", WS_CHILD | WS_VISIBLE, 0, 0, 0, 0, hwndTab, NULL, hInstance, NULL));
        lstScreenshots = CreateWindowExA(WS_EX_CLIENTEDGE, WC_LISTVIEWA, "", WS_CHILD | WS_VISIBLE | LVS_ICON | LVS_SINGLESEL | LVS_SHOWSELALWAYS, 0, 0, 0, 0, hwndTab, (HMENU)30, hInstance, NULL);
        ListView_SetExtendedListViewStyle(lstScreenshots, LVS_EX_FULLROWSELECT | LVS_EX_DOUBLEBUFFER);
        ListView_SetImageList(lstScreenshots, g_hImgListSS, LVSIL_NORMAL);
        LVCOLUMNA lvcSS = {0};
        lvcSS.mask = LVCF_WIDTH;
        lvcSS.cx = 140; // width of column
        ListView_InsertColumn(lstScreenshots, 0, &lvcSS);
        
        hwndPreview = CreateWindowA("STATIC", "", WS_CHILD | WS_VISIBLE | SS_BITMAP | SS_CENTERIMAGE | SS_REALSIZEIMAGE | WS_EX_CLIENTEDGE, 0, 0, 0, 0, hwndTab, NULL, hInstance, NULL);
        btnAddScreenshot = CreateWindowA("BUTTON", "Add Screenshot", WS_CHILD | WS_VISIBLE | BS_PUSHBUTTON, 0, 0, 0, 0, hwndTab, (HMENU)3, hInstance, NULL);
        btnClearScreenshots = CreateWindowA("BUTTON", "Clear All", WS_CHILD | WS_VISIBLE | BS_PUSHBUTTON, 0, 0, 0, 0, hwndTab, (HMENU)4, hInstance, NULL);
        
        invLabels.push_back(CreateWindowA("STATIC", "APK File:", WS_CHILD | WS_VISIBLE, 0, 0, 0, 0, hwndTab, NULL, hInstance, NULL));
        hwndApkLabel = CreateWindowExA(WS_EX_CLIENTEDGE, "STATIC", " No APK selected", WS_CHILD | WS_VISIBLE | SS_LEFT, 0, 0, 0, 0, hwndTab, NULL, hInstance, NULL);
        btnBrowse = CreateWindowA("BUTTON", "Browse APK...", WS_CHILD | WS_VISIBLE | BS_PUSHBUTTON, 0, 0, 0, 0, hwndTab, (HMENU)1, hInstance, NULL);
        btnDelete = CreateWindowA("BUTTON", "Delete Selected", WS_CHILD | WS_VISIBLE | BS_PUSHBUTTON, 0, 0, 0, 0, hwndTab, (HMENU)6, hInstance, NULL);
        btnClearForm = CreateWindowA("BUTTON", "New App", WS_CHILD | WS_VISIBLE | BS_PUSHBUTTON, 0, 0, 0, 0, hwndTab, (HMENU)5, hInstance, NULL);

        btnApply = CreateWindowA("BUTTON", "Apply", WS_CHILD | WS_VISIBLE | BS_PUSHBUTTON, 0, 0, 0, 0, hwnd, (HMENU)2, hInstance, NULL);
        
        hwndSplitter = CreateWindowExA(0, "STATIC", "", WS_CHILD | WS_VISIBLE | SS_NOTIFY, 0,0,0,0, hwndTab, NULL, hInstance, NULL);
        oldSplitterProc = (WNDPROC)SetWindowLongPtrA(hwndSplitter, GWLP_WNDPROC, (LONG_PTR)SplitterProc);

        hwndChin = CreateWindowExA(0, "STATIC", "", WS_CHILD | WS_VISIBLE | SS_ETCHEDHORZ, 0, 0, 0, 0, hwnd, NULL, hInstance, NULL);
        hwndLogLink = CreateWindowExA(0, "STATIC", "View LocalAPKStore Logs", WS_CHILD | WS_VISIBLE | SS_NOTIFY, 0, 0, 0, 0, hwnd, (HMENU)600, hInstance, NULL);
        btnExit = CreateWindowA("BUTTON", "Hide to Tray", WS_CHILD | WS_VISIBLE | BS_PUSHBUTTON, 0, 0, 0, 0, hwnd, (HMENU)7, hInstance, NULL);

        hwndLog = CreateWindowExA(WS_EX_CLIENTEDGE, "EDIT", "", WS_CHILD | WS_BORDER | WS_VSCROLL | ES_MULTILINE | ES_READONLY | ES_AUTOVSCROLL, 0, 0, 0, 0, hwndTab, NULL, hInstance, NULL);
        lblConnectedClients = CreateWindowA("STATIC", "Connected Clients (0):", WS_CHILD, 0, 0, 0, 0, hwndTab, NULL, hInstance, NULL);
        hwndClientList = CreateWindowExA(WS_EX_CLIENTEDGE, WC_LISTVIEWA, "",
            WS_CHILD | LVS_REPORT | LVS_SINGLESEL | WS_CLIPSIBLINGS,
            0, 0, 0, 0, hwndTab, (HMENU)11, hInstance, NULL);
        ListView_SetExtendedListViewStyle(hwndClientList, LVS_EX_FULLROWSELECT | LVS_EX_GRIDLINES | LVS_EX_DOUBLEBUFFER);

        LVCOLUMNA lvcClient = {0};
        lvcClient.mask = LVCF_TEXT | LVCF_WIDTH | LVCF_SUBITEM;
        lvcClient.iSubItem = 0; lvcClient.pszText = (LPSTR)"IP Address"; lvcClient.cx = 160; ListView_InsertColumn(hwndClientList, 0, &lvcClient);
        lvcClient.iSubItem = 1; lvcClient.pszText = (LPSTR)"Device Name"; lvcClient.cx = 240; ListView_InsertColumn(hwndClientList, 1, &lvcClient);
        lvcClient.iSubItem = 2; lvcClient.pszText = (LPSTR)"Last Active"; lvcClient.cx = 120; ListView_InsertColumn(hwndClientList, 2, &lvcClient);

        hwndServerStatus = CreateWindowA("STATIC", "Status: STOPPED", WS_CHILD, 0, 0, 0, 0, hwndTab, NULL, hInstance, NULL);
        btnToggleServer = CreateWindowA("BUTTON", "Start Server", WS_CHILD | BS_PUSHBUTTON, 0, 0, 0, 0, hwndTab, (HMENU)200, hInstance, NULL);

        HWND controlsToFont[] = {
            hwndTab, hwndApps, hwndName, hwndPackage, hwndVersion, hwndCat, hwndTags,
            hwndDesc, lstScreenshots, btnAddScreenshot, btnClearScreenshots, hwndApkLabel,
            btnBrowse, btnDelete, btnClearForm, btnApply, btnExit, hwndLog, lblConnectedClients, hwndClientList, hwndServerStatus,
            btnToggleServer, hwndLogLink
        };
        for (HWND c : controlsToFont) {
            if (c) SendMessageA(c, WM_SETFONT, (WPARAM)hFontSegoeNormal, TRUE);
        }
        for (HWND lbl : invLabels) {
            if (lbl) SendMessageA(lbl, WM_SETFONT, (WPARAM)hFontSegoeNormal, TRUE);
        }

        InitTooltips(hwnd);

        UpdateTabVisibility();
        RefreshAppList();
        InitTrayIcon(hwnd);
        SetTimer(hwnd, 1002, 1000, NULL);
        StartServer();
        break;
    }
    case WM_TIMER: {
        if (wParam == 1002) {
            RefreshClientListView();
            if (!serverRunning && g_timeServerStopped != 0) {
                UpdateServerStatusUI();
            }
        }
        return 0;
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
            InsertMenuA(hMenu, 0, MF_BYPOSITION | MF_STRING, ID_TRAY_OPEN_CONTEXT_MENU_ITEM, "Open Manager");
            InsertMenuA(hMenu, 1, MF_BYPOSITION | MF_STRING, ID_TRAY_EXIT_CONTEXT_MENU_ITEM, "Quit Server");
            SetForegroundWindow(hwnd);
            TrackPopupMenu(hMenu, TPM_BOTTOMALIGN | TPM_LEFTALIGN, pt.x, pt.y, 0, hwnd, NULL);
            DestroyMenu(hMenu);
        }
        break;
    }
    case WM_COMMAND: {
        int wmId = LOWORD(wParam);
        int wmEvent = HIWORD(wParam);

        if (wmId == 600 || (HWND)lParam == hwndLogLink) {
            OpenLogFile();
        }
        else if (wmId == 200) { // toggle server
            if (serverRunning) StopServer();
            else StartServer();
        }
        else if (wmId == ID_FILE_SETTINGS || wmId == ID_TOOLBAR_SETTINGS) {
            ShowSettingsDialog(hwnd);
        }
        else if (wmId == ID_FILE_VIEWLOG) {
            OpenLogFile();
        }
        else if (wmId == ID_FILE_EXIT) {
            PostMessage(hwnd, WM_CLOSE, 0, 0);
        }
        else if (wmId == ID_TOOLS_SCAN || wmId == ID_TOOLBAR_REFRESH) {
            RefreshAppList();
            LogToFileAndUI("Triggered manual refresh scan.");
        }
        else if (wmId == ID_TOOLS_TOGGLE || wmId == ID_TOOLBAR_TOGGLE || wmId == 2008) {
            if (serverRunning) StopServer();
            else StartServer();
        }
        else if (wmId == ID_HELP_GUIDANCE || wmId == ID_TOOLBAR_HELP) {
            ShowHelpDialog(hwnd);
        }
        else if (wmId == ID_HELP_ABOUT) {
            ShowAboutDialog(hwnd);
        }
        else if (wmId == ID_TOOLBAR_BROWSE) {
            SendMessageA(hwnd, WM_COMMAND, MAKEWPARAM(1, 0), (LPARAM)btnBrowse);
        }
        else if (wmId == ID_TRAY_OPEN_CONTEXT_MENU_ITEM) {
            ShowWindow(hwnd, SW_RESTORE);
            SetForegroundWindow(hwnd);
        }
        else if (wmId == 5000) {
            RefreshAppList();
        }
        else if (wmId == 5001) {
            RefreshClientListView();
        }
        else if (wmId == ID_TRAY_EXIT_CONTEXT_MENU_ITEM) {
            SaveConfig(hwnd);
            RemoveTrayIcon(hwnd);
            PostQuitMessage(0);
        }
        else if (wmId == 1) { // Browse APK
            OPENFILENAMEA ofn; ZeroMemory(&ofn, sizeof(ofn)); ofn.lStructSize = sizeof(ofn);
            ofn.hwndOwner = hwnd; ofn.lpstrFile = filePath; ofn.lpstrFile[0] = '\0';
            ofn.nMaxFile = sizeof(filePath); ofn.lpstrFilter = "APK Files\0*.apk\0All Files\0*.*\0";
            ofn.Flags = OFN_PATHMUSTEXIST | OFN_FILEMUSTEXIST;
            if (GetOpenFileNameA(&ofn)) {
                SetWindowTextA(hwndApkLabel, filePath);
                ParseApkMetadata(filePath);
            }
        }
        else if (wmId == 3) { // Add Screenshot
            char imgPath[MAX_PATH] = "";
            OPENFILENAMEA ofn; ZeroMemory(&ofn, sizeof(ofn)); ofn.lStructSize = sizeof(ofn);
            ofn.hwndOwner = hwnd; ofn.lpstrFile = imgPath; ofn.lpstrFile[0] = '\0';
            ofn.nMaxFile = sizeof(imgPath); ofn.lpstrFilter = "Image Files\0*.png;*.jpg;*.jpeg\0All Files\0*.*\0";
            ofn.Flags = OFN_PATHMUSTEXIST | OFN_FILEMUSTEXIST;
            if (GetOpenFileNameA(&ofn)) {
                screenshots.push_back(imgPath);
                int imgIdx = AddImageToImageList(g_hImgListSS, imgPath);
                LVITEMA lvi = {0};
                lvi.mask = LVIF_TEXT | LVIF_IMAGE;
                lvi.iItem = ListView_GetItemCount(lstScreenshots);
                lvi.iImage = imgIdx;
                std::string fname = fs::path(imgPath).filename().string();
                lvi.pszText = (LPSTR)fname.c_str();
                ListView_InsertItem(lstScreenshots, &lvi);
                UpdatePreviewImage(screenshots.back());
            }
        }
        else if (wmId == 4) { screenshots.clear(); ListView_DeleteAllItems(lstScreenshots); ImageList_RemoveAll(g_hImgListSS); UpdatePreviewImage(""); }
        else if (wmId == 5) ClearForm();
        else if (wmId == 6) DeleteSelectedApp();
        else if (wmId == 7) ShowWindow(hwnd, SW_HIDE);
        else if (wmId == 2) { // Apply
            char n[256], p[256], v[256], d[4096], c[256], t[512];
            GetWindowTextA(hwndName, n, 256); GetWindowTextA(hwndPackage, p, 256);
            GetWindowTextA(hwndVersion, v, 256); GetWindowTextA(hwndDesc, d, 4096);
            GetWindowTextA(hwndCat, c, 256); GetWindowTextA(hwndTags, t, 512);
            if (strlen(n) == 0 || strlen(p) == 0 || strlen(v) == 0) {
                MessageBoxA(hwnd, "Required fields missing (Name, Package, and Version must be specified)!", "Validation Error", MB_OK | MB_ICONWARNING);
                break;
            }
            ProcessApp(filePath, n, p, v, d, c, t);
        }
        break;
    }
    case WM_CLOSE:
        ShowWindow(hwnd, SW_HIDE);
        return 0;
    case WM_CTLCOLORSTATIC:
    case WM_CTLCOLORBTN: {
        HDC hdcStatic = (HDC)wParam;
        HWND hwndControl = (HWND)lParam;
        SetBkMode(hdcStatic, TRANSPARENT);
        return (LRESULT)GetStockObject(HOLLOW_BRUSH);
    }
    case WM_DESTROY:
        SaveConfig(hwnd);
        if (g_hAppIcon) { DestroyIcon(g_hAppIcon); g_hAppIcon = NULL; }
        KillTimer(hwnd, 1002);
        StopServer();
        UnregisterHotKey(hwnd, 1);
        RemoveTrayIcon(hwnd);
        if (hSmallIcons) { ImageList_Destroy(hSmallIcons); hSmallIcons = NULL; }
        if (hFontSegoeNormal) DeleteObject(hFontSegoeNormal);
        if (hFontSegoeBold) DeleteObject(hFontSegoeBold);
        if (hbrBanner) DeleteObject(hbrBanner);
        if (g_hTabImageList) { ImageList_Destroy(g_hTabImageList); g_hTabImageList = NULL; }
        PostQuitMessage(0);
        return 0;
    }
    return DefWindowProcA(hwnd, uMsg, wParam, lParam);
}

int WINAPI WinMain(HINSTANCE hInstance, HINSTANCE hPrevInstance, LPSTR lpCmdLine, int nCmdShow) {
    char path[MAX_PATH];
    GetModuleFileNameA(NULL, path, MAX_PATH);
    fs::path exePath = path;
    fs::current_path(exePath.parent_path());

    GdiplusStartupInput gdiplusStartupInput;
    GdiplusStartup(&gdiplusToken, &gdiplusStartupInput, NULL);
    LoadConfig();

    INITCOMMONCONTROLSEX icex; icex.dwSize = sizeof(INITCOMMONCONTROLSEX);
    icex.dwICC = ICC_WIN95_CLASSES | ICC_STANDARD_CLASSES | ICC_TAB_CLASSES | ICC_LISTVIEW_CLASSES | ICC_BAR_CLASSES;
    InitCommonControlsEx(&icex);

    WNDCLASSA wc = { }; wc.lpfnWndProc = WindowProc; wc.hInstance = hInstance;
    wc.lpszClassName = "EliteAppMarketplaceServer"; wc.hbrBackground = (HBRUSH)(COLOR_BTNFACE + 1);
    wc.hIcon = GetDynamicAppIcon(hInstance);
    RegisterClassA(&wc);

    HWND hwnd = CreateWindowExA(0, wc.lpszClassName, "Local APK Store - Server Manager", WS_OVERLAPPEDWINDOW, g_windowX, g_windowY, g_windowWidth, g_windowHeight, NULL, NULL, hInstance, NULL);
    if (hwnd == NULL) return 0;
    
    int showMode = g_windowMaximized ? SW_SHOWMAXIMIZED : nCmdShow;
    ShowWindow(hwnd, showMode);
    UpdateWindow(hwnd);

    MSG msg;
    while (GetMessageA(&msg, NULL, 0, 0)) {
        TranslateMessage(&msg);
        DispatchMessageA(&msg);
    }
    GdiplusShutdown(gdiplusToken);
    return msg.wParam;
}
