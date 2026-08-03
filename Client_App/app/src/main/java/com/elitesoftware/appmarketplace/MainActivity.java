package com.elitesoftware.appmarketplace;

import android.os.Bundle;
import android.widget.ImageButton;
import android.widget.ListView;
import android.widget.Toast;
import androidx.appcompat.app.AppCompatActivity;

public class MainActivity extends AppCompatActivity {

    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        
        // Hide default action bar as we created a custom legacy-looking one
        if (getSupportActionBar() != null) {
            getSupportActionBar().hide();
        }
        
        setContentView(R.layout.activity_main);

        ImageButton btnSettings = findViewById(R.id.btnSettings);
        btnSettings.setOnClickListener(v -> {
            Toast.makeText(this, "Settings clicked - Certificate installation coming soon!", Toast.LENGTH_SHORT).show();
        });
        
        ListView lvApps = findViewById(R.id.lvApps);
        // TODO: Fetch from C++ server (http://<server-ip>:8443/api/apps) and populate list
    }
}
