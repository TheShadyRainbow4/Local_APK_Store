package com.elitesoftware.appmarketplace;
import android.app.Activity;
import android.content.Intent;
import android.os.Build;
import android.os.Bundle;
import android.provider.Settings;
import android.net.Uri;
import android.widget.Button;
import android.widget.EditText;
import android.widget.LinearLayout;
import android.widget.Toast;

public class CustomFrameActivity extends Activity {
    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        
        LinearLayout layout = new LinearLayout(this);
        layout.setOrientation(LinearLayout.VERTICAL);
        layout.setPadding(32, 32, 32, 32);

        Button btnOverlay = new Button(this);
        btnOverlay.setText("Grant Overlay Permission");
        btnOverlay.setOnClickListener(v -> {
            if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.M && !Settings.canDrawOverlays(this)) {
                Intent intent = new Intent(Settings.ACTION_MANAGE_OVERLAY_PERMISSION, Uri.parse("package:" + getPackageName()));
                startActivity(intent);
            }
        });

        EditText pkgInput = new EditText(this);
        pkgInput.setHint("Enter Package Name (e.g. com.android.settings)");

        Button launchBtn = new Button(this);
        launchBtn.setText("Launch Custom Frame");
        launchBtn.setOnClickListener(v -> {
            if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.M && !Settings.canDrawOverlays(this)) {
                Toast.makeText(this, "Need Overlay Permission!", Toast.LENGTH_SHORT).show();
                return;
            }
            String pkg = pkgInput.getText().toString();
            Intent intent = new Intent(CustomFrameActivity.this, FloatingWidgetService.class);
            intent.putExtra("package", pkg);
            intent.putExtra("title", "Elite Frame: " + pkg);
            startService(intent);
            finish();
        });

        layout.addView(btnOverlay);
        layout.addView(pkgInput);
        layout.addView(launchBtn);
        setContentView(layout);
    }
}
