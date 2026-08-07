import re
with open('Manager_App/main.cpp', 'r') as f:
    code = f.read()

replacement = '''void ProcessApp(std::string name, std::string pkg, std::string ver, std::string desc, std::string cat, std::string tags, std::string apkName) {
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
            
            std::string tempIconP = fs::absolute(imgDir).string() + "\\\\" + pkg + "_icon.png";
            std::string iconP = imgDir + "/" + pkg + "_icon.png";
            if (fs::exists(tempIconP) && tempIconP != fs::absolute(iconP).string()) {
                CopyFileLocal(tempIconP, iconP);
            }
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
        
        std::string tempIconP = fs::absolute(imgDir).string() + "\\\\" + pkg + "_icon.png";
        std::string iconP = imgDir + "/" + pkg + "_icon.png";
        if (fs::exists(tempIconP) && tempIconP != fs::absolute(iconP).string()) {
            CopyFileLocal(tempIconP, iconP);
        }
        if (fs::exists(iconP)) newApp["icon"] = pkg + "_icon.png";
        
        db["apps"].push_back(newApp);
    }
    saveDb(db); RefreshAppList();
    MessageBoxA(hwndMain, "Application entry processed and saved successfully!", "Success", MB_OK | MB_ICONINFORMATION);
}'''

code = re.sub(
    r'void ProcessApp\(std::string name, std::string pkg, std::string ver, std::string desc, std::string cat, std::string tags, std::string apkName\)\s*\{.*?\n\}',
    replacement,
    code,
    flags=re.MULTILINE | re.DOTALL
)

with open('Manager_App/main.cpp', 'w') as f:
    f.write(code)
