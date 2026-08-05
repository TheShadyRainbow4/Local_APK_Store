## 2026-08-05T00:50:46Z
You are the Worker for Milestone 3 (Server Monitor Connected Clients Real-Time List).
Working directory for metadata: C:\Users\Administrator\Desktop\Local_APK_Store\.agents\worker_m3_r1

Read the following files for specification and requirements:
1. `C:\Users\Administrator\Desktop\Local_APK_Store\ORIGINAL_REQUEST.md`
2. `C:\Users\Administrator\Desktop\Local_APK_Store\PROJECT.md`
3. `C:\Users\Administrator\Desktop\Local_APK_Store\.agents\explorer_3\analysis.md`
4. `C:\Users\Administrator\Desktop\Local_APK_Store\.agents\explorer_3\handoff.md`

Your tasks:
1. **Client Heartbeat & Disconnect Protocol (Java)**:
   In `Client_App/app/src/main/java/com/elitesoftware/appmarketplace/MainActivity.java`:
   - Implement device name formatting helper (`Build.MANUFACTURER + " " + Build.MODEL`).
   - Derive unique client ID (`Settings.Secure.ANDROID_ID` or fallback UUID).
   - Implement periodic background heartbeat service sending HTTP POST `/api/heartbeat` with JSON body `{"client_id":"...", "device_name":"..."}` every 5 seconds after server discovery.
   - Send HTTP POST `/api/disconnect` with JSON body `{"client_id":"..."}` on app stop/pause (`onStop()`).

2. **Server Session Management & Timeout Cleanup (C++)**:
   In `Manager_App/main.cpp`:
   - Define `ClientInfo` struct (`client_id`, `ip_address`, `device_name`, `last_seen`).
   - Create thread-safe global registry `g_connectedClients` (`std::map<std::string, ClientInfo>` guarded by `std::mutex g_clientMutex`).
   - Register HTTP endpoints `/api/heartbeat` and `/api/disconnect` in `ServerThread()`:
     - `/api/heartbeat` updates or inserts client entry with remote IP, device name, and `steady_clock::now()`.
     - `/api/disconnect` erases client entry from `g_connectedClients`.
   - Implement `ClientCleanupThread()` running while `serverRunning` is true: checks every 3 seconds for clients with `last_seen` older than 15 seconds, removes them, and logs timeout messages.

3. **Server Monitor Client List UI (C++)**:
   In `Manager_App/main.cpp`:
   - Under Tab 1 (Server Monitor tab), create `lblConnectedClients` (`STATIC`) and `hwndClientList` (`SysListView32` with `LVS_REPORT | LVS_SINGLESEL | WS_CHILD | WS_VISIBLE | WS_CLIPSIBLINGS` and extended styles `LVS_EX_FULLROWSELECT | LVS_EX_GRIDLINES`).
   - Add columns: `IP Address` (width 160), `Device Name` (width 240), `Last Active` (width 120).
   - Adjust `WM_SIZE` tab 1 layout so `hwndLog` takes upper section and `hwndClientList` takes lower section above the status controls.
   - Configure a 1-second `WM_TIMER` (`SetTimer(hwnd, 1002, 1000, NULL)`) in `WndProc` calling `RefreshClientListView()` to safely update items in `hwndClientList` from `g_connectedClients` on the UI thread (using `WM_SETREDRAW`, `ListView_DeleteAllItems`, populating rows, updating label text `Connected Clients (N):`).

4. **Build & Verify**:
   - Run `Manager_App\build.bat` in `Manager_App` directory to compile `Elite_App_Marketplace-Server.exe`.
   - Ensure the executable builds cleanly with 0 errors.
   - Test starting the server and verifying the `/api/heartbeat` and `/api/disconnect` endpoints with curl/requests.

MANDATORY INTEGRITY WARNING:
DO NOT CHEAT. All implementations must be genuine. DO NOT hardcode test results, create dummy/facade implementations, or circumvent the intended task. A teamwork_preview_auditor will independently verify your work. Integrity violations WILL be detected and your work WILL be rejected.

Write your report to `C:\Users\Administrator\Desktop\Local_APK_Store\.agents\worker_m3_r1\handoff.md` including build/test logs and file changes.
When finished, send a message to the sub-orchestrator parent.
