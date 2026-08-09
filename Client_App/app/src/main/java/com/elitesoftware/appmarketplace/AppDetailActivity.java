package com.elitesoftware.appmarketplace;

import android.app.Activity;
import android.content.Intent;
import android.os.Bundle;
import android.view.View;
import android.widget.Button;
import android.widget.ImageButton;
import android.widget.ImageView;
import android.widget.ProgressBar;
import android.widget.TextView;
import android.widget.Toast;
import androidx.appcompat.app.AppCompatActivity;
import rikka.shizuku.Shizuku;
import org.json.JSONObject;
import java.io.BufferedInputStream;
import java.io.File;
import java.io.FileOutputStream;
import java.io.InputStream;
import java.io.OutputStream;
import java.net.HttpURLConnection;
import java.net.URL;

public class AppDetailActivity extends AppCompatActivity {

    @Override
    protected void onCreate(Bundle savedInstanceState) {
        android.content.SharedPreferences prefs = getSharedPreferences("prefs", MODE_PRIVATE);
        String theme = prefs.getString("theme", "light");
        if (theme.equals("light")) {
            androidx.appcompat.app.AppCompatDelegate.setDefaultNightMode(androidx.appcompat.app.AppCompatDelegate.MODE_NIGHT_NO);
        } else if (theme.equals("dark") || theme.equals("amoled")) {
            androidx.appcompat.app.AppCompatDelegate.setDefaultNightMode(androidx.appcompat.app.AppCompatDelegate.MODE_NIGHT_YES);
        }
        super.onCreate(savedInstanceState);
        setContentView(R.layout.activity_app_detail);
        
        if (theme.equals("amoled")) {
            getWindow().getDecorView().setBackgroundColor(android.graphics.Color.BLACK);
            android.view.View root = ((android.view.ViewGroup)findViewById(android.R.id.content)).getChildAt(0);
            if (root != null) root.setBackgroundColor(android.graphics.Color.BLACK);
        }

        if (getSupportActionBar() != null) getSupportActionBar().hide();
        
        ImageButton btnBack = findViewById(R.id.btnBack);
        btnBack.setOnClickListener(v -> finish());
        
        try {
            String appJsonStr = getIntent().getStringExtra("app_json");
            JSONObject app = new JSONObject(appJsonStr);
            String ipTemp = getIntent().getStringExtra("server_ip");
            if (ipTemp == null || ipTemp.isEmpty()) ipTemp = app.optString("_server_ip");
            final String ip = ipTemp;
            
            TextView detailName = findViewById(R.id.detailName);
            TextView detailPackage = findViewById(R.id.detailPackage);
            TextView detailCategory = findViewById(R.id.detailCategory);
            TextView detailDesc = findViewById(R.id.detailDesc);
            Button detailInstallBtn = findViewById(R.id.detailInstallBtn);
            com.elitesoftware.appmarketplace.EliteProgressBar detailProgressBar = findViewById(R.id.detailProgressBar);
            ImageView detailIcon = findViewById(R.id.detailIcon);
            
            Button btnAddScreenshots = findViewById(R.id.btnAddScreenshots);
            if (btnAddScreenshots != null) {
                btnAddScreenshots.setOnClickListener(v -> {
                    Intent uploadIntent = new Intent(AppDetailActivity.this, UploadActivity.class);
                    uploadIntent.putExtra("package_name", app.optString("package_name"));
                    uploadIntent.putExtra("server_ip", ip);
                    startActivity(uploadIntent);
                });
            }
            
            detailName.setText(app.optString("name", "Unknown"));
            detailPackage.setText(app.optString("package_name", ""));
            detailCategory.setText(app.optString("category", "Uncategorized"));
            detailDesc.setText(app.optString("description", "No description available."));
            detailIcon.setImageResource(R.mipmap.ic_launcher);
            
            android.widget.Spinner detailVersionSpinner = findViewById(R.id.detailVersionSpinner);
            java.util.List<org.json.JSONObject> sortedVersions = new java.util.ArrayList<>();
            org.json.JSONArray versionsArr = app.getJSONArray("versions");
            for (int i = 0; i < versionsArr.length(); i++) {
                sortedVersions.add(versionsArr.getJSONObject(i));
            }
            java.util.Collections.sort(sortedVersions, (o1, o2) -> {
                return compareVersions(o2.optString("version"), o1.optString("version")); // descending
            });
            // Update the original array to match sorted order (for installAction indexing)
            org.json.JSONArray newVersionsArr = new org.json.JSONArray();
            java.util.List<String> versionLabels = new java.util.ArrayList<>();
            for (org.json.JSONObject vObj : sortedVersions) {
                newVersionsArr.put(vObj);
                versionLabels.add(vObj.getString("version"));
            }
            app.put("versions", newVersionsArr);
            final org.json.JSONArray finalVersionsArr = newVersionsArr;
            
            android.widget.ArrayAdapter<String> adapter = new android.widget.ArrayAdapter<>(this, android.R.layout.simple_spinner_dropdown_item, versionLabels);
            detailVersionSpinner.setAdapter(adapter);
            
            if (app.has("icon") && !app.optString("icon").isEmpty()) {
                String iconVal = app.optString("icon");
                String iconUrl = iconVal.startsWith("local://") ? iconVal : "http://" + ip + ":8552/images/" + iconVal.replace(" ", "%20");
                loadImageAsync(iconUrl, detailIcon);
            }
            
            if (app.has("screenshots") && app.getJSONArray("screenshots").length() > 0) {
                TextView screenshotsLabel = findViewById(R.id.screenshotsLabel);
                android.widget.HorizontalScrollView screenshotsScrollView = findViewById(R.id.screenshotsScrollView);
                android.widget.LinearLayout screenshotsContainer = findViewById(R.id.screenshotsContainer);
                
                screenshotsLabel.setVisibility(View.VISIBLE);
                screenshotsScrollView.setVisibility(View.VISIBLE);
                
                org.json.JSONArray screenshots = app.getJSONArray("screenshots");
                for (int i = 0; i < screenshots.length(); i++) {
                    String screenshotName = screenshots.getString(i);
                    String screenshotUrl = "http://" + ip + ":8552/images/" + screenshotName.replace(" ", "%20");
                    
                    ImageView imgView = new ImageView(this);
                    android.widget.LinearLayout.LayoutParams lp = new android.widget.LinearLayout.LayoutParams(
                            (int)(120 * getResources().getDisplayMetrics().density), 
                            (int)(200 * getResources().getDisplayMetrics().density)
                    );
                    lp.setMargins(0, 0, (int)(8 * getResources().getDisplayMetrics().density), 0);
                    imgView.setLayoutParams(lp);
                    imgView.setScaleType(ImageView.ScaleType.CENTER_CROP);
                    imgView.setBackgroundColor(0xFFDDDDDD);
                    
                    final String finalUrl = screenshotUrl;
                    imgView.setOnClickListener(v -> {
                        android.content.Intent intent = new android.content.Intent(android.content.Intent.ACTION_VIEW);
                        intent.setDataAndType(android.net.Uri.parse(finalUrl), "image/*");
                        try { startActivity(intent); } catch(Exception e) {}
                    });
                    
                    screenshotsContainer.addView(imgView);
                    loadImageAsync(screenshotUrl, imgView);
                }
            }
            
            String pkgName = app.optString("package_name");
            String installedVersionTemp = null;
            try {
                android.content.pm.PackageInfo pi = getPackageManager().getPackageInfo(pkgName, 0);
                installedVersionTemp = pi.versionName;
            } catch (Exception e) {}
            final String installedVersion = installedVersionTemp;

            View.OnClickListener installAction = v -> {
                detailInstallBtn.setEnabled(false);
                detailProgressBar.setVisibility(View.VISIBLE);
                detailProgressBar.setProgress(0);
                
                new Thread(() -> {
                        try {
                            int selectedIdx = 0;
                            String selectedVer = "";
                            // Get selected index safely
                            java.util.concurrent.atomic.AtomicInteger ai = new java.util.concurrent.atomic.AtomicInteger(0);
                            runOnUiThread(() -> ai.set(detailVersionSpinner.getSelectedItemPosition()));
                            Thread.sleep(100); // wait for UI thread
                            selectedIdx = ai.get();
                            if(selectedIdx < 0) selectedIdx = 0;
                            
                            org.json.JSONObject verObj = finalVersionsArr.getJSONObject(selectedIdx);
                            String apkUrl = "http://" + ip + ":8552/apks/" + verObj.getString("file").replace(" ", "%20");
                            selectedVer = verObj.getString("version");
                            
                            URL url = new URL(apkUrl);
                            HttpURLConnection conn = (HttpURLConnection) url.openConnection();
                            conn.connect();
                            int fileLength = conn.getContentLength();
                            
                            // Add Premium Feel Delay
                            runOnUiThread(() -> detailInstallBtn.setText("PREPARING..."));
                            try { Thread.sleep(600); } catch(Exception e) {}
                            
                            InputStream input = new BufferedInputStream(url.openStream(), 8192);
                            String safeName = app.optString("name").replaceAll(" ", "_");
                            File apkFile = new File(getExternalFilesDir(null), safeName + "_v" + selectedVer + ".apk");
                            OutputStream output = new FileOutputStream(apkFile);
                            
                            byte data[] = new byte[8192];
                            long total = 0;
                            int count;
                            while ((count = input.read(data)) != -1) {
                                total += count;
                                int progress = (int) (total * 100 / fileLength);
                                runOnUiThread(() -> detailProgressBar.setProgress(progress));
                                output.write(data, 0, count);
                                // slight artificial delay for progress bar visibility
                                try { Thread.sleep(1); } catch(Exception e) {}
                            }
                            output.flush();
                            output.close();
                            input.close();
                            
                            runOnUiThread(() -> {
                                detailProgressBar.setVisibility(View.GONE);
                                detailInstallBtn.setText("INSTALLING...");
                            });
                            
                            // Premium feel delay for installation
                            try { Thread.sleep(800); } catch(Exception e) {}

                            // Install via Shizuku API Stream (Bypasses Scoped Storage)
                            boolean installed_ok = false;
                            String errorLog = "";
                            
                            String packageName = app.optString("package_name");
                            boolean isSelfUpdate = packageName.equals(getPackageName());
                            
                            try {
                                Process p = null;
                                boolean isSu = false;
                                if (Shizuku.pingBinder() && Shizuku.checkSelfPermission() == android.content.pm.PackageManager.PERMISSION_GRANTED) {
                                    p = Shizuku.newProcess(new String[]{"pm", "install", "-r", "-S", String.valueOf(apkFile.length())}, null, null);
                                } else {
                                    try {
                                        if (com.rosan.dhizuku.api.Dhizuku.isPermissionGranted()) {
                                            p = com.rosan.dhizuku.api.Dhizuku.newProcess(new String[]{"pm", "install", "-r", "-S", String.valueOf(apkFile.length())}, null, null);
                                        }
                                    } catch(Exception e) {}
                                    if (p == null) {
                                        // SU fallback
                                        isSu = true;
                                        p = Runtime.getRuntime().exec("su");
                                        p.getOutputStream().write(("pm install -r -S " + apkFile.length() + "\n").getBytes());
                                    }
                                }
                                
                                if (p != null) {
                                    java.io.OutputStream out = p.getOutputStream();
                                    java.io.FileInputStream in = new java.io.FileInputStream(apkFile);
                                    byte[] buf = new byte[65536];
                                    int len;
                                    try {
                                        while ((len = in.read(buf)) > 0) out.write(buf, 0, len);
                                        out.flush();
                                        if (isSu) {
                                            out.write("\nexit\n".getBytes());
                                            out.flush();
                                        }
                                        out.close();
                                    } catch (Exception streamErr) {
                                        errorLog += "Stream closed early: " + streamErr.getMessage() + ". ";
                                    }
                                    in.close();
                                    
                                    java.io.BufferedReader reader = new java.io.BufferedReader(new java.io.InputStreamReader(p.getErrorStream()));
                                    String line;
                                    while ((line = reader.readLine()) != null) errorLog += line + "\n";
                                    
                                    if (p.waitFor() == 0) {
                                        installed_ok = true;
                                        if (isSelfUpdate) {
                                            if (Shizuku.pingBinder() && Shizuku.checkSelfPermission() == android.content.pm.PackageManager.PERMISSION_GRANTED) {
                                                Shizuku.newProcess(new String[]{"sh", "-c", "am start -n " + getPackageName() + "/.MainActivity"}, null, null);
                                            } else {
                                                try {
                                                    if (com.rosan.dhizuku.api.Dhizuku.isPermissionGranted()) {
                                                        com.rosan.dhizuku.api.Dhizuku.newProcess(new String[]{"sh", "-c", "am start -n " + getPackageName() + "/.MainActivity"}, null, null);
                                                    }
                                                } catch(Exception e){}
                                            }
                                        }
                                    } else {
                                        errorLog += " Process returned non-zero. ";
                                    }
                                } else {
                                    errorLog += "Shizuku/Dhizuku/SU is not available or permission denied. ";
                                }
                            } catch (Exception e) {
                                errorLog += "Install Error: " + e.getMessage() + "\n";
                            }
                            
                            if (!installed_ok) {
                                runOnUiThread(() -> {
                                    try {
                                        android.content.Intent intent = new android.content.Intent(android.content.Intent.ACTION_VIEW);
                                        android.net.Uri apkUri = androidx.core.content.FileProvider.getUriForFile(AppDetailActivity.this, getPackageName() + ".provider", apkFile);
                                        intent.setDataAndType(apkUri, "application/vnd.android.package-archive");
                                        intent.setFlags(android.content.Intent.FLAG_ACTIVITY_NEW_TASK);
                                        intent.addFlags(android.content.Intent.FLAG_GRANT_READ_URI_PERMISSION);
                                        startActivity(intent);
                                    } catch (Exception e) {
                                        Toast.makeText(AppDetailActivity.this, "Installation failed: " + e.getMessage(), Toast.LENGTH_LONG).show();
                                    }
                                    detailInstallBtn.setText("INSTALL");
                                    detailInstallBtn.setEnabled(true);
                                    detailProgressBar.setVisibility(View.GONE);
                                });
                                return; // abort
                            }
                            
                            runOnUiThread(() -> {
                                detailInstallBtn.setText("OPEN");
                                detailInstallBtn.setEnabled(true);
                                try {
                                    android.content.SharedPreferences p = getSharedPreferences("prefs", MODE_PRIVATE);
                                    org.json.JSONArray cachedApps = new org.json.JSONArray(p.getString("cached_apps", "[]"));
                                    boolean exists = false;
                                    for (int i = 0; i < cachedApps.length(); i++) {
                                        if (cachedApps.getJSONObject(i).optString("package_name").equals(app.optString("package_name"))) {
                                            exists = true; break;
                                        }
                                    }
                                    if (!exists) {
                                        cachedApps.put(app);
                                        p.edit().putString("cached_apps", cachedApps.toString()).apply();
                                    }
                                } catch (Exception ex) {}
                                detailInstallBtn.setOnClickListener(v2 -> {
                                    Intent launchIntent = getPackageManager().getLaunchIntentForPackage(app.optString("package_name"));
                                    if (launchIntent != null) startActivity(launchIntent);
                                });
                            });
                        } catch (Exception e) {
                            e.printStackTrace();
                            runOnUiThread(() -> {
                                Toast.makeText(AppDetailActivity.this, "Download failed", Toast.LENGTH_SHORT).show();
                                detailInstallBtn.setEnabled(true);
                                detailInstallBtn.setText("INSTALL");
                                detailProgressBar.setVisibility(View.GONE);
                            });
                        }
                    }).start();
                };
            
            detailVersionSpinner.setOnItemSelectedListener(new android.widget.AdapterView.OnItemSelectedListener() {
                @Override
                public void onItemSelected(android.widget.AdapterView<?> parent, View view, int position, long id) {
                    String selected = versionLabels.get(position);
                    if (installedVersion != null) {
                        if (selected.equals(installedVersion)) {
                            detailInstallBtn.setText("OPEN");
                            detailInstallBtn.setOnClickListener(v -> {
                                if (pkgName.equals(getPackageName())) {
                                    Toast.makeText(AppDetailActivity.this, "You are already using this app!", Toast.LENGTH_SHORT).show();
                                    finish();
                                    return;
                                }
                                Intent launchIntent = getPackageManager().getLaunchIntentForPackage(pkgName);
                                if (launchIntent != null) startActivity(launchIntent);
                                else Toast.makeText(AppDetailActivity.this, "App cannot be opened.", Toast.LENGTH_SHORT).show();
                            });
                        } else {
                            int cmp = compareVersions(selected, installedVersion);
                            detailInstallBtn.setText(cmp > 0 ? "UPDATE" : "DOWNGRADE");
                            detailInstallBtn.setOnClickListener(installAction);
                        }
                    } else {
                        detailInstallBtn.setText("INSTALL");
                        detailInstallBtn.setOnClickListener(installAction);
                    }
                }
                @Override
                public void onNothingSelected(android.widget.AdapterView<?> parent) {}
            });
            
        } catch (Exception e) {
            e.printStackTrace();
            Toast.makeText(this, "Failed to load app details", Toast.LENGTH_SHORT).show();
            finish();
        }
    }
    
