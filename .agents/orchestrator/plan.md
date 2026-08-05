# Master Plan — Local APK Store Development

## Overview
This master plan guides the resolution of issues and feature additions for the Local APK Store project as requested in `ORIGINAL_REQUEST.md`.

## Key Objectives
1. **R1: UI Rendering Fixes (Windows App)**: Native OS Visual Styles (no custom backfill), fix element overlaps, dynamic ListView docking/resizing, strict WinForms / legacy Windows desktop aesthetic.
2. **R2: Automatic APK Icon Extraction & Display**: Server/client internal APK icon extraction (ZIP/AAPT/PNG parsing), Windows app listview rendering, Android store UI rendering.
3. **R3: Server Monitor Updates**: Real-time connected client list displaying IP Address and Device Name, with active connection management/disconnection handling.

## Phased Approach & Milestone Breakdown
- **Phase 0: Survey (COMPLETED)**
  - Synthesized reports from Explorer 1, Explorer 2, Explorer 3 into `PROJECT.md`.
- **Phase 1: E2E Test Suite Creation & Milestone Setup (IN_PROGRESS)**
  - Spawn E2E Testing Orchestrator to create test infrastructure and test cases for Tiers 1-4.
- **Phase 2: Milestone Execution**
  - **Milestone 1 (Win32 UI Rendering & Aesthetic Compliance)**: Implement Win32 OS default backfill styling, fix control overlaps, convert listbox to SysListView32 with dynamic WM_SIZE anchoring, add Segoe UI font, bottom Chin panel, 3D inset frame, Menubar, Toolbar, About/Help/Settings dialogs, tooltips, log viewer.
  - **Milestone 2 (Automatic APK Icon Extraction & Display)**: Implement server automatic APK icon & metadata extraction (with XML adaptive icon fallback), load extracted icons into HIMAGELIST in Manager App ListView, fix Android client Intent extras and image loading.
  - **Milestone 3 (Server Monitor Connected Clients Real-Time List)**: Implement HTTP POST `/api/heartbeat` & `/api/disconnect` in Android client, server-side client session map & 15s cleanup thread in Manager App, and live SysListView32 client list updated via 1s WM_TIMER in Server Monitor tab.
- **Phase 3: E2E Verification & Hardening**
  - Execute Tier 1-4 E2E Test Suite and Tier 5 Adversarial Coverage Hardening (Challenger loop).
  - Run Forensic Integrity Audit (`teamwork_preview_auditor`).
- **Phase 4: Sentinel Notification & Victory Claim**
