import socket
import subprocess
import time
import os
import ctypes
from ctypes import wintypes

# Win32 API declarations
user32 = ctypes.windll.user32
kernel32 = ctypes.windll.kernel32

EnumChildProc = ctypes.WINFUNCTYPE(wintypes.BOOL, wintypes.HWND, wintypes.LPARAM)

def get_window_text(hwnd):
    length = user32.GetWindowTextLengthW(hwnd)
    if length > 0:
        buff = ctypes.create_unicode_buffer(length + 1)
        user32.GetWindowTextW(hwnd, buff, length + 1)
        return buff.value
    return ""

def find_all_child_texts(parent_hwnd):
    texts = []
    def enum_child_cb(hwnd, lparam):
        txt = get_window_text(hwnd)
        if txt:
            texts.append((hwnd, txt))
        return True
    cb = EnumChildProc(enum_child_cb)
    user32.EnumChildWindows(parent_hwnd, cb, 0)
    return texts

def test_port_conflict():
    print("=== Testing Port Conflict ===")
    
    # 1. Bind socket to 0.0.0.0:8552
    conflict_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    conflict_sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    conflict_sock.bind(('0.0.0.0', 8552))
    conflict_sock.listen(5)
    print("Opened socket bound to 0.0.0.0:8552 successfully.")

    log_path = r"C:\EliteSoftware\Logs\LocalAPKStore.log"
    initial_log_size = 0
    if os.path.exists(log_path):
        initial_log_size = os.path.getsize(log_path)
    
    # 2. Launch server executable
    exe_path = r"C:\Users\Administrator\Desktop\Local_APK_Store\Manager_App\Elite_App_Marketplace-Server.exe"
    proc = subprocess.Popen([exe_path], cwd=os.path.dirname(exe_path))
    print(f"Launched {exe_path} (PID: {proc.pid})")
    
    time.sleep(2.0)
    
    # 3. Find Window
    hwnd = user32.FindWindowW("EliteAppMarketplaceServer", None)
    print(f"Main window HWND: {hwnd}")
    
    found_status_text = None
    if hwnd:
        child_texts = find_all_child_texts(hwnd)
        print("Child Window Texts found:")
        for h, t in child_texts:
            print(f"  - HWND {h}: '{t}'")
            if "Status:" in t:
                found_status_text = t
    
    # 4. Check Log file
    log_content = ""
    if os.path.exists(log_path):
        with open(log_path, "r", encoding="utf-8", errors="ignore") as f:
            f.seek(initial_log_size)
            log_content = f.read()
    
    print("\nNew Log Content:")
    print(log_content)

    # Clean up process and socket
    proc.terminate()
    proc.wait(timeout=5)
    conflict_sock.close()
    
    # Assertions
    expected_log = "ERROR: HTTP Server failed to bind to port 8552"
    expected_status = "Status: STOPPED (Port Error)"
    
    log_pass = expected_log in log_content
    status_pass = found_status_text == expected_status
    
    print(f"\n[Result] Log contains '{expected_log}': {log_pass}")
    print(f"[Result] UI Status text matches '{expected_status}': {status_pass} (Actual: '{found_status_text}')")
    
    return log_pass and status_pass

if __name__ == "__main__":
    success = test_port_conflict()
    if success:
        print("\nPORT CONFLICT TEST PASSED!")
    else:
        print("\nPORT CONFLICT TEST FAILED!")
