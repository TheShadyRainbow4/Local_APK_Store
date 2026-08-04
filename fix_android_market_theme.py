import os

base_dir = r"C:\Users\Administrator\Desktop\Local_APK_Store\Client_App\app\src\main\res\layout"
drawable_dir = r"C:\Users\Administrator\Desktop\Local_APK_Store\Client_App\app\src\main\res\drawable"

if not os.path.exists(drawable_dir):
    os.makedirs(drawable_dir)

# 1. Generate Drawables for 3D buttons and rounded backgrounds
rounded_bg_xml = '''<?xml version="1.0" encoding="utf-8"?>
<shape xmlns:android="http://schemas.android.com/apk/res/android">
    <solid android:color="?android:attr/colorBackgroundFloating" />
    <corners android:radius="12dp" />
</shape>
'''
with open(os.path.join(drawable_dir, "rounded_bg.xml"), "w") as f:
    f.write(rounded_bg_xml)

btn_3d_xml = '''<?xml version="1.0" encoding="utf-8"?>
<selector xmlns:android="http://schemas.android.com/apk/res/android">
    <item android:state_pressed="true">
        <shape>
            <solid android:color="#82A629"/>
            <corners android:radius="6dp"/>
            <stroke android:width="1dp" android:color="#556b2f"/>
        </shape>
    </item>
    <item>
        <shape>
            <solid android:color="#A4C639"/>
            <corners android:radius="6dp"/>
            <stroke android:width="1dp" android:color="#82A629"/>
            <!-- Simulate 3D shadow with an inset or solid border -->
            <padding android:left="8dp" android:top="8dp" android:right="8dp" android:bottom="8dp"/>
        </shape>
    </item>
</selector>
'''
with open(os.path.join(drawable_dir, "btn_3d.xml"), "w") as f:
    f.write(btn_3d_xml)


# 2. Update layout files to use DayNight theme colors
activity_main_xml = '''<?xml version="1.0" encoding="utf-8"?>
<LinearLayout xmlns:android="http://schemas.android.com/apk/res/android"
    android:layout_width="match_parent"
    android:layout_height="match_parent"
    android:orientation="vertical"
    android:background="?android:attr/colorBackground">

    <LinearLayout
        android:layout_width="match_parent"
        android:layout_height="60dp"
        android:background="#A4C639"
        android:orientation="horizontal"
        android:gravity="center_vertical"
        android:padding="8dp">

        <ImageView
            android:layout_width="48dp"
            android:layout_height="48dp"
            android:src="@mipmap/ic_launcher"
            android:contentDescription="Icon" />

        <TextView
            android:layout_width="0dp"
            android:layout_height="wrap_content"
            android:layout_weight="1"
            android:layout_marginStart="12dp"
            android:text="Market"
            android:textColor="#FFFFFF"
            android:textSize="24sp"
            android:textStyle="bold"
            android:shadowColor="#000000"
            android:shadowDx="1"
            android:shadowDy="1"
            android:shadowRadius="1.5" />

        <ImageButton
            android:id="@+id/btnSettings"
            android:layout_width="48dp"
            android:layout_height="48dp"
            android:background="?android:attr/selectableItemBackground"
            android:src="@drawable/settings"
            android:contentDescription="Settings"
            android:scaleType="fitCenter"
            android:padding="10dp"/>
    </LinearLayout>

    <LinearLayout
        android:layout_width="match_parent"
        android:layout_height="40dp"
        android:background="?android:attr/colorBackgroundFloating"
        android:orientation="horizontal"
        android:elevation="4dp">
        <TextView
            android:layout_width="0dp"
            android:layout_weight="1"
            android:layout_height="match_parent"
            android:gravity="center"
            android:text="APPS"
            android:textColor="#A4C639"
            android:textStyle="bold"/>
        <View android:layout_width="1dp" android:layout_height="match_parent" android:background="?android:attr/listDivider"/>
        <TextView
            android:layout_width="0dp"
            android:layout_weight="1"
            android:layout_height="match_parent"
            android:gravity="center"
            android:text="GAMES"
            android:textColor="?android:attr/textColorSecondary"
            android:textStyle="bold"/>
        <View android:layout_width="1dp" android:layout_height="match_parent" android:background="?android:attr/listDivider"/>
        <TextView
            android:layout_width="0dp"
            android:layout_weight="1"
            android:layout_height="match_parent"
            android:gravity="center"
            android:text="DOWNLOADS"
            android:textColor="?android:attr/textColorSecondary"
            android:textStyle="bold"/>
    </LinearLayout>

    <View
        android:layout_width="match_parent"
        android:layout_height="2dp"
        android:background="#A4C639" />

    <ListView
        android:id="@+id/lvApps"
        android:layout_width="match_parent"
        android:layout_height="match_parent"
        android:divider="@null"
        android:dividerHeight="0dp"
        android:clipToPadding="false"
        android:padding="8dp" />
</LinearLayout>
'''
with open(os.path.join(base_dir, "activity_main.xml"), "w") as f:
    f.write(activity_main_xml)


