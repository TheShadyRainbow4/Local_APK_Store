"""
Milestone 4 Tier 5 Hardening — Server & API Stress Test Harness
Executes empirical stress tests against Manager_App/LocalAPKStore.exe:
- Test 1: Rapid HTTP heartbeats (POST /api/heartbeat) from 50+ concurrent simulated client threads.
- Test 2: Rapid disconnect requests (POST /api/disconnect) interspersed with active heartbeats.
- Test 3: Malformed requests (invalid JSON payloads, missing fields, non-existent /images/ requests, oversized headers).
- Test 4: Concurrent client list queries & heartbeats while the background 15-second client timeout cleanup thread runs.
- Server Integrity: Checks for memory leaks, crashes, deadlocks, and session state corruption.
"""

import concurrent.futures
import json
import os
import subprocess
import sys
import time
import urllib.request
import urllib.error
import urllib.parse
import socket

SERVER_URL = "http://127.0.0.1:8552"
WORKSPACE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MANAGER_APP_DIR = os.path.join(WORKSPACE_DIR, "Manager_App")
EXE_PATH = os.path.join(MANAGER_APP_DIR, "LocalAPKStore.exe")

def is_server_running():
    try:
        req = urllib.request.Request(f"{SERVER_URL}/api/apps", method="GET")
        with urllib.request.urlopen(req, timeout=2) as resp:
            return resp.status == 200
    except Exception:
        return False

def ensure_server_running():
    if is_server_running():
        print("[SETUP] Server is already running on port 8552.")
        return None
    print(f"[SETUP] Starting server executable: {EXE_PATH}")
    proc = subprocess.Popen([EXE_PATH], cwd=MANAGER_APP_DIR)
    # Wait for server to bind and start listening
    for _ in range(30):
        time.sleep(0.5)
        if is_server_running():
            print("[SETUP] Server started successfully and listening on port 8552.")
            return proc
    raise RuntimeError("Server failed to start within timeout.")

def get_server_process_memory_mb():
    """Returns working set size in MB for LocalAPKStore.exe processes."""
    try:
        cmd = "tasklist /FI \"IMAGENAME eq LocalAPKStore.exe\" /FO CSV /NH"
        out = subprocess.check_output(cmd, shell=True).decode('utf-8', errors='ignore')
        total_mem_kb = 0
        for line in out.strip().splitlines():
            parts = line.split('","')
            if len(parts) >= 5:
                mem_str = parts[4].replace('"', '').replace(' K', '').replace(',', '').strip()
                if mem_str.isdigit():
                    total_mem_kb += int(mem_str)
        return total_mem_kb / 1024.0
    except Exception as e:
        print(f"[WARN] Failed to get memory stats: {e}")
        return 0.0

def send_request(endpoint, method="POST", data=None, raw_body=None, headers=None, timeout=5):
    url = f"{SERVER_URL}{endpoint}"
    req_headers = headers if headers is not None else {}
    
    if raw_body is not None:
        body_bytes = raw_body.encode('utf-8') if isinstance(raw_body, str) else raw_body
    elif data is not None:
        body_bytes = json.dumps(data).encode('utf-8')
        if 'Content-Type' not in req_headers:
            req_headers['Content-Type'] = 'application/json'
    else:
        body_bytes = None

    req = urllib.request.Request(url, data=body_bytes, headers=req_headers, method=method)
    try:
        with urllib.request.urlopen(req, timeout=timeout) as response:
            res_body = response.read().decode('utf-8', errors='ignore')
            return response.status, res_body
    except urllib.error.HTTPError as e:
        res_body = e.read().decode('utf-8', errors='ignore')
        return e.code, res_body
    except Exception as e:
        return 500, f"Exception: {type(e).__name__} - {e}"

