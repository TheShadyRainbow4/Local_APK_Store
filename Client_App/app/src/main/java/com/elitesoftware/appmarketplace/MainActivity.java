package com.elitesoftware.appmarketplace;

import android.app.AlertDialog;
import android.os.Bundle;
import android.text.InputType;
import android.widget.EditText;
import android.widget.ImageButton;
import android.widget.ListView;
import android.widget.Toast;
import android.widget.ArrayAdapter;
import androidx.appcompat.app.AppCompatActivity;

import java.net.DatagramPacket;
import java.net.DatagramSocket;
import java.net.InetAddress;
import java.util.ArrayList;
import java.util.concurrent.ExecutorService;
import java.util.concurrent.Executors;
import java.net.SocketTimeoutException;

public class MainActivity extends AppCompatActivity {

    private ArrayList<String> serverIPs = new ArrayList<>();
    private ListView lvApps;
    private ArrayList<String> appsList = new ArrayList<>();
    private ArrayAdapter<String> adapter;
    private ExecutorService executor = Executors.newFixedThreadPool(4);

    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        if (getSupportActionBar() != null) getSupportActionBar().hide();
        setContentView(R.layout.activity_main);

        ImageButton btnSettings = findViewById(R.id.btnSettings);
        btnSettings.setOnClickListener(v -> showSettingsDialog());

        lvApps = findViewById(R.id.lvApps);
        adapter = new ArrayAdapter<>(this, android.R.layout.simple_list_item_1, appsList);
        lvApps.setAdapter(adapter);

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
            intent.putExtra(android.security.KeyChain.EXTRA_CERTIFICATE, certBytes);
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
            try (DatagramSocket socket = new DatagramSocket()) {
                socket.setBroadcast(true);
                socket.setSoTimeout(3000);
                byte[] sendData = "ELITE_MARKET_DISCOVER".getBytes();
                
                InetAddress broadcastAddr = InetAddress.getByName("255.255.255.255");
                DatagramPacket sendPacket = new DatagramPacket(sendData, sendData.length, broadcastAddr, 8552);
                socket.send(sendPacket);
                
                // try 192.168.1.255 as a fallback
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
                
                org.json.JSONObject json = new org.json.JSONObject(response.toString());
                org.json.JSONArray apps = json.getJSONArray("apps");
                
                runOnUiThread(() -> {
                    for (int i = 0; i < apps.length(); i++) {
                        try {
                            org.json.JSONObject app = apps.getJSONObject(i);
                            String display = app.getString("name") + " - " + app.getString("category") + " (from " + ip + ")";
                            if (!appsList.contains(display)) {
                                appsList.add(display);
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
}
