# Server Manager (C++ Win32)

This application is built in C++ using the native Win32 API to comply with the legacy aesthetics outlined in the **EliteSoftwareTech Co.** guidelines. It provides both a Graphical User Interface (GUI) and a Command-Line Interface (CLI) to easily manage the Local APK Store backend.

## Features
- **APK Metadata Extraction:** Automatically parses `AndroidManifest.xml` via `pyaxmlparser` to extract the App Name, Package Name, Version, and Icon.
- **Multiple Screenshots:** Allows selecting multiple image files (JPG/PNG) to attach to an app release.
- **Automated Uploads:** Uses native Windows `curl.exe` under the hood to POST multipart form data directly to the local Python backend (`http://127.0.0.1:8443/api/upload`).
- **Version Retention:** Uploading an APK with the same package name but a different version will automatically retain the previous version on the server, allowing the Android client to display a "Versions" dropdown on the app page.

## CLI Usage

The tool can be fully controlled headlessly via the command line for automation purposes.

**Syntax:**
```cmd
Elite_App_Marketplace-Server.exe --upload <path_to_apk> [--desc "App Description"] [--screenshot <path_to_image>]
```

**Example:**
```cmd
Elite_App_Marketplace-Server.exe --upload "C:\Downloads\MyApp_v2.apk" --desc "Major update with new features!" --screenshot "C:\Downloads\promo1.jpg" --screenshot "C:\Downloads\promo2.png"
```

## GUI Usage
Simply launch `Elite_App_Marketplace-Server.exe` without arguments to open the UI. 
Click **"Browse APK..."** to select your file, which will trigger the metadata parser to auto-fill the text fields. You can then edit the description, attach screenshots, and click **"Apply"** to push the release to the server.