list_item_app_xml = '''<?xml version="1.0" encoding="utf-8"?>
<LinearLayout xmlns:android="http://schemas.android.com/apk/res/android"
    android:layout_width="match_parent"
    android:layout_height="wrap_content"
    android:layout_marginBottom="8dp">

    <RelativeLayout
        android:layout_width="match_parent"
        android:layout_height="wrap_content"
        android:padding="12dp"
        android:background="@drawable/rounded_bg"
        android:elevation="2dp"
        android:descendantFocusability="blocksDescendants">

        <ImageView
            android:id="@+id/ivAppIcon"
            android:layout_width="64dp"
            android:layout_height="64dp"
            android:src="@mipmap/ic_launcher"
            android:layout_marginEnd="12dp"
            android:layout_alignParentStart="true"
            android:layout_centerVertical="true" />

        <TextView
            android:id="@+id/tvAppName"
            android:layout_width="wrap_content"
            android:layout_height="wrap_content"
            android:layout_toEndOf="@id/ivAppIcon"
            android:layout_toStartOf="@+id/btnInstall"
            android:text="App Name"
            android:textColor="?android:attr/textColorPrimary"
            android:textSize="16sp"
            android:textStyle="bold"
            android:singleLine="true"
            android:ellipsize="end"/>

        <TextView
            android:id="@+id/tvAppDesc"
            android:layout_width="wrap_content"
            android:layout_height="wrap_content"
            android:layout_below="@id/tvAppName"
            android:layout_toEndOf="@id/ivAppIcon"
            android:layout_toStartOf="@+id/btnInstall"
            android:text="Description goes here."
            android:textColor="?android:attr/textColorSecondary"
            android:textSize="14sp"
            android:maxLines="2"
            android:ellipsize="end"
            android:layout_marginTop="4dp" />

        <Button
            android:id="@+id/btnInstall"
            android:layout_width="wrap_content"
            android:layout_height="wrap_content"
            android:layout_alignParentEnd="true"
            android:layout_centerVertical="true"
            android:text="INSTALL"
            android:textColor="#FFFFFF"
            android:background="@drawable/btn_3d"
            android:minHeight="36dp"
            android:textSize="12sp"
            android:textStyle="bold"
            android:shadowColor="#556b2f"
            android:shadowDx="1"
            android:shadowDy="1"
            android:shadowRadius="1"
            android:focusable="false"
            android:focusableInTouchMode="false" />
    </RelativeLayout>
</LinearLayout>
'''
with open(os.path.join(base_dir, "list_item_app.xml"), "w") as f:
    f.write(list_item_app_xml)


