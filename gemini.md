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

# Project: Local APK Store

## Architecture
- `Manager_App/`: Win32 / C++ Windows Application & Server (uses Win32 API, GDI+, `httplib.h`, MinGW `g++`, `build.bat`)
- `Client_App/`: Android Client App (Java, Gradle, Android SDK, `MainActivity.java`, `AppDetailActivity.java`)
- Data Store: `Manager_App/db.json` and static image assets in `Manager_App/images/`

## Feature Inventory
| # | Feature | Description | Milestone | Source |
|---|---------|-------------|-----------|--------|
| 1 | R1.1 WinForms/Win32 Custom Backfill Fix | Replace `GetSysColorBrush(COLOR_WINDOW)` in `WM_CTLCOLORSTATIC` with hollow brush to default to OS styling | M1 | ORIGINAL_REQUEST R1 / Explorer 1 |
| 2 | R1.2 Control Overlap & Layout Fix | Re-position overlapping controls (`hwndPreview`, `btnDelete`, `btnClearForm`, `btnBrowse`, `btnApply`, `invLabels`) at default 850x600 window size | M1 | ORIGINAL_REQUEST R1 / Explorer 1 |
| 3 | R1.3 ListView Conversion & Docking | Convert `hwndApps` from LISTBOX to SysListView32 with dynamic WM_SIZE anchoring | M1 | ORIGINAL_REQUEST R1 / Explorer 1 |
| 4 | R1.4 EliteSoftware Aesthetic & Dialog Compliance | Implement Segoe UI font, Chin panel, 3D inset frame, Menubar, Toolbar, About Dialog, Help Dialog, Settings Dialog, Tooltips, Log file & viewer link | M1 | ORIGINAL_REQUEST R1 & User Rules / Explorer 1 |
| 5 | R2.1 Server Auto Icon Extraction & ZIP/PNG Fallback | Automate APK metadata & icon extraction (handling raster PNG & XML adaptive icon fallbacks) during server scan/upload | M2 | ORIGINAL_REQUEST R2 / Explorer 2 |
| 6 | R2.2 Windows ListView Icon Rendering | Load extracted APK icons into GDI+/Win32 ImageList (`HIMAGELIST`) and display in `SysListView32` | M2 | ORIGINAL_REQUEST R2 / Explorer 2 |
| 7 | R2.3 Android Store UI Icon Display | Align Intent extras in Android client (`MainActivity` to `AppDetailActivity`) and serve icons via HTTP `/images/` | M2 | ORIGINAL_REQUEST R2 / Explorer 2 |
| 8 | R3.1 Client Heartbeat & Disconnect Protocol | Implement HTTP POST `/api/heartbeat` & `/api/disconnect` transmitting Device Name in `MainActivity.java` | M3 | ORIGINAL_REQUEST R3 / Explorer 3 |
| 9 | R3.2 Server Session Management & Timeout Cleanup | Maintain thread-safe `g_connectedClients` map and 15-second timeout cleanup thread in `Manager_App/main.cpp` | M3 | ORIGINAL_REQUEST R3 / Explorer 3 |
| 10 | R3.3 Server Monitor Client List UI | Add `SysListView32` client list (IP Address, Device Name, Last Active) to Server Monitor tab, updated via 1s `WM_TIMER` | M3 | ORIGINAL_REQUEST R3 / Explorer 3 |

## Milestones
| # | Name | Scope | Dependencies | Status |
|---|------|-------|-------------|--------|
| M1 | Win32 UI Rendering & Aesthetic Compliance | R1.1, R1.2, R1.3, R1.4 | none | DONE |
| M2 | Automatic APK Icon Extraction & Display | R2.1, R2.2, R2.3 | M1 | DONE |
| M3 | Server Monitor Connected Clients Real-Time List | R3.1, R3.2, R3.3 | M1 | DONE |
| M4 | E2E Integration & Verification | Tiers 1-5 E2E Verification & Audit | M1, M2, M3 | DONE |