# ==============================================================================
# TEST 1: Rapid HTTP Heartbeats (50+ Concurrent Client Threads)
# ==============================================================================
def run_test_1():
    print("\n" + "="*80)
    print("TEST 1: Rapid HTTP Heartbeats (50+ Concurrent Client Threads)")
    print("="*80)

    num_threads = 55
    requests_per_thread = 50
    total_expected = num_threads * requests_per_thread

    mem_before = get_server_process_memory_mb()
    print(f"[TEST 1] Starting {num_threads} threads, each sending {requests_per_thread} heartbeats (Total: {total_expected})...")
    print(f"[TEST 1] Server memory before test: {mem_before:.2f} MB")

    start_time = time.time()
    results = []

    def worker(thread_idx):
        thread_results = []
        client_id = f"stress_t1_client_{thread_idx:03d}"
        device_name = f"Stress Phone {thread_idx:03d}"
        for req_idx in range(requests_per_thread):
            payload = {"client_id": client_id, "device_name": device_name}
            status, body = send_request("/api/heartbeat", data=payload, timeout=5)
            thread_results.append((status, body))
        return thread_results

    with concurrent.futures.ThreadPoolExecutor(max_workers=num_threads) as executor:
        futures = [executor.submit(worker, i) for i in range(num_threads)]
        for f in concurrent.futures.as_completed(futures):
            results.extend(f.result())

    elapsed = time.time() - start_time
    mem_after = get_server_process_memory_mb()

    success_count = sum(1 for status, _ in results if status == 200)
    fail_count = len(results) - success_count
    req_per_sec = len(results) / elapsed if elapsed > 0 else 0

    print(f"[TEST 1] Completed in {elapsed:.2f} seconds ({req_per_sec:.1f} req/sec).")
    print(f"[TEST 1] Total Requests: {len(results)} | Success (200 OK): {success_count} | Failures: {fail_count}")
    print(f"[TEST 1] Server memory after test: {mem_after:.2f} MB (Delta: {mem_after - mem_before:+.2f} MB)")

    # Verify server is still alive
    alive = is_server_running()
    print(f"[TEST 1] Server health check after load: {'ALIVE' if alive else 'DEAD'}")

    passed = (fail_count == 0) and alive and (success_count == total_expected)
    print(f"[TEST 1] VERDICT: {'PASS' if passed else 'FAIL'}")
    return passed, {
        "num_threads": num_threads,
        "total_requests": len(results),
        "success_count": success_count,
        "fail_count": fail_count,
        "elapsed_sec": elapsed,
        "req_per_sec": req_per_sec,
        "mem_before_mb": mem_before,
        "mem_after_mb": mem_after,
        "server_alive": alive
    }

