package com.elitesoftware.appmarketplace;

import android.app.Service;
import android.content.Intent;
import android.graphics.PixelFormat;
import android.os.Build;
import android.os.IBinder;
import android.view.Gravity;
import android.view.MotionEvent;
import android.view.View;
import android.view.WindowManager;
import android.webkit.WebSettings;
import android.webkit.WebView;
import android.webkit.WebViewClient;
import android.widget.Button;
import android.widget.ImageView;
import android.widget.LinearLayout;
import android.widget.Toast;

public class FloatingWidgetService extends Service {
    private WindowManager mWindowManager;
    private View mFloatingWidget;
    private WindowManager.LayoutParams params;
    private LinearLayout header;
    private WebView webView;
    private ImageView collapsedIcon;
    private boolean isCollapsed = false;

    @Override
    public IBinder onBind(Intent intent) { return null; }

    @Override
    public void onCreate() {
        super.onCreate();
        
        mFloatingWidget = new LinearLayout(this);
        ((LinearLayout)mFloatingWidget).setOrientation(LinearLayout.VERTICAL);
        ((LinearLayout)mFloatingWidget).setBackgroundColor(0x00000000);
        
        header = new LinearLayout(this);
        header.setBackgroundColor(0xFFDDDDDD);
        header.setOrientation(LinearLayout.HORIZONTAL);
        
        Button closeBtn = new Button(this);
        closeBtn.setText("X");
        closeBtn.setOnClickListener(v -> stopSelf());
        
        Button resizeBtn = new Button(this);
        resizeBtn.setText("Scale");
        
        Button minBtn = new Button(this);
        minBtn.setText("_");
        minBtn.setOnClickListener(v -> toggleCollapse());
        
        header.addView(closeBtn);
        header.addView(minBtn);
        header.addView(resizeBtn);
        
        webView = new WebView(this);
        WebSettings webSettings = webView.getSettings();
        webSettings.setJavaScriptEnabled(true);
        webSettings.setDomStorageEnabled(true);
        webSettings.setUserAgentString("Mozilla/5.0 (Linux; Android 10) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.120 Mobile Safari/537.36");
        webView.setWebViewClient(new WebViewClient());
        webView.loadUrl("https://gemini.google.com/");
        
        collapsedIcon = new ImageView(this);
        collapsedIcon.setImageResource(R.mipmap.ic_launcher);
        collapsedIcon.setVisibility(View.GONE);
        collapsedIcon.setOnClickListener(v -> toggleCollapse());
        
        ((LinearLayout)mFloatingWidget).addView(header);
        ((LinearLayout)mFloatingWidget).addView(webView, new LinearLayout.LayoutParams(LinearLayout.LayoutParams.MATCH_PARENT, LinearLayout.LayoutParams.MATCH_PARENT));
        ((LinearLayout)mFloatingWidget).addView(collapsedIcon, new LinearLayout.LayoutParams(150, 150));
        
        int layoutFlag;
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.O) {
            layoutFlag = WindowManager.LayoutParams.TYPE_APPLICATION_OVERLAY;
        } else {
            layoutFlag = WindowManager.LayoutParams.TYPE_PHONE;
        }

        params = new WindowManager.LayoutParams(
                600, 800, layoutFlag,
                WindowManager.LayoutParams.FLAG_NOT_TOUCH_MODAL | WindowManager.LayoutParams.FLAG_WATCH_OUTSIDE_TOUCH,
                PixelFormat.TRANSLUCENT);

        params.gravity = Gravity.TOP | Gravity.LEFT;
        params.x = 0; params.y = 100;

        mWindowManager = (WindowManager) getSystemService(WINDOW_SERVICE);
        mWindowManager.addView(mFloatingWidget, params);

        View.OnTouchListener dragListener = new View.OnTouchListener() {
            private int initialX, initialY;
            private float initialTouchX, initialTouchY;

            @Override
            public boolean onTouch(View v, MotionEvent event) {
                switch (event.getAction()) {
                    case MotionEvent.ACTION_DOWN:
                        initialX = params.x; initialY = params.y;
                        initialTouchX = event.getRawX(); initialTouchY = event.getRawY();
                        return true;
                    case MotionEvent.ACTION_MOVE:
                        params.x = initialX + (int) (event.getRawX() - initialTouchX);
                        params.y = initialY + (int) (event.getRawY() - initialTouchY);
                        mWindowManager.updateViewLayout(mFloatingWidget, params);
                        return true;
                    case MotionEvent.ACTION_UP:
                        // Trigger click if it was a quick tap on the collapsed icon
                        if (isCollapsed && Math.abs(event.getRawX() - initialTouchX) < 10 && Math.abs(event.getRawY() - initialTouchY) < 10) {
                            toggleCollapse();
                        }
                        return true;
                }
                return false;
            }
        };

        header.setOnTouchListener(dragListener);
        collapsedIcon.setOnTouchListener(dragListener);
        
        resizeBtn.setOnTouchListener(new View.OnTouchListener() {
            private int initialWidth, initialHeight;
            private float initialTouchX, initialTouchY;

            @Override
            public boolean onTouch(View v, MotionEvent event) {
                switch (event.getAction()) {
                    case MotionEvent.ACTION_DOWN:
                        initialWidth = params.width; initialHeight = params.height;
                        initialTouchX = event.getRawX(); initialTouchY = event.getRawY();
                        return true;
                    case MotionEvent.ACTION_MOVE:
                        params.width = initialWidth + (int) (event.getRawX() - initialTouchX);
                        params.height = initialHeight + (int) (event.getRawY() - initialTouchY);
                        if (params.width < 300) params.width = 300;
                        if (params.height < 400) params.height = 400;
                        mWindowManager.updateViewLayout(mFloatingWidget, params);
                        return true;
                }
                return false;
            }
        });
    }
    
    private int oldWidth = 600;
    private int oldHeight = 800;

    private void toggleCollapse() {
        isCollapsed = !isCollapsed;
        if (isCollapsed) {
            oldWidth = params.width;
            oldHeight = params.height;
            header.setVisibility(View.GONE);
            webView.setVisibility(View.GONE);
            collapsedIcon.setVisibility(View.VISIBLE);
            params.width = WindowManager.LayoutParams.WRAP_CONTENT;
            params.height = WindowManager.LayoutParams.WRAP_CONTENT;
        } else {
            header.setVisibility(View.VISIBLE);
            webView.setVisibility(View.VISIBLE);
            collapsedIcon.setVisibility(View.GONE);
            params.width = oldWidth;
            params.height = oldHeight;
        }
        mWindowManager.updateViewLayout(mFloatingWidget, params);
    }

    @Override
    public void onDestroy() {
        super.onDestroy();
        if (mFloatingWidget != null) mWindowManager.removeView(mFloatingWidget);
    }
}
