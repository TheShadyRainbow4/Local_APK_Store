package com.elitesoftware.appmarketplace;

import android.app.Activity;
import android.content.Intent;
import android.os.Bundle;

public class TestAppLauncherActivity extends Activity {
    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        Intent intent = new Intent(this, FloatingWidgetService.class);
        intent.putExtra("package", "com.elitesoftware.appmarketplace.testapp");
        intent.putExtra("title", "Elite Test App");
        startService(intent);
        finish();
    }
}
