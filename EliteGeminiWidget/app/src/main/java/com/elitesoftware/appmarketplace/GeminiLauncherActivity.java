package com.elitesoftware.appmarketplace;
import android.app.Activity;
import android.content.Intent;
import android.os.Bundle;

public class GeminiLauncherActivity extends Activity {
    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        Intent intent = new Intent(this, FloatingWidgetService.class);
        intent.putExtra("url", "https://gemini.google.com/");
        intent.putExtra("title", "Elite Gemini");
        startService(intent);
        finish();
    }
}
