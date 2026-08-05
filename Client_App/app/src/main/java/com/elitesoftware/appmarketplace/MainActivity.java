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
        }

        if (getSupportActionBar() != null) getSupportActionBar().hide();

        ImageButton btnSettings = findViewById(R.id.btnSettings);
        btnSettings.setOnClickListener(v -> showSettingsDialog());

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
        
        setupTabs();

        discoverServers();
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
        builder.setTitle("Marketplace Settings");
        String[] options = {"Install Root Certificate", "Install PFX Certificate", "Manually Add Server IP", "Refresh Store", "Theme: Light", "Theme: Dark", "Theme: AMOLED Black"};
        builder.setItems(options, (dialog, which) -> {
            if (which == 0) installCertificate();
            else if (which == 1) installPfxCertificate();
            else if (which == 2) promptForServerIP();
            else if (which == 3) { appsList.clear(); filterApps(); discoverServers(); }
            else if (which >= 4 && which <= 6) {
                android.content.SharedPreferences prefs = getSharedPreferences("prefs", MODE_PRIVATE);
                if (which == 4) prefs.edit().putString("theme", "light").apply();
                else if (which == 5) prefs.edit().putString("theme", "dark").apply();
                else if (which == 6) prefs.edit().putString("theme", "amoled").apply();
                recreate();
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
            synchronized (serverIPs) {
                if (!serverIPs.contains(ip)) {
                    serverIPs.add(ip);
                    fetchAppsFromServer(ip);
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
            try (DatagramSocket socket = new DatagramSocket()) {
                socket.setBroadcast(true);
                socket.setSoTimeout(3000);
                byte[] sendData = "ELITE_MARKET_DISCOVER".getBytes();
                
                InetAddress broadcastAddr = InetAddress.getByName("255.255.255.255");
                DatagramPacket sendPacket = new DatagramPacket(sendData, sendData.length, broadcastAddr, 8552);
                socket.send(sendPacket);
                
                try {
                    InetAddress b2 = InetAddress.getByName("192.168.1.255");
                    socket.send(new DatagramPacket(sendData, sendData.length, b2, 8552));
                } catch(Exception e){}

                while (true) {
                    byte[] recvBuf = new byte[256];
                    DatagramPacket receivePacket = new DatagramPacket(recvBuf, recvBuf.length);
                    try {
                        socket.receive(receivePacket);
                        String response = new String(receivePacket.getData()).trim();
                        if (response.equals("ELITE_MARKET_HERE")) {
                            String ip = receivePacket.getAddress().getHostAddress();
                            synchronized (serverIPs) {
                                if (!serverIPs.contains(ip)) {
                                    serverIPs.add(ip);
                                    runOnUiThread(() -> Toast.makeText(this, "Found server: " + ip, Toast.LENGTH_SHORT).show());
                                    fetchAppsFromServer(ip);
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

    private void fetchAppsFromServer(String ip) {
        executor.execute(() -> {
            try {
                java.net.URL url = new java.net.URL("http://" + ip + ":8552/api/apps");
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
                    for (int i = 0; i < apps.length(); i++) {
                        try {
                            JSONObject app = apps.getJSONObject(i);
                            // add ip field so we know where it came from
                            app.put("_server_ip", ip);
                            boolean exists = false;
                            for (JSONObject existingApp : appsList) {
                                if (existingApp.getString("package_name").equals(app.getString("package_name"))) {
                                    exists = true;
                                    break;
                                }
                            }
                            if (!exists) {
                                appsList.add(app);
                            }
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

    private void checkForSelfUpdate(JSONObject app) {
        try {
            if (!app.getString("package_name").equals("com.elitesoftware.appmarketplace")) return;
            JSONArray versions = app.getJSONArray("versions");
            String latestVer = "";
            for (int i = 0; i < versions.length(); i++) {
                String ver = versions.getJSONObject(i).getString("version");
                if (ver.compareTo(latestVer) > 0) latestVer = ver;
            }
            android.content.pm.PackageInfo pInfo = getPackageManager().getPackageInfo(getPackageName(), 0);
            String currentVer = pInfo.versionName;
            
            if (latestVer.compareTo(currentVer) > 0) {
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
                String iconUrl = "http://" + app.optString("_server_ip") + ":8552/images/" + app.optString("icon");
                loadImageAsync(iconUrl, ivAppIcon);
            }
            
            boolean installed = false;
            try {
                MainActivity.this.getPackageManager().getPackageInfo(app.optString("package_name"), 0);
                installed = true;
            } catch (Exception e) {}
            
            ProgressBar pbInstall = convertView.findViewById(R.id.pbInstall);
            
            if (installed) {
                btnInstall.setText("OPEN");
                btnInstall.setOnClickListener(v -> {
                    Intent launchIntent = MainActivity.this.getPackageManager().getLaunchIntentForPackage(app.optString("package_name"));
                    if (launchIntent != null) {
                        MainActivity.this.startActivity(launchIntent);
                    } else {
                        Toast.makeText(MainActivity.this, "App cannot be opened.", Toast.LENGTH_SHORT).show();
                    }
                });
            } else {
                btnInstall.setText("INSTALL");
                btnInstall.setOnClickListener(v -> {
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
                            
                            java.io.InputStream input = new java.io.BufferedInputStream(url.openStream(), 8192);
                            String ver = app.getJSONArray("versions").getJSONObject(0).getString("version");
                            String safeName = app.optString("name").replaceAll(" ", "_");
                            java.io.File apkFile = new java.io.File(android.os.Environment.getExternalStoragePublicDirectory(android.os.Environment.DIRECTORY_DOWNLOADS), safeName + "_v" + ver + ".apk");
                            java.io.OutputStream output = new java.io.FileOutputStream(apkFile);
                            
                            byte data[] = new byte[1024];
                            long total = 0;
                            int count;
                            while ((count = input.read(data)) != -1) {
                                total += count;
                                int progress = (int) (total * 100 / fileLength);
                                runOnUiThread(() -> pbInstall.setProgress(progress));
                                output.write(data, 0, count);
                            }
                            output.flush();
                            output.close();
                            input.close();
                            
                            runOnUiThread(() -> {
                                pbInstall.setVisibility(View.GONE);
                                btnInstall.setText("INSTALLING...");
                            });
                            
                            // Install via Shizuku API / fallback to sh
                            boolean installed_ok = false;
                            try {
                                if (Shizuku.pingBinder()) {
                                    Process p = Shizuku.newProcess(new String[]{"pm", "install", "-r", apkFile.getAbsolutePath()}, null, null);
                                    if (p.waitFor() == 0) {
                                        installed_ok = true;
                                    }
                                }
                            } catch (Exception e) {}
                            
                            if (!installed_ok) {
                                Process p = Runtime.getRuntime().exec(new String[]{"sh", "-c", "dhizuku -c 'pm install -S " + apkFile.length() + "' || su -c 'pm install -S " + apkFile.length() + "'"});
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
                                btnInstall.setText("OPEN");
                                btnInstall.setEnabled(true);
                                btnInstall.setOnClickListener(v2 -> {
                                    Intent launchIntent = MainActivity.this.getPackageManager().getLaunchIntentForPackage(app.optString("package_name"));
                                    if (launchIntent != null) MainActivity.this.startActivity(launchIntent);
                                });
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
                });
            }
            
            return convertView;
        }
    }
    
    private void loadImageAsync(String urlStr, ImageView imageView) {
        imageView.setTag(urlStr);
        executor.execute(() -> {
            try {
                java.net.URL url = new java.net.URL(urlStr);
                android.graphics.Bitmap bmp = android.graphics.BitmapFactory.decodeStream(url.openConnection().getInputStream());
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
