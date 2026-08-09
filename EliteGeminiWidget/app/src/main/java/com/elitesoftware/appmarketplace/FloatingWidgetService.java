package com.elitesoftware.appmarketplace;

import android.app.Service;
import android.content.Intent;
import android.graphics.Color;
import android.graphics.PixelFormat;
import android.graphics.Typeface;
import android.graphics.drawable.GradientDrawable;
import android.os.Build;
import android.os.IBinder;
import android.view.Gravity;
import android.view.MotionEvent;
import android.view.View;
import android.view.ViewGroup;
import android.view.WindowManager;
import android.webkit.CookieManager;
import android.webkit.WebSettings;
import android.webkit.WebView;
import android.webkit.WebViewClient;
import android.widget.Button;
import android.widget.ImageView;
import android.widget.LinearLayout;
import android.widget.SeekBar;
import android.widget.TextView;
import java.util.ArrayList;
import java.util.List;

public class FloatingWidgetService extends Service {
    private WindowManager mWindowManager;
    private List<View> activeWindows = new ArrayList<>();

    @Override
    public IBinder onBind(Intent intent) { return null; }

    @Override
    public void onCreate() {
        super.onCreate();
        mWindowManager = (WindowManager) getSystemService(WINDOW_SERVICE);
    }

    @Override
    public int onStartCommand(Intent intent, int flags, int startId) {
        String url = "https://gemini.google.com/";
        String title = "Elite Gemini";
        if (intent != null && intent.hasExtra("url")) {
            url = intent.getStringExtra("url");
            title = intent.getStringExtra("title");
        }
        createWindow(url, title);
        return START_STICKY;
    }

    private void createWindow(String url, String titleText) {
        final LinearLayout mFloatingWidget = new LinearLayout(this);
        mFloatingWidget.setOrientation(LinearLayout.VERTICAL);
        mFloatingWidget.setBackgroundColor(Color.TRANSPARENT);

        // Windows Vista/7 Style Frame
        GradientDrawable frameDrawable = new GradientDrawable();
        frameDrawable.setColor(Color.argb(230, 240, 240, 240));
        frameDrawable.setStroke(4, Color.argb(255, 150, 170, 200));
        frameDrawable.setCornerRadius(16);

        final LinearLayout windowFrame = new LinearLayout(this);
        windowFrame.setOrientation(LinearLayout.VERTICAL);
        windowFrame.setBackground(frameDrawable);
        windowFrame.setPadding(8, 8, 8, 8);
        windowFrame.setLayoutParams(new LinearLayout.LayoutParams(LinearLayout.LayoutParams.MATCH_PARENT, LinearLayout.LayoutParams.MATCH_PARENT));

        // Windows Vista/7 Style Titlebar
        GradientDrawable titleDrawable = new GradientDrawable(
                GradientDrawable.Orientation.TOP_BOTTOM,
                new int[]{Color.argb(255, 180, 200, 230), Color.argb(255, 130, 160, 200)}
        );
        titleDrawable.setCornerRadii(new float[]{12, 12, 12, 12, 0, 0, 0, 0});
        
        final LinearLayout header = new LinearLayout(this);
        header.setBackground(titleDrawable);
        header.setOrientation(LinearLayout.HORIZONTAL);
        header.setGravity(Gravity.CENTER_VERTICAL);
        header.setPadding(10, 5, 10, 5);

        TextView titleView = new TextView(this);
        titleView.setText(titleText);
        titleView.setTextColor(Color.BLACK);
        titleView.setTypeface(null, Typeface.BOLD);
        titleView.setShadowLayer(2, 1, 1, Color.WHITE);
        LinearLayout.LayoutParams titleParams = new LinearLayout.LayoutParams(0, ViewGroup.LayoutParams.WRAP_CONTENT, 1.0f);
        header.addView(titleView, titleParams);

        // Transparency Slider
        SeekBar alphaSlider = new SeekBar(this);
        alphaSlider.setMax(255);
        alphaSlider.setProgress(230);
        LinearLayout.LayoutParams sliderParams = new LinearLayout.LayoutParams(150, ViewGroup.LayoutParams.WRAP_CONTENT);
        header.addView(alphaSlider, sliderParams);

        // Windows 10 style rectangular buttons (on the right)
        LinearLayout buttonContainer = new LinearLayout(this);
        buttonContainer.setOrientation(LinearLayout.HORIZONTAL);

        Button minBtn = createWin10Button("_");
        Button resizeBtn = createWin10Button("\u25A1");
        Button closeBtn = createWin10Button("X");
        closeBtn.setTextColor(Color.RED);

        buttonContainer.addView(minBtn);
        buttonContainer.addView(resizeBtn);
        buttonContainer.addView(closeBtn);
        header.addView(buttonContainer);

        // WebView with persistent data
        final WebView webView = new WebView(this);
        WebSettings webSettings = webView.getSettings();
        webSettings.setJavaScriptEnabled(true);
        webSettings.setDomStorageEnabled(true);
        webSettings.setDatabaseEnabled(true);
        CookieManager.getInstance().setAcceptCookie(true);
        CookieManager.getInstance().setAcceptThirdPartyCookies(webView, true);
        webSettings.setUserAgentString("Mozilla/5.0 (Linux; Android 10) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.120 Mobile Safari/537.36");
        webView.setWebViewClient(new WebViewClient());
        webView.loadUrl(url);

        final ImageView collapsedIcon = new ImageView(this);
        collapsedIcon.setImageResource(R.mipmap.ic_launcher);
        collapsedIcon.setVisibility(View.GONE);

        windowFrame.addView(header);
        windowFrame.addView(webView, new LinearLayout.LayoutParams(LinearLayout.LayoutParams.MATCH_PARENT, 0, 1.0f));
        
        mFloatingWidget.addView(windowFrame);
        mFloatingWidget.addView(collapsedIcon, new LinearLayout.LayoutParams(150, 150));

        int layoutFlag;
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.O) {
            layoutFlag = WindowManager.LayoutParams.TYPE_APPLICATION_OVERLAY;
        } else {
            layoutFlag = WindowManager.LayoutParams.TYPE_PHONE;
        }

