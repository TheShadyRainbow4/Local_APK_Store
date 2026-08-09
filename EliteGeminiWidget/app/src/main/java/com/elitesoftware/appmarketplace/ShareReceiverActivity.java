package com.elitesoftware.appmarketplace;
import android.app.Activity;
import android.content.Intent;
import android.os.Bundle;

public class ShareReceiverActivity extends Activity {
    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        Intent intent = getIntent();
        if (Intent.ACTION_SEND.equals(intent.getAction()) && "text/plain".equals(intent.getType())) {
            String sharedText = intent.getStringExtra(Intent.EXTRA_TEXT);
            if (sharedText != null) {
                Intent serviceIntent = new Intent(this, FloatingWidgetService.class);
                if (sharedText.startsWith("http")) {
                    serviceIntent.putExtra("url", sharedText);
                    serviceIntent.putExtra("title", "Elite Web");
                } else {
                    serviceIntent.putExtra("url", "https://google.com/search?q=" + sharedText);
                    serviceIntent.putExtra("title", "Elite Search");
                }
                startService(serviceIntent);
            }
        }
        finish();
    }
}