    private int compareVersions(String v1, String v2) {
        if (v1 == null) v1 = "";
        if (v2 == null) v2 = "";
        String[] parts1 = v1.replace("v", "").split("\\.");
        String[] parts2 = v2.replace("v", "").split("\\.");
        int length = Math.max(parts1.length, parts2.length);
        for (int i = 0; i < length; i++) {
            int p1 = i < parts1.length && !parts1[i].isEmpty() ? Integer.parseInt(parts1[i].replaceAll("[^0-9]", "0")) : 0;
            int p2 = i < parts2.length && !parts2[i].isEmpty() ? Integer.parseInt(parts2[i].replaceAll("[^0-9]", "0")) : 0;
            if (p1 < p2) return -1;
            if (p1 > p2) return 1;
        }
        return 0;
    }

    private static java.util.HashMap<String, android.graphics.Bitmap> imageCache = new java.util.HashMap<>();
    
    public static void clearImageCache() {
        if (imageCache != null) {
            imageCache.clear();
        }
    }
    
    private void loadImageAsync(String urlStr, ImageView imageView) {
        if (imageCache.containsKey(urlStr)) {
            imageView.setImageBitmap(imageCache.get(urlStr));
            return;
        }
        imageView.setTag(urlStr);
        new Thread(() -> {
            try {
                java.net.URL url = new java.net.URL(urlStr);
                android.graphics.Bitmap bmp = android.graphics.BitmapFactory.decodeStream(url.openConnection().getInputStream());
                if (bmp != null) imageCache.put(urlStr, bmp);
                runOnUiThread(() -> {
                    if (urlStr.equals(imageView.getTag())) {
                        imageView.setImageBitmap(bmp);
                    }
                });
            } catch(Exception e) {}
        }).start();
    }
}

