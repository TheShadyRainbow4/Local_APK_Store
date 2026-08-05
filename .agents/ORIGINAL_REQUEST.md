# Original User Request

## 2026-08-04T20:28:23-04:00

# Teamwork Project Prompt — Draft

> Status: Launched
> Goal: Craft prompt → get user approval → delegate to teamwork_preview

Fix UI rendering and functional issues in the Local APK Store application, automatically extract and display internal APK icons, and add a connected client list to the server monitor.

Working directory: C:\Users\Administrator\Desktop\Local_APK_Store
Integrity mode: development

## Requirements

### R1. UI Rendering Fixes (Windows App)
Ensure no UI elements have custom backfill colors (they must rely entirely on the OS/Visual Styles, strictly adhering to legacy Windows aesthetics). Fix any overlapping elements and ensure the listview is properly anchored/docked so it resizes dynamically with the window. Do not add any modern UI designs or change the core existing design layout. The Windows app must build upon the existing C++ (or C#/PowerShell depending on existing foundation) codebase without rewriting the underlying structure.

### R2. Automatic APK Icon Extraction & Display
Automatically extract the internal icon from APK files and display it within the Windows application's listview. This extraction must be fully integrated into the server and client apps directly, avoiding external tools/binaries unless absolutely required. Ensure this internal icon is also served and displayed correctly on the Android store application's UI, respecting its existing foundation.

### R3. Server Monitor Updates
Update the server monitor interface to display a real-time list of connected clients. The list must show both the IP Address and the Device Name of each connected client.

## Acceptance Criteria

### UI Rendering
- [ ] Programmatic/Visual Verification: No buttons or controls specify a custom background color; they default to OS styling.
- [ ] Programmatic/Visual Verification: No elements overlap when the main window is initialized at default size.
- [ ] Programmatic/Visual Verification: Resizing the window correctly resizes the listview without breaking the layout or obscuring other controls.

### APK Icons
- [ ] Programmatic Verification: The server logic successfully reads the internal APK icon for an uploaded/available APK.
- [ ] Visual Verification: The Windows app listview displays the correct internal icon.
- [ ] Visual Verification: The Android store UI successfully fetches and displays the internal APK icon.

### Server Monitor
- [ ] Programmatic Verification: When a client connects, the server UI updates to show their IP address and Device Name.
- [ ] Programmatic Verification: Disconnected clients are appropriately managed/removed from the list.
