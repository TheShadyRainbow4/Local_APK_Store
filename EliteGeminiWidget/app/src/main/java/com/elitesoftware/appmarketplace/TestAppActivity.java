package com.elitesoftware.appmarketplace;

import android.app.Activity;
import android.os.Bundle;
import android.widget.TextView;
import android.graphics.Color;
import android.view.Gravity;

public class TestAppActivity extends Activity {
    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        
        TextView textView = new TextView(this);
        textView.setText("Hello from TestAppActivity running inside the Elite Window Framework!");
        textView.setTextSize(24);
        textView.setTextColor(Color.WHITE);
        textView.setBackgroundColor(Color.DKGRAY);
        textView.setGravity(Gravity.CENTER);
        textView.setPadding(20, 20, 20, 20);
        
        setContentView(textView);
    }
}
