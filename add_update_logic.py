import os
import json
import sys

base_dir = r"C:\Users\Administrator\Desktop\Local_APK_Store\Client_App\app\src\main\java\com\elitesoftware\appmarketplace"

def modify_main_activity():
    path = os.path.join(base_dir, "MainActivity.java")
    with open(path, "r") as f:
        code = f.read()

    helper = '''    private int getAppInstallState(Context context, String packageName, String serverVersion) {
        try {
            android.content.pm.PackageInfo pInfo = context.getPackageManager().getPackageInfo(packageName, 0);
            String installedVersion = pInfo.versionName;
            if (serverVersion != null && serverVersion.equals(installedVersion)) {
                return 2; // OPEN
            } else {
                return 1; // UPDATE
            }
        } catch (android.content.pm.PackageManager.NameNotFoundException e) {
            return 0; // INSTALL
        }
    }'''

    if "getAppInstallState" not in code:
        code = code.replace("private class AppAdapter extends BaseAdapter {", helper + "\n\n    private class AppAdapter extends BaseAdapter {")

    getView_logic = '''
            TextView tvAppName = convertView.findViewById(R.id.tvAppName);
            TextView tvAppDesc = convertView.findViewById(R.id.tvAppDesc);
            Button btnInstall = convertView.findViewById(R.id.btnInstall);
            
            tvAppName.setText(app.optString("name", "Unknown App"));
            tvAppDesc.setText(app.optString("description", "No description available."));
            
            String packageName = app.optString("package_name", "");
            String serverVersion = "";
            try {
                org.json.JSONArray versions = app.getJSONArray("versions");
                if (versions.length() > 0) {
                    serverVersion = versions.getJSONObject(versions.length() - 1).optString("version", "");
                }
            } catch(Exception e) {}
            
            int state = getAppInstallState(MainActivity.this, packageName, serverVersion);
            if (state == 2) {
                btnInstall.setText("OPEN");
                btnInstall.setBackgroundColor(android.graphics.Color.parseColor("#444444"));
                btnInstall.setTextColor(android.graphics.Color.parseColor("#FFFFFF"));
            } else if (state == 1) {
                btnInstall.setText("UPDATE");
                btnInstall.setBackgroundColor(android.graphics.Color.parseColor("#FF8800"));
                btnInstall.setTextColor(android.graphics.Color.parseColor("#FFFFFF"));
            } else {
                btnInstall.setText("INSTALL");
                btnInstall.setBackgroundColor(android.graphics.Color.parseColor("#A4C639"));
                btnInstall.setTextColor(android.graphics.Color.parseColor("#000000"));
            }
            
            btnInstall.setOnClickListener(v -> {
                if (state == 2) {
                    Intent launchIntent = getPackageManager().getLaunchIntentForPackage(packageName);
                    if (launchIntent != null) {
                        startActivity(launchIntent);
                    } else {
                        Toast.makeText(MainActivity.this, "Cannot launch app", Toast.LENGTH_SHORT).show();
                    }
                } else {
                    String ip = app.optString("_server_ip", "");
                    Toast.makeText(MainActivity.this, (state == 1 ? "Updating " : "Installing ") + app.optString("name") + "...", Toast.LENGTH_SHORT).show();
                    // Implement actual download logic here in the future
                }
            });
            
            return convertView;
'''
    
    old_getView = '''            TextView tvAppName = convertView.findViewById(R.id.tvAppName);
            TextView tvAppDesc = convertView.findViewById(R.id.tvAppDesc);
            Button btnInstall = convertView.findViewById(R.id.btnInstall);
            
            tvAppName.setText(app.optString("name", "Unknown App"));
            tvAppDesc.setText(app.optString("description", "No description available."));
            
            btnInstall.setOnClickListener(v -> {
                // Keep it from triggering the list item click
                String ip = app.optString("_server_ip", "");
                Toast.makeText(MainActivity.this, "Installing " + app.optString("name") + "...", Toast.LENGTH_SHORT).show();
            });
            
            return convertView;'''

    code = code.replace(old_getView, getView_logic)
    with open(path, "w") as f:
        f.write(code)


