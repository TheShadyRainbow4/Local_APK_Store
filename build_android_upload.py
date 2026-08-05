import os

client_dir = r"C:\Users\Administrator\Desktop\Local_APK_Store\Client_App\app\src\main"
java_dir = os.path.join(client_dir, r"java\com\elitesoftware\appmarketplace")
res_dir = os.path.join(client_dir, "res")

# 1. Create activity_upload.xml
activity_upload_xml = """<?xml version="1.0" encoding="utf-8"?>
<ScrollView xmlns:android="http://schemas.android.com/apk/res/android"
    android:layout_width="match_parent"
    android:layout_height="match_parent"
    android:padding="16dp">

    <LinearLayout
        android:layout_width="match_parent"
        android:layout_height="wrap_content"
        android:orientation="vertical">

        <TextView
            android:layout_width="wrap_content"
            android:layout_height="wrap_content"
            android:text="Upload App / Update Listing"
            android:textSize="20sp"
            android:textStyle="bold"
            android:layout_marginBottom="16dp"/>

        <EditText
            android:id="@+id/editPackage"
            android:layout_width="match_parent"
            android:layout_height="wrap_content"
            android:hint="Package Name (Required)" />

        <EditText
            android:id="@+id/editName"
            android:layout_width="match_parent"
            android:layout_height="wrap_content"
            android:hint="App Name" />

        <EditText
            android:id="@+id/editVersion"
            android:layout_width="match_parent"
            android:layout_height="wrap_content"
            android:hint="Version (e.g. 1.0.0)" />

        <EditText
            android:id="@+id/editCategory"
            android:layout_width="match_parent"
            android:layout_height="wrap_content"
            android:hint="Category" />

        <EditText
            android:id="@+id/editDescription"
            android:layout_width="match_parent"
            android:layout_height="wrap_content"
            android:hint="Description"
            android:lines="4"
            android:gravity="top"/>

        <Button
            android:id="@+id/btnSelectApk"
            android:layout_width="match_parent"
            android:layout_height="wrap_content"
            android:text="Select APK File"
            android:layout_marginTop="8dp"/>

        <TextView
            android:id="@+id/txtApkStatus"
            android:layout_width="match_parent"
            android:layout_height="wrap_content"
            android:text="No APK selected"
            android:layout_marginBottom="8dp"/>

        <Button
            android:id="@+id/btnSelectScreenshots"
            android:layout_width="match_parent"
            android:layout_height="wrap_content"
            android:text="Select Screenshots" />

        <TextView
            android:id="@+id/txtScreenshotsStatus"
            android:layout_width="match_parent"
            android:layout_height="wrap_content"
            android:text="0 screenshots selected"
            android:layout_marginBottom="16dp"/>

        <Button
            android:id="@+id/btnUpload"
            android:layout_width="match_parent"
            android:layout_height="wrap_content"
            android:text="Upload to Store"
            android:backgroundTint="#A4C639"
            android:textColor="#FFFFFF"/>

    </LinearLayout>
</ScrollView>
"""
with open(os.path.join(res_dir, "layout", "activity_upload.xml"), "w", encoding="utf-8") as f:
    f.write(activity_upload_xml)

