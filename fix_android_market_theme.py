import os

base_dir = r"C:\Users\Administrator\Desktop\Local_APK_Store\Client_App\app\src\main\res\layout"

# 1. Restore activity_main.xml
activity_main_xml = '''<?xml version="1.0" encoding="utf-8"?>
<LinearLayout xmlns:android="http://schemas.android.com/apk/res/android"
    android:layout_width="match_parent"
    android:layout_height="match_parent"
    android:orientation="vertical"
    android:background="#2E2E2E">

    <!-- Top Action Bar (Gingerbread Market Legacy looking) -->
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
            android:src="@drawable/ic_settings"
            android:contentDescription="Settings"
            android:scaleType="fitCenter"
            android:padding="10dp"/>
    </LinearLayout>

    <LinearLayout
        android:layout_width="match_parent"
        android:layout_height="40dp"
        android:background="#111111"
        android:orientation="horizontal">
        <TextView
            android:layout_width="0dp"
            android:layout_weight="1"
            android:layout_height="match_parent"
            android:gravity="center"
            android:text="APPS"
            android:textColor="#A4C639"
            android:textStyle="bold"/>
        <View android:layout_width="1dp" android:layout_height="match_parent" android:background="#333333"/>
        <TextView
            android:layout_width="0dp"
            android:layout_weight="1"
            android:layout_height="match_parent"
            android:gravity="center"
            android:text="GAMES"
            android:textColor="#888888"
            android:textStyle="bold"/>
        <View android:layout_width="1dp" android:layout_height="match_parent" android:background="#333333"/>
        <TextView
            android:layout_width="0dp"
            android:layout_weight="1"
            android:layout_height="match_parent"
            android:gravity="center"
            android:text="DOWNLOADS"
            android:textColor="#888888"
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
        android:divider="#444444"
        android:dividerHeight="1dp"
        android:clipToPadding="false" />
</LinearLayout>
'''
with open(os.path.join(base_dir, "activity_main.xml"), "w") as f:
    f.write(activity_main_xml)


# 2. Fix list_item_app.xml to match the dark theme, while keeping the custom UI elements
list_item_app_xml = '''<?xml version="1.0" encoding="utf-8"?>
<RelativeLayout xmlns:android="http://schemas.android.com/apk/res/android"
    android:layout_width="match_parent"
    android:layout_height="wrap_content"
    android:padding="12dp"
    android:background="#333333"
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
        android:textColor="#FFFFFF"
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
        android:text="Description goes here and spans across two lines potentially."
        android:textColor="#BBBBBB"
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
        android:textColor="#000000"
        android:background="#A4C639"
        android:paddingStart="12dp"
        android:paddingEnd="12dp"
        android:minHeight="36dp"
        android:textSize="12sp"
        android:textStyle="bold"
        android:focusable="false"
        android:focusableInTouchMode="false" />

</RelativeLayout>
'''
with open(os.path.join(base_dir, "list_item_app.xml"), "w") as f:
    f.write(list_item_app_xml)


# 3. Fix activity_app_detail.xml to use the dark theme and look like the legacy Market
activity_app_detail_xml = '''<?xml version="1.0" encoding="utf-8"?>
<LinearLayout xmlns:android="http://schemas.android.com/apk/res/android"
    android:layout_width="match_parent"
    android:layout_height="match_parent"
    android:orientation="vertical"
    android:background="#2E2E2E">

    <!-- Top Action Bar (Gingerbread Market Legacy looking) -->
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
            android:background="#333333"
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
                        android:textColor="#FFFFFF"
                        android:textSize="22sp"
                        android:textStyle="bold" />
                        
                    <TextView
                        android:id="@+id/detailPackage"
                        android:layout_width="wrap_content"
                        android:layout_height="wrap_content"
                        android:text="com.example.app"
                        android:textColor="#AAAAAA"
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
                android:textColor="#000000"
                android:background="#A4C639"
                android:textSize="16sp"
                android:textStyle="bold" />

            <View
                android:layout_width="match_parent"
                android:layout_height="1dp"
                android:background="#555555"
                android:layout_marginTop="24dp"
                android:layout_marginBottom="16dp" />

            <TextView
                android:layout_width="wrap_content"
                android:layout_height="wrap_content"
                android:text="Description"
                android:textColor="#FFFFFF"
                android:textSize="16sp"
                android:textStyle="bold" />

            <TextView
                android:id="@+id/detailDesc"
                android:layout_width="match_parent"
                android:layout_height="wrap_content"
                android:text="Full app description goes here."
                android:textColor="#CCCCCC"
                android:textSize="15sp"
                android:layout_marginTop="8dp"
                android:lineSpacingExtra="4dp" />
                
        </LinearLayout>
    </ScrollView>
</LinearLayout>
'''
with open(os.path.join(base_dir, "activity_app_detail.xml"), "w") as f:
    f.write(activity_app_detail_xml)

