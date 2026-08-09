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
        frameDrawable.setColor(Color.argb(120, 255, 255, 255)); // Semi-transparent glass body
        frameDrawable.setStroke(2, Color.argb(180, 255, 255, 255)); // Bright glass edge
        frameDrawable.setCornerRadii(new float[]{20, 20, 20, 20, 20, 20, 20, 20});

        final LinearLayout windowFrame = new LinearLayout(this);
        windowFrame.setOrientation(LinearLayout.VERTICAL);
        windowFrame.setBackground(frameDrawable);
        windowFrame.setPadding(8, 8, 8, 8);
        windowFrame.setLayoutParams(new LinearLayout.LayoutParams(LinearLayout.LayoutParams.MATCH_PARENT, LinearLayout.LayoutParams.MATCH_PARENT));

        // Aero Titlebar
        GradientDrawable titleDrawable = new GradientDrawable(
                GradientDrawable.Orientation.TOP_BOTTOM,
                new int[]{Color.argb(160, 255, 255, 255), Color.argb(80, 200, 220, 255), Color.argb(120, 150, 190, 255)}
        );
        titleDrawable.setCornerRadii(new float[]{16, 16, 16, 16, 0, 0, 0, 0});
        
        final LinearLayout header = new LinearLayout(this);
        header.setBackground(titleDrawable);
        header.setOrientation(LinearLayout.HORIZONTAL);
        header.setGravity(Gravity.CENTER_VERTICAL);
        header.setPadding(15, 8, 15, 8);

        TextView titleView = new TextView(this);
        titleView.setText(titleText);
        titleView.setTextColor(Color.BLACK);
        titleView.setTypeface(null, Typeface.BOLD);
        titleView.setShadowLayer(3, 1, 1, Color.WHITE);
        LinearLayout.LayoutParams titleParams = new LinearLayout.LayoutParams(0, ViewGroup.LayoutParams.WRAP_CONTENT, 1.0f);
        header.addView(titleView, titleParams);

        // Transparency Slider
        SeekBar alphaSlider = new SeekBar(this);
        alphaSlider.setMax(255);
        alphaSlider.setProgress(255);
        LinearLayout.LayoutParams sliderParams = new LinearLayout.LayoutParams(180, ViewGroup.LayoutParams.WRAP_CONTENT);
        header.addView(alphaSlider, sliderParams);

        // Vista Style Window Buttons
        LinearLayout buttonContainer = new LinearLayout(this);
        buttonContainer.setOrientation(LinearLayout.HORIZONTAL);

        Button minBtn = createVistaButton("_", false);
        Button maxBtn = createVistaButton("\u25A1", false);
        Button closeBtn = createVistaButton("X", true);

        buttonContainer.addView(minBtn);
        buttonContainer.addView(maxBtn);
        buttonContainer.addView(closeBtn);
        header.addView(buttonContainer);

        View contentView = null;
        if (pkg != null && !pkg.isEmpty()) {
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
                            android.hardware.display.DisplayManager.VIRTUAL_DISPLAY_FLAG_PUBLIC
                    );

                    Intent launchIntent = getPackageManager().getLaunchIntentForPackage(pkg);
                    if (launchIntent != null) {
                        launchIntent.addFlags(Intent.FLAG_ACTIVITY_NEW_TASK | Intent.FLAG_ACTIVITY_MULTIPLE_TASK);
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

    private Button createVistaButton(String text, boolean isClose) {
        Button btn = new Button(this);
        btn.setText(text);
        btn.setSingleLine(true);
        btn.setTextSize(14);
        
        GradientDrawable bg = new GradientDrawable();
        if (isClose) {
            bg.setColors(new int[]{Color.argb(100, 255, 100, 100), Color.argb(120, 200, 20, 20)}); // More transparent red
            btn.setTextColor(Color.WHITE);
        } else {
            bg.setColors(new int[]{Color.argb(50, 255, 255, 255), Color.argb(80, 150, 180, 220)}); // Transparent
            btn.setTextColor(Color.BLACK);
        }
        bg.setCornerRadius(6);
        bg.setStroke(1, Color.argb(100, 255, 255, 255));
        
        btn.setBackground(bg);
        btn.setTypeface(null, Typeface.BOLD);
        btn.setPadding(0, 0, 0, 0);
        
        LinearLayout.LayoutParams lp = new LinearLayout.LayoutParams(70, 70); // Fixed size
        lp.setMargins(6, 0, 6, 0);
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


