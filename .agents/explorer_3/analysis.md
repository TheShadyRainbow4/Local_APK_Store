# Requirement R3 Analysis Report: Server Monitor Updates & Connected Clients

## Executive Summary
This report presents a thorough investigation and architectural blueprint for **Requirement R3: Server Monitor Updates** in the Local APK Store project. The objective is to enhance the C++ Win32 Server Manager (`Manager_App`) to maintain and display a real-time list of connected Android clients showing their **IP Address** and **Device Name**, while automatically removing disconnected clients upon exit or network timeout.

---

## 1. Existing System Architecture & Current Limitations

### 1.1 Server Infrastructure (`Manager_App/main.cpp`)
* **HTTP Framework**: Embedded `httplib::Server` (cpp-httplib) running in a C++ background thread (`ServerThread`), default port `8552`.
* **UDP Discovery**: `UDPDiscoveryThread` listens on UDP port `8552` for `"ELITE_MARKET_DISCOVER"` and responds with `"ELITE_MARKET_HERE"`.
* **Endpoints**:
  * `GET /api/apps` — Serves app catalog JSON.
  * `/apks` & `/images` — Static file mounts for APK downloads and app icon assets.
* **Server Monitor Tab UI**: Currently contains only a read-only `EDIT` control (`hwndLog`) for server logging, a `STATIC` label (`hwndServerStatus`), and a toggle `BUTTON` (`btnToggleServer`).
* **Deficiency**: The server has zero state management for client connections. Standard HTTP requests are handled statelessly, logged to text, and discarded.

### 1.2 Client Infrastructure (`Client_App/.../MainActivity.java`)
* **Discovery & Fetch**: Sends UDP broadcast to find the server, then makes HTTP GET requests (`GET /api/apps`) to fetch data.
* **Deficiency**: The client does not transmit its device identification model (e.g. `android.os.Build.MODEL` or `Build.MANUFACTURER + " " + Build.MODEL`) to the server. There is no active heartbeat mechanism or session registration.

---

## 2. Technical Solution Architecture for Requirement R3

To achieve real-time tracking with IP Address, Device Name display, and automatic disconnection handling, the system is designed across three tiers:

```
+----------------------------+     HTTP POST /api/heartbeat     +----------------------------------+
|      Android Client        | -------------------------------> |         C++ Web Server           |
| (MainActivity.java)        |                                  |        (Manager_App)             |
| - Collects Device Name     | <------------------------------- | - Receives remote_addr & name    |
| - Sends periodic heartbeat |      HTTP Response 200 OK        | - Updates thread-safe client map |
| - Sends /api/disconnect    |                                  | - Cleanup thread purges stale    |
+----------------------------+                                  +----------------------------------+
                                                                                  |
                                                                         Timer / Window Msg
                                                                                  v
                                                                +----------------------------------+
                                                                |    Server Monitor Win32 UI       |
                                                                | - ListView: IP | Device Name     |
                                                                | - Auto-refreshes in real-time    |
+---------------------------------------------------------------+----------------------------------+
```

---

## 3. Detailed Component Specifications

### 3.1 Client-Side Device Identification & Heartbeat Protocol

#### A. Device Name Extraction (Android Java)
In `MainActivity.java`:
```java
public String getDeviceName() {
    String manufacturer = android.os.Build.MANUFACTURER;
    String model = android.os.Build.MODEL;
    if (model.toLowerCase().startsWith(manufacturer.toLowerCase())) {
        return capitalize(model);
    } else {
        return capitalize(manufacturer) + " " + model;
    }
}

private String capitalize(String s) {
    if (s == null || s.length() == 0) return "";
    char first = s.charAt(0);
    if (Character.isUpperCase(first)) return s;
    return Character.toUpperCase(first) + s.substring(1);
}
```

#### B. Connection & Heartbeat Loop
* **Client Identification**: Unique client ID derived from `Settings.Secure.getString(getContentResolver(), Settings.Secure.ANDROID_ID)`.
* **Payload**:
  ```json
  {
    "client_id": "a1b2c3d4e5f6",
    "device_name": "Google Pixel 7"
  }
  ```
* **Schedule**:
  * Send `POST http://<server_ip>:8552/api/heartbeat` immediately upon server discovery.
  * Schedule a repeating `ScheduledExecutorService` timer every 5 seconds.
  * On app exit/stop (`onStop()`), send `POST http://<server_ip>:8552/api/disconnect`.

---

### 3.2 Server-Side Session Tracking & Cleanup Thread

#### A. Thread-Safe Registry (`Manager_App/main.cpp`)
```cpp
#include <map>
#include <mutex>
#include <chrono>

struct ClientInfo {
    std::string client_id;
    std::string ip_address;
    std::string device_name;
    std::chrono::steady_clock::time_point last_seen;
};

std::mutex g_clientMutex;
std::map<std::string, ClientInfo> g_connectedClients;
```

#### B. API Handlers in `ServerThread()`
```cpp
svrPtr->Post("/api/heartbeat", [](const httplib::Request& req, httplib::Response& res) {
    try {
        json j = json::parse(req.body);
        std::string clientId = j.value("client_id", req.remote_addr);
        std::string deviceName = j.value("device_name", "Android Device");
        std::string ip = req.remote_addr;

        {
            std::lock_guard<std::mutex> lock(g_clientMutex);
            g_connectedClients[clientId] = ClientInfo{
                clientId, ip, deviceName, std::chrono::steady_clock::now()
            };
        }
        res.set_content("{\"status\":\"ok\"}", "application/json");
    } catch (...) {
        res.status = 400;
    }
});

svrPtr->Post("/api/disconnect", [](const httplib::Request& req, httplib::Response& res) {
    try {
        json j = json::parse(req.body);
        std::string clientId = j.value("client_id", req.remote_addr);
        {
            std::lock_guard<std::mutex> lock(g_clientMutex);
            g_connectedClients.erase(clientId);
        }
        res.set_content("{\"status\":\"disconnected\"}", "application/json");
    } catch (...) {
        res.status = 400;
    }
});
```

