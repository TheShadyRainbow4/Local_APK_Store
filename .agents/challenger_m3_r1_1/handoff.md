# Milestone 3 Handoff Report - Server Monitor Connected Clients Real-Time List

## 1. Observation

### 1.1 Compilation Verification
- **Command executed**: `cmd /c "cd /d C:\Users\Administrator\Desktop\Local_APK_Store\Manager_App && build.bat"`
- **Result**: Exit code `0`.
- **Output**:
  ```text
  Building Manager App...
  Build successful: LocalAPKStore.exe
  ```
- **Binaries produced**: `LocalAPKStore.exe` and copied to `Elite_App_Marketplace-Server.exe` (size: 10,157,031 bytes).

### 1.2 REST API Verification
- **`/api/heartbeat`**:
  - `POST {"client_id":"c1", "device_name":"Pixel 8"}` -> HTTP 200 `{"status":"ok"}`.
  - `POST {"device_name":"Anonymous Tablet"}` (missing `client_id`) -> HTTP 200 `{"status":"ok"}` (uses `req.remote_addr` as fallback ID).
  - `POST {invalid_json` -> HTTP 400 `{"error":"invalid json"}`.
- **`/api/disconnect`**:
  - `POST {"client_id":"c1"}` -> HTTP 200 `{"status":"disconnected"}`.
  - Erases entry from `g_connectedClients` map immediately.

### 1.3 Empirical Failure Modes Observed

#### Failure Mode A: Cross-Thread `SendMessageA` GUI Deadlock in `ClientCleanupThread`
- **File**: `Manager_App/main.cpp`, lines 672-689 (`ClientCleanupThread`) and lines 118-145 (`LogToFileAndUI`).
- **Code Observation**:
  ```cpp
  // Line 678: ClientCleanupThread acquires g_clientMutex
  std::lock_guard<std::mutex> lock(g_clientMutex);
  for (auto it = g_connectedClients.begin(); it != g_connectedClients.end(); ) {
      if (elapsed > CLIENT_TIMEOUT_SECONDS) {
          // Line 682: Calls LogMessage while holding g_clientMutex!
          LogMessage("Client disconnected (timeout): " + it->second.device_name + " (" + it->second.ip_address + ")");
          it = g_connectedClients.erase(it);
      }
  }
  ```
  Inside `LogMessage` -> `LogToFileAndUI`:
  ```cpp
  // Line 142-143: Synchronous Win32 message call across threads!
  SendMessageA(hwndLog, EM_SETSEL, (WPARAM)l, (LPARAM)l);
  SendMessageA(hwndLog, EM_REPLACESEL, 0, (LPARAM)timestamp.c_str());
  ```
- **Empirical Execution Result**:
  - During test execution, when a client timeout occurred, `Invoke-RestMethod` threw:
    `Invoke-RestMethod : The underlying connection was closed: An unexpected error occurred on a receive.`
  - `ClientCleanupThread` held `g_clientMutex` while blocking inside `SendMessageA` waiting for GUI thread message processing.
  - Concurrently, `WM_TIMER` (fired every 1000ms on GUI thread) called `RefreshClientListView()` which attempted to acquire `g_clientMutex` (line 694).
  - Result: Lock inversion deadlock between Win32 GUI message queue and `g_clientMutex`. Server process crashed / froze.

#### Failure Mode B: Unchecked Socket Bind Failure & False "RUNNING" UI Status
- **File**: `Manager_App/main.cpp`, lines 794-795 (`ServerThread`).
- **Code Observation**:
  ```cpp
  LogMessage("HTTP API Listening on port " + std::to_string(serverPort));
  svrPtr->listen("0.0.0.0", serverPort);
  ```
  And in `StartServer()` (line 805):
  ```cpp
  SetWindowTextA(hwndServerStatus, "Status: RUNNING");
  ```
- **Empirical Execution Result**:
  - When restarting the server while port 8552 was in `TIME_WAIT` (or occupied), `svrPtr->listen()` failed to bind socket (`WSAEADDRINUSE`) and returned `false` immediately.
  - `ServerThread()` exited silently without logging an error.
  - The UI label `hwndServerStatus` continued to display `Status: RUNNING` even though no socket was listening on port 8552.

#### Failure Mode C: Uncached AAPT Lookup Startup Freeze & Unicode Encoding Corruption
- **File**: `Manager_App/main.cpp`, lines 201-228 (`GetAaptPath`) and lines 345-350 (`ExtractApkMetadataAndIcon`).
- **Code Observation**:
  - `GetAaptPath()` returns `""` when `aapt.exe` is not found, leaving `g_aaptPath` empty.
  - On startup, `RefreshAppList()` scans all 43 APKs in `apks/`, invoking `_popen("powershell -Command ...")` 43 consecutive times.