        final WindowManager.LayoutParams params = new WindowManager.LayoutParams(
                700, 900, layoutFlag,
                WindowManager.LayoutParams.FLAG_NOT_TOUCH_MODAL | WindowManager.LayoutParams.FLAG_WATCH_OUTSIDE_TOUCH,
                PixelFormat.TRANSLUCENT);

        params.gravity = Gravity.TOP | Gravity.LEFT;
        params.x = (activeWindows.size() * 50) % 300; 
        params.y = 100 + (activeWindows.size() * 50) % 300;

        mWindowManager.addView(mFloatingWidget, params);
        activeWindows.add(mFloatingWidget);

        // Alpha Slider Listener
        alphaSlider.setOnSeekBarChangeListener(new SeekBar.OnSeekBarChangeListener() {
            @Override public void onProgressChanged(SeekBar seekBar, int progress, boolean fromUser) {
                // Adjust the background alpha of the window frame
                frameDrawable.setAlpha(progress);
                windowFrame.setBackground(frameDrawable);
            }
            @Override public void onStartTrackingTouch(SeekBar seekBar) {}
            @Override public void onStopTrackingTouch(SeekBar seekBar) {}
        });

        // Close logic
        closeBtn.setOnClickListener(v -> {
            mWindowManager.removeView(mFloatingWidget);
            activeWindows.remove(mFloatingWidget);
            if (activeWindows.isEmpty()) stopSelf();
        });

        // Collapse logic
        final int[] oldSize = new int[]{700, 900};
        View.OnClickListener toggleCollapse = v -> {
            if (windowFrame.getVisibility() == View.VISIBLE) {
                oldSize[0] = params.width; oldSize[1] = params.height;
                windowFrame.setVisibility(View.GONE);
                collapsedIcon.setVisibility(View.VISIBLE);
                params.width = WindowManager.LayoutParams.WRAP_CONTENT;
                params.height = WindowManager.LayoutParams.WRAP_CONTENT;
            } else {
                windowFrame.setVisibility(View.VISIBLE);
                collapsedIcon.setVisibility(View.GONE);
                params.width = oldSize[0];
                params.height = oldSize[1];
            }
            mWindowManager.updateViewLayout(mFloatingWidget, params);
        };
        minBtn.setOnClickListener(toggleCollapse);
        collapsedIcon.setOnClickListener(toggleCollapse);

        // Drag logic
        View.OnTouchListener dragListener = new View.OnTouchListener() {
            private int initialX, initialY;
            private float initialTouchX, initialTouchY;
            private boolean isMoving = false;
            @Override
            public boolean onTouch(View v, MotionEvent event) {
                switch (event.getAction()) {
                    case MotionEvent.ACTION_DOWN:
                        initialX = params.x; initialY = params.y;
                        initialTouchX = event.getRawX(); initialTouchY = event.getRawY();
                        isMoving = false;
                        return true;
                    case MotionEvent.ACTION_MOVE:
                        if (Math.abs(event.getRawX() - initialTouchX) > 10 || Math.abs(event.getRawY() - initialTouchY) > 10) {
                            isMoving = true;
                        }
                        params.x = initialX + (int) (event.getRawX() - initialTouchX);
                        params.y = initialY + (int) (event.getRawY() - initialTouchY);
                        mWindowManager.updateViewLayout(mFloatingWidget, params);
                        return true;
                    case MotionEvent.ACTION_UP:
                        if (!isMoving && v == collapsedIcon) {
                            toggleCollapse.onClick(v);
                        }
                        return true;
                }
                return false;
            }
        };
        header.setOnTouchListener(dragListener);
        collapsedIcon.setOnTouchListener(dragListener);

        // Resize logic
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

    private Button createWin10Button(String text) {
        Button btn = new Button(this);
        btn.setText(text);
        btn.setBackgroundColor(Color.TRANSPARENT);
        btn.setTextColor(Color.BLACK);
        btn.setTypeface(null, Typeface.BOLD);
        btn.setPadding(20, 5, 20, 5);
        LinearLayout.LayoutParams lp = new LinearLayout.LayoutParams(ViewGroup.LayoutParams.WRAP_CONTENT, ViewGroup.LayoutParams.WRAP_CONTENT);
        lp.setMargins(2, 0, 2, 0);
        btn.setLayoutParams(lp);
        return btn;
    }

    @Override
    public void onDestroy() {
        super.onDestroy();
        for (View v : activeWindows) {
            if (v != null) mWindowManager.removeView(v);
        }
        activeWindows.clear();
    }
}

