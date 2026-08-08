package com.elitesoftware.appmarketplace;

import android.app.Service;
import android.app.usage.UsageStats;
import android.app.usage.UsageStatsManager;
import android.content.Context;
import android.content.Intent;
import android.graphics.PixelFormat;
import android.os.Build;
import android.os.Handler;
import android.os.IBinder;
import android.os.Looper;
import android.view.Gravity;
import android.view.MotionEvent;
import android.view.View;
import android.view.WindowManager;
import android.webkit.WebSettings;
import android.webkit.WebView;
import android.webkit.WebViewClient;
import android.widget.Button;
import android.widget.LinearLayout;
import android.widget.Toast;

import java.util.List;
import java.util.Timer;
import java.util.TimerTask;

public class FloatingWidgetService extends Service {
    private WindowManager mWindowManager;
    private View mFloatingWidget;
    private WindowManager.LayoutParams params;
    private LinearLayout header;
    private WebView webView;
    private boolean isPinned = false;
    
    private Timer timer;
    private Handler handler = new Handler(Looper.getMainLooper());

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
        
        Button pinBtn = new Button(this);
        pinBtn.setText("Pin");
        pinBtn.setOnClickListener(v -> {
            isPinned = true;
            header.setVisibility(View.GONE);
            Toast.makeText(FloatingWidgetService.this, "Pinned to Launcher!", Toast.LENGTH_SHORT).show();
            // Optional: You could lock touches or keep it interactive. We keep WebView interactive.
        });
        
        header.addView(closeBtn);
        header.addView(resizeBtn);
        header.addView(pinBtn);
        
        webView = new WebView(this);
        WebSettings webSettings = webView.getSettings();
        webSettings.setJavaScriptEnabled(true);
        webSettings.setDomStorageEnabled(true);
        webSettings.setUserAgentString("Mozilla/5.0 (Linux; Android 10) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.120 Mobile Safari/537.36");
        webView.setWebViewClient(new WebViewClient());
        webView.loadUrl("https://gemini.google.com/");
        
        ((LinearLayout)mFloatingWidget).addView(header);
        ((LinearLayout)mFloatingWidget).addView(webView, new LinearLayout.LayoutParams(LinearLayout.LayoutParams.MATCH_PARENT, LinearLayout.LayoutParams.MATCH_PARENT));
        
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

        header.setOnTouchListener(new View.OnTouchListener() {
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
                }
                return false;
            }
        });
        
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
        
        startForegroundAppMonitor();
    }
    
    private void startForegroundAppMonitor() {
        timer = new Timer();
        timer.scheduleAtFixedRate(new TimerTask() {
            @Override
            public void run() {
                if (!isPinned) return;
                
                String currentApp = getForegroundApp();
                boolean isLauncher = currentApp.contains("launcher") || 
                                     currentApp.equals("com.sec.android.app.launcher") || 
                                     currentApp.equals("com.elitesoftware.geminiwidget") ||
                                     currentApp.equals("com.android.systemui");
                                     
                handler.post(() -> {
                    if (isLauncher) {
                        mFloatingWidget.setVisibility(View.VISIBLE);
                    } else {
                        mFloatingWidget.setVisibility(View.GONE);
                    }
                });
            }
        }, 0, 500);
    }
    
    private String getForegroundApp() {
        UsageStatsManager usm = (UsageStatsManager) getSystemService(Context.USAGE_STATS_SERVICE);
        long time = System.currentTimeMillis();
        List<UsageStats> appList = usm.queryUsageStats(UsageStatsManager.INTERVAL_DAILY, time - 1000 * 1000, time);
        if (appList != null && appList.size() > 0) {
            UsageStats myStats = null;
            for (UsageStats usageStats : appList) {
                if (myStats == null || myStats.getLastTimeUsed() < usageStats.getLastTimeUsed()) {
                    myStats = usageStats;
                }
            }
            if (myStats != null) {
                return myStats.getPackageName();
            }
        }
        return "";
    }

    @Override
    public void onDestroy() {
        super.onDestroy();
        if (timer != null) timer.cancel();
        if (mFloatingWidget != null) mWindowManager.removeView(mFloatingWidget);
    }
}
