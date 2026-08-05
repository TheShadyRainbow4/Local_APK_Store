import os
import re

file_path = r'C:\Users\Administrator\Desktop\Local_APK_Store\Manager_App\main.cpp'

with open(file_path, 'r', encoding='utf-8') as f:
    content = f.read()

# Find the insertion point, right before the server starts or after another endpoint.
# Line 1027 is /api/disconnect. I'll search for it.
insert_idx = content.find('svrPtr->Post("/api/disconnect"')
if insert_idx == -1:
    print("Could not find insertion point!")
    exit(1)

endpoints = """
    svrPtr->Post("/api/upload_apk", [](const httplib::Request& req, httplib::Response& res, const httplib::ContentReader& content_reader) {
        if (!req.has_header("X-File-Name")) {
            res.status = 400;
            res.set_content("{\\"error\\":\\"Missing X-File-Name header\\"}", "application/json");
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
            res.set_content("{\\"status\\":\\"ok\\"}", "application/json");
        } else {
            res.status = 500;
            res.set_content("{\\"error\\":\\"Could not open file for writing\\"}", "application/json");
        }
    });

    svrPtr->Post("/api/upload_image", [](const httplib::Request& req, httplib::Response& res, const httplib::ContentReader& content_reader) {
        if (!req.has_header("X-File-Name")) {
            res.status = 400;
            res.set_content("{\\"error\\":\\"Missing X-File-Name header\\"}", "application/json");
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
            res.set_content("{\\"status\\":\\"ok\\"}", "application/json");
        } else {
            res.status = 500;
            res.set_content("{\\"error\\":\\"Could not open file for writing\\"}", "application/json");
        }
    });

    svrPtr->Post("/api/update_app", [](const httplib::Request& req, httplib::Response& res) {
        try {
            json j = json::parse(req.body);
            std::string pkg = j.value("package_name", "");
            if (pkg.empty()) {
                res.status = 400;
                res.set_content("{\\"error\\":\\"missing package_name\\"}", "application/json");
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
            PostMessageA(g_hwndMain, WM_COMMAND, 5000, 0);

            res.set_content("{\\"status\\":\\"ok\\"}", "application/json");
        } catch (...) {
            res.status = 400;
            res.set_content("{\\"error\\":\\"invalid json\\"}", "application/json");
        }
    });

"""

new_content = content[:insert_idx] + endpoints + content[insert_idx:]

with open(file_path, 'w', encoding='utf-8') as f:
    f.write(new_content)

print("Endpoints added!")