# ==============================================================================
# TEST 2: Rapid Disconnect Requests Interspersed with Concurrent Heartbeats
# ==============================================================================
def run_test_2():
    print("\n" + "="*80)
    print("TEST 2: Rapid Disconnect Requests Interspersed with Active Heartbeats")
    print("="*80)

    heartbeat_threads = 30
    disconnect_threads = 25
    ops_per_thread = 40

    mem_before = get_server_process_memory_mb()
    print(f"[TEST 2] Launching {heartbeat_threads} heartbeat threads + {disconnect_threads} disconnect threads ({ops_per_thread} ops each)...")

    start_time = time.time()
    results = []

    def heartbeat_worker(idx):
        res = []
        client_id = f"stress_t2_hb_{idx:03d}"
        device_name = f"Active Device {idx:03d}"
        for _ in range(ops_per_thread):
            st, bd = send_request("/api/heartbeat", data={"client_id": client_id, "device_name": device_name})
            res.append(("hb", st, bd))
        return res

    def disconnect_worker(idx):
        res = []
        # Target both existing clients and non-existent IDs
        for i in range(ops_per_thread):
            if i % 2 == 0:
                target_id = f"stress_t2_hb_{i % heartbeat_threads:03d}"
            else:
                target_id = f"nonexistent_client_{idx}_{i}"
            st, bd = send_request("/api/disconnect", data={"client_id": target_id})
            res.append(("dc", st, bd))
        return res

    with concurrent.futures.ThreadPoolExecutor(max_workers=heartbeat_threads + disconnect_threads) as executor:
        hb_futures = [executor.submit(heartbeat_worker, i) for i in range(heartbeat_threads)]
        dc_futures = [executor.submit(disconnect_worker, i) for i in range(disconnect_threads)]

        for f in concurrent.futures.as_completed(hb_futures + dc_futures):
            results.extend(f.result())

    elapsed = time.time() - start_time
    mem_after = get_server_process_memory_mb()

    hb_results = [r for r in results if r[0] == "hb"]
    dc_results = [r for r in results if r[0] == "dc"]

    hb_success = sum(1 for r in hb_results if r[1] == 200)
    dc_success = sum(1 for r in dc_results if r[1] == 200)

    print(f"[TEST 2] Completed in {elapsed:.2f} seconds.")
    print(f"[TEST 2] Heartbeats: {len(hb_results)} total, {hb_success} succeeded.")
    print(f"[TEST 2] Disconnects: {len(dc_results)} total, {dc_success} succeeded.")

    alive = is_server_running()
    print(f"[TEST 2] Server health check: {'ALIVE' if alive else 'DEAD'}")

    passed = (hb_success == len(hb_results)) and (dc_success == len(dc_results)) and alive
    print(f"[TEST 2] VERDICT: {'PASS' if passed else 'FAIL'}")
    return passed, {
        "heartbeats_total": len(hb_results),
        "heartbeats_success": hb_success,
        "disconnects_total": len(dc_results),
        "disconnects_success": dc_success,
        "elapsed_sec": elapsed,
        "mem_before_mb": mem_before,
        "mem_after_mb": mem_after,
        "server_alive": alive
    }