# 2. Create UploadActivity.java
upload_activity_java = """package com.elitesoftware.appmarketplace;

import android.app.Activity;
import android.content.Intent;
import android.database.Cursor;
import android.net.Uri;
import android.os.Bundle;
import android.provider.OpenableColumns;
import android.view.View;
import android.widget.Button;
import android.widget.EditText;
import android.widget.TextView;
import android.widget.Toast;

import androidx.annotation.Nullable;
import androidx.appcompat.app.AppCompatActivity;

import org.json.JSONArray;
import org.json.JSONObject;

import java.io.InputStream;
import java.io.OutputStream;
import java.net.HttpURLConnection;
import java.net.URL;
import java.util.ArrayList;
import java.util.List;

public class UploadActivity extends AppCompatActivity {

    private static final int PICK_APK_REQUEST = 1;
    private static final int PICK_SCREENSHOTS_REQUEST = 2;

    private EditText editPackage, editName, editVersion, editCategory, editDescription;
    private TextView txtApkStatus, txtScreenshotsStatus;

    private Uri apkUri = null;
    private List<Uri> screenshotUris = new ArrayList<>();

    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        setContentView(R.layout.activity_upload);

        editPackage = findViewById(R.id.editPackage);
        editName = findViewById(R.id.editName);
        editVersion = findViewById(R.id.editVersion);
        editCategory = findViewById(R.id.editCategory);
        editDescription = findViewById(R.id.editDescription);

        txtApkStatus = findViewById(R.id.txtApkStatus);
        txtScreenshotsStatus = findViewById(R.id.txtScreenshotsStatus);

        findViewById(R.id.btnSelectApk).setOnClickListener(v -> {
            Intent intent = new Intent(Intent.ACTION_GET_CONTENT);
            intent.setType("application/vnd.android.package-archive");
            startActivityForResult(intent, PICK_APK_REQUEST);
        });

        findViewById(R.id.btnSelectScreenshots).setOnClickListener(v -> {
            Intent intent = new Intent(Intent.ACTION_GET_CONTENT);
            intent.setType("image/*");
            intent.putExtra(Intent.EXTRA_ALLOW_MULTIPLE, true);
            startActivityForResult(intent, PICK_SCREENSHOTS_REQUEST);
        });

        findViewById(R.id.btnUpload).setOnClickListener(v -> uploadData());
    }

    @Override
    protected void onActivityResult(int requestCode, int resultCode, @Nullable Intent data) {
        super.onActivityResult(requestCode, resultCode, data);
        if (resultCode == Activity.RESULT_OK && data != null) {
            if (requestCode == PICK_APK_REQUEST) {
                apkUri = data.getData();
                txtApkStatus.setText("APK Selected: " + getFileName(apkUri));
            } else if (requestCode == PICK_SCREENSHOTS_REQUEST) {
                screenshotUris.clear();
                if (data.getClipData() != null) {
                    int count = data.getClipData().getItemCount();
                    for (int i = 0; i < count; i++) {
                        screenshotUris.add(data.getClipData().getItemAt(i).getUri());
                    }
                } else if (data.getData() != null) {
                    screenshotUris.add(data.getData());
                }
                txtScreenshotsStatus.setText(screenshotUris.size() + " screenshots selected");
            }
        }
    }

    private String getFileName(Uri uri) {
        String result = null;
        if (uri.getScheme().equals("content")) {
            Cursor cursor = getContentResolver().query(uri, null, null, null, null);
            try {
                if (cursor != null && cursor.moveToFirst()) {
                    result = cursor.getString(cursor.getColumnIndex(OpenableColumns.DISPLAY_NAME));
                }
            } finally {
                if (cursor != null) cursor.close();
            }
        }
        if (result == null) {
            result = uri.getPath();
            int cut = result.lastIndexOf('/');
            if (cut != -1) {
                result = result.substring(cut + 1);
            }
        }
        return result;
    }

    private void uploadData() {
        String pkg = editPackage.getText().toString();
        if (pkg.isEmpty()) {
            Toast.setMessage("Package name is required");
            return;
        }

        String serverIp = getSharedPreferences("StorePrefs", MODE_PRIVATE).getString("server_ip", "");
        if (serverIp.isEmpty()) {
            Toast.makeText(this, "Server IP not set!", Toast.LENGTH_SHORT).show();
            return;
        }

        new Thread(() -> {
            try {
                String baseUrl = "http://" + serverIp + ":41530";
                
                String apkFileName = null;
                if (apkUri != null) {
                    apkFileName = getFileName(apkUri);
                    uploadFile(apkUri, baseUrl + "/api/upload_apk", apkFileName);
                }

                List<String> screenshotNames = new ArrayList<>();
                for (Uri uri : screenshotUris) {
                    String sName = getFileName(uri);
                    screenshotNames.add(sName);
                    uploadFile(uri, baseUrl + "/api/upload_image", sName);
                }

                JSONObject appJson = new JSONObject();
                appJson.put("package_name", pkg);
                if (!editName.getText().toString().isEmpty()) appJson.put("name", editName.getText().toString());
                if (!editCategory.getText().toString().isEmpty()) appJson.put("category", editCategory.getText().toString());
                if (!editDescription.getText().toString().isEmpty()) appJson.put("description", editDescription.getText().toString());
                
                if (!screenshotNames.isEmpty()) {
                    JSONArray arr = new JSONArray();
                    for (String s : screenshotNames) arr.put(s);
                    appJson.put("screenshots", arr);
                }
                
                if (apkFileName != null) {
                    JSONArray versions = new JSONArray();
                    JSONObject v = new JSONObject();
                    v.put("file", apkFileName);
                    String ver = editVersion.getText().toString();
                    if (ver.isEmpty()) ver = "1.0.0";
                    v.put("version", ver);
                    versions.put(v);
                    appJson.put("versions", versions);
                }

                URL url = new URL(baseUrl + "/api/update_app");
                HttpURLConnection conn = (HttpURLConnection) url.openConnection();
                conn.setRequestMethod("POST");
                conn.setDoOutput(true);
                conn.setRequestProperty("Content-Type", "application/json");
                
                OutputStream os = conn.getOutputStream();
                os.write(appJson.toString().getBytes());
                os.flush();
                os.close();

                int code = conn.getResponseCode();
                runOnUiThread(() -> {
                    if (code == 200) {
                        Toast.makeText(UploadActivity.this, "Upload successful!", Toast.LENGTH_SHORT).show();
                        finish();
                    } else {
                        Toast.makeText(UploadActivity.this, "Upload failed: " + code, Toast.LENGTH_SHORT).show();
                    }
                });
            } catch (Exception e) {
                e.printStackTrace();
                runOnUiThread(() -> Toast.makeText(UploadActivity.this, "Error: " + e.getMessage(), Toast.LENGTH_LONG).show());
            }
        }).start();
    }

    private void uploadFile(Uri uri, String urlString, String filename) throws Exception {
        URL url = new URL(urlString);
        HttpURLConnection conn = (HttpURLConnection) url.openConnection();
        conn.setRequestMethod("POST");
        conn.setDoOutput(true);
        conn.setRequestProperty("X-File-Name", filename);
        
        InputStream is = getContentResolver().openInputStream(uri);
        OutputStream os = conn.getOutputStream();
        byte[] buffer = new byte[8192];
        int bytesRead;
        while ((bytesRead = is.read(buffer)) != -1) {
            os.write(buffer, 0, bytesRead);
        }
        os.flush();
        os.close();
        is.close();
        
        if (conn.getResponseCode() != 200) {
            throw new Exception("File upload failed with code " + conn.getResponseCode());
        }
    }
}
"""
with open(os.path.join(java_dir, "UploadActivity.java"), "w", encoding="utf-8") as f:
    f.write(upload_activity_java)

