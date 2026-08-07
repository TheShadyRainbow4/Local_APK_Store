import re
with open('Manager_App/main.cpp', 'r') as f:
    code = f.read()

# 1. g_hImgListSS initialization
code = re.sub(
    r'hwndMain = hwnd;\s*RegisterHotKey',
    r'hwndMain = hwnd;\n        g_hImgListSS = ImageList_Create(120, 200, ILC_COLOR32 | ILC_MASK, 5, 5);\n        RegisterHotKey',
    code
)

# 2. Fix lstScreenshots style to LVS_REPORT | LVS_NOCOLUMNHEADER
code = re.sub(
    r'lstScreenshots = CreateWindowExA\(WS_EX_CLIENTEDGE, WC_LISTVIEWA, \"\", WS_CHILD \| WS_VISIBLE \| LVS_ICON \| LVS_SINGLESEL \| LVS_SHOWSELALWAYS, 0, 0, 0, 0, hwndTab, \(HMENU\)30, hInstance, NULL\);',
    r'lstScreenshots = CreateWindowExA(WS_EX_CLIENTEDGE, WC_LISTVIEWA, "", WS_CHILD | WS_VISIBLE | LVS_REPORT | LVS_NOCOLUMNHEADER | LVS_SINGLESEL | LVS_SHOWSELALWAYS, 0, 0, 0, 0, hwndTab, (HMENU)30, hInstance, NULL);',
    code
)

# 3. Fix lstScreenshots ImageList (LVSIL_SMALL instead of LVSIL_NORMAL)
code = re.sub(
    r'ListView_SetImageList\(lstScreenshots, g_hImgListSS, LVSIL_NORMAL\);',
    r'ListView_SetImageList(lstScreenshots, g_hImgListSS, LVSIL_SMALL);',
    code
)

# 4. Remove text from lstScreenshots
code = re.sub(
    r'lvi\.mask = LVIF_TEXT \| LVIF_IMAGE;\s*lvi\.iItem = ListView_GetItemCount\(lstScreenshots\);\s*lvi\.iImage = imgIdx;\s*lvi\.pszText = \(LPSTR\)s\.get<std::string>\(\)\.c_str\(\);\s*ListView_InsertItem\(lstScreenshots, &lvi\);',
    r'lvi.mask = LVIF_IMAGE;\n            lvi.iItem = ListView_GetItemCount(lstScreenshots);\n            lvi.iImage = imgIdx;\n            ListView_InsertItem(lstScreenshots, &lvi);',
    code
)
code = re.sub(
    r'lvi\.mask = LVIF_TEXT \| LVIF_IMAGE;\s*lvi\.iItem = ListView_GetItemCount\(lstScreenshots\);\s*lvi\.iImage = imgIdx;\s*std::string fname = fs::path\(path\)\.filename\(\)\.string\(\);\s*lvi\.pszText = \(LPSTR\)fname\.c_str\(\);\s*ListView_InsertItem\(lstScreenshots, &lvi\);',
    r'lvi.mask = LVIF_IMAGE;\n                lvi.iItem = ListView_GetItemCount(lstScreenshots);\n                lvi.iImage = imgIdx;\n                ListView_InsertItem(lstScreenshots, &lvi);',
    code
)
code = re.sub(
    r'lvi\.mask = LVIF_TEXT \| LVIF_IMAGE;\s*lvi\.iItem = ListView_GetItemCount\(lstScreenshots\);\s*lvi\.iImage = imgIdx;\s*std::string fname = fs::path\(imgPath\)\.filename\(\)\.string\(\);\s*lvi\.pszText = \(LPSTR\)fname\.c_str\(\);\s*ListView_InsertItem\(lstScreenshots, &lvi\);',
    r'lvi.mask = LVIF_IMAGE;\n                lvi.iItem = ListView_GetItemCount(lstScreenshots);\n                lvi.iImage = imgIdx;\n                ListView_InsertItem(lstScreenshots, &lvi);',
    code
)

# 5. Handle double-click on lstScreenshots
code = re.sub(
    r'else if \(pnmh->hwndFrom == lstScreenshots && \(pnmh->code == LVN_ITEMCHANGED \|\| pnmh->code == NM_CLICK\)\) \{\s*int sIdx = ListView_GetNextItem\(lstScreenshots, -1, LVNI_SELECTED\);\s*if \(sIdx >= 0 && sIdx < \(int\)screenshots\.size\(\)\) UpdatePreviewImage\(screenshots\[sIdx\]\);\s*\}',
    r'''else if (pnmh->hwndFrom == lstScreenshots && pnmh->code == NM_DBLCLK) {
            int sIdx = ListView_GetNextItem(lstScreenshots, -1, LVNI_SELECTED);
            if (sIdx >= 0 && sIdx < (int)screenshots.size()) {
                ShellExecuteA(NULL, "open", screenshots[sIdx].c_str(), NULL, NULL, SW_SHOWNORMAL);
            }
        }''',
    code
)

# 6. Add SS_NOTIFY to hwndPreview
code = re.sub(
    r'hwndPreview = CreateWindowA\(\"STATIC\", \"\", WS_CHILD \| WS_VISIBLE \| SS_BITMAP \| SS_CENTERIMAGE \| SS_REALSIZEIMAGE \| WS_EX_CLIENTEDGE, 0, 0, 0, 0, hwndTab, NULL, hInstance, NULL\);',
    r'hwndPreview = CreateWindowA("STATIC", "", WS_CHILD | WS_VISIBLE | SS_BITMAP | SS_CENTERIMAGE | SS_REALSIZEIMAGE | WS_EX_CLIENTEDGE | SS_NOTIFY, 0, 0, 0, 0, hwndTab, (HMENU)40, hInstance, NULL);',
    code
)

