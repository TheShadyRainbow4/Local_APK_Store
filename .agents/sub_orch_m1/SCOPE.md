# Scope: Milestone 1 (Win32 UI Rendering & Aesthetic Compliance)

## Target Codebase
- File: `Manager_App/main.cpp`
- Build script: `Manager_App/build.bat`
- Executable target: `Manager_App/LocalAPKStore.exe`

## Detailed Tasks
1. **WM_CTLCOLORSTATIC Fix**:
   - Locate line ~472 (`WM_CTLCOLORSTATIC`).
   - Remove custom white background patch brush return (`GetStockObject(WHITE_BRUSH)` or custom white brush).
   - Use standard Win32 native static text background (`SetBkMode(hdc, TRANSPARENT)`, return native dialog background brush like `(LRESULT)GetSysColorBrush(COLOR_BTNFACE)` or default OS rendering).
2. **Control Alignment & Resizing Fix**:
   - Re-arrange and fix overlapping controls at default 850x600 window dimensions.
   - Adjust `hwndPreview`, `btnDelete`, `btnClearForm`, `btnBrowse`, `btnApply`, `invLabels[8]`, `invLabels[0]`.
3. **Control Upgrade**:
   - Upgrade `hwndApps` from LISTBOX to `SysListView32` (`WC_LISTVIEW`) with report view columns (`Name`, `Package`, `Version`, `Size`, `Status`).
   - Implement dynamic layout anchoring in `WM_SIZE` so controls scale / re-anchor properly when resized.
4. **EliteSoftware Aesthetic & Component Rules Compliance**:
   - Segoe UI Font applied to all controls.
   - Distinct Title Banner at top with application title & icon.
   - 3D Inset Area for main active area.
   - Client Edge & Frame with native Windows dialog-style border.
   - Bottom Chin panel (darker background `#D0D0D0` or `COLOR_BTNFACE` / dark frame anchoring action buttons `Apply`, `Cancel`, `Exit`, etc.).
   - Standard Button Styling (OS styled, no custom back-fill, standard nomenclature like "Done", "Apply", "Cancel", "Exit", "Okay" - never "OK").
   - Native Menubar & Toolbar.
   - About Dialog: native Windows info blue circle icon, titlebar/banner icon, expandable extra info dropdown button.
   - Help Dialog: native Windows blue circle `?` icon.
   - Settings Dialog: separate settings button and dialog.
   - Hover tooltips for every interactive UI element (with accurate, witty undertone).
   - Logger: log to `%SystemDrive%\EliteSoftware\Logs\LocalAPKStore.log` with clickable "View LocalAPKStore Logs" link in UI launching notepad.exe.
