import subprocess
import time
import urllib.request
import urllib.error
import json
import concurrent.futures
import sys
import os

SERVER_EXE = r"C:\Users\Administrator\Desktop\Local_APK_Store\Manager_App\Elite_App_Marketplace-Server.exe"
SERVER_DIR = r"C:\Users\Administrator\Desktop\Local_APK_Store\Manager_App"
SERVER_URL = "http://127.0.0.1:8552"

def stop_any_running_server():
    try:
        subprocess.run(["powershell", "-Command", "Stop-Process -Name 'Elite_App_Marketplace-Server' -Force -ErrorAction SilentlyContinue"], capture_output=True)
        subprocess.run(["powershell", "-Command", "Stop-Process -Name 'LocalAPKStore' -Force -ErrorAction SilentlyContinue"], capture_output=True)
    except Exception as e:
        print(f"Cleanup error: {e}")
    time.sleep(1)

def start_server_process():
    stop_any_running_server()
    print(f"Launching {SERVER_EXE}...")
    proc = subprocess.Popen([SERVER_EXE], cwd=SERVER_DIR)
    time.sleep(3) # Wait for server initialization
    print(f"Server process started with PID: {proc.pid}")
    return proc

def post_json(endpoint, data=None, raw_body=None, timeout=5):
    url = f"{SERVER_URL}{endpoint}"
    if raw_body is not None:
        body_bytes = raw_body.encode('utf-8') if isinstance(raw_body, str) else raw_body
    elif data is not None:
        body_bytes = json.dumps(data).encode('utf-8')
    else:
        body_bytes = b""
    
    req = urllib.request.Request(url, data=body_bytes, headers={'Content-Type': 'application/json'})
    try:
        with urllib.request.urlopen(req, timeout=timeout) as response:
            res_body = response.read().decode('utf-8')
            return response.status, res_body
    except urllib.error.HTTPError as e:
        res_body = e.read().decode('utf-8')
        return e.code, res_body
    except Exception as e:
        return 500, f"Exception: {type(e).__name__} - {e}"

def test_suite_1_concurrency():
    print("\n--- [TEST SUITE 1] Concurrent Heartbeats (10 distinct client IDs x 20 iterations = 200 requests) ---")
    results = []
    
    def client_worker(client_num):
        client_id = f"device_id_{client_num:02d}"
        device_name = f"Android Device {client_num}"
        success_count = 0
        for loop in range(20):
            payload = {"client_id": client_id, "device_name": device_name}
            status, resp = post_json("/api/heartbeat", data=payload)
            if status == 200 and '"status":"ok"' in resp:
                success_count += 1
            else:
                print(f"  Worker {client_num} loop {loop} failed: status={status}, resp={resp}")
            time.sleep(0.01)
        return client_num, success_count

    with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
        futures = [executor.submit(client_worker, i) for i in range(10)]
        for f in concurrent.futures.as_completed(futures):
            c_num, count = f.result()
            results.append((c_num, count))
            print(f"  Client ID device_id_{c_num:02d}: {count}/20 successful heartbeats")

    total_success = sum(c for _, c in results)
    print(f"Total successful concurrent heartbeats: {total_success}/200")
    if total_success != 200:
        raise RuntimeError(f"Expected 200 successful heartbeats, got {total_success}")
    print("[PASS] Test Suite 1: Concurrent heartbeats handled without data corruption or crash.")

def test_suite_2_malformed_payloads():
    print("\n--- [TEST SUITE 2] Malformed JSON Payloads and Invalid Endpoints ---")
    
    test_cases = [
        ("Non-JSON raw text", "/api/heartbeat", "NOT_JSON_BODY", 400, '"error":"invalid json"'),
        ("Empty string body", "/api/heartbeat", "", 400, '"error":"invalid json"'),
        ("Malformed JSON missing quotes", "/api/heartbeat", "{client_id: missing_quotes}", 400, '"error":"invalid json"'),
        ("Unterminated JSON bracket", "/api/heartbeat", '{"client_id": "test"', 400, '"error":"invalid json"'),
        ("JSON integer value", "/api/heartbeat", "12345", 400, '"error":"invalid json"'),
        ("JSON null value", "/api/heartbeat", "null", 400, '"error":"invalid json"'),
        ("Missing fields heartbeat (empty object)", "/api/heartbeat", "{}", 200, '"status":"ok"'),
        ("Missing fields disconnect (empty object)", "/api/disconnect", "{}", 200, '"status":"disconnected"'),
        ("Non-JSON text to disconnect", "/api/disconnect", "MALFORMED_TEXT", 400, '"error":"invalid json"'),
        ("Empty body to disconnect", "/api/disconnect", "", 400, '"error":"invalid json"'),
    ]
    
    passed_cases = 0
    for name, endpoint, body, expected_status, expected_substr in test_cases:
        status, resp = post_json(endpoint, raw_body=body)
        status_ok = (status == expected_status)
        content_ok = (expected_substr in resp)
        if status_ok and content_ok:
            print(f"  [PASS] {name} -> HTTP {status}, Body: {resp}")
            passed_cases += 1
        else:
            print(f"  [FAIL] {name} -> Expected HTTP {expected_status} containing '{expected_substr}', got HTTP {status}: {resp}")
            
    if passed_cases != len(test_cases):
        raise RuntimeError(f"Passed {passed_cases}/{len(test_cases)} malformed payload tests.")
    print("[PASS] Test Suite 2: All malformed payload edge cases correctly returned HTTP 400 / expected response without server crash.")

def test_suite_3_rapid_connect_disconnect():
    print("\n--- [TEST SUITE 3] Rapid Connect/Disconnect Cleanup ---")
    
    print("  Sending rapid connect (heartbeat) and immediate disconnect for 20 clients...")
    rapid_success = 0
    for i in range(20):
        c_id = f"rapid_client_{i:02d}"
        h_status, h_resp = post_json("/api/heartbeat", data={"client_id": c_id, "device_name": f"Rapid Device {i}"})
        d_status, d_resp = post_json("/api/disconnect", data={"client_id": c_id})
        if h_status == 200 and d_status == 200 and '"status":"disconnected"' in d_resp:
            rapid_success += 1

    print(f"  Rapid connect/disconnect cycles successful: {rapid_success}/20")
    if rapid_success != 20:
        raise RuntimeError(f"Expected 20 successful rapid connect/disconnect cycles, got {rapid_success}")

    print("  Disconnecting remaining Test Suite 1 clients...")
    for i in range(10):
        c_id = f"device_id_{i:02d}"
        post_json("/api/disconnect", data={"client_id": c_id})

    print("[PASS] Test Suite 3: Rapid connect/disconnect sequences completed successfully.")

def run_all_tests():
    proc = start_server_process()
    try:
        test_suite_1_concurrency()
        test_suite_2_malformed_payloads()
        test_suite_3_rapid_connect_disconnect()
        print("\n=======================================================")
        print("ALL EMPIRICAL TESTS PASSED SUCCESSFULLY!")
        print("=======================================================")
        return True
    except Exception as e:
        print(f"\n[FATAL ERROR IN STRESS TEST]: {e}")
        return False
    finally:
        print("Cleaning up server process...")
        proc.terminate()
        try:
            proc.wait(timeout=3)
        except Exception:
            proc.kill()
        stop_any_running_server()

if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)
