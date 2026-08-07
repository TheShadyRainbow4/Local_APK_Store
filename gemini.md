# Gemini Operational Rules & Project Architecture

This file tracks specific instructions, workflow behaviors, and architectural overviews that Gemini (and other AI assistants) must follow when working on the `Local_APK_Store` project. This ensures a smooth development process and provides a clear map of how the ecosystem functions.

## 1. Core Operational Rules

### Version Control & History (Auto-Pushing)
- **Rule:** Every time a file is modified, created, or any change is applied to the project, Gemini **must** immediately `git add .`, `git commit -m "..."`, and `git push -u origin master` to push the changes to `origin`.
- **Reasoning:** A constant, unbroken change history is required so the user doesn't need to manually worry about pushing, and we have a reliable log of all actions regardless of whether the specific code actually worked on the first try.

### Line Endings (CRLF)
- **Rule:** Ensure all source files use `CRLF` (Windows style) line endings.
- **Reasoning:** Standardization across the Windows-based EliteSoftware ecosystem. Enforced via `.gitattributes`.

### Continuous Changelog
- **Rule:** A `changelog.md` file must be continuously updated whenever things are changed or added to the project.
- **Reasoning:** Provides a human-readable, centralized history of new features, bug fixes, and architectural changes over time.

### Elite App Marketplace Scope & Signatures
- **Rule (App Name):** The Android Client must strictly be named **"Elite App Marketplace"**.
- **Rule (APK Signing):** All processed APKs, including the Elite App Marketplace APK itself, must be signed using the master certificate located at `C:\Users\Administrator\Desktop\Local_APK_Store\Elite-EasySigner\EliteSoftware_Special.pfx` (Password: `Minecraft145!!`).
- **Rule (Client Features):** The marketplace client must support categorization, tagging, user reviews/comments, and the ability to download the `EliteSoftware_Special.cer` root certificate directly to the Android device via its internal Settings menu.

---

## 2. Project Architecture & Components

The project is split into two primary components: the **Windows Server Manager** and the **Android Client**. 

### A. Windows Server Manager (`/Manager_App/`)
This is a monolithic C++ Win32 desktop application that acts as both a GUI management tool and an HTTP server for the Android clients.
- `main.cpp`: The core C++ source file containing the Win32 GUI event loop and the `httplib` web server endpoints. It handles uploading APKs, modifying database entries, and serving files to the Android app.
- `db.json`: The database file holding all metadata (App Names, Package Names, Icons, Screenshots, Reviews) for every APK available in the marketplace.
- `apks/` and `images/`: Directories storing the physical `.apk` files and their corresponding icons/screenshots.
- `build.bat`: The primary build script for compiling the server and initiating the full pipeline (detailed below).

### B. Android Client (`/Client_App/`)
This is the standard Android Studio project for the "Elite App Marketplace" app. It connects to the C++ Windows Server.
- Built using Java/Android SDK.
- Connects to the local server (via IP address configured by the user) to fetch the JSON app catalog, download APKs, and submit new apps/updates.
- Contains an `UploadActivity.java` which parses metadata (Package Name, Version, App Name) dynamically directly from the selected `.apk` file using Android's native `PackageManager`.

---

## 3. The Automated Build & Release Pipeline

The project features a **fully automated**, end-to-end continuous integration and deployment pipeline that spans building the C++ server, building the Android APK, signing it, updating the database, pushing to git, and creating a GitHub release.

**How to trigger a full build & release:**
You simply execute `build.bat` in the `Manager_App` directory.
```powershell
cmd.exe /c "build.bat"
```

**Step-by-Step Breakdown of the Pipeline:**
1. **`Manager_App\build.bat` (The Entry Point):**
   - Kills any running instances of the server.
   - Cleans old binaries.
   - Compiles the C++ source using `g++` and `windres` (statically linked).
   - If the C++ compilation is **successful**, it automatically calls `..\publish_release.ps1` to execute the rest of the pipeline.

2. **`publish_release.ps1` (The Automator):**
   - **Auto-Versioning:** It reads `Manager_App/db.json` to find the latest version of the Elite App Marketplace client and increments the patch number automatically (e.g., `v1.0.53` -> `v1.0.54`).
   - **Android Versioning:** Updates `versionCode` and `versionName` inside `Client_App/app/build.gradle` to match the newly generated version.
   - **Android Compilation:** Triggers `Client_App\build_apk.ps1` to run the Gradle tasks (`assembleDebug` / `assembleRelease`) to compile the `.apk`.
   - **APK Signing:** Uses the `apksigner` build-tool to sign the output APK securely with the `EliteSoftware_Special.pfx` certificate.
   - **Database Injection:** Automatically copies the newly signed APK into the `Manager_App\apks\` folder and updates `Manager_App/db.json` to register the new version. (This allows existing clients to see and download the update immediately).
   - **Git Push:** Stages all changes, commits them as "Auto-build and release v1.0.x", and pushes directly to the `master` branch.
   - **GitHub Release:** Uses the GitHub CLI (`gh release create`) to push a new versioned release, attaching both the Windows `Elite_App_Marketplace-Server.exe` and the `Elite_App_Marketplace-Client_v[version].apk`.
   - **Restart:** Automatically launches the newly compiled Windows Server Executable.

**CRITICAL RULE:** Never separate the build and publish steps. `build.bat` must always remain the entry point, and it must always seamlessly trigger `publish_release.ps1` upon a successful compile.

**Build Logging Details:**
- `build.bat` uses a self-logging pattern to prevent it from hanging in the background and keeping the terminal process stuck. 
- When executed, the outer script intercepts execution, creates a `build_log.txt` file (wiping the old one cleanly), pipes the entire compilation run into the log file, and immediately calls `exit` when finished to gracefully close the parent process. 

## 4. Android Client Self-Update Architecture
The Elite App Marketplace Android application contains built-in self-updating architecture that must handle edge cases when the Android OS attempts to kill the package while it's being updated.
- **Root/Shizuku Path:** Automated background installations via Shizuku (`pm install`) *must* include the `-r` flag (`pm install -r -S <size>`) so that the package manager knows to overwrite the existing APK, rather than throwing an `INSTALL_FAILED_ALREADY_EXISTS` exception.
- **Standard Fallback Path:** For non-rooted updates, we do not use `Intent.ACTION_VIEW` targeting a local `FileProvider` because Android violently kills the running app during the self-update process, terminating the `FileProvider` mid-stream and corrupting the install. Instead, the application invokes the **PackageInstaller Session API** to stream the raw APK payload directly into the Android OS's staging area *before* committing the install.
