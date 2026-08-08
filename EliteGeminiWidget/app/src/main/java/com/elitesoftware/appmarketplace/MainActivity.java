package com.elitesoftware.appmarketplace;

import android.app.Activity;
import android.app.AppOpsManager;
import android.content.Context;
import android.content.Intent;
import android.net.Uri;
import android.os.Build;
import android.os.Bundle;
import android.provider.Settings;
import android.widget.Button;
import android.widget.LinearLayout;
import android.widget.TextView;
import android.widget.Toast;

public class MainActivity extends Activity {
    private static final int DRAW_OVER_OTHER_APP_PERMISSION_REQUEST_CODE = 2084;
    private static final int USAGE_STATS_PERMISSION_REQUEST_CODE = 2085;

    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);

        LinearLayout layout = new LinearLayout(this);
        layout.setOrientation(LinearLayout.VERTICAL);
        layout.setPadding(32, 32, 32, 32);

        TextView tv = new TextView(this);
        tv.setText("Gemini Widget Settings");
        tv.setTextSize(24);
        tv.setPadding(0, 0, 0, 32);

        Button btnOverlay = new Button(this);
        btnOverlay.setText("1. Grant Overlay Permission");
        btnOverlay.setOnClickListener(v -> {
            if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.M && !Settings.canDrawOverlays(this)) {
                Intent intent = new Intent(Settings.ACTION_MANAGE_OVERLAY_PERMISSION, Uri.parse("package:" + getPackageName()));
                startActivityForResult(intent, DRAW_OVER_OTHER_APP_PERMISSION_REQUEST_CODE);
            } else {
                Toast.makeText(this, "Overlay already granted", Toast.LENGTH_SHORT).show();
            }
        });

        Button btnUsage = new Button(this);
        btnUsage.setText("2. Grant Usage Access (for Auto-Hide)");
        btnUsage.setOnClickListener(v -> {
            if (!hasUsageStatsPermission()) {
                Intent intent = new Intent(Settings.ACTION_USAGE_ACCESS_SETTINGS);
                startActivityForResult(intent, USAGE_STATS_PERMISSION_REQUEST_CODE);
            } else {
                Toast.makeText(this, "Usage Access already granted", Toast.LENGTH_SHORT).show();
            }
        });

        Button btnLaunch = new Button(this);
        btnLaunch.setText("3. Launch Widget");
        btnLaunch.setOnClickListener(v -> {
            if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.M && !Settings.canDrawOverlays(this)) {
                Toast.makeText(this, "Need Overlay Permission!", Toast.LENGTH_SHORT).show();
                return;
            }
            if (!hasUsageStatsPermission()) {
                Toast.makeText(this, "Need Usage Access for Pinning!", Toast.LENGTH_SHORT).show();
                return;
            }
            startService(new Intent(MainActivity.this, FloatingWidgetService.class));
            finish();
        });

        layout.addView(tv);
        layout.addView(btnOverlay);
        layout.addView(btnUsage);
        layout.addView(btnLaunch);

        setContentView(layout);
    }

    private boolean hasUsageStatsPermission() {
        AppOpsManager appOps = (AppOpsManager) getSystemService(Context.APP_OPS_SERVICE);
        int mode = appOps.checkOpNoThrow(AppOpsManager.OPSTR_GET_USAGE_STATS, android.os.Process.myUid(), getPackageName());
        return mode == AppOpsManager.MODE_ALLOWED;
    }
}
