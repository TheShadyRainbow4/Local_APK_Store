# Handoff Report — Explorer 3 (Requirement R3: Server Monitor Updates)

## 1. Observation
* **Server Implementation (`Manager_App/main.cpp`)**:
  * Line 13: Embeds `httplib.h` for HTTP REST functionality.
  * Line 347–372 (`ServerThread`): Listens on port `8552` (defined on line 46). Exposes endpoints `GET /api/apps`, `/apks`, and `/images`.
  * Line 628–632: Server Monitor tab currently instantiates `hwndLog` (multi-line `EDIT`), `hwndServerStatus` (`STATIC`), and `btnToggleServer` (`BUTTON`). There is no control or logic to track or display connected clients.
  * Line 322–345 (`UDPDiscoveryThread`): Handles UDP discovery broadcasts `"ELITE_MARKET_DISCOVER"`.
* **Client Implementation (`Client_App/.../MainActivity.java`)**:
  * Line 217–269 (`discoverServers`): Sends UDP broadcast `"ELITE_MARKET_DISCOVER"` to port 8552.
  * Line 271–311 (`fetchAppsFromServer`): Connects via HTTP `GET http://<ip>:8552/api/apps`.
  * The Android app does not transmit its device identification model (`android.os.Build.MODEL`) or send any heartbeat requests to the server.

---

## 2. Logic Chain
1. **Goal**: Requirement R3 mandates displaying a real-time list of connected clients (showing IP Address and Device Name) in the Server Monitor UI and removing disconnected clients cleanly.
2. **Client Identification**: Because HTTP GET requests currently carry no device identity, the client must transmit its model/device name (e.g. `android.os.Build.MANUFACTURER + " " + android.os.Build.MODEL`) along with a unique `client_id` via HTTP POST `/api/heartbeat`.
3. **Server Session Management**:
   - HTTP is stateless; therefore, the C++ server must maintain a thread-safe global registry `g_connectedClients` (`std::map<std::string, ClientInfo>` guarded by `g_clientMutex`).
   - When `/api/heartbeat` is called, `req.remote_addr` captures the client IP Address, and the body provides the Device Name.
   - A background thread (`ClientCleanupThread`) periodically checks `last_seen` timestamps and removes clients whose last heartbeat exceeds `15` seconds (handling ungraceful disconnects / crashes).
   - An explicit `/api/disconnect` endpoint allows immediate removal when the app stops gracefully.
4. **Server Monitor UI Enhancement**:
   - In `Manager_App/main.cpp`, add a native Win32 `ListView` control (`hwndClientList`) with columns `IP Address`, `Device Name`, and `Last Active` under the Server Monitor tab (`hwndTab` index 1).
   - Set up a 1-second Win32 GUI timer (`WM_TIMER`) to safely update `hwndClientList` from `g_connectedClients` on the main UI thread.

---

## 3. Caveats
* **Network Topology**: `req.remote_addr` extracts the direct IP connecting to `httplib`. If clients connect through NAT gateways or proxies, multiple devices could share an IP address; using `client_id` (e.g. `ANDROID_ID`) as the primary key ensures distinct client tracking regardless of IP duplication.
* **Firewall / Port Permissions**: UDP discovery on port 8552 and HTTP server on port 8552 must remain open in Windows Firewall.
* **Read-Only Scope**: This report is produced during a read-only investigation phase. Source code in `Manager_App` and `Client_App` has not been modified yet. Full implementation instructions and code specifications are provided for the implementer agent.

---

## 4. Conclusion
Requirement R3 can be completely satisfied without external dependencies by:
1. Adding periodic heartbeat HTTP POST requests (`/api/heartbeat` and `/api/disconnect`) carrying device metadata in `Client_App/app/src/main/java/com/elitesoftware/appmarketplace/MainActivity.java`.
2. Adding a thread-safe client map, HTTP heartbeat handlers, and a 15-second timeout cleanup thread in `Manager_App/main.cpp`.
3. Adding a native Win32 `ListView` (`WC_LISTVIEW`) with Report view to the Server Monitor tab, updated every second via a Win32 timer.

Full architectural details and complete code snippets are documented in `C:\Users\Administrator\Desktop\Local_APK_Store\.agents\explorer_3\analysis.md`.

---

## 5. Verification Method
1. **Build Verification**:
   - Compile `Manager_App` by executing `Manager_App\build.bat` using MinGW `g++`.
   - Verify `Elite_App_Marketplace-Server.exe` builds cleanly with 0 errors.
2. **Functional & UI Verification**:
   - Run `Elite_App_Marketplace-Server.exe` and select the "Server Monitor" tab.
   - Launch `Client_App` or issue a test curl command:
     `curl -X POST http://localhost:8552/api/heartbeat -d "{\"client_id\":\"test1\", \"device_name\":\"Pixel 7\"}"`
   - Observe `hwndClientList` in Server Monitor tab: IP Address (`127.0.0.1`) and Device Name (`Pixel 7`) must appear immediately.
   - Stop client / curl requests: After 15 seconds, verify `ClientCleanupThread` detects the timeout and the client is automatically removed from the UI list.
