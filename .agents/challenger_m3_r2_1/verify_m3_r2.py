import time
import subprocess
import os
import sys
import json
import urllib.request
import urllib.error

LOG_PATH = r"C:\EliteSoftware\Logs\LocalAPKStore.log"
EXE_PATH = r"C:\Users\Administrator\Desktop\Local_APK_Store\Manager_App\Elite_App_Marketplace-Server.exe"
CWD = r"C:\Users\Administrator\Desktop\Local_APK_Store\Manager_App"
SERVER_URL = "http://127.0.0.1:8552"

def wait_for_server(timeout_sec=15):
    start_t = time.time()
    while time.time() - start_t < timeout_sec:
        try:
            req = urllib.request.Request(f"{SERVER_URL}/api/apps", method='GET')
            with urllib.request.urlopen(req, timeout=2) as resp:
                if resp.status == 200:
                    print(f"Server is ready after {time.time() - start_t:.2f} seconds.")
                    return True
        except Exception:
            time.sleep(0.5)
    return False

def post_json(endpoint, payload):
    url = f"{SERVER_URL}{endpoint}"
    data = json.dumps(payload).encode('utf-8')
    req = urllib.request.Request(url, data=data, headers={'Content-Type': 'application/json'}, method='POST')
    try:
        with urllib.request.urlopen(req, timeout=5) as response:
            return response.status, response.read().decode('utf-8')
    except urllib.error.HTTPError as e:
        return e.code, e.read().decode('utf-8')
    except Exception as e:
        return -1, str(e)

def get_json(endpoint):
    url = f"{SERVER_URL}{endpoint}"
    req = urllib.request.Request(url, method='GET')
    try:
        start_t = time.time()
        with urllib.request.urlopen(req, timeout=5) as response:
            elapsed = time.time() - start_t
            return response.status, response.read().decode('utf-8'), elapsed
    except urllib.error.HTTPError as e:
        return e.code, e.read().decode('utf-8'), 0.0
    except Exception as e:
        return -1, str(e), 0.0

def get_log_content():
    if os.path.exists(LOG_PATH):
        with open(LOG_PATH, 'r', encoding='utf-8', errors='ignore') as f:
            return f.read()
    return ""

def run_test():
    print("=== STARTING M3 ITERATION 2 VERIFICATION ===")
    
    # Kill existing processes
    subprocess.run(["powershell", "-Command", "Get-Process -Name 'Elite_App_Marketplace-Server', 'LocalAPKStore' -ErrorAction SilentlyContinue | Stop-Process -Force -ErrorAction SilentlyContinue"], capture_output=True)
    time.sleep(1)
    
    print(f"Launching server: {EXE_PATH}")
    proc = subprocess.Popen([EXE_PATH], cwd=CWD)
    
    ready = wait_for_server(15)
    if not ready or proc.poll() is not None:
        print("ERROR: Server process failed to start or listen in time!")
        if proc.poll() is None:
            proc.kill()
        return False

    results = {}

    # Record initial log position
    log_before = get_log_content()

    # Step 1: Send Heartbeat for dev_test
    print("\n[Step 1] Sending POST /api/heartbeat for 'dev_test' (Pixel 8)...")
    status, body = post_json("/api/heartbeat", {"client_id": "dev_test", "device_name": "Pixel 8"})
    print(f"Heartbeat response: status={status}, body={body}")
    results['heartbeat'] = (status == 200 and '"status":"ok"' in body.replace(" ", ""))

    # Step 2: Wait 16 seconds for ClientCleanupThread
    print("\n[Step 2] Waiting 16 seconds for ClientCleanupThread timeout cleanup...")
    time.sleep(16)
    
    log_content = get_log_content()[len(log_before):]
    timeout_logged = "Client disconnected (timeout): Pixel 8" in log_content
    print(f"Timeout logged in log file: {timeout_logged}")
    results['timeout_logged'] = timeout_logged

    # Step 3: Test server responsiveness via GET /api/apps immediately after timeout
    print("\n[Step 3] Sending GET /api/apps to check server responsiveness...")
    status, body, elapsed = get_json("/api/apps")
    print(f"/api/apps response: status={status}, elapsed={elapsed:.3f}s, body_len={len(body)}")
    server_responsive = (status == 200 and "apps" in body and elapsed < 2.0)
    results['server_responsive'] = server_responsive

    # Step 4: Test /api/disconnect immediate client erasure
    print("\n[Step 4] Testing POST /api/heartbeat + POST /api/disconnect for dev_test2 (Pixel 9)...")
    st1, b1 = post_json("/api/heartbeat", {"client_id": "dev_test2", "device_name": "Pixel 9"})
    print(f"Heartbeat dev_test2: status={st1}, body={b1}")
    
    st2, b2 = post_json("/api/disconnect", {"client_id": "dev_test2"})
    print(f"Disconnect dev_test2: status={st2}, body={b2}")
    
    log_content_after = get_log_content()[len(log_before):]
    disconnect_logged = "Client disconnected (explicit): Pixel 9" in log_content_after
    print(f"Explicit disconnect logged in log file: {disconnect_logged}")
    results['disconnect_immediate'] = (st2 == 200 and '"status":"disconnected"' in b2.replace(" ", "") and disconnect_logged)

    # Clean up server process
    print("\nCleaning up server process...")
    proc.terminate()
    try:
        proc.wait(timeout=3)
    except subprocess.TimeoutExpired:
        proc.kill()

    print("\n=== VERIFICATION SUMMARY ===")
    for k, v in results.items():
        print(f"  {k}: {'PASS' if v else 'FAIL'}")

    all_passed = all(results.values())
    print(f"\nOVERALL RESULT: {'PASS' if all_passed else 'FAIL'}")
    return all_passed

if __name__ == '__main__':
    success = run_test()
    sys.exit(0 if success else 1)
