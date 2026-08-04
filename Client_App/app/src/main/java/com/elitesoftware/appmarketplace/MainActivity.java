package com.elitesoftware.appmarketplace;

import android.app.AlertDialog;
import android.content.Context;
import android.content.Intent;
import android.net.wifi.WifiManager;
import android.os.Bundle;
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
import java.util.concurrent.ExecutorService;
import java.util.concurrent.Executors;

public class MainActivity extends AppCompatActivity {

    private ArrayList<String> serverIPs = new ArrayList<>();
    private ListView lvApps;
    private ArrayList<JSONObject> appsList = new ArrayList<>();
    private AppAdapter adapter;
    private ExecutorService executor = Executors.newFixedThreadPool(4);

    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        if (getSupportActionBar() != null) getSupportActionBar().hide();
        setContentView(R.layout.activity_main);

        ImageButton btnSettings = findViewById(R.id.btnSettings);
        btnSettings.setOnClickListener(v -> showSettingsDialog());

        lvApps = findViewById(R.id.lvApps);
        adapter = new AppAdapter();
        lvApps.setAdapter(adapter);

        lvApps.setOnItemClickListener((parent, view, position, id) -> {
            JSONObject app = appsList.get(position);
            Intent intent = new Intent(MainActivity.this, AppDetailActivity.class);
            intent.putExtra("app_json", app.toString());
            // Assume the server IP is the first one found for simplicity right now
            if (!serverIPs.isEmpty()) {
                intent.putExtra("server_ip", serverIPs.get(0));
            }
            startActivity(intent);
        });

        discoverServers();
    }

    private void showSettingsDialog() {
        AlertDialog.Builder builder = new AlertDialog.Builder(this);
        builder.setTitle("Marketplace Settings");
        String[] options = {"Install Root Certificate", "Manually Add Server IP", "Refresh Store"};
        builder.setItems(options, (dialog, which) -> {
            if (which == 0) installCertificate();
            else if (which == 1) promptForServerIP();
            else if (which == 2) { appsList.clear(); adapter.notifyDataSetChanged(); discoverServers(); }
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
            intent.putExtra(android.security.KeyChain.EXTRA_PKCS12, certBytes);
            intent.putExtra(android.security.KeyChain.EXTRA_NAME, "EliteSoftware Root CA");
            startActivity(intent);
        } catch (Exception e) {
            Toast.makeText(this, "Failed to load cert", Toast.LENGTH_SHORT).show();
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
            if (!serverIPs.contains(ip)) {
                serverIPs.add(ip);
                fetchAppsFromServer(ip);
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
                            if (!serverIPs.contains(ip)) {
                                serverIPs.add(ip);
                                runOnUiThread(() -> Toast.makeText(this, "Found server: " + ip, Toast.LENGTH_SHORT).show());
                                fetchAppsFromServer(ip);
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
                        } catch (Exception e) {}
                    }
                    adapter.notifyDataSetChanged();
                });
            } catch (Exception e) {
                e.printStackTrace();
            }
        });
    }

    private class AppAdapter extends BaseAdapter {
        @Override
        public int getCount() {
            return appsList.size();
        }

        @Override
        public Object getItem(int position) {
            return appsList.get(position);
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
            
            JSONObject app = appsList.get(position);
            
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
                            java.io.File apkFile = new java.io.File(MainActivity.this.getExternalFilesDir(null), app.optString("package_name") + ".apk");
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
                                    p.waitFor();
                                    installed_ok = true;
                                }
                            } catch (Exception e) {}
                            
                            if (!installed_ok) {
                                Process p = Runtime.getRuntime().exec(new String[]{"sh", "-c", "dhizuku -c 'pm install -r " + apkFile.getAbsolutePath() + "' || su -c 'pm install -r " + apkFile.getAbsolutePath() + "' || shizuku -c 'pm install -r " + apkFile.getAbsolutePath() + "'"});
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
}