# 7. Add Double Click handler for hwndPreview
code = re.sub(
    r'else if \(wmId == 4\) \{ screenshots\.clear\(\); ListView_DeleteAllItems\(lstScreenshots\); ImageList_RemoveAll\(g_hImgListSS\); UpdatePreviewImage\(\"\"\); \}',
    r'''else if (wmId == 4) { screenshots.clear(); ListView_DeleteAllItems(lstScreenshots); ImageList_RemoveAll(g_hImgListSS); UpdatePreviewImage(""); }
        else if (HIWORD(wParam) == STN_DBLCLK && LOWORD(wParam) == 40) {
            if (selectedAppIndex >= 0 && selectedAppIndex < (int)dbCache["apps"].size()) {
                std::string iconFile = dbCache["apps"][selectedAppIndex].value("icon", "");
                if (!iconFile.empty()) ShellExecuteA(NULL, "open", (imgDir + "\\\\" + iconFile).c_str(), NULL, NULL, SW_SHOWNORMAL);
            }
        }''',
    code
)

# 8. Modify Settings Button to open website
code = re.sub(
    r'else if \(wmId == ID_FILE_SETTINGS \|\| wmId == ID_TOOLBAR_SETTINGS\) \{\s*ShowSettingsDialog\(hwnd\);\s*\}',
    r'''else if (wmId == ID_FILE_SETTINGS) {
            ShowSettingsDialog(hwnd);
        }
        else if (wmId == ID_TOOLBAR_SETTINGS) {
            std::string url = "http://127.0.0.1:" + std::to_string(serverPort) + "/";
            ShellExecuteA(NULL, "open", url.c_str(), NULL, NULL, SW_SHOWNORMAL);
        }''',
    code
)

# 9. Clear background in UpdatePreviewImage
code = re.sub(
    r'Graphics g\(resized\);\s*g\.SetInterpolationMode\(InterpolationModeHighQualityBicubic\);',
    r'Graphics g(resized);\n            g.Clear(Color(255, 255, 255));\n            g.SetInterpolationMode(InterpolationModeHighQualityBicubic);',
    code
)

# 10. Remove UpdatePreviewImage for screenshots
code = re.sub(r'\s*UpdatePreviewImage\(screenshots\[0\]\);', r'', code)
code = re.sub(r'\s*UpdatePreviewImage\(screenshots\.back\(\)\);', r'', code)
code = re.sub(r'if \(screenshots\.size\(\) > 0\) \{\s*\} else \{\s*', r'', code)
# Fix the bracket for if(screenshots.size() > 0) else {
# Wait, actually let's just do a string replace for that whole block
block = """    if (screenshots.size() > 0) {
        
    } else {
        std::string iconP = app.value("icon", "");
        if (!iconP.empty() && fs::exists(imgDir + "\\\\" + iconP)) {
            UpdatePreviewImage(imgDir + "\\\\" + iconP);
        } else {
            UpdatePreviewImage("");
        }
    }"""
code = code.replace(
    """    if (screenshots.size() > 0) {
        UpdatePreviewImage(screenshots[0]);
    } else {
        std::string iconP = app.value("icon", "");
        if (!iconP.empty() && fs::exists(imgDir + "\\\\" + iconP)) {
            UpdatePreviewImage(imgDir + "\\\\" + iconP);
        } else {
            UpdatePreviewImage("");
        }
    }""",
    """    std::string iconP = app.value("icon", "");
    if (!iconP.empty() && fs::exists(imgDir + "\\\\" + iconP)) {
        UpdatePreviewImage(imgDir + "\\\\" + iconP);
    } else {
        UpdatePreviewImage("");
    }"""
)

# 11. Fix extract icon path issue! Update SaveAppFromForm to look at the temp path
code = re.sub(
    r'std::string iconP = imgDir \+ \"/\" \+ pkg \+ \"_icon\.png\";\s*if \(fs::exists\(iconP\)\) app\[\"icon\"\] = pkg \+ \"_icon\.png\";',
    r'''std::string tempIconP = fs::absolute(imgDir).string() + "\\\\" + tempApp["package_name"].get<std::string>() + "_icon.png";
            std::string iconP = imgDir + "/" + pkg + "_icon.png";
            if (pkg != tempApp["package_name"].get<std::string>() && fs::exists(tempIconP)) {
                CopyFileLocal(tempIconP, iconP);
            }
            if (fs::exists(iconP)) app["icon"] = pkg + "_icon.png";
            else if (fs::exists(tempIconP)) app["icon"] = tempApp["package_name"].get<std::string>() + "_icon.png";''',
    code
)
code = re.sub(
    r'std::string iconP = imgDir \+ \"/\" \+ pkg \+ \"_icon\.png\";\s*if \(fs::exists\(iconP\)\) newApp\[\"icon\"\] = pkg \+ \"_icon\.png\";',
    r'''std::string tempIconP = fs::absolute(imgDir).string() + "\\\\" + tempApp["package_name"].get<std::string>() + "_icon.png";
        std::string iconP = imgDir + "/" + pkg + "_icon.png";
        if (pkg != tempApp["package_name"].get<std::string>() && fs::exists(tempIconP)) {
            CopyFileLocal(tempIconP, iconP);
        }
        if (fs::exists(iconP)) newApp["icon"] = pkg + "_icon.png";
        else if (fs::exists(tempIconP)) newApp["icon"] = tempApp["package_name"].get<std::string>() + "_icon.png";''',
    code
)

with open('Manager_App/main.cpp', 'w') as f:
    f.write(code)