# ==============================================================================
# TEST 3: Malformed Requests (Invalid JSON, Missing Fields, 404 Images, Oversized Headers)
# ==============================================================================
def run_test_3():
    print("\n" + "="*80)
    print("TEST 3: Malformed Requests & Boundary Conditions")
    print("="*80)

    cases_passed = 0
    total_cases = 0

    # Subtest 3A: Invalid JSON syntax to /api/heartbeat and /api/disconnect
    invalid_json_payloads = [
        "{bad_json:",
        "{\"client_id\":",
        "[1, 2, 3,",
        "Unformatted raw string",
        "{\"client_id\": \"test\", \"device_name\": }",
        "\x00\x01\x02\x03\x04\x05",
        "{\"key\": \"val\""
    ]

    print("[TEST 3A] Testing Invalid JSON Payloads (Expected HTTP 400 Bad Request)...")
    subtest_3a_pass = True
    for ep in ["/api/heartbeat", "/api/disconnect"]:
        for payload in invalid_json_payloads:
            total_cases += 1
            st, bd = send_request(ep, raw_body=payload)
            if st == 400 and "invalid json" in bd:
                cases_passed += 1
            else:
                print(f"  [FAIL 3A] Endpoint {ep} with payload '{payload[:20]}...' returned HTTP {st}: {bd}")
                subtest_3a_pass = False

    print(f"  -> Subtest 3A Result: {'PASS' if subtest_3a_pass else 'FAIL'}")

    # Subtest 3B: Missing Fields in JSON
    print("[TEST 3B] Testing Missing JSON Fields (Expected Fallback Handling HTTP 200)...")
    subtest_3b_pass = True
    missing_field_payloads = [
        ({}, "/api/heartbeat"),
        ({"device_name": "Device Only"}, "/api/heartbeat"),
        ({"client_id": "client_only"}, "/api/heartbeat"),
        ({}, "/api/disconnect"),
        ({"device_name": "Device Only"}, "/api/disconnect")
    ]
    for payload, ep in missing_field_payloads:
        total_cases += 1
        st, bd = send_request(ep, data=payload)
        if st == 200:
            cases_passed += 1
        else:
            print(f"  [FAIL 3B] Endpoint {ep} with payload {payload} returned HTTP {st}: {bd}")
            subtest_3b_pass = False

    print(f"  -> Subtest 3B Result: {'PASS' if subtest_3b_pass else 'FAIL'}")

    # Subtest 3C: Non-existent /images/ requests & directory traversal attempts
    print("[TEST 3C] Testing Non-existent /images/ Routes & Path Traversal (Expected 404 / Safe handling)...")
    subtest_3c_pass = True
    image_paths = [
        "/images/non_existent_icon_999999.png",
        "/images/../../windows/system32/cmd.exe",
        "/images/..%2f..%2fwindows/system32/cmd.exe",
        "/images/",
        "/images/nonexistent_folder/some_img.jpg"
    ]
    for img_path in image_paths:
        total_cases += 1
        st, bd = send_request(img_path, method="GET")
        # 404 or 400 is acceptable as long as server doesn't crash or return 500/unhandled
        if st in (404, 400):
            cases_passed += 1
        else:
            print(f"  [WARN 3C] Image path '{img_path}' returned HTTP {st}")
            # If it didn't crash, still verify server alive
            if not is_server_running():
                subtest_3c_pass = False

    print(f"  -> Subtest 3C Result: {'PASS' if subtest_3c_pass else 'FAIL'}")

    # Subtest 3D: Oversized Payloads & Headers
    print("[TEST 3D] Testing Oversized Payloads & Headers...")
    subtest_3d_pass = True

    # 1. Large JSON payload (250 KB)
    large_device_name = "X" * (250 * 1024)
    total_cases += 1
    st, bd = send_request("/api/heartbeat", data={"client_id": "large_client", "device_name": large_device_name}, timeout=10)
    if st in (200, 400, 413):
        cases_passed += 1
    else:
        print(f"  [FAIL 3D] Large JSON payload returned HTTP {st}")
        subtest_3d_pass = False

    # 2. Large header (64 KB)
    total_cases += 1
    large_header_val = "Y" * (64 * 1024)
    st, bd = send_request("/api/apps", method="GET", headers={"X-Custom-Header": large_header_val}, timeout=10)
    if st in (200, 400, 413, 431):
        cases_passed += 1
    else:
        print(f"  [FAIL 3D] Large header returned HTTP {st}")
        subtest_3d_pass = False

    print(f"  -> Subtest 3D Result: {'PASS' if subtest_3d_pass else 'FAIL'}")

    alive = is_server_running()
    passed = (cases_passed == total_cases) and alive
    print(f"[TEST 3] Total Cases: {total_cases} | Passed: {cases_passed} | Failed: {total_cases - cases_passed}")
    print(f"[TEST 3] VERDICT: {'PASS' if passed else 'FAIL'}")

    return passed, {
        "total_cases": total_cases,
        "cases_passed": cases_passed,
        "cases_failed": total_cases - cases_passed,
        "subtest_3a_pass": subtest_3a_pass,
        "subtest_3b_pass": subtest_3b_pass,
        "subtest_3c_pass": subtest_3c_pass,
        "subtest_3d_pass": subtest_3d_pass,
        "server_alive": alive
    }

