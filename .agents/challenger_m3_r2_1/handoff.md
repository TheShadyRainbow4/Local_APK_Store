# Handoff Report — Challenger 1 (Milestone 3 Iteration 2)

## 1. Observation

- **Build Execution**:
  `cmd /c "cd /d C:\Users\Administrator\Desktop\Local_APK_Store\Manager_App && build.bat"`
  Output: `Build successful: LocalAPKStore.exe` and copied to `Elite_App_Marketplace-Server.exe`.

- **Empirical Test Execution**:
  - Test Script: `C:\Users\Administrator\Desktop\Local_APK_Store\.agents\challenger_m3_r2_1\debug_test.py`
  - Command: `python debug_test.py`
  - Output:
    ```
    Starting server process...
    Server is listening.
    Sending heartbeat...
    Heartbeat resp: 200
    t=1s: Server still running...
    ...
    t=16s: Server still running...
    CRASH DETECTED at t=17s! Exit code: 3221225477 (0xC0000005 STATUS_ACCESS_VIOLATION)
    ```

- **Subsequent Requests Result**:
  All subsequent requests (`GET /api/apps`, `POST /api/heartbeat`, `POST /api/disconnect`) failed with `<urlopen error [WinError 10061] No connection could be made because the target machine actively refused it>` because the server process crashed and was terminated by the OS.

- **Code Source Inspection** (`Manager_App\main.cpp` lines 139-144 and 748-750):
  ```cpp
  // ClientCleanupThread (Worker Thread):
  for (const auto& logMsg : timedOutLogs) {
      LogMessage(logMsg);
  }

  // LogToFileAndUI (Called from LogMessage):
  if (hwndLog && IsWindow(hwndLog)) {
      std::string timestamp = "[Log] " + msg + "\r\n";
      int l = GetWindowTextLengthA(hwndLog);
      SendMessageA(hwndLog, EM_SETSEL, (WPARAM)l, (LPARAM)l);
      SendMessageA(hwndLog, EM_REPLACESEL, 0, (LPARAM)timestamp.c_str());
  }
  ```

## 2. Logic Chain

1. **Initial Connection**: A client sends `POST /api/heartbeat` with `{"client_id":"crash_test","device_name":"Pixel 8"}`. The client is stored in `g_connectedClients` with timestamp $T_0$.
2. **Timeout Threshold Reached**: At $T_0 + 15\text{s}$, `ClientCleanupThread()` executes its loop, detects that `elapsed > 15` seconds, erases the client from `g_connectedClients`, and builds log string `timedOutLogs.push_back("Client disconnected (timeout): Pixel 8 (127.0.0.1)")`.
3. **Cross-Thread GUI Call**: `ClientCleanupThread()` calls `LogMessage(...)` which invokes `LogToFileAndUI(...)`.
4. **Access Violation Crash**: `LogToFileAndUI()` attempts to update the Win32 edit control `hwndLog` on the main thread from the background worker thread via `SendMessageA(hwndLog, EM_REPLACESEL, 0, (LPARAM)timestamp.c_str())`. Because `timestamp.c_str()` resides on the worker thread's stack memory and Win32 Edit control messages are handled asynchronously/cross-thread, this causes an Access Violation `0xC0000005` (exit code `3221225477` / `-1073741819`), immediately crashing the entire process.
5. **Server Outage**: Because `Elite_App_Marketplace-Server.exe` crashes when any client times out, the server process dies completely, dropping all connections and failing all subsequent HTTP requests (`/api/apps`, `/api/heartbeat`, `/api/disconnect`).

## 3. Caveats

- **No caveats**: The process crash is 100% reproducible upon client timeout.

## 4. Conclusion

While `g_clientMutex` deadlock was avoided by unlocking before logging, calling `SendMessageA` with a local stack pointer from `ClientCleanupThread` to update `hwndLog` causes a fatal `STATUS_ACCESS_VIOLATION` (0xC0000005) crash when any client times out. To fix this safely, GUI logging from background threads must use `PostMessage` with heap-allocated memory or standard thread-safe message posting (`WM_USER` message or thread-safe log queue).

## 5. Verification Method

To independently reproduce the crash:
1. Open PowerShell and run: `python C:\Users\Administrator\Desktop\Local_APK_Store\.agents\challenger_m3_r2_1\debug_test.py`
2. Observe output at `t=17s`–`t=19s`: `CRASH DETECTED! Exit code: 3221225477` (or non-zero exit code).

VERDICT: REJECT
