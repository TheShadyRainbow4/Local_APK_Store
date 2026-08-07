import re
with open('Client_App/app/src/main/java/com/elitesoftware/appmarketplace/AppDetailActivity.java', 'r') as f:
    code = f.read()

replacement = '''            if (app.has("icon") && !app.optString("icon").isEmpty()) {
                String iconVal = app.optString("icon");
                String iconUrl = iconVal.startsWith("local://") ? iconVal : "http://" + ip + ":8552/images/" + iconVal;
                loadImageAsync(iconUrl, detailIcon);
            }
            
            if (app.has("screenshots") && app.getJSONArray("screenshots").length() > 0) {
                TextView screenshotsLabel = findViewById(R.id.screenshotsLabel);
                android.widget.HorizontalScrollView screenshotsScrollView = findViewById(R.id.screenshotsScrollView);
                android.widget.LinearLayout screenshotsContainer = findViewById(R.id.screenshotsContainer);
                
                screenshotsLabel.setVisibility(View.VISIBLE);
                screenshotsScrollView.setVisibility(View.VISIBLE);
                
                org.json.JSONArray screenshots = app.getJSONArray("screenshots");
                for (int i = 0; i < screenshots.length(); i++) {
                    String screenshotName = screenshots.getString(i);
                    String screenshotUrl = "http://" + ip + ":8552/images/" + screenshotName;
                    
                    ImageView imgView = new ImageView(this);
                    android.widget.LinearLayout.LayoutParams lp = new android.widget.LinearLayout.LayoutParams(
                            (int)(120 * getResources().getDisplayMetrics().density), 
                            (int)(200 * getResources().getDisplayMetrics().density)
                    );
                    lp.setMargins(0, 0, (int)(8 * getResources().getDisplayMetrics().density), 0);
                    imgView.setLayoutParams(lp);
                    imgView.setScaleType(ImageView.ScaleType.CENTER_CROP);
                    imgView.setBackgroundColor(0xFFDDDDDD);
                    
                    final String finalUrl = screenshotUrl;
                    imgView.setOnClickListener(v -> {
                        android.content.Intent intent = new android.content.Intent(android.content.Intent.ACTION_VIEW);
                        intent.setDataAndType(android.net.Uri.parse(finalUrl), "image/*");
                        try { startActivity(intent); } catch(Exception e) {}
                    });
                    
                    screenshotsContainer.addView(imgView);
                    loadImageAsync(screenshotUrl, imgView);
                }
            }'''

code = re.sub(
    r'if \(app\.has\("icon"\) && !app\.optString\("icon"\)\.isEmpty\(\)\) \{\s*String iconVal = app\.optString\("icon"\);\s*String iconUrl = iconVal\.startsWith\("local://"\) \? iconVal : "http://" \+ ip \+ ":8552/images/" \+ iconVal;\s*loadImageAsync\(iconUrl, detailIcon\);\s*\}',
    replacement,
    code,
    flags=re.MULTILINE
)

with open('Client_App/app/src/main/java/com/elitesoftware/appmarketplace/AppDetailActivity.java', 'w') as f:
    f.write(code)
