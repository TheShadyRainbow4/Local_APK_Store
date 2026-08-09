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
        
        AlertDialog.Builder builder = new AlertDialog.Builder(this);
        builder.setTitle("Launch Package in Elite Frame");
        
        final EditText input = new EditText(this);
        input.setHint("e.g. com.android.settings");
        
        LinearLayout layout = new LinearLayout(this);
        layout.setOrientation(LinearLayout.VERTICAL);
        layout.setPadding(50, 20, 50, 20);
        layout.addView(input);
        
        builder.setView(layout);
        
        builder.setPositiveButton("Launch", (dialog, which) -> {
            String pkg = input.getText().toString().trim();
            if (!pkg.isEmpty()) {
                Intent intent = new Intent(this, FloatingWidgetService.class);
                intent.putExtra("package", pkg);
                intent.putExtra("title", pkg);
                startService(intent);
            } else {
                Toast.makeText(this, "Package name cannot be empty", Toast.LENGTH_SHORT).show();
            }
            finish();
        });
        
        builder.setNegativeButton("Cancel", (dialog, which) -> {
            dialog.cancel();
            finish();
        });
        
        builder.setOnCancelListener(dialog -> finish());
        
        builder.show();
    }
}
