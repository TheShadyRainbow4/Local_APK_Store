# Elite Window Framework API 

The Elite Window Framework provides a robust, intent-based API allowing third-party applications, shell scripts (via ADB/Shizuku), and automation tools (like Tasker or MacroDroid) to spawn native floating Aero windows.

## Overview
You can launch either a **native Android application package** (which will run inside an isolated virtual display) or a **web URL** (which will render inside an accelerated WebView). 

All requests are handled by broadcasting an intent to the `com.elitesoftware.appmarketplace.LAUNCH_WINDOW` action.

---

## Intent Specifications

**Action:** `com.elitesoftware.appmarketplace.LAUNCH_WINDOW`
**Target Package:** `com.elitesoftware.appmarketplace`
**Component (Receiver):** `com.elitesoftware.appmarketplace.WindowApiReceiver`

### Extras (Parameters)
| Key | Type | Description | Required |
| :--- | :--- | :--- | :--- |
| `title` | `String` | The text to display in the Aero Titlebar. | No (Defaults to App Name/URL) |
| `package` | `String` | The application package name to launch inside the virtual display (e.g., `com.android.settings`). | Yes* |
| `url` | `String` | The web address to load inside a floating WebView. | Yes* |

*\*Note: You must provide either `package` or `url`. If both are provided, `package` takes priority.*

---

## Usage Examples

### 1. Launching via ADB / Shell (Shizuku / Dhizuku)
If you are running scripts on the device or sending commands via ADB, use the `am broadcast` command.

**Launch an App (e.g., Chrome):**
```bash
am broadcast -a com.elitesoftware.appmarketplace.LAUNCH_WINDOW \
    -n com.elitesoftware.appmarketplace/.WindowApiReceiver \
    --es package "com.android.chrome" \
    --es title "Floating Chrome"
```

**Launch a Webpage:**
```bash
am broadcast -a com.elitesoftware.appmarketplace.LAUNCH_WINDOW \
    -n com.elitesoftware.appmarketplace/.WindowApiReceiver \
    --es url "https://google.com" \
    --es title "Google Search"
```

### 2. Launching via Java / Kotlin (Third-Party Android Apps)
Any third-party app can broadcast to this receiver to integrate with the Elite Window Framework.

```java
Intent intent = new Intent("com.elitesoftware.appmarketplace.LAUNCH_WINDOW");
intent.setComponent(new ComponentName(
    "com.elitesoftware.appmarketplace", 
    "com.elitesoftware.appmarketplace.WindowApiReceiver"
));

// Set parameters
intent.putExtra("package", "com.sec.android.app.calculator");
intent.putExtra("title", "Samsung Calculator");

// Send Broadcast
context.sendBroadcast(intent);
```

### 3. Launching via Tasker / MacroDroid
You can easily hook the window framework into your automated workflows.

1. Create a new **Send Intent** action.
2. **Action:** `com.elitesoftware.appmarketplace.LAUNCH_WINDOW`
3. **Package:** `com.elitesoftware.appmarketplace`
4. **Class:** `com.elitesoftware.appmarketplace.WindowApiReceiver`
5. **Extra 1:** `package:com.android.settings`
6. **Extra 2:** `title:System Settings`
7. **Target:** `Broadcast Receiver`

---

## Security & Limitations
- **No Background Launch Limits:** Because the API relies on a BroadcastReceiver passing the intent to a `SYSTEM_ALERT_WINDOW` authorized service, you bypass Android 10+ background activity limitations. Windows will instantly spawn even if your app is in the background.
- **App Support:** Not all apps support being rendered on a Virtual Display. If an app explicitly defines `android:resizeableActivity="false"`, it may refuse to render correctly or crash its internal view context.
