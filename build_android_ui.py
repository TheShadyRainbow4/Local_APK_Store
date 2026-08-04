import os
import json

base_dir = r"C:\Users\Administrator\Desktop\Local_APK_Store\Client_App\app\src\main"
layout_dir = os.path.join(base_dir, "res", "layout")
java_dir = os.path.join(base_dir, "java", "com", "elitesoftware", "appmarketplace")

# 1. Update activity_main.xml (make it Holo Light themed properly)
activity_main_xml = '''<?xml version="1.0" encoding="utf-8"?>
<LinearLayout xmlns:android="http://schemas.android.com/apk/res/android"
    android:layout_width="match_parent"
    android:layout_height="match_parent"
    android:orientation="vertical"
    android:background="#EBEBEB">

    <!-- Top Action Bar (ICS/Jelly Bean Play Store style) -->
    <LinearLayout
        android:layout_width="match_parent"
        android:layout_height="?android:attr/actionBarSize"
        android:background="#F3F3F3"
        android:orientation="horizontal"
        android:gravity="center_vertical"
        android:padding="8dp">

        <ImageView
            android:layout_width="48dp"
            android:layout_height="48dp"
            android:src="@mipmap/ic_launcher"
            android:padding="4dp"/>

        <TextView
            android:layout_width="0dp"
            android:layout_height="wrap_content"
            android:layout_weight="1"
            android:layout_marginStart="12dp"
            android:text="Market"
            android:textColor="#33B5E5"
            android:textSize="22sp"
            android:textStyle="bold" />

        <ImageButton
            android:id="@+id/btnSettings"
            android:layout_width="48dp"
            android:layout_height="48dp"
            android:background="?android:attr/selectableItemBackground"
            android:src="@drawable/settings"
            android:scaleType="centerInside" />
    </LinearLayout>
    
    <View android:layout_width="match_parent" android:layout_height="2dp" android:background="#33B5E5" />

    <ListView
        android:id="@+id/lvApps"
        android:layout_width="match_parent"
        android:layout_height="match_parent"
        android:divider="#D9D9D9"
        android:dividerHeight="1dp"
        android:padding="8dp"
        android:clipToPadding="false" />
</LinearLayout>
'''
with open(os.path.join(layout_dir, "activity_main.xml"), "w") as f:
    f.write(activity_main_xml)


# 2. list_item_app.xml
list_item_app_xml = '''<?xml version="1.0" encoding="utf-8"?>
<RelativeLayout xmlns:android="http://schemas.android.com/apk/res/android"
    android:layout_width="match_parent"
    android:layout_height="wrap_content"
    android:padding="12dp"
    android:background="@android:color/white"
    android:layout_marginBottom="8dp"
    android:elevation="2dp">

    <ImageView
        android:id="@+id/ivAppIcon"
        android:layout_width="64dp"
        android:layout_height="64dp"
        android:src="@mipmap/ic_launcher"
        android:layout_marginEnd="12dp"
        android:layout_alignParentStart="true"
        android:layout_centerVertical="true" />

    <TextView
        android:id="@+id/tvAppName"
        android:layout_width="wrap_content"
        android:layout_height="wrap_content"
        android:layout_toEndOf="@id/ivAppIcon"
        android:layout_toStartOf="@+id/btnInstall"
        android:text="App Name"
        android:textColor="#333333"
        android:textSize="16sp"
        android:textStyle="bold"
        android:singleLine="true"
        android:ellipsize="end"/>

    <TextView
        android:id="@+id/tvAppDesc"
        android:layout_width="wrap_content"
        android:layout_height="wrap_content"
        android:layout_below="@id/tvAppName"
        android:layout_toEndOf="@id/ivAppIcon"
        android:layout_toStartOf="@+id/btnInstall"
        android:text="Description goes here and spans across two lines potentially."
        android:textColor="#666666"
        android:textSize="14sp"
        android:maxLines="2"
        android:ellipsize="end"
        android:layout_marginTop="4dp" />

    <Button
        android:id="@+id/btnInstall"
        android:layout_width="wrap_content"
        android:layout_height="wrap_content"
        android:layout_alignParentEnd="true"
        android:layout_centerVertical="true"
        android:text="INSTALL"
        android:textColor="#FFFFFF"
        android:background="#A4C639"
        android:paddingStart="12dp"
        android:paddingEnd="12dp"
        android:minHeight="36dp"
        android:textSize="12sp"
        android:textStyle="bold" />

</RelativeLayout>
'''
with open(os.path.join(layout_dir, "list_item_app.xml"), "w") as f:
    f.write(list_item_app_xml)


