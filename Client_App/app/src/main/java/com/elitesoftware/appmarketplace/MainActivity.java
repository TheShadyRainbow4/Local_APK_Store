package com.elitesoftware.appmarketplace;

import android.app.AlertDialog;
import android.content.Context;
import android.content.Intent;
import android.net.wifi.WifiManager;
import android.os.Build;
import android.os.Bundle;
import android.provider.Settings;
import android.text.InputType;
import android.view.LayoutInflater;
import android.view.View;
import android.view.ViewGroup;
import android.widget.BaseAdapter;
import android.widget.Button;
import android.widget.EditText;
import android.widget.ImageButton;
import android.widget.ImageView;
import android.widget.ListView;
import android.widget.ProgressBar;
import android.widget.TextView;
import android.widget.Toast;
import androidx.appcompat.app.AppCompatActivity;
import rikka.shizuku.Shizuku;

import org.json.JSONArray;
import org.json.JSONObject;

import java.net.DatagramPacket;
import java.net.DatagramSocket;
import java.net.InetAddress;
import java.net.SocketTimeoutException;
import java.util.ArrayList;
import java.util.HashSet;
import java.util.concurrent.ExecutorService;
import java.util.concurrent.Executors;
import java.util.concurrent.ScheduledExecutorService;
import java.util.concurrent.ScheduledFuture;
import java.util.concurrent.TimeUnit;

public class MainActivity extends AppCompatActivity {

    private HashSet<String> serverIPs = new HashSet<>();
    private ArrayList<JSONObject> appsList = new ArrayList<>();
    private ArrayList<JSONObject> displayedAppsList = new ArrayList<>();
    private int currentTab = 0; // 0=APPS, 1=GAMES, 2=DOWNLOADS
    private String currentSearchQuery = "";
    private AppAdapter adapter;
    private ExecutorService executor = Executors.newFixedThreadPool(4);
    private ScheduledExecutorService heartbeatScheduler = Executors.newSingleThreadScheduledExecutor();
    private ScheduledFuture<?> heartbeatFuture;


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
        setContentView(R.layout.activity_main);
        
        if (theme.equals("amoled")) {
            getWindow().getDecorView().setBackgroundColor(android.graphics.Color.BLACK);
            android.view.View root = ((android.view.ViewGroup)findViewById(android.R.id.content)).getChildAt(0);
            if (root != null) root.setBackgroundColor(android.graphics.Color.BLACK);
            ListView lv = findViewById(R.id.lvApps);
            if (lv != null) lv.setBackgroundColor(android.graphics.Color.BLACK);
        }

        if (getSupportActionBar() != null) getSupportActionBar().hide();

        ImageButton btnSettings = findViewById(R.id.btnSettings);
        btnSettings.setOnClickListener(v -> showSettingsDialog());

        ImageButton btnUpload = findViewById(R.id.btnUpload);
        if (btnUpload != null) {
            btnUpload.setOnClickListener(v -> {
                String ip = "192.168.1.100"; // fallback
                if (!serverIPs.isEmpty()) {
                    ip = serverIPs.iterator().next();
                }
                Intent intent = new Intent(MainActivity.this, UploadActivity.class);
                intent.putExtra("server_ip", ip);
                startActivity(intent);
            });
        }

        ListView lvApps = findViewById(R.id.lvApps);
        adapter = new AppAdapter();
        lvApps.setAdapter(adapter);

        lvApps.setOnItemClickListener((parent, view, position, id) -> {
            JSONObject app = displayedAppsList.get(position);
            Intent intent = new Intent(MainActivity.this, AppDetailActivity.class);
            intent.putExtra("app_json", app.toString());
            intent.putExtra("server_ip", app.optString("_server_ip"));
            startActivity(intent);
        });
        
        if (Shizuku.pingBinder()) {
            if (Shizuku.checkSelfPermission() != android.content.pm.PackageManager.PERMISSION_GRANTED) {
                Shizuku.requestPermission(1001);
            }
        }
        
