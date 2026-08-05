## 2026-08-05T00:50:06Z
You are the Sub-Orchestrator for Milestone 3 (Server Monitor Connected Clients Real-Time List).
Working directory for metadata: C:\Users\Administrator\Desktop\Local_APK_Store\.agents\sub_orch_m3

Scope & Target:
- Read `C:\Users\Administrator\Desktop\Local_APK_Store\ORIGINAL_REQUEST.md` and `C:\Users\Administrator\Desktop\Local_APK_Store\PROJECT.md`.
- Read analysis and handoff reports from Explorer 3 in `C:\Users\Administrator\Desktop\Local_APK_Store\.agents\explorer_3\`.
- Execute Milestone 3 features:
  1. **Client Heartbeat & Disconnect Protocol (Java)**: In `Client_App/app/src/main/java/com/elitesoftware/appmarketplace/MainActivity.java`, implement a periodic background heartbeat service sending HTTP POST `/api/heartbeat` with JSON body `{"client_id":"...", "device_name":"..."}` (using `Build.MANUFACTURER + " " + Build.MODEL`). Send HTTP POST `/api/disconnect` on app pause/stop.
  2. **Server Session Management & Timeout Cleanup (C++)**: In `Manager_App/main.cpp`, implement thread-safe global registry `g_connectedClients` (`std::map<std::string, ClientInfo>` guarded by mutex), HTTP endpoints `/api/heartbeat` and `/api/disconnect`, and a 15-second timeout cleanup thread (`ClientCleanupThread`).
  3. **Server Monitor Client List UI (C++)**: In `Manager_App/main.cpp`, add a `SysListView32` control (`hwndClientList`) with columns `IP Address`, `Device Name`, `Last Active` under the Server Monitor tab, updated safely via 1-second `WM_TIMER`.

Iteration Loop:
1. Spawn Explorer/Worker to implement C++ changes in `Manager_App/main.cpp` (compile via `Manager_App/build.bat`) and Java changes in `Client_App/`.
2. Spawn Reviewers to check concurrency safety, network endpoints, and UI list updates.
3. Spawn Challengers to empirically verify client connection, real-time list updating, and disconnection timeout handling.
4. Spawn Forensic Auditor (`teamwork_preview_auditor`) to perform integrity verification.
5. Record gate status in `GATE_STATUS.md`.

Upon Gate PASS:
- Mark M3 as DONE in `PROJECT.md`.
- Write handoff report in `C:\Users\Administrator\Desktop\Local_APK_Store\.agents\sub_orch_m3\handoff.md`.
- Send completion message to parent (03746e5f-4965-4314-909a-9db0c7eafb3f).
