package com.elitesoftware.appmarketplace;

import android.content.BroadcastReceiver;
import android.content.Context;
import android.content.Intent;
import android.widget.Toast;

public class WindowApiReceiver extends BroadcastReceiver {
    @Override
    public void onReceive(Context context, Intent intent) {
        if ("com.elitesoftware.appmarketplace.LAUNCH_WINDOW".equals(intent.getAction())) {
            String pkg = intent.getStringExtra("package");
            String url = intent.getStringExtra("url");
            String title = intent.getStringExtra("title");

            if ((pkg == null || pkg.isEmpty()) && (url == null || url.isEmpty())) {
                Toast.makeText(context, "Elite API Error: 'package' or 'url' extra is required.", Toast.LENGTH_SHORT).show();
                return;
            }

            if (title == null || title.isEmpty()) {
                title = (pkg != null && !pkg.isEmpty()) ? pkg : url;
            }

            Intent serviceIntent = new Intent(context, FloatingWidgetService.class);
            if (pkg != null && !pkg.isEmpty()) {
                serviceIntent.putExtra("package", pkg);
            } else if (url != null && !url.isEmpty()) {
                serviceIntent.putExtra("url", url);
            }
            serviceIntent.putExtra("title", title);
            
            try {
                context.startService(serviceIntent);
            } catch (Exception e) {
                Toast.makeText(context, "Elite API Error: Could not launch window service.", Toast.LENGTH_SHORT).show();
            }
        }
    }
}