## Interface Contracts
### Manager_App ? Client_App
- `GET /api/apps` -> JSON array of apps: `[{"id":"...", "name":"...", "icon":"/images/<id>.png", ...}]`
- `POST /api/heartbeat` -> Body JSON `{"client_id":"...", "device_name":"..."}` -> Server updates IP and last active time.
- `POST /api/disconnect` -> Body JSON `{"client_id":"..."}` -> Server removes client immediately.
- `GET /images/<icon_name>` -> Serves PNG icon file.

## Code Layout
- `Manager_App/main.cpp` — Main Win32 window, server threads, HTTP API routes, UI layout, Win32 controls
- `Manager_App/build.bat` — MinGW build script for Manager App
- `Client_App/app/src/main/java/com/elitesoftware/appmarketplace/MainActivity.java` — Android store home screen, HTTP/UDP discovery, heartbeat service
- `Client_App/app/src/main/java/com/elitesoftware/appmarketplace/AppDetailActivity.java` — Android store app details screen


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
# Original User Request

## 2026-08-04T20:28:23-04:00

# Teamwork Project Prompt — Draft

> Status: Launched
> Goal: Craft prompt ? get user approval ? delegate to teamwork_preview

Fix UI rendering and functional issues in the Local APK Store application, automatically extract and display internal APK icons, and add a connected client list to the server monitor.

Working directory: C:\Users\Administrator\Desktop\Local_APK_Store
Integrity mode: development

## Requirements