        try {
            com.rosan.dhizuku.api.Dhizuku.init(this);
            if (!com.rosan.dhizuku.api.Dhizuku.isPermissionGranted()) {
                com.rosan.dhizuku.api.Dhizuku.requestPermission(new com.rosan.dhizuku.api.DhizukuRequestPermissionListener() {
                    @Override
                    public void onRequestPermission(int i) {}
                });
            }
        } catch(Exception e) {}

        setupTabs();
        
        EditText etSearch = findViewById(R.id.etSearch);
        Button btnSearch = findViewById(R.id.btnSearch);
        btnSearch.setOnClickListener(v -> {
            currentSearchQuery = etSearch.getText().toString().trim().toLowerCase();
            if (!serverIPs.isEmpty()) {
                fetchAppsFromServer(serverIPs.iterator().next(), currentSearchQuery);
            }
        });

        loadCachedApps();
        discoverServers();
    }
    
    private boolean isAppDisplayed(String packageName) {
        for (JSONObject app : displayedAppsList) {
            if (app.optString("package_name").equals(packageName)) return true;
        }
        return false;
    }

    private void loadCachedApps() {
        try {
            android.content.SharedPreferences prefs = getSharedPreferences("prefs", MODE_PRIVATE);
            org.json.JSONArray cachedApps = new org.json.JSONArray(prefs.getString("cached_apps", "[]"));
            for (int i = 0; i < cachedApps.length(); i++) {
                JSONObject app = cachedApps.getJSONObject(i);
                boolean exists = false;
                for (JSONObject existingApp : appsList) {
                    if (existingApp.optString("package_name").equals(app.optString("package_name"))) {
                        exists = true; break;
                    }
                }
                if (!exists) appsList.add(app);
            }
            
            filterApps();
        } catch (Exception e) {
            e.printStackTrace();
        }
    }

    private void setupTabs() {
        TextView tabApps = findViewById(R.id.tabApps);
        TextView tabGames = findViewById(R.id.tabGames);
        TextView tabDownloads = findViewById(R.id.tabDownloads);
        
        android.view.View.OnClickListener tabListener = v -> {
            int unselectedColor = android.graphics.Color.parseColor("#888888"); // A neutral grey that looks fine in light and dark mode, or use context color
            tabApps.setTextColor(unselectedColor);
            tabGames.setTextColor(unselectedColor);
            tabDownloads.setTextColor(unselectedColor);
            
            ((TextView) v).setTextColor(android.graphics.Color.parseColor("#A4C639"));
            
            if (v == tabApps) currentTab = 0;
            else if (v == tabGames) currentTab = 1;
            else if (v == tabDownloads) currentTab = 2;
            
            filterApps();
        };
        
        tabApps.setOnClickListener(tabListener);
        tabGames.setOnClickListener(tabListener);
        tabDownloads.setOnClickListener(tabListener);
        tabApps.setTextColor(android.graphics.Color.parseColor("#A4C639"));
    }
    
    private void filterApps() {
        displayedAppsList.clear();
        for (JSONObject app : appsList) {
            if (currentTab == 0) {
                displayedAppsList.add(app);
            } else if (currentTab == 1) {
                if (app.optString("category", "").toLowerCase().contains("game")) {
                    displayedAppsList.add(app);
                }
            } else if (currentTab == 2) {
                boolean installed = false;
                try {
                    getPackageManager().getPackageInfo(app.optString("package_name"), 0);
                    installed = true;
                } catch (Exception e) {}
                if (installed) displayedAppsList.add(app);
            }
        }
        adapter.notifyDataSetChanged();
    }
    
    @Override
    public boolean onCreateOptionsMenu(android.view.Menu menu) {
        menu.add(0, 1, 0, "Theme: Light");
        menu.add(0, 2, 0, "Theme: Dark");
        menu.add(0, 3, 0, "Theme: AMOLED Black");
        return super.onCreateOptionsMenu(menu);
    }
    
    @Override
    public boolean onOptionsItemSelected(android.view.MenuItem item) {
        android.content.SharedPreferences prefs = getSharedPreferences("prefs", MODE_PRIVATE);
        if (item.getItemId() == 1) prefs.edit().putString("theme", "light").apply();
        else if (item.getItemId() == 2) prefs.edit().putString("theme", "dark").apply();
        else if (item.getItemId() == 3) prefs.edit().putString("theme", "amoled").apply();
        else return super.onOptionsItemSelected(item);
        recreate();
        return true;
    }

    private void showSettingsDialog() {
        AlertDialog.Builder builder = new AlertDialog.Builder(this);
        String currentServerIp = getSharedPreferences("prefs", MODE_PRIVATE).getString("server_ip", "None");
        builder.setTitle("Marketplace Settings (" + currentServerIp + ":8552)");
        String[] options = {"Install Root Certificate", "Install PFX Certificate", "Manually Add Server IP", "Refresh Store", "Theme: Light", "Theme: Dark", "Theme: AMOLED Black", "View Latest Release on GitHub", "View Local Server Website"};
        builder.setItems(options, (dialog, which) -> {
            if (which == 0) installCertificate();
            else if (which == 1) installPfxCertificate();
            else if (which == 2) promptForServerIP();
            else if (which == 3) { appsList.clear(); serverIPs.clear(); filterApps(); discoverServers(); }
            else if (which >= 4 && which <= 6) {
                android.content.SharedPreferences prefs = getSharedPreferences("prefs", MODE_PRIVATE);
                if (which == 4) prefs.edit().putString("theme", "light").apply();
                else if (which == 5) prefs.edit().putString("theme", "dark").apply();
                else if (which == 6) prefs.edit().putString("theme", "amoled").apply();
                recreate();
            }
            else if (which == 7) {
                android.content.Intent browserIntent = new android.content.Intent(android.content.Intent.ACTION_VIEW, android.net.Uri.parse("https://github.com/TheShadyRainbow4/Local_APK_Store/releases/latest"));
                startActivity(browserIntent);
            }
            else if (which == 8) {
                android.content.SharedPreferences prefs = getSharedPreferences("prefs", MODE_PRIVATE);
                String serverIp = prefs.getString("server_ip", "");
                if (!serverIp.isEmpty()) {
                    android.content.Intent browserIntent = new android.content.Intent(android.content.Intent.ACTION_VIEW, android.net.Uri.parse("http://" + serverIp + ":8552/"));
                    startActivity(browserIntent);
                } else {
                    android.widget.Toast.makeText(this, "No server IP configured. Connect to server first.", android.widget.Toast.LENGTH_SHORT).show();
                }
            }
        });
        builder.show();
    }

    private void installCertificate() {
        try {
            java.io.InputStream is = getResources().openRawResource(R.raw.elite_cert);
            byte[] certBytes = new byte[is.available()];
            is.read(certBytes);
            is.close();

            android.content.Intent intent = android.security.KeyChain.createInstallIntent();
            intent.putExtra(android.security.KeyChain.EXTRA_CERTIFICATE, certBytes);
            intent.putExtra(android.security.KeyChain.EXTRA_NAME, "EliteSoftware Root CA");
            startActivity(intent);
        } catch (Exception e) {
            Toast.makeText(this, "Failed to load cert", Toast.LENGTH_SHORT).show();
        }
    }

    private void installPfxCertificate() {
        try {
            java.io.InputStream is = getResources().openRawResource(R.raw.elite_cert_pfx);
            byte[] certBytes = new byte[is.available()];
            is.read(certBytes);
            is.close();

            android.content.Intent intent = android.security.KeyChain.createInstallIntent();
            intent.putExtra(android.security.KeyChain.EXTRA_PKCS12, certBytes);
            intent.putExtra(android.security.KeyChain.EXTRA_NAME, "EliteSoftware Special PFX");
            startActivity(intent);
        } catch (Exception e) {
            Toast.makeText(this, "Failed to load PFX cert", Toast.LENGTH_SHORT).show();
        }
    }

    private void promptForServerIP() {
        AlertDialog.Builder builder = new AlertDialog.Builder(this);
        builder.setTitle("Enter Server IP");
        final EditText input = new EditText(this);
        input.setInputType(InputType.TYPE_CLASS_TEXT);
        builder.setView(input);
        builder.setPositiveButton("Add", (dialog, which) -> {
            String ip = input.getText().toString();
            getSharedPreferences("prefs", MODE_PRIVATE).edit().putString("server_ip", ip).apply();
            synchronized (serverIPs) {
                if (!serverIPs.contains(ip)) {
                    serverIPs.add(ip);
                    fetchAppsFromServer(ip, currentSearchQuery);
                    startHeartbeat();
                }
            }
        });
        builder.setNegativeButton("Cancel", (dialog, which) -> dialog.cancel());
        builder.show();
    }

    private void discoverServers() {
        executor.execute(() -> {
            WifiManager wifi = (WifiManager) getApplicationContext().getSystemService(Context.WIFI_SERVICE);
            WifiManager.MulticastLock lock = null;
            if (wifi != null) {
                lock = wifi.createMulticastLock("EliteMarketplaceDiscovery");
                lock.acquire();
            }
            try (java.net.DatagramSocket socket = new java.net.DatagramSocket()) {
                socket.setBroadcast(true);
                socket.setSoTimeout(3000);
                byte[] sendData = "ELITE_MARKET_DISCOVER".getBytes("UTF-8");
                
                try {
                    java.net.InetAddress broadcastAddr = java.net.InetAddress.getByName("255.255.255.255");
                    socket.send(new java.net.DatagramPacket(sendData, sendData.length, broadcastAddr, 8552));
                } catch(Exception e){}
                
                try {
                    if (wifi != null) {
                        android.net.DhcpInfo dhcp = wifi.getDhcpInfo();
                        if (dhcp != null) {
                            int broadcast = (dhcp.ipAddress & dhcp.netmask) | ~dhcp.netmask;
                            byte[] quads = new byte[4];
                            for (int k = 0; k < 4; k++)
                                quads[k] = (byte) ((broadcast >> k * 8) & 0xFF);
                            java.net.InetAddress actualBroadcast = java.net.InetAddress.getByAddress(quads);
                            socket.send(new java.net.DatagramPacket(sendData, sendData.length, actualBroadcast, 8552));
                        }
                    }
                } catch(Exception e){}

                try {
                    java.net.InetAddress b2 = java.net.InetAddress.getByName("192.168.1.255");
                    socket.send(new java.net.DatagramPacket(sendData, sendData.length, b2, 8552));
                } catch(Exception e){}

                while (true) {
                    byte[] recvBuf = new byte[256];
                    java.net.DatagramPacket receivePacket = new java.net.DatagramPacket(recvBuf, recvBuf.length);
                    try {
                        socket.receive(receivePacket);
                        String response = new String(receivePacket.getData(), 0, receivePacket.getLength(), "UTF-8").trim();
                        if (response.startsWith("ELITE_MARKET_HERE")) {
                            String ip = receivePacket.getAddress().getHostAddress();
                            if (response.contains(":")) {
                                ip = response.split(":")[1];
                            }
                            final String finalIp = ip;
                            getSharedPreferences("prefs", MODE_PRIVATE).edit().putString("server_ip", finalIp).apply();
                            synchronized (serverIPs) {
                                if (!serverIPs.contains(finalIp)) {
                                    serverIPs.add(finalIp);
                                    runOnUiThread(() -> Toast.makeText(this, "Found server: " + finalIp, Toast.LENGTH_SHORT).show());
                                    fetchAppsFromServer(finalIp, currentSearchQuery);
                                    startHeartbeat();
                                }
                            }
                        }
                    } catch (SocketTimeoutException e) {
                        break;
                    }
                }
            } catch (Exception e) {
                e.printStackTrace();
            }
            if (lock != null && lock.isHeld()) {
                lock.release();
            }
            runOnUiThread(() -> {
                if (serverIPs.isEmpty()) {
                    Toast.makeText(this, "No servers found. Add IP manually in Settings.", Toast.LENGTH_LONG).show();
                }
            });
        });
    }

    private void fetchAppsFromServer(String ip, String query) {
        executor.execute(() -> {
            try {
                String urlStr = "http://" + ip + ":8552/api/apps";
                if (query != null && !query.isEmpty()) {
                    urlStr += "?q=" + java.net.URLEncoder.encode(query, "UTF-8");
                }
                java.net.URL url = new java.net.URL(urlStr);
                java.net.HttpURLConnection conn = (java.net.HttpURLConnection) url.openConnection();
                conn.setRequestMethod("GET");
                java.io.BufferedReader in = new java.io.BufferedReader(new java.io.InputStreamReader(conn.getInputStream()));
                String inputLine;
                StringBuilder response = new StringBuilder();
                while ((inputLine = in.readLine()) != null) response.append(inputLine);
                in.close();
                
                JSONObject json = new JSONObject(response.toString());
                JSONArray apps = json.getJSONArray("apps");
                
                runOnUiThread(() -> {
                    appsList.clear(); // Clear existing when fetching from server (search replaces list)
                    for (int i = 0; i < apps.length(); i++) {
                        try {
                            JSONObject app = apps.getJSONObject(i);
                            app.put("_server_ip", ip);
                            appsList.add(app);
                            checkForSelfUpdate(app);
                        } catch (Exception e) {}
                    }
                    filterApps();
                });
            } catch (Exception e) {
                e.printStackTrace();
            }
        });
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

    private void checkForSelfUpdate(JSONObject app) {
        try {
            if (!app.getString("package_name").equals("com.elitesoftware.appmarketplace")) return;
            JSONArray versions = app.getJSONArray("versions");
            String latestVer = "";
            for (int i = 0; i < versions.length(); i++) {
                String ver = versions.getJSONObject(i).getString("version");
                if (compareVersions(ver, latestVer) > 0) latestVer = ver;
            }
            android.content.pm.PackageInfo pInfo = getPackageManager().getPackageInfo(getPackageName(), 0);
            String currentVer = pInfo.versionName;
            
            if (compareVersions(latestVer, currentVer) > 0) {
                AlertDialog.Builder builder = new AlertDialog.Builder(this);
                builder.setTitle("Store Update Available");
                builder.setMessage("A new version of the Marketplace (" + latestVer + ") is available. View update?");
                builder.setPositiveButton("Yes", (dialog, which) -> {
                    android.content.Intent intent = new android.content.Intent(MainActivity.this, AppDetailActivity.class);
                    intent.putExtra("app_json", app.toString());
                    startActivity(intent);
                });
                builder.setNegativeButton("Later", null);
                builder.show();
            }
        } catch (Exception e) {}
    }

    private class AppAdapter extends BaseAdapter {
        @Override
        public int getCount() {
            return displayedAppsList.size();
        }

        @Override
        public Object getItem(int position) {
            return displayedAppsList.get(position);
        }

        @Override
        public long getItemId(int position) {
            return position;
        }

        @Override
        public View getView(int position, View convertView, ViewGroup parent) {
            if (convertView == null) {
                convertView = LayoutInflater.from(MainActivity.this).inflate(R.layout.list_item_app, parent, false);
            }
            
            JSONObject app = displayedAppsList.get(position);
            
            TextView tvAppName = convertView.findViewById(R.id.tvAppName);
            TextView tvAppDesc = convertView.findViewById(R.id.tvAppDesc);
            Button btnInstall = convertView.findViewById(R.id.btnInstall);
            ImageView ivAppIcon = convertView.findViewById(R.id.ivAppIcon);
            
            tvAppName.setText(app.optString("name", "Unknown App"));
            tvAppDesc.setText(app.optString("description", "No description available."));
            ivAppIcon.setImageResource(R.mipmap.ic_launcher);
            
            if (app.has("icon") && !app.optString("icon").isEmpty()) {
                String iconVal = app.optString("icon");
                String iconUrl = iconVal.startsWith("local://") ? iconVal : "http://" + app.optString("_server_ip") + ":8552/images/" + iconVal;
                loadImageAsync(iconUrl, ivAppIcon);
            }
            
            boolean installed = false;
            boolean updateAvailable = false;
            try {
                android.content.pm.PackageInfo pi = MainActivity.this.getPackageManager().getPackageInfo(app.optString("package_name"), 0);
                installed = true;
                String installedVersion = pi.versionName;
                org.json.JSONArray versions = app.getJSONArray("versions");
                String latestVer = "";
                for (int i = 0; i < versions.length(); i++) {
                    String ver = versions.getJSONObject(i).getString("version");
                    if (compareVersions(ver, latestVer) > 0) latestVer = ver;
                }
                if (compareVersions(latestVer, installedVersion) > 0) updateAvailable = true;
            } catch (Exception e) {}
            
            com.elitesoftware.appmarketplace.EliteProgressBar pbInstall = convertView.findViewById(R.id.pbInstall);
            
            View.OnClickListener installAction = v -> {
                btnInstall.setEnabled(false);
                pbInstall.setVisibility(View.VISIBLE);
                pbInstall.setProgress(0);
                    
                    new Thread(() -> {
                        try {
                            String apkUrl = "http://" + app.optString("_server_ip") + ":8552/apks/" + app.getJSONArray("versions").getJSONObject(0).getString("file");
                            java.net.URL url = new java.net.URL(apkUrl);
                            java.net.HttpURLConnection conn = (java.net.HttpURLConnection) url.openConnection();
                            conn.connect();
                            int fileLength = conn.getContentLength();
                            
                            // Add Premium Feel Delay
                            runOnUiThread(() -> btnInstall.setText("PREPARING..."));
                            try { Thread.sleep(600); } catch(Exception e) {}
                            
                            java.io.InputStream input = new java.io.BufferedInputStream(url.openStream(), 8192);
                            String ver = app.getJSONArray("versions").getJSONObject(0).getString("version");
                            String safeName = app.optString("name").replaceAll(" ", "_");
                            java.io.File apkFile = new java.io.File(MainActivity.this.getExternalFilesDir(null), safeName + "_v" + ver + ".apk");
                            java.io.OutputStream output = new java.io.FileOutputStream(apkFile);
                            
                            byte data[] = new byte[8192];
                            long total = 0;
                            int count;
                            while ((count = input.read(data)) != -1) {
                                total += count;
                                int progress = (int) (total * 100 / fileLength);
                                runOnUiThread(() -> pbInstall.setProgress(progress));
                                output.write(data, 0, count);
                                // slight artificial delay for progress bar visibility
                                try { Thread.sleep(1); } catch(Exception e) {}
                            }
                            output.flush();
                            output.close();
                            input.close();
                            
                            runOnUiThread(() -> {
                                pbInstall.setVisibility(View.GONE);
                                btnInstall.setText("INSTALLING...");
                            });
                            
                            // Premium feel delay for installation
                            try { Thread.sleep(800); } catch(Exception e) {}
                            
                            // Install via Shizuku API Stream (Bypasses Scoped Storage)
                            boolean installed_ok = false;
                            String errorLog = "";
                            
                            try {
                                Process p = null;
                                boolean isSu = false;
                                if (Shizuku.pingBinder() && Shizuku.checkSelfPermission() == android.content.pm.PackageManager.PERMISSION_GRANTED) {
                                    p = Shizuku.newProcess(new String[]{"pm", "install", "-S", String.valueOf(apkFile.length())}, null, null);
                                } else {
                                    try {
                                        if (com.rosan.dhizuku.api.Dhizuku.isPermissionGranted()) {
                                            p = com.rosan.dhizuku.api.Dhizuku.newProcess(new String[]{"pm", "install", "-S", String.valueOf(apkFile.length())}, null, null);
                                        }
                                    } catch(Exception e) {}
                                    if (p == null) {
                                        // SU fallback
                                        isSu = true;
                                        p = Runtime.getRuntime().exec("su");
                                        p.getOutputStream().write(("pm install -S " + apkFile.length() + "\n").getBytes());
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
                                        if (app.optString("package_name").equals(getPackageName())) {
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
                                // Fallback to standard package installer
                                runOnUiThread(() -> {
                                    try {
                                        android.content.Intent intent = new android.content.Intent(android.content.Intent.ACTION_VIEW);
                                        android.net.Uri apkUri = androidx.core.content.FileProvider.getUriForFile(MainActivity.this, getPackageName() + ".provider", apkFile);
                                        intent.setDataAndType(apkUri, "application/vnd.android.package-archive");
                                        intent.setFlags(android.content.Intent.FLAG_ACTIVITY_NEW_TASK);
                                        intent.addFlags(android.content.Intent.FLAG_GRANT_READ_URI_PERMISSION);
                                        startActivity(intent);
                                    } catch (Exception e) {
                                        Toast.makeText(MainActivity.this, "Installation failed: " + e.getMessage(), Toast.LENGTH_LONG).show();
                                    }
                                    btnInstall.setText("INSTALL");
                                    btnInstall.setEnabled(true);
                                    pbInstall.setVisibility(View.GONE);
                                });
                            } else {
                                runOnUiThread(() -> {
                                    btnInstall.setText("OPEN");
                                    btnInstall.setEnabled(true);
                                    pbInstall.setVisibility(View.GONE);
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
                                    } catch (Exception e) {}
                                    filterApps();
                                });
                            }
                            btnInstall.setOnClickListener(v2 -> {
                                Intent launchIntent = MainActivity.this.getPackageManager().getLaunchIntentForPackage(app.optString("package_name"));
                                if (launchIntent != null) MainActivity.this.startActivity(launchIntent);
                            });
                        } catch (Exception e) {
                            e.printStackTrace();
                            runOnUiThread(() -> {
                                Toast.makeText(MainActivity.this, "Download failed", Toast.LENGTH_SHORT).show();
                                btnInstall.setEnabled(true);
                                btnInstall.setText("INSTALL");
                                pbInstall.setVisibility(View.GONE);
                            });
                        }
                    }).start();
            };
            
            if (installed && !updateAvailable) {
                btnInstall.setText("OPEN");
                btnInstall.setOnClickListener(v -> {
                    if (app.optString("package_name").equals(MainActivity.this.getPackageName())) {
                        Toast.makeText(MainActivity.this, "You are already using this app!", Toast.LENGTH_SHORT).show();
                        return;
                    }
                    Intent launchIntent = MainActivity.this.getPackageManager().getLaunchIntentForPackage(app.optString("package_name"));
                    if (launchIntent != null) {
                        MainActivity.this.startActivity(launchIntent);
                    } else {
                        Toast.makeText(MainActivity.this, "App cannot be opened.", Toast.LENGTH_SHORT).show();
                    }
                });
            } else {
                btnInstall.setText(updateAvailable ? "UPDATE" : "INSTALL");
                btnInstall.setOnClickListener(installAction);
            }
            
            return convertView;
        }
    }
    
    private static java.util.HashMap<String, android.graphics.Bitmap> imageCache = new java.util.HashMap<>();
    
    private void loadImageAsync(String urlStr, ImageView imageView) {
        if (imageCache.containsKey(urlStr)) {
            imageView.setImageBitmap(imageCache.get(urlStr));
            return;
        }
        imageView.setTag(urlStr);
        executor.execute(() -> {
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
        });
    }

    public String getDeviceName() {
        String manufacturer = Build.MANUFACTURER;
        String model = Build.MODEL;
        if (model != null && manufacturer != null && model.toLowerCase().startsWith(manufacturer.toLowerCase())) {
            return capitalize(model);
        } else {
            return capitalize(manufacturer) + " " + (model != null ? model : "");
        }
    }

    private String capitalize(String s) {
        if (s == null || s.length() == 0) return "";
        char first = s.charAt(0);
        if (Character.isUpperCase(first)) return s;
        return Character.toUpperCase(first) + s.substring(1);
    }

    private String getClientId() {
        String id = Settings.Secure.getString(getContentResolver(), Settings.Secure.ANDROID_ID);
        if (id == null || id.isEmpty() || "9774d56d682e549c".equals(id)) {
            android.content.SharedPreferences prefs = getSharedPreferences("prefs", MODE_PRIVATE);
            id = prefs.getString("client_uuid", null);
            if (id == null) {
                id = java.util.UUID.randomUUID().toString();
                prefs.edit().putString("client_uuid", id).apply();
            }
        }
        return id;
    }

    private synchronized void startHeartbeat() {
        if (heartbeatFuture != null && !heartbeatFuture.isCancelled()) return;
        heartbeatFuture = heartbeatScheduler.scheduleAtFixedRate(() -> {
            sendHeartbeat();
        }, 0, 5, TimeUnit.SECONDS);
    }

    private void sendHeartbeat() {
        HashSet<String> ipsCopy;
        synchronized (serverIPs) {
            ipsCopy = new HashSet<>(serverIPs);
        }
        if (ipsCopy.isEmpty()) return;

        String clientId = getClientId();
        String deviceName = getDeviceName();

        try {
            JSONObject json = new JSONObject();
            json.put("client_id", clientId);
            json.put("device_name", deviceName);
            byte[] body = json.toString().getBytes("UTF-8");

            for (String ip : ipsCopy) {
                try {
                    java.net.URL url = new java.net.URL("http://" + ip + ":8552/api/heartbeat");
                    java.net.HttpURLConnection conn = (java.net.HttpURLConnection) url.openConnection();
                    conn.setRequestMethod("POST");
                    conn.setRequestProperty("Content-Type", "application/json");
                    conn.setDoOutput(true);
                    conn.setConnectTimeout(3000);
                    conn.setReadTimeout(3000);
                    conn.setFixedLengthStreamingMode(body.length);
                    conn.setRequestProperty("Content-Length", String.valueOf(body.length));
                    java.io.OutputStream os = conn.getOutputStream();
                    os.write(body);
                    os.flush();
                    os.close();
                    int code = conn.getResponseCode();
                    conn.disconnect();
                } catch (Exception e) {
                    // Ignore transient network errors on heartbeat
                }
            }
        } catch (Exception e) {
            e.printStackTrace();
        }
    }

    private void sendDisconnect() {
        HashSet<String> ipsCopy;
        synchronized (serverIPs) {
            ipsCopy = new HashSet<>(serverIPs);
        }
        if (ipsCopy.isEmpty()) return;

        String clientId = getClientId();
        executor.execute(() -> {
            try {
                JSONObject json = new JSONObject();
                json.put("client_id", clientId);
                byte[] body = json.toString().getBytes("UTF-8");

                for (String ip : ipsCopy) {
                    try {
                        java.net.URL url = new java.net.URL("http://" + ip + ":8552/api/disconnect");
                        java.net.HttpURLConnection conn = (java.net.HttpURLConnection) url.openConnection();
                        conn.setRequestMethod("POST");
                        conn.setRequestProperty("Content-Type", "application/json");
                        conn.setDoOutput(true);
                        conn.setConnectTimeout(2000);
                        conn.setReadTimeout(2000);
                        java.io.OutputStream os = conn.getOutputStream();
                        os.write(body);
                        os.flush();
                        os.close();
                        int code = conn.getResponseCode();
                        conn.disconnect();
                    } catch (Exception e) {
                        // Ignore transient network errors on disconnect
                    }
                }
            } catch (Exception e) {
                e.printStackTrace();
            }
        });
    }

    @Override
    protected void onStart() {
        super.onStart();
        synchronized (serverIPs) {
            if (!serverIPs.isEmpty()) {
                startHeartbeat();
            }
        }
    }

    @Override
    protected void onStop() {
        super.onStop();
        sendDisconnect();
    }
}