- **Empirical Execution Result**:
  - Server startup blocked for ~70 seconds before `StartServer()` was invoked.
  - Filenames containing non-ASCII / Unicode characters (`♤♡Łŭçƙƴ.Pąṭçĥëř.◇♧.ver.11.8.4.build.1944.apk`, `나눔명조.FlipFont...`) produced verbatim PowerShell syntax errors in console/process output:
    `The string is missing the terminator: '.`
    `Missing ')' in method call.`
    `Unexpected token '~^"",3' in expression or statement.`

---

## 2. Logic Chain

1. **Observation**: `ClientCleanupThread` acquires `g_clientMutex` before checking client timeouts. When a timeout occurs, line 682 calls `LogMessage()`, which invokes `SendMessageA(hwndLog, ...)`.
2. **Deduction**: `SendMessageA` sends a Win32 message across thread boundaries to the GUI thread and synchronously waits for completion.
3. **Observation**: `WM_TIMER` (line 1616) fires every 1000ms on the GUI thread, calling `RefreshClientListView()`, which attempts to acquire `g_clientMutex` at line 694.
4. **Conclusion 1**: Lock inversion deadlock is guaranteed when `ClientCleanupThread` logs a timeout: `ClientCleanupThread` holds `g_clientMutex` and waits for GUI thread to process `SendMessageA`, while GUI thread waits for `g_clientMutex` to execute `RefreshClientListView()`. The server hangs or crashes.
5. **Observation**: `ServerThread()` logs `HTTP API Listening on port 8552` *before* calling `svrPtr->listen("0.0.0.0", serverPort)` and ignores `listen()`'s return value.
6. **Conclusion 2**: If port binding fails (`WSAEADDRINUSE`), `ServerThread` exits immediately while UI displays misleading `Status: RUNNING`.
7. **Observation**: `GetAaptPath()` does not cache negative search results when `aapt.exe` is not found.
8. **Conclusion 3**: Every APK scan launches a blocking PowerShell process via `_popen`. For 43 APKs, startup is delayed by 70+ seconds and non-ASCII filenames break PowerShell command string parsing.

---

## 3. Caveats

- **No code modification constraint**: As an adversarial reviewer, implementation code was not altered in `Manager_App/main.cpp`. All tests were performed empirically via test harnesses written in the workspace metadata directory (`.agents/challenger_m3_r1_1/`).
- **Environment**: Tested on Windows 10/11 x64 environment with MSYS2/MinGW g++ compiler and standard Win32 assemblies.

---

## 4. Conclusion

While the server implementation satisfies basic HTTP endpoints (`/api/heartbeat` and `/api/disconnect`) under single-threaded ideal conditions, empirical stress-testing revealed **three critical system failures**:
1. **Fatal Deadlock**: Cross-thread `SendMessageA` inside `g_clientMutex` during client timeout cleanup deadlocks the GUI thread and HTTP server thread.
2. **Silent Network Failure**: `httplib::Server::listen()` return value is unhandled, resulting in a false "RUNNING" UI state when port binding fails.
3. **Severe Startup Latency**: Uncached `aapt` lookups launch 43 sequential PowerShell subprocesses, causing a 70-second startup freeze and encoding corruptions on Unicode APK filenames.

Because the real-time client monitoring cleanup causes application deadlock and crashes, Milestone 3 cannot be approved in its current state.

**VERDICT: REJECT**

---

## 5. Verification Method

To independently verify these findings:

1. **Re-compilation**:
   ```cmd
   cd /d C:\Users\Administrator\Desktop\Local_APK_Store\Manager_App
   build.bat
   ```
2. **Execute Empirical Test Harness**:
   ```powershell
   powershell -ExecutionPolicy Bypass -File C:\Users\Administrator\Desktop\Local_APK_Store\.agents\challenger_m3_r1_1\run_live_tests.ps1
   ```
3. **Verify Deadlock / Crash**:
   - Send heartbeat POST: `Invoke-RestMethod -Uri "http://127.0.0.1:8552/api/heartbeat" -Method Post -Body '{"client_id":"c1","device_name":"Test"}' -ContentType "application/json"`
   - Wait 15 seconds for `ClientCleanupThread` to trigger timeout cleanup.
   - Observe GUI freeze and HTTP connection crash (`The underlying connection was closed`).
4. **Invalidation Condition**:
   - Fix `ClientCleanupThread` by unlocking `g_clientMutex` before calling `LogMessage` (or using `PostMessageA` instead of `SendMessageA`).
   - Check return code of `svrPtr->listen()` and update status UI accordingly.
   - Cache `g_aaptPath = "NOT_FOUND";` on failed lookup to prevent 70-second startup delay.