#### C. Automatic Timeout Purge Thread (Ungraceful Disconnections)
To gracefully handle network disconnections, app crashes, or Wi-Fi drops without explicit `/api/disconnect`:
```cpp
const int CLIENT_TIMEOUT_SECONDS = 15;

void ClientCleanupThread() {
    while (serverRunning) {
        std::this_thread::sleep_for(std::chrono::seconds(3));
        auto now = std::chrono::steady_clock::now();
        std::lock_guard<std::mutex> lock(g_clientMutex);
        for (auto it = g_connectedClients.begin(); it != g_connectedClients.end(); ) {
            auto elapsed = std::chrono::duration_cast<std::chrono::seconds>(now - it->second.last_seen).count();
            if (elapsed > CLIENT_TIMEOUT_SECONDS) {
                LogMessage("Client disconnected (timeout): " + it->second.device_name + " (" + it->second.ip_address + ")");
                it = g_connectedClients.erase(it);
            } else {
                ++it;
            }
        }
    }
}
```

---

### 3.3 Server Monitor Win32 Real-Time UI Updates

#### A. UI Control Layout Specification
Add a native Win32 `ListView` control to Tab 1 ("Server Monitor"):
* **Controls**:
  * `lblConnectedClients`: Static label showing `Connected Clients (X):`
  * `hwndClientList`: `WC_LISTVIEW` with styles `LVS_REPORT | LVS_SINGLESEL | WS_CHILD | WS_VISIBLE | WS_CLIPSIBLINGS`
  * Extended ListView styles: `LVS_EX_FULLROWSELECT | LVS_EX_GRIDLINES`
* **Columns**:
  1. `IP Address` (width: 160px)
  2. `Device Name` (width: 240px)
  3. `Last Active` (width: 120px)

```cpp
HWND hwndClientList = NULL;
HWND lblConnectedClients = NULL;
```

#### B. Dynamic Window Layout (`WM_SIZE`)
Inside `WM_SIZE` under Server Monitor view:
* `hwndLog`: `tabRect.left`, `tabRect.top`, `tabRect.right - tabRect.left`, `180` (top half).
* `lblConnectedClients`: `tabRect.left`, `tabRect.top + 190`, `250`, `20`.
* `hwndClientList`: `tabRect.left`, `tabRect.top + 215`, `tabRect.right - tabRect.left`, `tabRect.bottom - tabRect.top - 260`.
* `hwndServerStatus` & `btnToggleServer`: anchored at bottom.

#### C. Thread-Safe UI Refreshing
A 1000ms Win32 timer (`SetTimer(hwnd, 1002, 1000, NULL)`) triggers UI update on the main GUI thread safely:
```cpp
void RefreshClientListView() {
    if (!hwndClientList) return;
    
    std::lock_guard<std::mutex> lock(g_clientMutex);
    
    // Preserve focus / redraw state
    SendMessage(hwndClientList, WM_SETREDRAW, FALSE, 0);
    ListView_DeleteAllItems(hwndClientList);
    
    int index = 0;
    auto now = std::chrono::steady_clock::now();
    for (const auto& [id, client] : g_connectedClients) {
        LVITEM lvi = {0};
        lvi.mask = LVIF_TEXT;
        lvi.iItem = index;
        lvi.iSubItem = 0;
        lvi.pszText = (LPSTR)client.ip_address.c_str();
        ListView_InsertItem(hwndClientList, &lvi);
        
        ListView_SetItemText(hwndClientList, index, 1, (LPSTR)client.device_name.c_str());
        
        auto secAgo = std::chrono::duration_cast<std::chrono::seconds>(now - client.last_seen).count();
        std::string statusStr = std::to_string(secAgo) + "s ago";
        ListView_SetItemText(hwndClientList, index, 2, (LPSTR)statusStr.c_str());
        
        index++;
    }
    
    SendMessage(hwndClientList, WM_SETREDRAW, TRUE, 0);
    InvalidateRect(hwndClientList, NULL, TRUE);
    
    std::string countStr = "Connected Clients (" + std::to_string(g_connectedClients.size()) + "):";
    SetWindowText(lblConnectedClients, countStr.c_str());
}
```

---

## 4. Summary & Implementation Steps for Implementer

1. **Client Modifications (`Client_App`)**:
   - Add `getDeviceName()` and `startHeartbeat()` methods to `MainActivity.java`.
   - Send periodic HTTP POST `/api/heartbeat` requests with JSON `{"client_id": ..., "device_name": ...}`.
   - Send `/api/disconnect` on app shutdown.

2. **Server Modifications (`Manager_App/main.cpp`)**:
   - Add client map registry and mutex.
   - Implement `/api/heartbeat` and `/api/disconnect` endpoints.
   - Implement `ClientCleanupThread()` for purging inactive clients after 15 seconds.
   - Add `hwndClientList` `ListView` control to Server Monitor tab.
   - Configure 1s timer to refresh the `ListView` from the client map.

3. **Compilation & Testing**:
   - Compile using `g++` via `build.bat`.
   - Test client connection, verify IP Address & Device Name appear in real-time, test graceful exit, and test 15s timeout disconnection.
