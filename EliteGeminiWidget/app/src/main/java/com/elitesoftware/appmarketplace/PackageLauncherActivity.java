package com.elitesoftware.appmarketplace;

import android.app.Activity;
import android.app.AlertDialog;
import android.content.Intent;
import android.os.Bundle;
import android.widget.EditText;
import android.widget.LinearLayout;
import android.widget.Toast;

public class PackageLauncherActivity extends Activity {
    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        
        LinearLayout layout = new LinearLayout(this);
        layout.setOrientation(LinearLayout.VERTICAL);
        layout.setPadding(50, 100, 50, 50);
        
        android.widget.TextView title = new android.widget.TextView(this);
        title.setText("Launch Package in Elite Frame");
        title.setTextSize(20);
        title.setPadding(0, 0, 0, 20);
        layout.addView(title);
        
        final EditText input = new EditText(this);
        input.setHint("e.g. com.android.settings");
        layout.addView(input);
        
        android.widget.Button launchBtn = new android.widget.Button(this);
        launchBtn.setText("Launch");
        launchBtn.setOnClickListener(v -> {
            String pkg = input.getText().toString().trim();
            if (!pkg.isEmpty()) {
                Intent intent = new Intent(this, FloatingWidgetService.class);
                intent.putExtra("package", pkg);
                intent.putExtra("title", pkg);
                startService(intent);
                finish();
            } else {
                Toast.makeText(this, "Package name cannot be empty", Toast.LENGTH_SHORT).show();
            }
        });
        layout.addView(launchBtn);
        
        setContentView(layout);
    }
}
