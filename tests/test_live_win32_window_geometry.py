#!/usr/bin/env python3
"""
Empirical Live Win32 HWND Geometry Inspector
Launches Manager_App/LocalAPKStore.exe and inspects live HWND bounding rectangles via Win32 API.
"""

import subprocess
import time
import ctypes
from ctypes import wintypes
import os

user32 = ctypes.windll.user32

class RECT(ctypes.Structure):
    _fields_ = [
        ("left", wintypes.LONG),
        ("top", wintypes.LONG),
        ("right", wintypes.LONG),
        ("bottom", wintypes.LONG)
    ]

def get_window_rect(hwnd):
    rect = RECT()
    user32.GetWindowRect(hwnd, ctypes.byref(rect))
    return (rect.left, rect.top, rect.right - rect.left, rect.bottom - rect.top)

def get_client_rect(hwnd):
    rect = RECT()
    user32.GetClientRect(hwnd, ctypes.byref(rect))
    return (rect.left, rect.top, rect.right - rect.left, rect.bottom - rect.top)

def test_live_window():
    exe_path = os.path.join("Manager_App", "LocalAPKStore.exe")
    if not os.path.exists(exe_path):
        print(f"Executable {exe_path} not found.")
        return

    print("Launching LocalAPKStore.exe for empirical HWND inspection...")
    proc = subprocess.Popen([exe_path], cwd="Manager_App")
    time.sleep(2.0) # Wait for window creation

    hwnd_main = user32.FindWindowA(b"EliteAppMarketplaceServer", None)
    if not hwnd_main:
        print("Failed to find HWND for EliteAppMarketplaceServer")
        proc.terminate()
        return

    print(f"Found Main HWND: 0x{hwnd_main:X}")
    main_rect = get_window_rect(hwnd_main)
    print(f"Main Window Rect: {main_rect}")

    # Enumerate child windows of Main HWND
    child_hwnds = []
    
    WNDENUMPROC = ctypes.WINFUNCTYPE(wintypes.BOOL, wintypes.HWND, wintypes.LPARAM)
    
    def enum_windows_callback(hwnd, lparam):
        child_hwnds.append(hwnd)
        return True

    user32.EnumChildWindows(hwnd_main, WNDENUMPROC(enum_windows_callback), 0)
    print(f"Found {len(child_hwnds)} child HWNDs.")

    # Resize window to 850x600 explicitly
    user32.SetWindowPos(hwnd_main, 0, 100, 100, 850, 600, 0x0004 | 0x0040)
    time.sleep(0.5)

    # Re-inspect child rects
    labels_and_controls = []
    for ch in child_hwnds:
        buf = ctypes.create_string_buffer(256)
        user32.GetClassNameA(ch, buf, 256)
        cls_name = buf.value.decode('utf-8', errors='ignore')
        
        txt_buf = ctypes.create_string_buffer(256)
        user32.GetWindowTextA(ch, txt_buf, 256)
        txt = txt_buf.value.decode('utf-8', errors='ignore')
        
        rc = get_window_rect(ch)
        labels_and_controls.append((ch, cls_name, txt, rc))
        print(f"  Child 0x{ch:X} | Class: {cls_name:<16} | Text: {txt:<25} | Rect: {rc}")

    # Clean up test process
    user32.PostMessageA(hwnd_main, 0x0010, 0, 0) # WM_CLOSE
    proc.terminate()

if __name__ == "__main__":
    test_live_window()