def modify_detail_activity():
    path = os.path.join(base_dir, "AppDetailActivity.java")
    with open(path, "r") as f:
        code = f.read()

    helper = '''    private int getAppInstallState(android.content.Context context, String packageName, String serverVersion) {
        try {
            android.content.pm.PackageInfo pInfo = context.getPackageManager().getPackageInfo(packageName, 0);
            String installedVersion = pInfo.versionName;
            if (serverVersion != null && serverVersion.equals(installedVersion)) {
                return 2; // OPEN
            } else {
                return 1; // UPDATE
            }
        } catch (android.content.pm.PackageManager.NameNotFoundException e) {
            return 0; // INSTALL
        }
    }'''

    if "getAppInstallState" not in code:
        code = code.replace("protected void onCreate(Bundle savedInstanceState) {", helper + "\n\n    @Override\n    protected void onCreate(Bundle savedInstanceState) {")

    logic = '''            detailName.setText(app.optString("name", "Unknown"));
            detailPackage.setText(app.optString("package_name", ""));
            detailCategory.setText(app.optString("category", "Uncategorized"));
            detailDesc.setText(app.optString("description", "No description available."));
            
            String packageName = app.optString("package_name", "");
            String serverVersion = "";
            try {
                org.json.JSONArray versions = app.getJSONArray("versions");
                if (versions.length() > 0) {
                    serverVersion = versions.getJSONObject(versions.length() - 1).optString("version", "");
                }
            } catch(Exception e) {}
            
            int state = getAppInstallState(this, packageName, serverVersion);
            if (state == 2) {
                detailInstallBtn.setText("OPEN");
                detailInstallBtn.setBackgroundColor(android.graphics.Color.parseColor("#444444"));
                detailInstallBtn.setTextColor(android.graphics.Color.parseColor("#FFFFFF"));
            } else if (state == 1) {
                detailInstallBtn.setText("UPDATE (" + serverVersion + ")");
                detailInstallBtn.setBackgroundColor(android.graphics.Color.parseColor("#FF8800"));
                detailInstallBtn.setTextColor(android.graphics.Color.parseColor("#FFFFFF"));
            } else {
                detailInstallBtn.setText("INSTALL");
                detailInstallBtn.setBackgroundColor(android.graphics.Color.parseColor("#A4C639"));
                detailInstallBtn.setTextColor(android.graphics.Color.parseColor("#000000"));
            }

            detailInstallBtn.setOnClickListener(v -> {
                if (state == 2) {
                    android.content.Intent launchIntent = getPackageManager().getLaunchIntentForPackage(packageName);
                    if (launchIntent != null) {
                        startActivity(launchIntent);
                    } else {
                        Toast.makeText(this, "Cannot launch app", Toast.LENGTH_SHORT).show();
                    }
                } else {
                    Toast.makeText(this, "Downloading from " + ip + "...", Toast.LENGTH_SHORT).show();
                    // TODO: Implement actual APK download and Shizuku install here
                }
            });'''

    old_logic = '''            detailName.setText(app.optString("name", "Unknown"));
            detailPackage.setText(app.optString("package_name", ""));
            detailCategory.setText(app.optString("category", "Uncategorized"));
            detailDesc.setText(app.optString("description", "No description available."));
            
            detailInstallBtn.setOnClickListener(v -> {
                Toast.makeText(this, "Downloading from " + ip + "...", Toast.LENGTH_SHORT).show();
                // TODO: Implement actual APK download and Shizuku install here
            });'''

    code = code.replace(old_logic, logic)
    with open(path, "w") as f:
        f.write(code)

modify_main_activity()
modify_detail_activity()

