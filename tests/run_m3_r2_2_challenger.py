import os
import sys
import time
import socket
import json
import subprocess
import urllib.request
import urllib.error
import concurrent.futures
import ctypes

SERVER_EXE = r"C:\Users\Administrator\Desktop\Local_APK_Store\Manager_App\Elite_App_Marketplace-Server.exe"
SERVER_DIR = r"C:\Users\Administrator\Desktop\Local_APK_Store\Manager_App"
LOG_FILE = r"C:\EliteSoftware\Logs\LocalAPKStore.log"

def kill_all_servers():
    subprocess.run(["powershell", "-Command", "Stop-Process -Name 'Elite_App_Marketplace-Server' -Force -ErrorAction SilentlyContinue"], capture_output=True)
    subprocess.run(["powershell", "-Command", "Stop-Process -Name 'LocalAPKStore' -Force -ErrorAction SilentlyContinue"], capture_output=True)
    time.sleep(1)

def get_window_status_texts():
    texts = []
    user32 = ctypes.windll.user32
    
    found_hwnds = []
    def enum_windows_cb(hwnd, lparam):
        length = user32.GetWindowTextLengthA(hwnd)
        if length > 0:
            buf = ctypes.create_string_buffer(length + 1)
            user32.GetWindowTextA(hwnd, buf, length + 1)
            title = buf.value.decode('latin1', errors='ignore')
            if "Elite App Marketplace" in title or "Local APK Store" in title:
                found_hwnds.append(hwnd)
        return True
    
    WNDENUMPROC = ctypes.WINFUNCTYPE(ctypes.c_bool, ctypes.c_int, ctypes.c_void_p)
    cb = WNDENUMPROC(enum_windows_cb)
    user32.EnumWindows(cb, None)
    if not found_hwnds:
        return []

    hwnd_main = found_hwnds[0]

    def enum_child_cb(hwnd, lparam):
        length = user32.GetWindowTextLengthA(hwnd)
        if length > 0:
            buf = ctypes.create_string_buffer(length + 1)
            user32.GetWindowTextA(hwnd, buf, length + 1)
            text = buf.value.decode('latin1', errors='ignore')
            texts.append(text)
        return True

    cb_child = WNDENUMPROC(enum_child_cb)
    user32.EnumChildWindows(hwnd_main, cb_child, None)
    return texts

def run_empirical_tests():
    print("==================================================")
    print("EMPIRICAL VERIFICATION - CHALLENGER M3 R2 2")
    print("==================================================")

    # 1. Build Verification
    print("\n[TEST 1] Re-compiling Manager_App via build.bat...")
    kill_all_servers()
    build_proc = subprocess.run(["cmd.exe", "/c", "build.bat"], cwd=SERVER_DIR, capture_output=True, text=True)
    print("Build returncode:", build_proc.returncode)
    print("Build stdout:", build_proc.stdout.strip())
    test1_pass = (build_proc.returncode == 0) and os.path.exists(SERVER_EXE)
    print(f"Test 1 Result: {'PASS' if test1_pass else 'FAIL'}")

    # 2. Port Conflict Handling
    print("\n[TEST 2] Port Conflict Error Handling...")
    kill_all_servers()

    # Occupy port 8552
    s4 = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        s4.setsockopt(socket.SOL_SOCKET, -5, 1) # SO_EXCLUSIVEADDRUSE
    except Exception:
        pass
    s4.bind(('0.0.0.0', 8552))
    s4.listen(1)

    # Record log size
    before_lines = 0
    if os.path.exists(LOG_FILE):
        with open(LOG_FILE, 'r', encoding='latin1') as f:
            before_lines = len(f.readlines())

    server_proc = subprocess.Popen([SERVER_EXE], cwd=SERVER_DIR)
    time.sleep(2.5)

    new_logs = ""
    if os.path.exists(LOG_FILE):
        with open(LOG_FILE, 'r', encoding='latin1') as f:
            all_l = f.readlines()
            new_logs = "".join(all_l[before_lines:])

    ui_texts = get_window_status_texts()
    log_bind_err = "ERROR: HTTP Server failed to bind to port 8552" in new_logs
    ui_bind_err = any("Status: STOPPED (Port Error)" in t for t in ui_texts)

    print(f"  Log contains 'ERROR: HTTP Server failed to bind to port 8552': {log_bind_err}")
    print(f"  UI Status shows 'Status: STOPPED (Port Error)': {ui_bind_err}")
    print(f"  UI Window Texts captured: {ui_texts}")
    print(f"  New Logs captured:\n{new_logs.strip()}")

    test2_pass = log_bind_err and ui_bind_err
    print(f"Test 2 Result: {'PASS' if test2_pass else 'FAIL'}")

    server_proc.terminate()
    s4.close()
    kill_all_servers()

    # 3. Startup Latency
    print("\n[TEST 3] Startup Latency & AAPT Negative Lookup Caching...")
    kill_all_servers()

    t0 = time.perf_counter()
    server_proc = subprocess.Popen([SERVER_EXE], cwd=SERVER_DIR)

    ready = False
    latency = 0.0
    while time.perf_counter() - t0 < 5.0:
        try:
            req = urllib.request.Request("http://127.0.0.1:8552/api/apps")
            with urllib.request.urlopen(req, timeout=0.5) as resp:
                if resp.status == 200:
                    latency = time.perf_counter() - t0
                    ready = True
                    break
        except Exception:
            time.sleep(0.02)

    print(f"  Server ready flag: {ready}")
    print(f"  Startup latency measured: {latency:.3f}s")
    test3_pass = ready and (latency < 1.0)
    print(f"Test 3 Result: {'PASS' if test3_pass else 'FAIL'}")

    # 4. 100 Concurrent Heartbeats
    print("\n[TEST 4] 100 Concurrent POST /api/heartbeat Requests...")
    
    def send_hb(idx):
        cid = f"client_id_{idx:03d}"
        dname = f"Device_{idx:03d}"
        url = "http://127.0.0.1:8552/api/heartbeat"
        payload = json.dumps({"client_id": cid, "device_name": dname}).encode('utf-8')
        req = urllib.request.Request(url, data=payload, headers={'Content-Type': 'application/json'})
        try:
            with urllib.request.urlopen(req, timeout=5) as resp:
                body = resp.read().decode('utf-8')
                return resp.status == 200 and '"status":"ok"' in body
        except Exception as e:
            return False

    with concurrent.futures.ThreadPoolExecutor(max_workers=50) as executor:
        futures = [executor.submit(send_hb, i) for i in range(100)]
        results = [f.result() for f in concurrent.futures.as_completed(futures)]

    success_cnt = sum(results)
    print(f"  Concurrent heartbeats succeeded: {success_cnt}/100")
    test4_pass = (success_cnt == 100)
    print(f"Test 4 Result: {'PASS' if test4_pass else 'FAIL'}")

    kill_all_servers()

    print("\n==================================================")
    print("FINAL SUMMARY")
    print(f"Test 1 (Build): {'PASS' if test1_pass else 'FAIL'}")
    print(f"Test 2 (Port Conflict): {'PASS' if test2_pass else 'FAIL'}")
    print(f"Test 3 (Startup Latency <1s): {'PASS' if test3_pass else 'FAIL'} ({latency:.3f}s)")
    print(f"Test 4 (100 Concurrent HBs): {'PASS' if test4_pass else 'FAIL'} ({success_cnt}/100)")
    print("==================================================")

if __name__ == '__main__':
    run_empirical_tests()
