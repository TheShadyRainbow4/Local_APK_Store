import re
with open('Client_App/app/src/main/res/layout/activity_app_detail.xml', 'r') as f:
    code = f.read()

replacement = '''            <TextView
                android:layout_width="wrap_content"
                android:layout_height="wrap_content"
                android:text="Description"
                android:textColor="?android:attr/textColorPrimary"
                android:textSize="16sp"
                android:textStyle="bold" />

            <TextView
                android:id="@+id/detailDesc"
                android:layout_width="match_parent"
                android:layout_height="wrap_content"
                android:text="Full app description goes here."
                android:textColor="?android:attr/textColorSecondary"
                android:textSize="15sp"
                android:layout_marginTop="8dp"
                android:lineSpacingExtra="4dp" />
                
            <TextView
                android:id="@+id/screenshotsLabel"
                android:layout_width="wrap_content"
                android:layout_height="wrap_content"
                android:text="Screenshots"
                android:textColor="?android:attr/textColorPrimary"
                android:textSize="16sp"
                android:textStyle="bold"
                android:layout_marginTop="16dp"
                android:visibility="gone" />

            <HorizontalScrollView
                android:id="@+id/screenshotsScrollView"
                android:layout_width="match_parent"
                android:layout_height="wrap_content"
                android:layout_marginTop="8dp"
                android:scrollbars="none"
                android:visibility="gone">
                <LinearLayout
                    android:id="@+id/screenshotsContainer"
                    android:layout_width="wrap_content"
                    android:layout_height="wrap_content"
                    android:orientation="horizontal" />
            </HorizontalScrollView>'''

code = re.sub(
    r'<TextView\s*android:layout_width="wrap_content"\s*android:layout_height="wrap_content"\s*android:text="Description"[^>]*>\s*<TextView\s*android:id="@+id/detailDesc"[^>]*>',
    replacement,
    code,
    flags=re.MULTILINE | re.DOTALL
)

with open('Client_App/app/src/main/res/layout/activity_app_detail.xml', 'w') as f:
    f.write(code)
