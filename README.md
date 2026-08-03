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
