import os
import sys
import time
import subprocess
import socket
import json
import urllib.request
import concurrent.futures
import ctypes
from ctypes import wintypes

user32 = ctypes.windll.user32
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

def main():
    print("==========================================================", flush=True)
    print("  EMPIRICAL CHALLENGER VERIFICATION HARNESS - M3 R3 Task 2", flush=True)
    print("==========================================================", flush=True)

    manager_dir = r"C:\Users\Administrator\Desktop\Local_APK_Store\Manager_App"
    exe_path = os.path.join(manager_dir, "Elite_App_Marketplace-Server.exe")
    log_path = r"C:\EliteSoftware\Logs\LocalAPKStore.log"

    # --- STEP 1: Re-compile Manager_App ---
    print("\n--- STEP 1: Re-compiling Manager_App using build.bat ---")
    build_bat = os.path.join(manager_dir, "build.bat")
    build_proc = subprocess.run([build_bat], cwd=manager_dir, capture_output=True, text=True)
    print(build_proc.stdout)
    if build_proc.returncode != 0 or "Build successful" not in build_proc.stdout:
        print("ERROR: Build failed!")
        sys.exit(1)
    
    exe_stat = os.stat(exe_path)
    print(f"Compilation Successful. File: {exe_path}, Size: {exe_stat.st_size} bytes")

    # --- STEP 2: Port Conflict Test ---
    print("\n--- STEP 2: Port Conflict Error Logging & UI Status Test ---")
    conflict_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    conflict_sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    conflict_sock.bind(('0.0.0.0', 8552))
    conflict_sock.listen(5)
    print("Bound test socket to 0.0.0.0:8552")

    log_size_before = os.path.getsize(log_path) if os.path.exists(log_path) else 0

    server_proc = subprocess.Popen([exe_path], cwd=manager_dir)
    time.sleep(2.0)

    hwnd = user32.FindWindowW("EliteAppMarketplaceServer", None)
    ui_status_text = None
    if hwnd:
        for h, t in find_all_child_texts(hwnd):
            if "Status:" in t:
                ui_status_text = t
    
    log_added = ""
    if os.path.exists(log_path):
        with open(log_path, "r", encoding="utf-8", errors="ignore") as f:
            f.seek(log_size_before)
            log_added = f.read()

    server_proc.terminate()
    server_proc.wait(timeout=5)
    conflict_sock.close()

    expected_err_log = "ERROR: HTTP Server failed to bind to port 8552"
    expected_ui_status = "Status: STOPPED (Port Error)"

    step2_log_ok = expected_err_log in log_added
    step2_ui_ok = (ui_status_text == expected_ui_status)
    print(f"  Logged Error Found: {step2_log_ok} (Found: '{expected_err_log}' in log)")
    print(f"  UI Status Text Match: {step2_ui_ok} (Actual UI text: '{ui_status_text}')")

    # --- STEP 3: Startup Latency Test ---
    print("\n--- STEP 3: Startup Latency Test ---")
    t0 = time.perf_counter()
    server_proc = subprocess.Popen([exe_path], cwd=manager_dir)
    
    launch_time = None
    timeout = 5.0
    while (time.perf_counter() - t0) < timeout:
        try:
            req = urllib.request.Request("http://127.0.0.1:8552/api/apps")
            with urllib.request.urlopen(req, timeout=0.5) as resp:
                if resp.status == 200:
                    t1 = time.perf_counter()
                    launch_time = t1 - t0
                    break
        except Exception:
            time.sleep(0.01)

    step3_ok = launch_time is not None and launch_time < 1.0
    print(f"  Measured Launch Latency: {launch_time:.4f}s (Threshold: < 1.0s) -> PASS: {step3_ok}")

    # --- STEP 4: Concurrent Heartbeat Requests Test ---
    print("\n--- STEP 4: 100 Concurrent HTTP POST /api/heartbeat Requests ---")
    num_clients = 100

    def post_hb(idx):
        url = "http://127.0.0.1:8552/api/heartbeat"
        body = json.dumps({"client_id": f"cli_test_{idx:03d}", "device_name": f"Device_{idx:03d}"}).encode('utf-8')
        req = urllib.request.Request(url, data=body, headers={'Content-Type': 'application/json'}, method='POST')
        try:
            with urllib.request.urlopen(req, timeout=5.0) as r:
                return (r.status, r.read().decode('utf-8'))
        except Exception as ex:
            return (0, str(ex))

    with concurrent.futures.ThreadPoolExecutor(max_workers=50) as pool:
        hb_results = list(pool.map(post_hb, range(1, num_clients + 1)))

    hb_success = sum(1 for status, txt in hb_results if status == 200 and '"status":"ok"' in txt)
    time.sleep(1.5)

    hwnd = user32.FindWindowW("EliteAppMarketplaceServer", None)
    client_count_ui = None
    if hwnd:
        for h, t in find_all_child_texts(hwnd):
            if "Connected Clients" in t:
                client_count_ui = t

    server_proc.terminate()
    server_proc.wait(timeout=5)

    step4_ok = (hb_success == num_clients)
    print(f"  Heartbeat Success Rate: {hb_success}/{num_clients} ({hb_success/num_clients*100:.1f}%) -> PASS: {step4_ok}")
    print(f"  UI Client Count Label: '{client_count_ui}'")

    print("\n==========================================================")
    print("  FINAL VERDICT SUMMARY:")
    print(f"  Step 1 (Build): PASS")
    print(f"  Step 2 (Port Conflict): {'PASS' if (step2_log_ok and step2_ui_ok) else 'FAIL'}")
    print(f"  Step 3 (Startup Latency): {'PASS' if step3_ok else 'FAIL'} ({launch_time:.4f}s)")
    print(f"  Step 4 (100 Concurrent Heartbeats): {'PASS' if step4_ok else 'FAIL'} ({hb_success}/100)")
    print("==========================================================")

if __name__ == "__main__":
    main()
