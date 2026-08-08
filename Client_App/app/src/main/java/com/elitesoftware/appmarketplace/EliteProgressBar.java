package com.elitesoftware.appmarketplace;

import android.animation.ValueAnimator;
import android.content.Context;
import android.graphics.Canvas;
import android.graphics.Color;
import android.graphics.LinearGradient;
import android.graphics.Paint;
import android.graphics.Path;
import android.graphics.RectF;
import android.graphics.Shader;
import android.util.AttributeSet;
import android.view.View;
import android.view.animation.LinearInterpolator;

public class EliteProgressBar extends View {
    private int progress = 0;
    private int max = 100;

    private Paint backgroundPaint;
    private Paint progressPaint;
    private Paint stripePaint;
    private Paint glossPaint;
    private Paint borderPaint;

    private RectF bounds = new RectF();
    private RectF progressBounds = new RectF();
    
    private float stripeOffset = 0f;
    private ValueAnimator animator;

    public EliteProgressBar(Context context) {
        super(context);
        init();
    }

    public EliteProgressBar(Context context, AttributeSet attrs) {
        super(context, attrs);
        init();
    }

    private void init() {
        backgroundPaint = new Paint(Paint.ANTI_ALIAS_FLAG);
        
        progressPaint = new Paint(Paint.ANTI_ALIAS_FLAG);
        
        stripePaint = new Paint(Paint.ANTI_ALIAS_FLAG);
        stripePaint.setColor(Color.argb(50, 255, 255, 255));
        
        glossPaint = new Paint(Paint.ANTI_ALIAS_FLAG);
        
        borderPaint = new Paint(Paint.ANTI_ALIAS_FLAG);
        borderPaint.setStyle(Paint.Style.STROKE);
        borderPaint.setStrokeWidth(2f);
        borderPaint.setColor(Color.parseColor("#1a1a1a"));

        animator = ValueAnimator.ofFloat(0f, 40f);
        animator.setDuration(1000);
        animator.setRepeatCount(ValueAnimator.INFINITE);
        animator.setInterpolator(new LinearInterpolator());
        animator.addUpdateListener(a -> {
            stripeOffset = (float) a.getAnimatedValue();
            invalidate();
        });
    }

    public void setProgress(int progress) {
        this.progress = Math.max(0, Math.min(progress, max));
        invalidate();
    }
    
    public void setMax(int max) {
        this.max = max;
    }

    @Override
    protected void onAttachedToWindow() {
        super.onAttachedToWindow();
        animator.start();
    }

    @Override
    protected void onDetachedFromWindow() {
        super.onDetachedFromWindow();
        animator.cancel();
    }

    @Override
    protected void onSizeChanged(int w, int h, int oldw, int oldh) {
        super.onSizeChanged(w, h, oldw, oldh);
        bounds.set(0, 0, w, h);
        
        backgroundPaint.setShader(new LinearGradient(0, 0, 0, h,
                new int[]{Color.parseColor("#1e1e1e"), Color.parseColor("#3a3a3a"), Color.parseColor("#1e1e1e")},
                null, Shader.TileMode.CLAMP));
                
        progressPaint.setShader(new LinearGradient(0, 0, 0, h,
                new int[]{Color.parseColor("#004d00"), Color.parseColor("#00b300"), Color.parseColor("#004d00")},
                null, Shader.TileMode.CLAMP));
                
        glossPaint.setShader(new LinearGradient(0, 0, 0, h / 2f,
                Color.argb(120, 255, 255, 255), Color.argb(0, 255, 255, 255),
                Shader.TileMode.CLAMP));
    }

    @Override
    protected void onDraw(Canvas canvas) {
        super.onDraw(canvas);
        float radius = getHeight() / 2f;
        
        // Background
        canvas.drawRoundRect(bounds, radius, radius, backgroundPaint);
        
        // Progress
        float progressWidth = (bounds.width() * progress) / max;
        if (progressWidth > 0) {
            progressBounds.set(0, 0, progressWidth, getHeight());
            canvas.drawRoundRect(progressBounds, radius, radius, progressPaint);
            
            // Stripes
            canvas.save();
            canvas.clipRect(progressBounds);
            Path stripePath = new Path();
            float stripeWidth = 20f;
            float spacing = 20f;
            for (float x = -getHeight() + stripeOffset; x < progressWidth; x += stripeWidth + spacing) {
                stripePath.reset();
                stripePath.moveTo(x, getHeight());
                stripePath.lineTo(x + stripeWidth, getHeight());
                stripePath.lineTo(x + stripeWidth + getHeight(), 0);
                stripePath.lineTo(x + getHeight(), 0);
                stripePath.close();
                canvas.drawPath(stripePath, stripePaint);
            }
            canvas.restore();
            
            // Gloss
            canvas.drawRoundRect(progressBounds, radius, radius, glossPaint);
        }
        
        // Border
        canvas.drawRoundRect(bounds, radius, radius, borderPaint);
    }
}
