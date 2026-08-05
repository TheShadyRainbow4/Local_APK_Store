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
### Manager_App ↔ Client_App
- `GET /api/apps` -> JSON array of apps: `[{"id":"...", "name":"...", "icon":"/images/<id>.png", ...}]`
- `POST /api/heartbeat` -> Body JSON `{"client_id":"...", "device_name":"..."}` -> Server updates IP and last active time.
- `POST /api/disconnect` -> Body JSON `{"client_id":"..."}` -> Server removes client immediately.
- `GET /images/<icon_name>` -> Serves PNG icon file.

## Code Layout
- `Manager_App/main.cpp` — Main Win32 window, server threads, HTTP API routes, UI layout, Win32 controls
- `Manager_App/build.bat` — MinGW build script for Manager App
- `Client_App/app/src/main/java/com/elitesoftware/appmarketplace/MainActivity.java` — Android store home screen, HTTP/UDP discovery, heartbeat service
- `Client_App/app/src/main/java/com/elitesoftware/appmarketplace/AppDetailActivity.java` — Android store app details screen
