import time
import subprocess
import os
import urllib.request
import urllib.parse
import json
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

def test_startup_and_heartbeats():
    print("=== Testing Startup Latency & Concurrent Heartbeats ===")
    exe_path = r"C:\Users\Administrator\Desktop\Local_APK_Store\Manager_App\Elite_App_Marketplace-Server.exe"
    
    # 1. Startup Latency Test
    t0 = time.perf_counter()
    proc = subprocess.Popen([exe_path], cwd=os.path.dirname(exe_path))
    print(f"Launched process PID: {proc.pid}")
    
    server_ready = False
    launch_time = None
    timeout = 5.0
    
    while (time.perf_counter() - t0) < timeout:
        try:
            req = urllib.request.Request("http://127.0.0.1:8552/api/apps")
            with urllib.request.urlopen(req, timeout=0.5) as resp:
                if resp.status == 200:
                    t1 = time.perf_counter()
                    launch_time = t1 - t0
                    server_ready = True
                    break
        except Exception:
            time.sleep(0.01)
            
    print(f"Server Ready: {server_ready}, Launch Latency: {launch_time:.4f} seconds" if launch_time else "Server failed to respond within timeout.")

    if not server_ready or launch_time is None:
        proc.terminate()
        return False, launch_time, 0, "Server failed to start"

    # 2. Concurrent Heartbeats Test (100 requests)
    print("\n--- Sending 100 Concurrent POST /api/heartbeat Requests ---")
    num_requests = 100
    
    def send_heartbeat(client_idx):
        url = "http://127.0.0.1:8552/api/heartbeat"
        payload = json.dumps({
            "client_id": f"client_id_{client_idx:03d}",
            "device_name": f"Test_Device_{client_idx:03d}"
        }).encode('utf-8')
        
        req = urllib.request.Request(
            url,
            data=payload,
            headers={'Content-Type': 'application/json'},
            method='POST'
        )
        try:
            with urllib.request.urlopen(req, timeout=5.0) as resp:
                body = resp.read().decode('utf-8')
                return (resp.status, body)
        except Exception as e:
            return (0, str(e))

    results = []
    with concurrent.futures.ThreadPoolExecutor(max_workers=50) as executor:
        futures = [executor.submit(send_heartbeat, i) for i in range(1, num_requests + 1)]
        for f in concurrent.futures.as_completed(futures):
            results.append(f.result())

    success_count = sum(1 for status, body in results if status == 200 and '"status":"ok"' in body)
    print(f"Heartbeat Successes: {success_count}/{num_requests} ({success_count/num_requests*100:.1f}%)")
    
    # Wait for UI timer to refresh client list count
    time.sleep(1.5)
    
    # Find Window and inspect client count text
    hwnd = user32.FindWindowW("EliteAppMarketplaceServer", None)
    connected_clients_text = None
    if hwnd:
        child_texts = find_all_child_texts(hwnd)
        for h, t in child_texts:
            if "Connected Clients" in t:
                connected_clients_text = t

    print(f"UI Connected Clients Text: '{connected_clients_text}'")
    
    # Clean up process
    proc.terminate()
    proc.wait(timeout=5)
    
    latency_pass = launch_time < 1.0
    heartbeat_pass = (success_count == num_requests)
    
    print(f"\n[Result] Launch Latency < 1.0s: {latency_pass} ({launch_time:.4f}s)")
    print(f"[Result] Heartbeat 100% Success Rate: {heartbeat_pass} ({success_count}/{num_requests})")
    
    overall_pass = latency_pass and heartbeat_pass
    return overall_pass, launch_time, success_count, connected_clients_text

if __name__ == "__main__":
    pass_flag, launch_t, hb_count, ui_text = test_startup_and_heartbeats()
    if pass_flag:
        print("\nSTARTUP LATENCY & HEARTBEAT TESTS PASSED!")
    else:
        print("\nSTARTUP LATENCY & HEARTBEAT TESTS FAILED!")