# 3. Add to AndroidManifest.xml
manifest_path = os.path.join(client_dir, "AndroidManifest.xml")
with open(manifest_path, "r", encoding="utf-8") as f:
    manifest_content = f.read()

if "<activity android:name=\".UploadActivity\"" not in manifest_content:
    manifest_content = manifest_content.replace("</application>", "    <activity android:name=\".UploadActivity\" />\n    </application>")
    with open(manifest_path, "w", encoding="utf-8") as f:
        f.write(manifest_content)

# 4. Add Upload Button to activity_main.xml
activity_main_xml_path = os.path.join(res_dir, "layout", "activity_main.xml")
with open(activity_main_xml_path, "r", encoding="utf-8") as f:
    main_xml = f.read()

if "btnUpload" not in main_xml:
    new_btn = """        <ImageButton
            android:id="@+id/btnUpload"
            android:layout_width="48dp"
            android:layout_height="48dp"
            android:background="?android:attr/selectableItemBackground"
            android:src="@android:drawable/ic_menu_upload"
            android:contentDescription="Upload"
            android:scaleType="fitCenter"
            android:padding="10dp"/>
"""
    main_xml = main_xml.replace('</LinearLayout>\n\n    <LinearLayout\n        android:layout_width="match_parent"\n        android:layout_height="40dp"', new_btn + '</LinearLayout>\n\n    <LinearLayout\n        android:layout_width="match_parent"\n        android:layout_height="40dp"')
    with open(activity_main_xml_path, "w", encoding="utf-8") as f:
        f.write(main_xml)

# 5. Wire up the button in MainActivity.java
main_activity_java_path = os.path.join(java_dir, "MainActivity.java")
with open(main_activity_java_path, "r", encoding="utf-8") as f:
    main_java = f.read()

if "btnUpload" not in main_java:
    setup_code = """
        findViewById(R.id.btnUpload).setOnClickListener(v -> {
            startActivity(new Intent(this, UploadActivity.class));
        });
"""
    # Find btnSettings setup and insert after it
    idx = main_java.find("findViewById(R.id.btnSettings).setOnClickListener")
    if idx != -1:
        end_idx = main_java.find("});", idx) + 3
        main_java = main_java[:end_idx] + setup_code + main_java[end_idx:]
        with open(main_activity_java_path, "w", encoding="utf-8") as f:
            f.write(main_java)

print("Android Upload logic generated successfully!")
