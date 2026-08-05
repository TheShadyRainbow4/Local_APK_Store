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

def kill_server_processes():
    try:
        subprocess.run(["powershell", "-Command", "Stop-Process -Name 'Elite_App_Marketplace-Server' -Force -ErrorAction SilentlyContinue"], capture_output=True)
        subprocess.run(["powershell", "-Command", "Stop-Process -Name 'LocalAPKStore' -Force -ErrorAction SilentlyContinue"], capture_output=True)
    except Exception as e:
        print(f"Error killing server processes: {e}")
    time.sleep(1)

def get_window_texts():
    """Enum child windows of the main app window to find status text."""
    texts = []
    user32 = ctypes.windll.user32
    
    hwnd_main = user32.FindWindowA(None, b"Elite App Marketplace - Server Manager")
    if not hwnd_main:
        hwnd_main = user32.FindWindowA(None, b"Local APK Store Manager")
        
    if not hwnd_main:
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
        if found_hwnds:
            hwnd_main = found_hwnds[0]
            
    if not hwnd_main:
        return []

    def enum_child_cb(hwnd, lparam):
        length = user32.GetWindowTextLengthA(hwnd)
        if length > 0:
            buf = ctypes.create_string_buffer(length + 1)
            user32.GetWindowTextA(hwnd, buf, length + 1)
            text = buf.value.decode('latin1', errors='ignore')
            texts.append(text)
        return True

    WNDENUMPROC = ctypes.WINFUNCTYPE(ctypes.c_bool, ctypes.c_int, ctypes.c_void_p)
    cb_child = WNDENUMPROC(enum_child_cb)
    user32.EnumChildWindows(hwnd_main, cb_child, None)
    return texts

def test_port_conflict():
    print("\n--- [TEST 2] Port Conflict Error Handling ---")
    kill_server_processes()
    
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    s.bind(('0.0.0.0', 8552))
    s.listen(1)
    print("Bound test socket to 0.0.0.0:8552 successfully.")
    
    proc = subprocess.Popen([SERVER_EXE], cwd=SERVER_DIR)
    print(f"Launched server process PID={proc.pid} while port 8552 is occupied.")
    time.sleep(2)
    
    log_content = ""
    if os.path.exists(LOG_FILE):
        with open(LOG_FILE, 'r', encoding='utf-8', errors='ignore') as f:
            log_content = f.read()
            
    log_pass = "ERROR: HTTP Server failed to bind to port 8552" in log_content
    print(f"Log contains 'ERROR: HTTP Server failed to bind to port 8552': {log_pass}")
    
    texts = get_window_texts()
    print("UI Window Texts found:", texts)
    ui_pass = any("Status: STOPPED (Port Error)" in t for t in texts)
    print(f"UI Status shows 'Status: STOPPED (Port Error)': {ui_pass}")
    
    try:
        proc.terminate()
        proc.wait(timeout=2)
    except Exception:
        pass
    s.close()
    kill_server_processes()
    
    return log_pass and ui_pass

def test_startup_latency():
    print("\n--- [TEST 3] Startup Latency (< 1s) ---")
    kill_server_processes()
    
    t0 = time.perf_counter()
    proc = subprocess.Popen([SERVER_EXE], cwd=SERVER_DIR)
    
    server_ready = False
    elapsed = 0.0
    while time.perf_counter() - t0 < 5.0:
        try:
            req = urllib.request.Request("http://127.0.0.1:8552/api/apps")
            with urllib.request.urlopen(req, timeout=0.5) as resp:
                if resp.status == 200:
                    server_ready = True
                    elapsed = time.perf_counter() - t0
                    break
        except Exception:
            time.sleep(0.02)
            
    print(f"Server ready in {elapsed:.3f} seconds. Server ready flag: {server_ready}")
    fast_pass = server_ready and (elapsed < 1.0)
    print(f"Startup latency < 1s: {fast_pass} ({elapsed:.3f}s)")
    return proc, fast_pass, elapsed

def test_100_concurrent_heartbeats():
    print("\n--- [TEST 4] 100 Concurrent POST /api/heartbeat Requests ---")
    
    def send_hb(client_num):
        client_id = f"client_id_{client_num:03d}"
        device_name = f"Device_{client_num:03d}"
        url = "http://127.0.0.1:8552/api/heartbeat"
        data = json.dumps({"client_id": client_id, "device_name": device_name}).encode('utf-8')
        req = urllib.request.Request(url, data=data, headers={'Content-Type': 'application/json'})
        
        try:
            with urllib.request.urlopen(req, timeout=5) as response:
                body = response.read().decode('utf-8')
                return response.status == 200 and '"status":"ok"' in body
        except Exception as e:
            return False

    with concurrent.futures.ThreadPoolExecutor(max_workers=50) as executor:
        futures = [executor.submit(send_hb, i) for i in range(100)]
        results = [f.result() for f in concurrent.futures.as_completed(futures)]
        
    success_count = sum(results)
    print(f"Successful heartbeats: {success_count}/100")
    success_pass = (success_count == 100)
    return success_pass

def main():
    print("==========================================")
    print("RUNNING CHALLENGER M3 R2 2 SUITE")
    print("==========================================")
    
    # 2. Port conflict test
    res_port = test_port_conflict()
    
    # 3. Startup latency test
    proc, res_latency, elapsed_sec = test_startup_latency()
    
    # 4. Concurrency test
    res_concurrency = test_100_concurrent_heartbeats()
    
    kill_server_processes()
    
    print("\n==========================================")
    print("FINAL SUMMARY")
    print(f"Port Conflict Test: {'PASS' if res_port else 'FAIL'}")
    print(f"Startup Latency (< 1s): {'PASS' if res_latency else 'FAIL'} ({elapsed_sec:.3f}s)")
    print(f"100 Concurrent Heartbeats: {'PASS' if res_concurrency else 'FAIL'}")
    print("==========================================")
    
    all_passed = res_port and res_latency and res_concurrency
    sys.exit(0 if all_passed else 1)

if __name__ == "__main__":
    main()
