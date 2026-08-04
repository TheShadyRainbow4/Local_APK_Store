package com.elitesoftware.appmarketplace;

import android.app.Activity;
import android.os.Bundle;
import android.widget.Button;
import android.widget.ImageButton;
import android.widget.TextView;
import android.widget.Toast;
import org.json.JSONObject;

public class AppDetailActivity extends Activity {
    private int getAppInstallState(android.content.Context context, String packageName, String serverVersion) {
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
    }

    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        if (getActionBar() != null) getActionBar().hide();
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
            
            detailName.setText(app.optString("name", "Unknown"));
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

            android.widget.ProgressBar pbDetailDownload = findViewById(R.id.pbDetailDownload);
            detailInstallBtn.setOnClickListener(v -> {
                if (state == 2) {
                    android.content.Intent launchIntent = getPackageManager().getLaunchIntentForPackage(packageName);
                    if (launchIntent != null) {
                        startActivity(launchIntent);
                    } else {
                        Toast.makeText(this, "Cannot launch app", Toast.LENGTH_SHORT).show();
                    }
                } else {
                    detailInstallBtn.setEnabled(false);
                    detailInstallBtn.setText("DOWNLOADING...");
                    pbDetailDownload.setVisibility(android.view.View.VISIBLE);
                    pbDetailDownload.setProgress(0);
                    
                    new Thread(() -> {
                        for(int i=1; i<=10; i++) {
                            try { Thread.sleep(300); } catch(Exception e) {}
                            final int p = i * 10;
                            runOnUiThread(() -> pbDetailDownload.setProgress(p));
                        }
                        runOnUiThread(() -> {
                            detailInstallBtn.setText("INSTALLING...");
                            Toast.makeText(this, "Requesting Shizuku/Dhizuku Install...", Toast.LENGTH_LONG).show();
                            pbDetailDownload.setVisibility(android.view.View.GONE);
                            detailInstallBtn.setEnabled(true);
                            detailInstallBtn.setText("OPEN");
                            detailInstallBtn.setBackgroundColor(android.graphics.Color.parseColor("#444444"));
                            detailInstallBtn.setTextColor(android.graphics.Color.parseColor("#FFFFFF"));
                        });
                    }).start();
                }
            });
            
        } catch(Exception e) {
            e.printStackTrace();
            Toast.makeText(this, "Error loading details", Toast.LENGTH_SHORT).show();
            finish();
        }
    }
}