activity_app_detail_xml = '''<?xml version="1.0" encoding="utf-8"?>
<LinearLayout xmlns:android="http://schemas.android.com/apk/res/android"
    android:layout_width="match_parent"
    android:layout_height="match_parent"
    android:orientation="vertical"
    android:background="?android:attr/colorBackground">

    <LinearLayout
        android:layout_width="match_parent"
        android:layout_height="60dp"
        android:background="#A4C639"
        android:orientation="horizontal"
        android:gravity="center_vertical"
        android:padding="8dp">

        <ImageButton
            android:id="@+id/btnBack"
            android:layout_width="48dp"
            android:layout_height="48dp"
            android:background="?android:attr/selectableItemBackground"
            android:src="@android:drawable/ic_menu_revert"
            android:scaleType="centerInside" />

        <TextView
            android:layout_width="0dp"
            android:layout_height="wrap_content"
            android:layout_weight="1"
            android:layout_marginStart="8dp"
            android:text="App Details"
            android:textColor="#FFFFFF"
            android:textSize="22sp"
            android:textStyle="bold"
            android:shadowColor="#000000"
            android:shadowDx="1"
            android:shadowDy="1"
            android:shadowRadius="1.5" />
    </LinearLayout>
    
    <View android:layout_width="match_parent" android:layout_height="2dp" android:background="#A4C639" />

    <ScrollView
        android:layout_width="match_parent"
        android:layout_height="match_parent"
        android:padding="16dp">
        
        <LinearLayout
            android:layout_width="match_parent"
            android:layout_height="wrap_content"
            android:orientation="vertical"
            android:background="@drawable/rounded_bg"
            android:elevation="4dp"
            android:padding="16dp">

            <LinearLayout
                android:layout_width="match_parent"
                android:layout_height="wrap_content"
                android:orientation="horizontal"
                android:gravity="center_vertical">
                
                <ImageView
                    android:id="@+id/detailIcon"
                    android:layout_width="80dp"
                    android:layout_height="80dp"
                    android:src="@mipmap/ic_launcher" />
                    
                <LinearLayout
                    android:layout_width="match_parent"
                    android:layout_height="wrap_content"
                    android:orientation="vertical"
                    android:layout_marginStart="16dp">
                    
                    <TextView
                        android:id="@+id/detailName"
                        android:layout_width="wrap_content"
                        android:layout_height="wrap_content"
                        android:text="App Name"
                        android:textColor="?android:attr/textColorPrimary"
                        android:textSize="22sp"
                        android:textStyle="bold" />
                        
                    <TextView
                        android:id="@+id/detailPackage"
                        android:layout_width="wrap_content"
                        android:layout_height="wrap_content"
                        android:text="com.example.app"
                        android:textColor="?android:attr/textColorSecondary"
                        android:textSize="14sp"
                        android:layout_marginTop="2dp" />

                    <TextView
                        android:id="@+id/detailCategory"
                        android:layout_width="wrap_content"
                        android:layout_height="wrap_content"
                        android:text="Category"
                        android:textColor="#A4C639"
                        android:textSize="14sp"
                        android:layout_marginTop="4dp" />
                </LinearLayout>
            </LinearLayout>

            <Button
                android:id="@+id/detailInstallBtn"
                android:layout_width="match_parent"
                android:layout_height="48dp"
                android:layout_marginTop="24dp"
                android:text="INSTALL"
                android:textColor="#FFFFFF"
                android:background="@drawable/btn_3d"
                android:textSize="16sp"
                android:textStyle="bold"
                android:shadowColor="#556b2f"
                android:shadowDx="1"
                android:shadowDy="1"
                android:shadowRadius="1" />

            <ProgressBar
                android:id="@+id/detailProgressBar"
                style="?android:attr/progressBarStyleHorizontal"
                android:layout_width="match_parent"
                android:layout_height="wrap_content"
                android:layout_marginTop="8dp"
                android:visibility="gone"
                android:max="100" />

            <View
                android:layout_width="match_parent"
                android:layout_height="1dp"
                android:background="?android:attr/listDivider"
                android:layout_marginTop="24dp"
                android:layout_marginBottom="16dp" />

            <TextView
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
                
        </LinearLayout>
    </ScrollView>
</LinearLayout>
'''
with open(os.path.join(base_dir, "activity_app_detail.xml"), "w") as f:
    f.write(activity_app_detail_xml)

print("Applied DayNight theme and 3D rounded button styles successfully.")
