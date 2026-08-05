## 2026-08-04T20:50:18Z

You are Worker 1 for Milestone 2 (Automatic APK Icon Extraction & Display).
Your working directory for metadata is: C:\Users\Administrator\Desktop\Local_APK_Store\.agents\worker_m2_1

Scope & Tasks:
You must implement the changes described below in `Manager_App/main.cpp` and `Client_App/app/src/main/java/com/elitesoftware/appmarketplace/MainActivity.java` (and `AppDetailActivity.java`).

Mandatory Reading Files:
- C:\Users\Administrator\Desktop\Local_APK_Store\ORIGINAL_REQUEST.md
- C:\Users\Administrator\Desktop\Local_APK_Store\PROJECT.md
- C:\Users\Administrator\Desktop\Local_APK_Store\.agents\explorer_2\analysis.md
- C:\Users\Administrator\Desktop\Local_APK_Store\.agents\explorer_2\handoff.md

Detailed Requirements:
1. **Server Auto Icon Extraction (C++) in `Manager_App/main.cpp`**:
   - Update `RefreshAppList()` and APK upload endpoints so that when scanning `apks/` directory or uploading an APK, if an app entry lacks an `"icon"` key or has an unknown package name, automatically extract metadata and internal APK icons.
   - For Adaptive XML Icons: If the icon path extracted via `aapt dump badging` ends with `.xml` (e.g. `res/mipmap-anydpi-v26/ic_launcher.xml`), parse the APK ZIP file for raster PNG fallbacks in priority order (`res/mipmap-xxxhdpi-v4/ic_launcher.png`, `res/mipmap-xxhdpi-v4/ic_launcher.png`, `res/mipmap-xhdpi-v4/ic_launcher.png`, `res/mipmap-hdpi-v4/ic_launcher.png`, `res/mipmap-mdpi-v4/ic_launcher.png`, `res/drawable*/*.png`, or ZIP `*.png` search matching `*ic_launcher*.png` or `*icon*.png`).
   - Save extracted PNG icons to `Manager_App/images/<pkg_name>_icon.png` (or `<app_id>.png` as referenced in db.json `"icon"` property). Ensure `db.json` is saved with the updated `"icon"` and `"package_name"` properties.

2. **Windows ListView Icon Rendering (C++) in `Manager_App/main.cpp`**:
   - Upgrade `hwndApps` from `LISTBOX` to `SysListView32` (`WC_LISTVIEW`) with `LVS_REPORT | LVS_SINGLESEL | LVS_SHOWSELALWAYS`.
   - Create and attach a Win32 ImageList (`HIMAGELIST`) to `hwndApps` via `ListView_SetImageList(hwndApps, hSmallIcons, LVSIL_SMALL)`.
   - Populate `hSmallIcons` by loading each app's extracted PNG icon using GDI+ (`Gdiplus::Bitmap::FromFile`) and converting to `HICON`.
   - Insert items into `hwndApps` ListView with their corresponding `iImage` index so icons render next to app titles in the GUI.
   - Ensure app selection events work properly with `SysListView32` (`LVN_ITEMCHANGED` or `NM_CLICK` / `LBN_SELCHANGE` handling) so preview and detail updating still work.

3. **Android Client Intent Extra Alignment & Icon Display (Java)**:
   - In `Client_App/app/src/main/java/com/elitesoftware/appmarketplace/MainActivity.java`:
     When setting the item click listener for `lvApps`, ensure the Intent extras match what `AppDetailActivity.java` expects:
     `intent.putExtra("app_json", app.toString());`
     `intent.putExtra("server_ip", app.optString("_server_ip"));`
   - In `AppDetailActivity.java`:
     Verify that `app_json` and `server_ip` are read cleanly and that the icon URL `http://<server_ip>:8552/images/<icon>` is constructed and rendered asynchronously on the detail view.

4. **Build & Verify**:
   - Run `Manager_App/build.bat` to compile the Windows app server. Verify compilation succeeds with exit code 0.
   - Run `Client_App/gradlew assembleDebug` (if Gradle/Android SDK is installed on host) or verify Java syntax correctness.
   - Run a test execution or script to verify icon extraction generates valid PNG files in `Manager_App/images/` and updates `Manager_App/db.json`.