# 3. activity_app_detail.xml
activity_app_detail_xml = '''<?xml version="1.0" encoding="utf-8"?>
<LinearLayout xmlns:android="http://schemas.android.com/apk/res/android"
    android:layout_width="match_parent"
    android:layout_height="match_parent"
    android:orientation="vertical"
    android:background="#EBEBEB">

    <LinearLayout
        android:layout_width="match_parent"
        android:layout_height="?android:attr/actionBarSize"
        android:background="#F3F3F3"
        android:orientation="horizontal"
        android:gravity="center_vertical"
        android:padding="8dp">

        <ImageButton
            android:id="@+id/btnBack"
            android:layout_width="48dp"
            android:layout_height="48dp"
            android:background="?android:attr/selectableItemBackground"
            android:src="@android:drawable/ic_menu_revert"
            android:scaleType="centerInside" />

        <TextView
            android:layout_width="wrap_content"
            android:layout_height="wrap_content"
            android:layout_marginStart="8dp"
            android:text="App Details"
            android:textColor="#33B5E5"
            android:textSize="20sp"
            android:textStyle="bold" />
    </LinearLayout>
    
    <View android:layout_width="match_parent" android:layout_height="2dp" android:background="#33B5E5" />

    <ScrollView
        android:layout_width="match_parent"
        android:layout_height="match_parent"
        android:padding="16dp">
        
        <LinearLayout
            android:layout_width="match_parent"
            android:layout_height="wrap_content"
            android:orientation="vertical"
            android:background="@android:color/white"
            android:padding="16dp"
            android:elevation="2dp">

            <LinearLayout
                android:layout_width="match_parent"
                android:layout_height="wrap_content"
                android:orientation="horizontal"
                android:gravity="center_vertical">
                
                <ImageView
                    android:id="@+id/detailIcon"
                    android:layout_width="80dp"
                    android:layout_height="80dp"
                    android:src="@mipmap/ic_launcher" />
                    
                <LinearLayout
                    android:layout_width="match_parent"
                    android:layout_height="wrap_content"
                    android:orientation="vertical"
                    android:layout_marginStart="16dp">
                    
                    <TextView
                        android:id="@+id/detailName"
                        android:layout_width="wrap_content"
                        android:layout_height="wrap_content"
                        android:text="App Name"
                        android:textColor="#333333"
                        android:textSize="22sp"
                        android:textStyle="bold" />
                        
                    <TextView
                        android:id="@+id/detailPackage"
                        android:layout_width="wrap_content"
                        android:layout_height="wrap_content"
                        android:text="com.example.app"
                        android:textColor="#888888"
                        android:textSize="14sp"
                        android:layout_marginTop="2dp" />

                    <TextView
                        android:id="@+id/detailCategory"
                        android:layout_width="wrap_content"
                        android:layout_height="wrap_content"
                        android:text="Category"
                        android:textColor="#33B5E5"
                        android:textSize="14sp"
                        android:layout_marginTop="4dp" />
                </LinearLayout>
            </LinearLayout>

            <Button
                android:id="@+id/detailInstallBtn"
                android:layout_width="match_parent"
                android:layout_height="48dp"
                android:layout_marginTop="24dp"
                android:text="INSTALL"
                android:textColor="#FFFFFF"
                android:background="#A4C639"
                android:textSize="16sp"
                android:textStyle="bold" />

            <ProgressBar
                android:id="@+id/detailProgressBar"
                style="?android:attr/progressBarStyleHorizontal"
                android:layout_width="match_parent"
                android:layout_height="wrap_content"
                android:layout_marginTop="8dp"
                android:visibility="gone"
                android:max="100" />

            <View
                android:layout_width="match_parent"
                android:layout_height="1dp"
                android:background="#E0E0E0"
                android:layout_marginTop="24dp"
                android:layout_marginBottom="16dp" />

            <TextView
                android:layout_width="wrap_content"
                android:layout_height="wrap_content"
                android:text="Description"
                android:textColor="#333333"
                android:textSize="16sp"
                android:textStyle="bold" />

            <TextView
                android:id="@+id/detailDesc"
                android:layout_width="match_parent"
                android:layout_height="wrap_content"
                android:text="Full app description goes here."
                android:textColor="#666666"
                android:textSize="15sp"
                android:layout_marginTop="8dp"
                android:lineSpacingExtra="4dp" />
                
        </LinearLayout>
    </ScrollView>
</LinearLayout>
'''
with open(os.path.join(layout_dir, "activity_app_detail.xml"), "w") as f:
    f.write(activity_app_detail_xml)


# 4. AppDetailActivity.java
app_detail_java = '''package com.elitesoftware.appmarketplace;

import android.app.Activity;
import android.content.Intent;
import android.os.Bundle;
import android.view.View;
import android.widget.Button;
import android.widget.ImageButton;
import android.widget.ProgressBar;
import android.widget.TextView;
import android.widget.Toast;
import org.json.JSONObject;
import java.io.BufferedInputStream;
import java.io.File;
import java.io.FileOutputStream;
import java.io.InputStream;
import java.io.OutputStream;
import java.net.HttpURLConnection;
import java.net.URL;

public class AppDetailActivity extends Activity {
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
            ProgressBar detailProgressBar = findViewById(R.id.detailProgressBar);
            
            detailName.setText(app.optString("name", "Unknown"));
            detailPackage.setText(app.optString("package_name", ""));
            detailCategory.setText(app.optString("category", "Uncategorized"));
            detailDesc.setText(app.optString("description", "No description available."));
            
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
                            
                            // Install via Shizuku / root
                            Process p = Runtime.getRuntime().exec(new String[]{"sh", "-c", "shizuku -c 'pm install -r " + apkFile.getAbsolutePath() + "' || su -c 'pm install -r " + apkFile.getAbsolutePath() + "' || dhizuku -c 'pm install -r " + apkFile.getAbsolutePath() + "'"});
                            p.waitFor();
                            
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
}
'''
with open(os.path.join(java_dir, "AppDetailActivity.java"), "w") as f:
    f.write(app_detail_java)

# 5. Add AppDetailActivity to AndroidManifest.xml
manifest_path = os.path.join(base_dir, "AndroidManifest.xml")
with open(manifest_path, "r") as f:
    manifest = f.read()

if "AppDetailActivity" not in manifest:
    manifest = manifest.replace("</application>", '''
        <activity
            android:name=".AppDetailActivity"
            android:exported="false"
            android:label="App Details" />
    </application>''')
    with open(manifest_path, "w") as f:
        f.write(manifest)

