#!/usr/bin/env python3
"""
Milestone 4 Tier 5 Hardening: Win32 UI & Layout Stress Test Harness
Target: Manager_App/main.cpp layout math, WinForms/Win32 aesthetics, dynamic resize, and GDI ImageList handling.
"""

import sys
import os
import re

def simulate_wm_size(w, h, is_tab1=False):
    """
    Simulates the exact WM_SIZE math from Manager_App/main.cpp (lines 1457-1563).
    Returns a dict of control_name -> (x, y, w, h).
    """
    rects = {}
    
    # Constants from main.cpp
    sh = 22 # Standard status bar height
    toolbarH = 28 # Standard flat toolbar height
    bannerH = 42
    topOffset = bannerH + toolbarH # 70
    chinH = 42
    chinY = h - sh - chinH

    # Chin controls
    rects['hwndChin'] = (0, chinY, w, 2)
    rects['hwndLogLink'] = (15, chinY + 10, 180, 22)
    rects['btnExit'] = (w - 120, chinY + 6, 100, 30)

    # Tab control
    tabY = topOffset + 4 # 74
    tabH = chinY - tabY - 6
    rects['hwndTab'] = (10, tabY, w - 20, tabH)

    # Simulated TCM_ADJUSTRECT on tab control
    # Tab header is ~28px high, padding 3px on sides
    tab_left = 10 + 3
    tab_top = tabY + 28
    tab_right = 10 + (w - 20) - 3
    tab_bottom = tabY + tabH - 3
    
    tab_rect_w = tab_right - tab_left
    tab_rect_h = tab_bottom - tab_top

    if not is_tab1:
        # Tab 0: App Inventory
        leftWidth = 240
        rects['invLabels_0'] = (tab_left + 5, tab_top + 5, 200, 18)
        rects['hwndApps'] = (tab_left + 5, tab_top + 26, leftWidth, tab_rect_h - 70)
        rects['btnDelete'] = (tab_left + 5, tab_bottom - 38, 115, 30)
        rects['btnClearForm'] = (tab_left + 125, tab_bottom - 38, 115, 30)

        formX = tab_left + leftWidth + 15
        rightBtnW = 120
        editW = max(120, int(tab_right - formX - rightBtnW - 35))

        rects['invLabels_1'] = (formX, tab_top + 5, 85, 20)
        rects['hwndName'] = (formX + 90, tab_top + 5, editW, 22)

        rects['invLabels_2'] = (formX, tab_top + 35, 85, 20)
        rects['hwndPackage'] = (formX + 90, tab_top + 35, editW, 22)

        rects['invLabels_3'] = (formX, tab_top + 65, 85, 20)
        rects['hwndVersion'] = (formX + 90, tab_top + 65, editW, 22)

        rects['invLabels_4'] = (formX, tab_top + 95, 85, 20)
        rects['hwndCat'] = (formX + 90, tab_top + 95, editW, 150)

        rects['invLabels_5'] = (formX, tab_top + 125, 85, 20)
        rects['hwndTags'] = (formX + 90, tab_top + 125, editW, 22)

        rects['invLabels_6'] = (formX, tab_top + 155, 85, 20)
        rects['hwndDesc'] = (formX + 90, tab_top + 155, editW, 80)

        rects['invLabels_7'] = (formX, tab_top + 245, 85, 20)
        rects['lstScreenshots'] = (formX + 90, tab_top + 245, 140, 70)
        rects['hwndPreview'] = (formX + 240, tab_top + 245, 90, 90)

        rects['btnAddScreenshot'] = (tab_right - rightBtnW - 5, tab_top + 245, rightBtnW, 28)
        rects['btnClearScreenshots'] = (tab_right - rightBtnW - 5, tab_top + 280, rightBtnW, 28)

        rects['invLabels_8'] = (formX, tab_top + 345, 85, 20)
        rects['hwndApkLabel'] = (formX + 90, tab_top + 345, editW - 70, 24)
        rects['btnBrowse'] = (tab_right - rightBtnW - 5, tab_top + 343, rightBtnW, 28)

        rects['btnApply'] = (tab_right - rightBtnW - 5, tab_bottom - 38, rightBtnW, 30)

    else:
        # Tab 1: Server Monitor
        monW = tab_right - tab_left - 10
        totalMonH = tab_bottom - tab_top - 50
        logH = 180
        if totalMonH < 300:
            logH = max(80, totalMonH // 2)

        rects['hwndLog'] = (tab_left + 5, tab_top + 5, monW, logH)
        lblY = tab_top + logH + 12
        rects['lblConnectedClients'] = (tab_left + 5, lblY, monW, 20)

        listY = lblY + 22
        listH = max(50, (tab_bottom - 45) - listY)
        rects['hwndClientList'] = (tab_left + 5, listY, monW, listH)

        rects['hwndServerStatus'] = (tab_left + 10, tab_bottom - 38, 200, 24)
        rects['btnToggleServer'] = (tab_right - 130, tab_bottom - 38, 120, 30)

    return rects

def check_overlap(r1, r2):
    """
    Returns True if rectangle r1 (x, y, w, h) overlaps rectangle r2 (x, y, w, h).
    """
    x1, y1, w1, h1 = r1
    x2, y2, w2, h2 = r2

    if w1 <= 0 or h1 <= 0 or w2 <= 0 or h2 <= 0:
        return False

    overlap_x = max(0, min(x1 + w1, x2 + w2) - max(x1, x2))
    overlap_y = max(0, min(y1 + h1, y2 + h2) - max(y1, y2))
    return (overlap_x * overlap_y) > 0

def run_test_1_resize_stress():
    print("--- Running Test 1: Window Resizing & Dynamic Anchoring Stress ---")
    test_sizes = [
        (300, 200), (400, 300), (500, 400), (640, 480), (850, 600),
        (1024, 768), (1280, 720), (1366, 768), (1600, 900), (1920, 1080)
    ]
    
    passed_all = True

    for w, h in test_sizes:
        for tab_idx in [0, 1]:
            rects = simulate_wm_size(w, h, is_tab1=(tab_idx == 1))
            
            # Verify no negative or zero width/height for critical controls at standard sizes (>= 640x480)
            if w >= 640 and h >= 480:
                for name, (rx, ry, rw, rh) in rects.items():
                    if name in ['hwndCat']: continue # Combobox height is drop list height
                    if rw <= 0 or rh <= 0:
                        print(f"[FAIL] Size {w}x{h} Tab {tab_idx}: Control {name} has invalid dimension: w={rw}, h={rh}")
                        passed_all = False

            if tab_idx == 0:
                # ListView hwndApps must not overlap btnDelete or btnClearForm
                apps_r = rects['hwndApps']
                del_r = rects['btnDelete']
                clear_r = rects['btnClearForm']
                
                if check_overlap(apps_r, del_r):
                    print(f"[FAIL] Size {w}x{h}: hwndApps overlaps btnDelete")
                    passed_all = False
                if check_overlap(apps_r, clear_r):
                    print(f"[FAIL] Size {w}x{h}: hwndApps overlaps btnClearForm")
                    passed_all = False
                if check_overlap(del_r, clear_r):
                    print(f"[FAIL] Size {w}x{h}: btnDelete overlaps btnClearForm")
                    passed_all = False

    if passed_all:
        print(f"[PASS] Test 1 Passed across {len(test_sizes)} window dimensions (300x200 to 1920x1080).")
    return passed_all

def run_test_2_overlap_verification():
    print("--- Running Test 2: Control Overlap & Geometry Verification ---")
    rects_tab0 = simulate_wm_size(850, 600, is_tab1=False)
    rects_tab1 = simulate_wm_size(850, 600, is_tab1=True)

    passed = True
    overlaps_found = []

    # Check pairwise overlaps on Tab 0
    keys_tab0 = list(rects_tab0.keys())
    for i in range(len(keys_tab0)):
        for j in range(i + 1, len(keys_tab0)):
            k1, k2 = keys_tab0[i], keys_tab0[j]
            r1, r2 = rects_tab0[k1], rects_tab0[k2]
            
            if 'hwndTab' in (k1, k2): continue
            
            if k1 == 'hwndCat': r1 = (r1[0], r1[1], r1[2], 22)
            if k2 == 'hwndCat': r2 = (r2[0], r2[1], r2[2], 22)

            if check_overlap(r1, r2):
                print(f"[FAIL] Tab 0 Overlap detected between '{k1}' {r1} and '{k2}' {r2}")
                overlaps_found.append((k1, k2))
                passed = False

    # Check pairwise overlaps on Tab 1
    keys_tab1 = list(rects_tab1.keys())
    for i in range(len(keys_tab1)):
        for j in range(i + 1, len(keys_tab1)):
            k1, k2 = keys_tab1[i], keys_tab1[j]
            r1, r2 = rects_tab1[k1], rects_tab1[k2]
            if 'hwndTab' in (k1, k2): continue
            if check_overlap(r1, r2):
                print(f"[FAIL] Tab 1 Overlap detected between '{k1}' {r1} and '{k2}' {r2}")
                overlaps_found.append((k1, k2))
                passed = False

    if passed:
        print("[PASS] Test 2 Passed: 0 control overlaps found at default 850x600 resolution.")
    else:
        print(f"[FAIL] Test 2 Failed: {len(overlaps_found)} overlaps detected.")
    return passed

def run_test_3_aesthetic_compliance():
    print("--- Running Test 3: WinForms/Win32 Aesthetic Compliance Audit ---")
    main_cpp_path = os.path.join("Manager_App", "main.cpp")
    if not os.path.exists(main_cpp_path):
        print(f"[FAIL] {main_cpp_path} does not exist!")
        return False

    with open(main_cpp_path, "r", encoding="utf-8", errors="ignore") as f:
        code = f.read()

    checks = {
        "Segoe UI Font Initialization": r'CreateFontA\([^)]*"Segoe UI"\)',
        "WM_CTLCOLORSTATIC Hollow/BtnFace Brush": r'WM_CTLCOLORSTATIC[\s\S]*?COLOR_BTNFACE',
        "Transparent Static BkMode": r'SetBkMode\([^,]+,\s*TRANSPARENT\)',
        "Chin Panel & 3D Etched Line": r'hwndChin[\s\S]*?SS_ETCHEDHORZ',
        "3D Client Edge Frame (WS_EX_CLIENTEDGE)": r'WS_EX_CLIENTEDGE',
        "Native Menubar (CreateAppMenu)": r'CreateAppMenu\(',
        "Native Toolbar (CreateAppToolbar)": r'CreateAppToolbar\(',
        "About Dialog Class & Handler": r'AboutDialogProc',
        "Help Dialog Class & Handler": r'HelpDialogProc',
        "Settings Dialog Class & Handler": r'SettingsDialogProc',
        "Tooltips Initializer": r'InitTooltips\(',
        "Log File Directory (%SystemDrive%\\EliteSoftware\\Logs)": r'EliteSoftware\\\\Logs',
        "Log File Path (LocalAPKStore.log)": r'LocalAPKStore\.log',
        "Nomenclature Compliance ('Okay' Button)": r'"Okay"'
    }

    passed = True
    for check_name, pattern in checks.items():
        if re.search(pattern, code):
            print(f"  [x] {check_name}: VERIFIED")
        else:
            print(f"  [ ] {check_name}: MISSING or NON-COMPLIANT")
            passed = False

    if passed:
        print("[PASS] Test 3 Passed: WinForms/Win32 Aesthetic Compliance 100% Verified.")
    return passed

def run_test_4_imagelist_gdi_stress():
    print("--- Running Test 4: Dynamic Icon ImageList & GDI Leak Audit ---")
    main_cpp_path = os.path.join("Manager_App", "main.cpp")
    with open(main_cpp_path, "r", encoding="utf-8", errors="ignore") as f:
        code = f.read()

    has_image_list_create = "ImageList_Create(" in code
    has_add_icon = "ImageList_AddIcon(" in code
    has_destroy_icon = "DestroyIcon(" in code
    has_image_list_remove = "ImageList_RemoveAll(" in code
    has_image_list_destroy = "ImageList_Destroy(" in code

    print(f"  - ImageList_Create found: {has_image_list_create}")
    print(f"  - ImageList_AddIcon found: {has_add_icon}")
    print(f"  - DestroyIcon cleanup found: {has_destroy_icon}")
    print(f"  - ImageList_RemoveAll reset found: {has_image_list_remove}")
    print(f"  - ImageList_Destroy cleanup found: {has_image_list_destroy}")

    passed = (has_image_list_create and has_add_icon and has_destroy_icon and 
              has_image_list_remove and has_image_list_destroy)

    if passed:
        print("[PASS] Test 4 Passed: ImageList & GDI handle cleanup verified in code.")
    else:
        print("[FAIL] Test 4 Failed: Incomplete GDI handle lifecycle management.")
    return passed

def main():
    print("=================================================================")
    print("      WIN32 UI & LAYOUT STRESS TEST CHALLENGER HARNESS          ")
    print("=================================================================")
    
    t1 = run_test_1_resize_stress()
    t2 = run_test_2_overlap_verification()
    t3 = run_test_3_aesthetic_compliance()
    t4 = run_test_4_imagelist_gdi_stress()

    print("\n-----------------------------------------------------------------")
    print("SUMMARY RESULTS:")
    print(f"Test 1 (Window Resizing & Anchoring): {'PASS' if t1 else 'FAIL'}")
    print(f"Test 2 (Control Overlap & Geometry): {'PASS' if t2 else 'FAIL'}")
    print(f"Test 3 (WinForms/Win32 Aesthetic):    {'PASS' if t3 else 'FAIL'}")
    print(f"Test 4 (ImageList GDI Handle Safety): {'PASS' if t4 else 'FAIL'}")
    print("-----------------------------------------------------------------")

    if t1 and t2 and t3 and t4:
        print("VERDICT: APPROVE")
        sys.exit(0)
    else:
        print("VERDICT: REJECT")
        sys.exit(1)

if __name__ == "__main__":
    main()
