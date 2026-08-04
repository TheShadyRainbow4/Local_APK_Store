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
import android.widget.TextView;
import android.widget.Toast;
import android.app.Activity;

import org.json.JSONArray;
import org.json.JSONObject;

import java.net.DatagramPacket;
import java.net.DatagramSocket;
import java.net.InetAddress;
import java.net.SocketTimeoutException;
import java.util.ArrayList;
import java.util.concurrent.ExecutorService;
import java.util.concurrent.Executors;

public class MainActivity extends Activity {

    private ArrayList<String> serverIPs = new ArrayList<>();
    private ListView lvApps;
    private ArrayList<JSONObject> appsList = new ArrayList<>();
    private AppAdapter adapter;
    private ExecutorService executor = Executors.newFixedThreadPool(4);

    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        if (getActionBar() != null) getActionBar().hide();
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

        private int getAppInstallState(Context context, String packageName, String serverVersion) {
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
            
            tvAppName.setText(app.optString("name", "Unknown App"));
            tvAppDesc.setText(app.optString("description", "No description available."));
            
            String packageName = app.optString("package_name", "");
            String serverVersion = "";
            try {
                org.json.JSONArray versions = app.getJSONArray("versions");
                if (versions.length() > 0) {
                    serverVersion = versions.getJSONObject(versions.length() - 1).optString("version", "");
                }
            } catch(Exception e) {}
            
            int state = getAppInstallState(MainActivity.this, packageName, serverVersion);
            if (state == 2) {
                btnInstall.setText("OPEN");
                btnInstall.setBackgroundColor(android.graphics.Color.parseColor("#444444"));
                btnInstall.setTextColor(android.graphics.Color.parseColor("#FFFFFF"));
            } else if (state == 1) {
                btnInstall.setText("UPDATE");
                btnInstall.setBackgroundColor(android.graphics.Color.parseColor("#FF8800"));
                btnInstall.setTextColor(android.graphics.Color.parseColor("#FFFFFF"));
            } else {
                btnInstall.setText("INSTALL");
                btnInstall.setBackgroundColor(android.graphics.Color.parseColor("#A4C639"));
                btnInstall.setTextColor(android.graphics.Color.parseColor("#000000"));
            }
            
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
                    Toast.makeText(MainActivity.this, (state == 1 ? "Updating " : "Installing ") + app.optString("name") + "...", Toast.LENGTH_SHORT).show();
                    // Implement actual download logic here in the future
                }
            });
            
            return convertView;

        }
    }
}
