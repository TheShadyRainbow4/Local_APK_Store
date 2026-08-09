package com.elitesoftware.appmarketplace;

import android.app.Activity;
import android.content.Intent;
import android.os.Bundle;

public class CalculatorLauncherActivity extends Activity {
    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        Intent intent = new Intent(this, FloatingWidgetService.class);
        // Try the standard Google Calculator package, which is most common
        intent.putExtra("package", "com.google.android.calculator");
        intent.putExtra("title", "Calculator");
        startService(intent);
        finish();
    }
}
