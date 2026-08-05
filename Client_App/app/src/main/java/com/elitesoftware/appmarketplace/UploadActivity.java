package com.elitesoftware.appmarketplace;

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
            Toast.makeText(this, "Package name is required", Toast.LENGTH_SHORT).show();
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
