# Changelog

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