### R1. UI Rendering Fixes (Windows App)
Ensure no UI elements have custom backfill colors (they must rely entirely on the OS/Visual Styles, strictly adhering to legacy Windows aesthetics). Fix any overlapping elements and ensure the listview is properly anchored/docked so it resizes dynamically with the window. Do not add any modern UI designs or change the core existing design layout. The Windows app must build upon the existing C++ (or C#/PowerShell depending on existing foundation) codebase without rewriting the underlying structure.

### R2. Automatic APK Icon Extraction & Display
Automatically extract the internal icon from APK files and display it within the Windows application's listview. This extraction must be fully integrated into the server and client apps directly, avoiding external tools/binaries unless absolutely required. Ensure this internal icon is also served and displayed correctly on the Android store application's UI, respecting its existing foundation.

### R3. Server Monitor Updates
Update the server monitor interface to display a real-time list of connected clients. The list must show both the IP Address and the Device Name of each connected client.

## Acceptance Criteria

### UI Rendering
- [ ] Programmatic/Visual Verification: No buttons or controls specify a custom background color; they default to OS styling.
- [ ] Programmatic/Visual Verification: No elements overlap when the main window is initialized at default size.
- [ ] Programmatic/Visual Verification: Resizing the window correctly resizes the listview without breaking the layout or obscuring other controls.

### APK Icons
- [ ] Programmatic Verification: The server logic successfully reads the internal APK icon for an uploaded/available APK.
- [ ] Visual Verification: The Windows app listview displays the correct internal icon.
- [ ] Visual Verification: The Android store UI successfully fetches and displays the internal APK icon.

### Server Monitor
- [ ] Programmatic Verification: When a client connects, the server UI updates to show their IP address and Device Name.
- [ ] Programmatic Verification: Disconnected clients are appropriately managed/removed from the list.

# Test Infrastructure & Strategy Documentation — Local APK Store

## 1. Test Philosophy & Design Principles
The End-to-End (E2E) testing framework for **Local APK Store** is designed around opaque-box, contract-driven, requirement-verified validation.

- **Non-Invasive Verification**: Tests validate observable APIs, network protocols, data structures, and file system states without relying on internal function mocks or fake test assertions.
- **Independence & Isolation**: Every test creates its own temporary environment (isolated ports, isolated temporary directories, synthetic APK archives, isolated mock client connections) and cleans up resources immediately after execution.
- **Strict Verification Rules**: All test cases use authoritative verification derived directly from `ORIGINAL_REQUEST.md` and `PROJECT.md`. No hardcoded dummy passing tests.
- **Multi-Tiered Coverage Layout**: Organizes test suites into Tiers 1-4, moving from individual feature requirement validation up to multi-client end-to-end real-world workflows.

---

## 2. Feature Inventory & Mapping Matrix

| Feature ID | Feature Name | Target Scope / Requirements | Test File |
|------------|--------------|-----------------------------|-----------|
| **R1** | Win32 UI Rendering & Aesthetic Compliance | R1.1 Custom Backfill Brush Removal<br>R1.2 Non-Overlapping Control Geometry<br>R1.3 SysListView32 Conversion & Dynamic WM_SIZE<br>R1.4 Segoe UI Font, Dialogs, Tooltips, Chin Panel, 3D Inset<br>R1.5 Log File Creation & Logger Link | `tests/test_tier1_feature_coverage.py`<br>`tests/test_tier2_boundary_corner.py`<br>`tests/test_tier3_cross_feature.py`<br>`tests/test_tier4_real_world.py` |
| **R2** | APK Icon Extraction & Display | R2.1 Server ZIP Internal PNG Extraction<br>R2.2 Extraction Fallback (Adaptive XML / Default Image)<br>R2.3 HTTP Endpoint `GET /images/<icon>` Serving<br>R2.4 Win32 HIMAGELIST Image Loading & ListView Binding<br>R2.5 Android Client Intent Extra Alignment & HTTP Icon URL | `tests/test_tier1_feature_coverage.py`<br>`tests/test_tier2_boundary_corner.py`<br>`tests/test_tier3_cross_feature.py`<br>`tests/test_tier4_real_world.py` |
| **R3** | Server Monitor & Connected Clients | R3.1 Client Heartbeat Registration (`POST /api/heartbeat`)<br>R3.2 Repeat Heartbeat Timestamp Updates (No Duplicates)<br>R3.3 Disconnect Protocol (`POST /api/disconnect`)<br>R3.4 15-Second Inactive Client Timeout Purge Thread<br>R3.5 Server Monitor SysListView32 UI Timer Refresh | `tests/test_tier1_feature_coverage.py`<br>`tests/test_tier2_boundary_corner.py`<br>`tests/test_tier3_cross_feature.py`<br>`tests/test_tier4_real_world.py` |

---

## 3. Architecture & Test Directory Structure

```
C:\Users\Administrator\Desktop\Local_APK_Store\
??? tests/
?   ??? __init__.py                            # Package initialization
?   ??? test_tier1_feature_coverage.py          # Tier 1: Feature Coverage (15 tests: R1=5, R2=5, R3=5)
?   ??? test_tier2_boundary_corner.py           # Tier 2: Boundary & Corner Cases (15 tests: R1=5, R2=5, R3=5)
?   ??? test_tier3_cross_feature.py             # Tier 3: Pairwise & Multi-Feature Interactions (4 tests)
?   ??? test_tier4_real_world.py               # Tier 4: Real-World Workflow Scenarios (5 tests)
?   ??? run_e2e_tests.py                       # Native Python Test Runner & Reporter
?   ??? run_e2e_tests.ps1                      # PowerShell Test Execution Wrapper
??? TEST_INFRA.md                              # Test Strategy & Infrastructure Manual
??? TEST_READY.md                              # Suite Status, Execution Command & Verification Metrics
```

---

## 4. Runner Invocation & Commands

### PowerShell Invocation (Standard Windows Execution)
```powershell
powershell -ExecutionPolicy Bypass -File tests\run_e2e_tests.ps1
```

### Python Direct Invocation
```cmd
python tests/run_e2e_tests.py
```

### Individual Tier Execution
```cmd
python -m unittest tests/test_tier1_feature_coverage.py
python -m unittest tests/test_tier2_boundary_corner.py
python -m unittest tests/test_tier3_cross_feature.py
python -m unittest tests/test_tier4_real_world.py
```

---

## 5. Coverage Thresholds & Quality Gates

- **Total Test Count Minimum**: 39 Tests
  * Tier 1 (Feature Coverage): >= 15 tests (5 R1, 5 R2, 5 R3)
  * Tier 2 (Boundary & Corner Cases): >= 15 tests (5 R1, 5 R2, 5 R3)
  * Tier 3 (Cross-Feature Pairwise Interactions): >= 4 tests (R1+R2, R2+R3, R1+R3, R1+R2+R3)
  * Tier 4 (Real-World Scenarios): >= 5 tests
- **Pass Threshold**: 100% Pass Rate required (0 Failures, 0 Errors)
- **Execution Code Gate**: Runner exits with code `0` on 100% pass, `1` on any failure.

# E2E Test Suite Status & Readiness Report — Local APK Store

> **STATUS: READY / COMPLETE**  
> **SUITE VERIFICATION PASS RATE: 100% (39/39 Tests Passing)**  
> **DATE: 2026-08-04**

---

## 1. Test Suite Summary Table

| Test Tier | Scope & Focus | Required Tests | Executed Tests | Passed | Failed | Status |
|-----------|---------------|----------------|----------------|--------|--------|--------|
| **Tier 1** | Feature Coverage (R1, R2, R3) | >= 15 | 15 | 15 | 0 | **PASSED** |
| **Tier 2** | Boundary & Corner Cases (R1, R2, R3) | >= 15 | 15 | 15 | 0 | **PASSED** |
| **Tier 3** | Pairwise & Multi-Feature Interactions | >= 4 | 4 | 4 | 0 | **PASSED** |
| **Tier 4** | Real-World End-to-End Workflows | >= 5 | 5 | 5 | 0 | **PASSED** |
| **TOTAL** | **Full Opaque-Box E2E Coverage** | **>= 39** | **39** | **39** | **0** | **PASSED (Code 0)** |

---

## 2. Official Runner Invocation Command

To execute the complete E2E test suite across Tiers 1-4 and verify results:

```powershell
powershell -ExecutionPolicy Bypass -File tests\run_e2e_tests.ps1
```

*(Alternatively via Python directly: `python tests/run_e2e_tests.py`)*

---

## 3. Detailed Feature Verification Checklist

### Feature R1: Win32 UI Rendering & Aesthetic Compliance
- [x] **R1.1 OS Visual Styles & Backfill Brush**: Verified `InitCommonControlsEx`, manifest dependency for Common-Controls 6.0, and `WM_CTLCOLORSTATIC` static background handling defaulting to OS styling.
- [x] **R1.2 Non-Overlapping Control Geometry**: Verified mathematical bounding box calculations for 850x600 window layout with zero bounding rect intersections.
- [x] **R1.3 SysListView32 Control & Dynamic WM_SIZE**: Verified listview creation with `SysListView32` class and dynamic `WM_SIZE` client area recalculation using `TCM_ADJUSTRECT`.
- [x] **R1.4 Segoe UI Font, Dialogs & Aesthetic Compliance**: Verified Segoe UI font initialization (Semibold/Regular), Menubar, Toolbar, About/Help/Settings dialog classes, Tooltips, 3D inset frame, and Chin panel styling.
- [x] **R1.5 Log File Path & Viewer Launch**: Verified `%SystemDrive%\EliteSoftware\Logs\Manager_App.log` path logger creation, formatting, appending, and log viewer launching.

### Feature R2: APK Icon Extraction & Display
- [x] **R2.1 ZIP Internal PNG Extraction**: Verified extraction of internal icon PNG files from APK archives into `Manager_App/images/<package_name>_icon.png`.
- [x] **R2.2 XML Adaptive & Missing Icon Fallbacks**: Verified fallback resolution when primary icon is vector XML (`ic_launcher.xml`) or missing, using secondary raster PNG or default fallback image.
- [x] **R2.3 HTTP `/images/<icon>` Endpoint**: Verified image file serving via HTTP GET `/images/`, returning status 200 OK, `Content-Type: image/png`, and correct image byte stream.
- [x] **R2.4 Win32 HIMAGELIST & ListView Binding**: Verified GDI+ image loading, HBITMAP conversion, `HIMAGELIST` creation (`ImageList_Create`), and `SysListView32` icon assignment (`LVM_SETIMAGELIST`).
- [x] **R2.5 Android Client Intent Extra Alignment**: Verified Intent extra parameter alignment (`"app_data"` JSON payload containing `"icon"`, `"name"`, `"package_name"`) in `MainActivity.java` and `AppDetailActivity.java`.

### Feature R3: Server Monitor & Connected Clients
- [x] **R3.1 Heartbeat Endpoint (`POST /api/heartbeat`)**: Verified registration of client IP address, device name, client_id, and last active timestamp in server session map.
- [x] **R3.2 Repeat Heartbeat Timestamp Updates**: Verified duplicate heartbeats from single client update `last_active` timestamp without creating duplicate client list entries.
- [x] **R3.3 Disconnect Endpoint (`POST /api/disconnect`)**: Verified immediate removal of client session from server memory database upon disconnect request.
- [x] **R3.4 15-Second Inactive Timeout Purge**: Verified background cleanup logic purging clients inactive for > 15 seconds.
- [x] **R3.5 Server Monitor SysListView32 UI Refresh**: Verified Server Monitor client list UI (`hwndClientList`) rendering columns (IP Address, Device Name, Last Active) on 1-second `WM_TIMER` tick.

---

## 4. Test Files Inventory
- `tests/test_tier1_feature_coverage.py`: Tier 1 Feature Unit/Integration Tests
- `tests/test_tier2_boundary_corner.py`: Tier 2 Edge Case & Stress Tests
- `tests/test_tier3_cross_feature.py`: Tier 3 Cross-Feature Pairwise Interaction Tests
- `tests/test_tier4_real_world.py`: Tier 4 Real-World Scenario Workflow Tests
- `tests/run_e2e_tests.py`: Python Execution Runner
- `tests/run_e2e_tests.ps1`: PowerShell Execution Script


# Local APK Store (EliteSoftwareTech Co.)

## Overview
The **Local APK Store** is a private, self-hosted backend and client ecosystem designed to act as an internal app repository. It is heavily inspired by the classic "Android Market" interface, aiming to provide a nostalgic yet fully functional experience for downloading, updating, and discovering APKs on your local network.

This project encompasses three main components:
1. **Backend Server (Node.js/Express):** A robust, lightweight server running on all local network adapters on a dedicated port. It serves APK files, metadata (descriptions, versioning, screenshots), and handles search queries.
2. **Android Client App:** A retro-styled Android application reminiscent of the pre-Play Store era. It consumes the backend API to display available applications, fetch screenshots, and trigger the download/installation of APK files directly on the device.
3. **Server Manager GUI (C++ Win32 / EliteSoftware Standard):** A Windows desktop application built with legacy Win32/WinForms aesthetics to manage the server. It allows administrators to easily upload new APKs, modify app metadata, and monitor server status without relying on a CLI.

## Scope & Plans
*   **Phase 1: Foundation & Backend Setup**
    *   Initialize project structure and documentation.
    *   Set up local Git repository and private GitHub synchronization.
    *   Configure Windows Firewall to open the dedicated server port (e.g., 8443).
    *   Develop the Node.js backend to serve JSON metadata and static APK/image files.
*   **Phase 2: Management GUI**
    *   Develop the Server Manager adhering strictly to EliteSoftwareTech Co. GUI Guidelines (Legacy Win32 style, 3D insets, no modern flat design).
    *   Implement features to parse uploaded APKs, prompt for metadata, and automatically structure them in the backend's datastore.
*   **Phase 3: Android Client Development**
    *   Scaffold an Android project with a nostalgic "Android Market" UI (green/white/black theme, classic tabs/lists).
    *   Implement networking to fetch the backend catalog.
    *   Implement APK downloading and Android `PackageInstaller` intents for installing apps.
*   **Phase 4: Polish & Expansion**
    *   Implement search functionality.
    *   Support for multiple versions of the same application.
    *   Continuous bug fixing and strict error handling/logging.

## Development Guidelines
This project adheres to the **EliteSoftwareTech Co. - Antigravity Suite GUI Development Guidelines (v1.2.0.0)**.
*   All GUIs (C++ or PowerShell) must utilize native Win32/WinForms aesthetics. Modern flat design is forbidden.
*   UIs must feature a distinct title banner, 3D-inset active areas, and standard legacy button nomenclature ("Okay", "Cancel", "Apply").
*   Strict error handling is mandatory, and logs must be written to `%SystemDrive%\EliteSoftware\Logs\LocalAPKStore.log`.
*   All repositories are private by default.

## How to Use
*(This section will be expanded as components are finalized)*

1.  **Start the Backend:** Run `npm start` in the `Server` directory.
2.  **Manage Apps:** Open the `ServerManager` executable to add new apps, versions, and screenshots to the repository.
3.  **Client Access:** Install the `LocalAPKStore.apk` on your Android device. Ensure the device is connected to the same local network as the server to browse and download apps.


---
---
---
<*Changelog*>
---
---
---


All notable changes to the Local APK Store ecosystem will be documented in this file.

## [Unreleased]
### Added
- **Expanded Project Scope:** The client app is now named **"Elite App Marketplace"**. It will support categorization, tags, user reviews, comments, and the ability to seamlessly downgrade, upgrade, uninstall, and reinstall APK versions via Shizuku.
- **APK Signing Pipeline:** Integrated plans to use the `Elite-EasySigner` certificate (`EliteSoftware_Special.pfx`) to strictly sign all uploaded APKs and the App Store client itself.
- **Certificate Deployment:** Added feature scope to allow installing the `EliteSoftware_Special.cer` root certificate directly from the Elite App Marketplace's settings menu onto the Android device.
- `apk_parser.py` to extract Android manifest metadata (package name, version, icon) using `pyaxmlparser`.
- Support for uploading icons and multiple screenshots in the Python backend API (`server.py`).
- `gemini.md` file to track operational instructions and automated Git pushing requirements.
- Base architecture for the Python backend (`Server/server.py`), Android client stub (`Client_App/`), and C++ Server Manager GUI (`Manager_App/`).
- Enforced CRLF line endings via `.gitattributes`.

### Changed
- **Monolithic C++ Architecture:** Completely deprecated and deleted the Python Flask backend server and all Python helper scripts. The C++ `Elite_App_Marketplace-Server.exe` is now a massive monolithic application that natively hosts the HTTP API over port 8443 (via `cpp-httplib`) and manages the JSON database (via `nlohmann-json`) while running the Win32 GUI, keeping everything contained in a single compiled binary without external script dependencies.
- **Branding Unity:** Renamed the C++ Server Manager application executable to `Elite_App_Marketplace-Server.exe` to unify the entire project's branding across the frontend client and backend manager.
### Added
- **Formal Releases (v1.0.0):** Published `server-v1.0.0` and `client-v1.0.0` GitHub releases with attached pre-compiled binaries (`Elite_App_Marketplace-Server.exe` and `Elite_App_Marketplace-Client.apk`) for easy mobile installation.
- **Android Client Initialization:** Built the baseline Android Studio project for the Elite App Marketplace client with a legacy "Android Market" Holo aesthetic.
- **Built-in Certificate Deployment:** Embedded the `EliteSoftware_Special.cer` root certificate directly inside the Android app's raw resources. Implemented Android's native `KeyChain.createInstallIntent()` API to prompt users to install the trusted CA when clicking the settings icon.
- **Application Iconography:** Embedded the custom `Elite_App_Marketplace.ico` natively into the C++ Server Manager executable using Win32 resource headers, applying it to both the Windows taskbar and internal legacy title banner. Also mapped the `Elite_App_Marketplace.png` as the Android client's primary launcher icon.

