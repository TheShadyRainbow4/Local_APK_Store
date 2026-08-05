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
        }

        if (getSupportActionBar() != null) getSupportActionBar().hide();
        
        ImageButton btnBack = findViewById(R.id.btnBack);
        btnBack.setOnClickListener(v -> finish());
        
        try {
            String appJsonStr = getIntent().getStringExtra("app_json");
            String ip = getIntent().getStringExtra("server_ip");
            JSONObject app = new JSONObject(appJsonStr);
            
            TextView detailName = findViewById(R.id.detailName);
            TextView detailPackage = findViewById(R.id.detailPackage);
            TextView detailCategory = findViewById(R.id.detailCategory);
            TextView detailDesc = findViewById(R.id.detailDesc);
            Button detailInstallBtn = findViewById(R.id.detailInstallBtn);
            ProgressBar detailProgressBar = findViewById(R.id.detailProgressBar);
            ImageView detailIcon = findViewById(R.id.detailIcon);
            
            detailName.setText(app.optString("name", "Unknown"));
            detailPackage.setText(app.optString("package_name", ""));
            detailCategory.setText(app.optString("category", "Uncategorized"));
            detailDesc.setText(app.optString("description", "No description available."));
            detailIcon.setImageResource(R.mipmap.ic_launcher);
            
            android.widget.Spinner detailVersionSpinner = findViewById(R.id.detailVersionSpinner);
            java.util.List<String> versionLabels = new java.util.ArrayList<>();
            org.json.JSONArray versionsArr = app.getJSONArray("versions");
            for (int i = 0; i < versionsArr.length(); i++) {
                versionLabels.add(versionsArr.getJSONObject(i).getString("version"));
            }
            android.widget.ArrayAdapter<String> adapter = new android.widget.ArrayAdapter<>(this, android.R.layout.simple_spinner_dropdown_item, versionLabels);
            detailVersionSpinner.setAdapter(adapter);
            
            if (app.has("icon") && !app.optString("icon").isEmpty()) {
                String iconUrl = "http://" + ip + ":8552/images/" + app.optString("icon");
                loadImageAsync(iconUrl, detailIcon);
            }
            
            boolean installed = false;
            try {
                getPackageManager().getPackageInfo(app.optString("package_name"), 0);
                installed = true;
            } catch (Exception e) {}

            if (installed) {
                detailInstallBtn.setText("OPEN");
                detailInstallBtn.setOnClickListener(v -> {
                    Intent launchIntent = getPackageManager().getLaunchIntentForPackage(app.optString("package_name"));
                    if (launchIntent != null) startActivity(launchIntent);
                });
            } else {
                detailInstallBtn.setText("INSTALL");
                detailInstallBtn.setOnClickListener(v -> {
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
                            
                            org.json.JSONObject verObj = versionsArr.getJSONObject(selectedIdx);
                            String apkUrl = "http://" + ip + ":8552/apks/" + verObj.getString("file");
                            selectedVer = verObj.getString("version");
                            
                            URL url = new URL(apkUrl);
                            HttpURLConnection conn = (HttpURLConnection) url.openConnection();
                            conn.connect();
                            int fileLength = conn.getContentLength();
                            
                            InputStream input = new BufferedInputStream(url.openStream(), 8192);
                            String safeName = app.optString("name").replaceAll(" ", "_");
                            File apkFile = new File(android.os.Environment.getExternalStoragePublicDirectory(android.os.Environment.DIRECTORY_DOWNLOADS), safeName + "_v" + selectedVer + ".apk");
                            OutputStream output = new FileOutputStream(apkFile);
                            
                            byte data[] = new byte[1024];
                            long total = 0;
                            int count;
                            while ((count = input.read(data)) != -1) {
                                total += count;
                                int progress = (int) (total * 100 / fileLength);
                                runOnUiThread(() -> detailProgressBar.setProgress(progress));
                                output.write(data, 0, count);
                            }
                            output.flush();
                            output.close();
                            input.close();
                            
                            runOnUiThread(() -> {
                                detailProgressBar.setVisibility(View.GONE);
                                detailInstallBtn.setText("INSTALLING...");
                            });
                            
                            // Install via Shizuku API / fallback to sh
                            boolean installed_ok = false;
                            
                            String packageName = app.optString("package_name");
                            boolean isSelfUpdate = packageName.equals(getPackageName());
                            String installCmd = "pm install -r '" + apkFile.getAbsolutePath() + "'";
                            if (isSelfUpdate) {
                                installCmd += " && am start -n " + getPackageName() + "/.MainActivity";
                            }
                            
                            try {
                                if (Shizuku.pingBinder()) {
                                    Process p = Shizuku.newProcess(new String[]{"sh", "-c", installCmd}, null, null);
                                    if (p.waitFor() == 0) {
                                        installed_ok = true;
                                    }
                                }
                            } catch (Exception e) {}
                            
                            if (!installed_ok) {
                                String streamInstallCmd = "dhizuku -c 'pm install -S " + apkFile.length() + "' || su -c 'pm install -S " + apkFile.length() + "'";
                                // We cannot easily chain am start with stream install because standard input must be fed to the pm command.
                                // However, dhizuku or su runs sh -c.
                                Process p = Runtime.getRuntime().exec(new String[]{"sh", "-c", streamInstallCmd});
                                java.io.OutputStream out = p.getOutputStream();
                                java.io.FileInputStream in = new java.io.FileInputStream(apkFile);
                                byte[] buf = new byte[8192];
                                int len;
                                while ((len = in.read(buf)) > 0) out.write(buf, 0, len);
                                in.close();
                                out.flush();
                                out.close();
                                p.waitFor();
                            }
                            
                            runOnUiThread(() -> {
                                detailInstallBtn.setText("OPEN");
                                detailInstallBtn.setEnabled(true);
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
                });
            }
            
        } catch(Exception e) {
            e.printStackTrace();
            Toast.makeText(this, "Error loading details", Toast.LENGTH_SHORT).show();
            finish();
        }
    }
    
    private void loadImageAsync(String urlStr, ImageView imageView) {
        imageView.setTag(urlStr);
        new Thread(() -> {
            try {
                java.net.URL url = new java.net.URL(urlStr);
                android.graphics.Bitmap bmp = android.graphics.BitmapFactory.decodeStream(url.openConnection().getInputStream());
                runOnUiThread(() -> {
                    if (urlStr.equals(imageView.getTag())) {
                        imageView.setImageBitmap(bmp);
                    }
                });
            } catch(Exception e) {}
        }).start();
    }
}
