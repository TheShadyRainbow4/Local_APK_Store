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
        String pkg = null;
        
        if (intent != null) {
            if (intent.hasExtra("url")) {
                url = intent.getStringExtra("url");
                title = intent.getStringExtra("title");
            }
            if (intent.hasExtra("package")) {
                pkg = intent.getStringExtra("package");
                title = intent.getStringExtra("title");
            }
        }
        createWindow(url, title, pkg);
        return START_STICKY;
    }

    private void createWindow(String url, String titleText, String pkg) {
        final LinearLayout mFloatingWidget = new LinearLayout(this);
        mFloatingWidget.setOrientation(LinearLayout.VERTICAL);
        mFloatingWidget.setBackgroundColor(Color.TRANSPARENT);

        // Windows Vista Aero Glass Style Frame
        GradientDrawable frameDrawable = new GradientDrawable();
        frameDrawable.setColor(Color.argb(90, 0, 0, 0)); // Dark glassy body
        frameDrawable.setStroke(2, Color.argb(200, 255, 255, 255)); // Bright glass edge
        frameDrawable.setCornerRadii(new float[]{20, 20, 20, 20, 20, 20, 20, 20});

        final LinearLayout windowFrame = new LinearLayout(this);
        windowFrame.setOrientation(LinearLayout.VERTICAL);
        windowFrame.setBackground(frameDrawable);
        windowFrame.setPadding(8, 8, 8, 8);
        windowFrame.setLayoutParams(new LinearLayout.LayoutParams(LinearLayout.LayoutParams.MATCH_PARENT, LinearLayout.LayoutParams.MATCH_PARENT));

        // Aero Titlebar
        GradientDrawable titleDrawable = new GradientDrawable(
                GradientDrawable.Orientation.TOP_BOTTOM,
                new int[]{Color.argb(140, 255, 255, 255), Color.argb(60, 255, 255, 255), Color.argb(40, 150, 150, 150)}
        );
        titleDrawable.setCornerRadii(new float[]{16, 16, 16, 16, 0, 0, 0, 0});
        
        final LinearLayout header = new LinearLayout(this);
        header.setBackground(titleDrawable);
        header.setOrientation(LinearLayout.HORIZONTAL);
        header.setGravity(Gravity.CENTER_VERTICAL);
        header.setPadding(15, 4, 8, 4);

        TextView titleView = new TextView(this);
        titleView.setText(titleText);
        titleView.setTextColor(Color.BLACK);
        titleView.setTypeface(null, Typeface.BOLD);
        titleView.setShadowLayer(3, 1, 1, Color.WHITE);
        titleView.setSingleLine(true);
        titleView.setEllipsize(android.text.TextUtils.TruncateAt.END);
        LinearLayout.LayoutParams titleParams = new LinearLayout.LayoutParams(ViewGroup.LayoutParams.WRAP_CONTENT, ViewGroup.LayoutParams.WRAP_CONTENT, 1.0f);
        header.addView(titleView, titleParams);

        SeekBar alphaSlider = new SeekBar(this);
        alphaSlider.setMax(255);
        alphaSlider.setProgress(255);
        alphaSlider.setVisibility(View.GONE);
        LinearLayout.LayoutParams sliderParams = new LinearLayout.LayoutParams(0, ViewGroup.LayoutParams.WRAP_CONTENT, 1.0f);
        header.addView(alphaSlider, sliderParams);

        // Toggle slider is now handled by custom drag listener logic

        // Vista Style Window Buttons
        LinearLayout buttonContainer = new LinearLayout(this);
        buttonContainer.setOrientation(LinearLayout.HORIZONTAL);
        buttonContainer.setPadding(0, 0, 0, 0);

        Button minBtn = createVistaButton("_", false, false);
        Button maxBtn = createVistaButton("\u25A1", false, true);
        Button closeBtn = createVistaButton("X", true, false);

        buttonContainer.addView(minBtn);
        buttonContainer.addView(maxBtn);
        buttonContainer.addView(closeBtn);
        header.addView(buttonContainer);

        View contentView = null;
        if ("elite_settings".equals(pkg) || "com.android.settings".equals(pkg)) {
            // Custom Elite Settings View
            LinearLayout settingsLayout = new LinearLayout(this);
            settingsLayout.setOrientation(LinearLayout.VERTICAL);
            settingsLayout.setPadding(20, 20, 20, 20);
            settingsLayout.setBackgroundColor(Color.argb(230, 250, 250, 250));
            
            TextView settingsTitle = new TextView(this);
            settingsTitle.setText("Elite Window Framework - Global Settings");
            settingsTitle.setTextSize(18);
            settingsTitle.setTypeface(null, Typeface.BOLD);
            settingsTitle.setTextColor(Color.BLACK);
            
            TextView infoText = new TextView(this);
            infoText.setText("Default Opacity: 100%\nSaved Logins: 0\nAero Theme: Enabled\nVirtual Display: Active");
            infoText.setPadding(0, 20, 0, 0);
            infoText.setTextColor(Color.DKGRAY);
            
            settingsLayout.addView(settingsTitle);
            settingsLayout.addView(infoText);
            contentView = settingsLayout;
        } else if (pkg != null && !pkg.isEmpty()) {
            final android.view.TextureView textureView = new android.view.TextureView(this);
            textureView.setSurfaceTextureListener(new android.view.TextureView.SurfaceTextureListener() {
                android.hardware.display.VirtualDisplay virtualDisplay;
                android.view.Surface mSurface;
                @Override
                public void onSurfaceTextureAvailable(android.graphics.SurfaceTexture surface, int width, int height) {
                    mSurface = new android.view.Surface(surface);
                    android.hardware.display.DisplayManager displayManager = (android.hardware.display.DisplayManager) getSystemService(android.content.Context.DISPLAY_SERVICE);
                    virtualDisplay = displayManager.createVirtualDisplay(
                            "EliteVirtualDisplay",
                            width > 0 ? width : 700, height > 0 ? height : 900, 160,
                            mSurface,
                            android.hardware.display.DisplayManager.VIRTUAL_DISPLAY_FLAG_PUBLIC | android.hardware.display.DisplayManager.VIRTUAL_DISPLAY_FLAG_OWN_CONTENT_ONLY
                    );

                    Intent launchIntent = getPackageManager().getLaunchIntentForPackage(pkg);
                    if (launchIntent == null && pkg.equals("com.android.settings")) {
                        launchIntent = new Intent(android.provider.Settings.ACTION_SETTINGS);
                    } else if (pkg.equals("com.elitesoftware.appmarketplace.testapp")) {
                        launchIntent = new Intent(FloatingWidgetService.this, TestAppActivity.class);
                    }
                    if (launchIntent != null) {
                        launchIntent.addFlags(Intent.FLAG_ACTIVITY_NEW_TASK | Intent.FLAG_ACTIVITY_MULTIPLE_TASK | Intent.FLAG_ACTIVITY_CLEAR_TOP);
                        android.app.ActivityOptions options = android.app.ActivityOptions.makeBasic();
                        try {
                            options.setLaunchDisplayId(virtualDisplay.getDisplay().getDisplayId());
                            startActivity(launchIntent, options.toBundle());
                        } catch (Exception e) {
                            android.widget.Toast.makeText(FloatingWidgetService.this, "Launch Failed: " + e.getMessage(), android.widget.Toast.LENGTH_SHORT).show();
                        }
                    }
                }
                @Override
                public void onSurfaceTextureSizeChanged(android.graphics.SurfaceTexture surface, int width, int height) {
                    if (virtualDisplay != null && width > 0 && height > 0) {
                        virtualDisplay.resize(width, height, 160);
                    }
                }
                @Override
                public boolean onSurfaceTextureDestroyed(android.graphics.SurfaceTexture surface) {
                    if (virtualDisplay != null) {
                        virtualDisplay.release();
                    }
                    if (mSurface != null) {
                        mSurface.release();
                    }
                    return true;
                }
                @Override
                public void onSurfaceTextureUpdated(android.graphics.SurfaceTexture surface) {
                }
            });
            contentView = textureView;
        } else {
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
            contentView = webView;
        }

        final ImageView collapsedIcon = new ImageView(this);
        collapsedIcon.setImageResource(R.mipmap.ic_launcher);
        collapsedIcon.setVisibility(View.GONE);

        // Grab Handle for Resizing
        ImageView grabHandle = new ImageView(this);
        grabHandle.setImageResource(android.R.drawable.ic_menu_sort_by_size);
        LinearLayout.LayoutParams grabParams = new LinearLayout.LayoutParams(60, 60);
        grabParams.gravity = Gravity.BOTTOM | Gravity.RIGHT;
        
        // Add content
        LinearLayout contentLayout = new LinearLayout(this);
        contentLayout.setOrientation(LinearLayout.VERTICAL);
        contentLayout.addView(contentView, new LinearLayout.LayoutParams(LinearLayout.LayoutParams.MATCH_PARENT, 0, 1.0f));
        contentLayout.addView(grabHandle, grabParams);

        windowFrame.addView(header);
        windowFrame.addView(contentLayout, new LinearLayout.LayoutParams(LinearLayout.LayoutParams.MATCH_PARENT, 0, 1.0f));
        
        mFloatingWidget.addView(windowFrame);
        mFloatingWidget.addView(collapsedIcon, new LinearLayout.LayoutParams(150, 150));

        int layoutFlag;
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.O) {
            layoutFlag = WindowManager.LayoutParams.TYPE_APPLICATION_OVERLAY;
        } else {
            layoutFlag = WindowManager.LayoutParams.TYPE_PHONE;
        }

        final WindowManager.LayoutParams params = new WindowManager.LayoutParams(
                800, 1000, layoutFlag,
                WindowManager.LayoutParams.FLAG_NOT_TOUCH_MODAL | WindowManager.LayoutParams.FLAG_WATCH_OUTSIDE_TOUCH,
                PixelFormat.TRANSLUCENT);

        params.gravity = Gravity.TOP | Gravity.LEFT;
        params.x = (activeWindows.size() * 50) % 300; 
        params.y = 100 + (activeWindows.size() * 50) % 300;

        mWindowManager.addView(mFloatingWidget, params);
        activeWindows.add(mFloatingWidget);

        // Set entire window alpha
        alphaSlider.setOnSeekBarChangeListener(new SeekBar.OnSeekBarChangeListener() {
            @Override public void onProgressChanged(SeekBar seekBar, int progress, boolean fromUser) {
                // Controls the entire popup window opacity
                mFloatingWidget.setAlpha(progress / 255.0f);
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
        final int[] oldSize = new int[]{800, 1000};
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
            private android.os.Handler handler = new android.os.Handler(android.os.Looper.getMainLooper());
            private Runnable longPressRunnable = new Runnable() {
                @Override
                public void run() {
                    if (!isMoving) {
                        if (alphaSlider.getVisibility() == View.VISIBLE) {
                            alphaSlider.setVisibility(View.GONE);
                            titleParams.weight = 1.0f;
                        } else {
                            alphaSlider.setVisibility(View.VISIBLE);
                            titleParams.weight = 0.0f;
                        }
                        titleView.setLayoutParams(titleParams);
                    }
                }
            };
            
            @Override
            public boolean onTouch(View v, MotionEvent event) {
                switch (event.getAction()) {
                    case MotionEvent.ACTION_DOWN:
                        initialX = params.x; initialY = params.y;
                        initialTouchX = event.getRawX(); initialTouchY = event.getRawY();
                        isMoving = false;
                        handler.postDelayed(longPressRunnable, 500);
                        return true; // Consume event
                    case MotionEvent.ACTION_MOVE:
                        if (!isMoving && (Math.abs(event.getRawX() - initialTouchX) > 10 || Math.abs(event.getRawY() - initialTouchY) > 10)) {
                            isMoving = true;
                            handler.removeCallbacks(longPressRunnable); // Cancel long press
                            // Un-maximize if dragging
                            if (params.width == WindowManager.LayoutParams.MATCH_PARENT) {
                                params.width = oldSize[0];
                                params.height = oldSize[1];
                                // Adjust position so mouse is roughly in center of restored header
                                initialX = (int) (event.getRawX() - (params.width / 2));
                                initialY = (int) event.getRawY() - 30; // offset for touch
                                params.x = initialX;
                                params.y = initialY;
                                // Need to update initialTouch to not jump immediately
                                initialTouchX = event.getRawX();
                                initialTouchY = event.getRawY();
                            }
                        }
                        if (isMoving) {
                            params.x = initialX + (int) (event.getRawX() - initialTouchX);
                            params.y = initialY + (int) (event.getRawY() - initialTouchY);
                            mWindowManager.updateViewLayout(mFloatingWidget, params);
                        }
                        return true;
                    case MotionEvent.ACTION_UP:
                    case MotionEvent.ACTION_CANCEL:
                        handler.removeCallbacks(longPressRunnable);
                        if (!isMoving && v == collapsedIcon) {
                            toggleCollapse.onClick(v);
                        }
                        return true;
                }
                return false;
            }
        };
        header.setOnTouchListener(dragListener);
        titleView.setOnTouchListener(dragListener);
        collapsedIcon.setOnTouchListener(dragListener);

        // Maximize logic
        maxBtn.setOnClickListener(v -> {
            if (params.width == WindowManager.LayoutParams.MATCH_PARENT) {
                params.width = oldSize[0];
                params.height = oldSize[1];
                params.x = 100;
                params.y = 100;
            } else {
                oldSize[0] = params.width;
                oldSize[1] = params.height;
                params.width = WindowManager.LayoutParams.MATCH_PARENT;
                params.height = WindowManager.LayoutParams.MATCH_PARENT;
                params.x = 0;
                params.y = 0;
            }
            mWindowManager.updateViewLayout(mFloatingWidget, params);
        });

        // Resize logic (Grab Handle)
        grabHandle.setOnTouchListener(new View.OnTouchListener() {
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

    private Button createVistaButton(String text, boolean isClose, boolean isMax) {
        Button btn = new Button(this);
        btn.setText(text);
        btn.setSingleLine(true);
        btn.setTextSize(isMax ? 12 : 14);
        
        GradientDrawable bg = new GradientDrawable();
        if (isClose) {
            bg.setColors(new int[]{Color.argb(200, 200, 50, 50), Color.argb(255, 150, 10, 10)});
            btn.setTextColor(Color.WHITE);
        } else {
            bg.setColors(new int[]{Color.argb(40, 255, 255, 255), Color.argb(10, 255, 255, 255)});
            btn.setTextColor(Color.WHITE);
        }
        bg.setCornerRadius(6); // Slightly rounded buttons
        bg.setStroke(1, Color.argb(120, 255, 255, 255));
        
        btn.setBackground(bg);
        btn.setTypeface(null, Typeface.BOLD);
        btn.setPadding(0, 0, 0, 0);
        
        // Make buttons rectangular like Vista
        int width = isClose ? 75 : 55;
        LinearLayout.LayoutParams lp = new LinearLayout.LayoutParams(width, 42);
        lp.setMargins(0, 0, 0, 0); // No gaps between buttons in Vista
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


