import os

base_dir = r"C:\Users\Administrator\Desktop\Local_APK_Store\Client_App\app\src\main\res\layout"

# 1. Update list_item_app.xml
path = os.path.join(base_dir, "list_item_app.xml")
with open(path, "r") as f:
    xml = f.read()

prog = '''
    <ProgressBar
        android:id="@+id/pbDownload"
        style="?android:attr/progressBarStyleHorizontal"
        android:layout_width="match_parent"
        android:layout_height="wrap_content"
        android:layout_below="@id/tvAppDesc"
        android:layout_marginTop="8dp"
        android:max="100"
        android:visibility="gone" />
</RelativeLayout>'''
xml = xml.replace('</RelativeLayout>', prog)
with open(path, "w") as f:
    f.write(xml)


# 2. Update activity_app_detail.xml
path = os.path.join(base_dir, "activity_app_detail.xml")
with open(path, "r") as f:
    xml = f.read()

prog2 = '''
            <ProgressBar
                android:id="@+id/pbDetailDownload"
                style="?android:attr/progressBarStyleHorizontal"
                android:layout_width="match_parent"
                android:layout_height="wrap_content"
                android:layout_marginTop="8dp"
                android:max="100"
                android:visibility="gone" />

            <View'''
xml = xml.replace('<View', prog2, 1)
with open(path, "w") as f:
    f.write(xml)


# 3. Update MainActivity.java logic
path = r"C:\Users\Administrator\Desktop\Local_APK_Store\Client_App\app\src\main\java\com\elitesoftware\appmarketplace\MainActivity.java"
with open(path, "r") as f:
    code = f.read()

logic = '''            ProgressBar pbDownload = convertView.findViewById(R.id.pbDownload);
            
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
                    btnInstall.setEnabled(false);
                    btnInstall.setText("DOWNLOADING...");
                    pbDownload.setVisibility(View.VISIBLE);
                    pbDownload.setProgress(0);
                    
                    // Mock progress for now
                    new Thread(() -> {
                        for(int i=1; i<=10; i++) {
                            try { Thread.sleep(300); } catch(Exception e) {}
                            final int p = i * 10;
                            runOnUiThread(() -> pbDownload.setProgress(p));
                        }
                        runOnUiThread(() -> {
                            btnInstall.setText("INSTALLING...");
                            Toast.makeText(MainActivity.this, "Requesting Shizuku/Dhizuku Install...", Toast.LENGTH_LONG).show();
                            pbDownload.setVisibility(View.GONE);
                            btnInstall.setEnabled(true);
                            btnInstall.setText("OPEN");
                            btnInstall.setBackgroundColor(android.graphics.Color.parseColor("#444444"));
                            btnInstall.setTextColor(android.graphics.Color.parseColor("#FFFFFF"));
                        });
                    }).start();
                }
            });'''

code = code.replace('''            btnInstall.setOnClickListener(v -> {
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
            });''', logic)
with open(path, "w") as f:
    f.write(code)


# 4. Update AppDetailActivity.java logic
path = r"C:\Users\Administrator\Desktop\Local_APK_Store\Client_App\app\src\main\java\com\elitesoftware\appmarketplace\AppDetailActivity.java"
with open(path, "r") as f:
    code = f.read()

logic2 = '''            android.widget.ProgressBar pbDetailDownload = findViewById(R.id.pbDetailDownload);
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
            });'''
            
code = code.replace('''            detailInstallBtn.setOnClickListener(v -> {
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
            });''', logic2)
with open(path, "w") as f:
    f.write(code)