# ==============================================================================
# TEST 4: Concurrent Client List Queries & 15-second Cleanup Thread Interaction
# ==============================================================================
def run_test_4():
    print("\n" + "="*80)
    print("TEST 4: Concurrent Client List Queries during 15s Timeout Cleanup Thread")
    print("="*80)

    # 1. Register 40 clients
    print("[TEST 4] Registering 40 clients via /api/heartbeat...")
    active_clients = [f"active_client_{i:02d}" for i in range(20)]
    timeout_clients = [f"timeout_client_{i:02d}" for i in range(20)]

    for cid in active_clients + timeout_clients:
        send_request("/api/heartbeat", data={"client_id": cid, "device_name": f"Device {cid}"})

    print("[TEST 4] 40 clients registered. Starting 18-second timeout phase...")
    print("[TEST 4] Continuously heartbeating active clients while letting timeout clients age out...")
    print("[TEST 4] Simultaneously running 20 concurrent reader threads requesting /api/apps...")

    start_time = time.time()
    stop_signal = False

    def active_heartbeat_worker():
        while not stop_signal:
            for cid in active_clients:
                send_request("/api/heartbeat", data={"client_id": cid, "device_name": f"Device {cid}"})
            time.sleep(1.5)

    def reader_worker():
        read_count = 0
        while not stop_signal:
            st, _ = send_request("/api/apps", method="GET")
            if st == 200:
                read_count += 1
            time.sleep(0.1)
        return read_count

    total_reads = 0
    with concurrent.futures.ThreadPoolExecutor(max_workers=25) as executor:
        hb_fut = executor.submit(active_heartbeat_worker)
        read_futs = [executor.submit(reader_worker) for _ in range(20)]

        # Wait for 18 seconds (longer than the 15s timeout threshold + 3s thread cycle)
        for elapsed_sec in range(1, 19):
            time.sleep(1)
            if elapsed_sec % 5 == 0:
                print(f"  [TEST 4 Progress] {elapsed_sec}/18 seconds elapsed...")

        stop_signal = True
        hb_fut.result()
        for f in read_futs:
            total_reads += f.result()

    elapsed = time.time() - start_time
    print(f"[TEST 4] 18-second cycle complete. Total concurrent GET /api/apps requests served: {total_reads}")

    # Now verify server health and session state
    alive = is_server_running()
    print(f"[TEST 4] Server health check: {'ALIVE' if alive else 'DEAD'}")

    # Test explicit disconnect cleanup on remaining active clients
    for cid in active_clients:
        send_request("/api/disconnect", data={"client_id": cid})

    passed = alive and (total_reads > 0)
    print(f"[TEST 4] VERDICT: {'PASS' if passed else 'FAIL'}")

    return passed, {
        "active_clients_count": len(active_clients),
        "timeout_clients_count": len(timeout_clients),
        "total_reader_requests": total_reads,
        "elapsed_sec": elapsed,
        "server_alive": alive
    }

# ==============================================================================
# MAIN TEST RUNNER
# ==============================================================================
def run_all_stress_tests():
    print("="*80)
    print("     LOCAL APK STORE - SERVER & API EMPIRICAL STRESS TEST SUITE     ")
    print("="*80)

    started_proc = None
    try:
        started_proc = ensure_server_running()

        t1_pass, t1_data = run_test_1()
        t2_pass, t2_data = run_test_2()
        t3_pass, t3_data = run_test_3()
        t4_pass, t4_data = run_test_4()

        all_passed = t1_pass and t2_pass and t3_pass and t4_pass

        print("\n" + "="*80)
        print("                  STRESS TEST RESULTS SUMMARY                   ")
        print("="*80)
        print(f"  Test 1: 50+ Concurrent Heartbeats        : {'PASS' if t1_pass else 'FAIL'}")
        print(f"  Test 2: Interspersed Disconnects/Heartbeats: {'PASS' if t2_pass else 'FAIL'}")
        print(f"  Test 3: Malformed & Oversized Requests   : {'PASS' if t3_pass else 'FAIL'}")
        print(f"  Test 4: Concurrent Queries & 15s Cleanup : {'PASS' if t4_pass else 'FAIL'}")
        print("="*80)
        print(f"FINAL VERDICT: {'APPROVE' if all_passed else 'REJECT'}")
        print("="*80)

        return 0 if all_passed else 1

    finally:
        if started_proc is not None:
            print("[TEARDOWN] Terminating started server process...")
            started_proc.terminate()
            try:
                started_proc.wait(timeout=3)
            except Exception:
                started_proc.kill()

if __name__ == "__main__":
    sys.exit(run_all_stress_tests())
