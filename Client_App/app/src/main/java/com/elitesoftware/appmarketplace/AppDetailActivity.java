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
        super.onCreate(savedInstanceState);
        if (getSupportActionBar() != null) getSupportActionBar().hide();
        setContentView(R.layout.activity_app_detail);
        
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
                            String apkUrl = "http://" + ip + ":8552/apks/" + app.getJSONArray("versions").getJSONObject(0).getString("file");
                            URL url = new URL(apkUrl);
                            HttpURLConnection conn = (HttpURLConnection) url.openConnection();
                            conn.connect();
                            int fileLength = conn.getContentLength();
                            
                            InputStream input = new BufferedInputStream(url.openStream(), 8192);
                            File apkFile = new File(getExternalFilesDir(null), app.optString("package_name") + ".apk");
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
                            try {
                                if (Shizuku.pingBinder()) {
                                    Process p = Shizuku.newProcess(new String[]{"pm", "install", "-r", apkFile.getAbsolutePath()}, null, null);
                                    p.waitFor();
                                    installed_ok = true;
                                }
                            } catch (Exception e) {}
                            
                            if (!installed_ok) {
                                Process p = Runtime.getRuntime().exec(new String[]{"sh", "-c", "dhizuku -c 'pm install -r " + apkFile.getAbsolutePath() + "' || su -c 'pm install -r " + apkFile.getAbsolutePath() + "' || shizuku -c 'pm install -r " + apkFile.getAbsolutePath() + "'"});
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
