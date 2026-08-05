import subprocess
import time
import socket
import urllib.request
import json
import os
import sys

EXE_PATH = r"C:\Users\Administrator\Desktop\Local_APK_Store\Manager_App\Elite_App_Marketplace-Server.exe"
CWD_PATH = r"C:\Users\Administrator\Desktop\Local_APK_Store\Manager_App"
LOG_PATH = r"C:\EliteSoftware\Logs\LocalAPKStore.log"

print("=== Starting Verification of M3 R3 Fixes ===")

# Test 3: Startup Latency
print("\n--- Test 3: Startup Latency (< 1.0s) ---")
t0 = time.perf_counter()
p_latency = subprocess.Popen([EXE_PATH], cwd=CWD_PATH)
responded = False
latency = 0.0

for _ in range(40): # 40 * 50ms = 2s max wait
    time.sleep(0.05)
    try:
        req = urllib.request.urlopen("http://127.0.0.1:8552/api/apps", timeout=0.5)
        if req.status == 200:
            latency = time.perf_counter() - t0
            responded = True
            break
    except Exception:
        pass

p_latency.terminate()
p_latency.wait()

print(f"Server Startup Latency: {latency:.3f}s")
if responded and latency < 1.0:
    print("[PASS] Startup Latency requirement met (< 1.0s)")
else:
    print(f"[FAIL] Startup Latency requirement NOT met (responded={responded}, latency={latency:.3f}s)")

# Test 2: Port Conflict Error Handling
print("\n--- Test 2: Port Conflict Error Handling ---")
# Bind socket on port 8552
dummy_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
dummy_sock.bind(("0.0.0.0", 8552))
dummy_sock.listen(1)

# Record current log file content size
log_initial_size = 0
if os.path.exists(LOG_PATH):
    with open(LOG_PATH, "r", encoding="utf-8", errors="ignore") as f:
        log_initial_size = len(f.read())

p_port = subprocess.Popen([EXE_PATH], cwd=CWD_PATH)
time.sleep(1.0)
p_port.terminate()
p_port.wait()

dummy_sock.close()

port_error_logged = False
if os.path.exists(LOG_PATH):
    with open(LOG_PATH, "r", encoding="utf-8", errors="ignore") as f:
        log_content = f.read()[log_initial_size:]
        if "ERROR: HTTP Server failed to bind to port 8552" in log_content:
            port_error_logged = True

print(f"Port Error Logged: {port_error_logged}")
if port_error_logged:
    print("[PASS] Port Conflict Error Handling verified")
else:
    print("[FAIL] Port Conflict Error Handling NOT verified")

# Test 1: Cross-Thread Logging Crash (Client Timeout)
print("\n--- Test 1: Cross-Thread Logging Crash (Client Timeout) ---")
p_server = subprocess.Popen([EXE_PATH], cwd=CWD_PATH)
time.sleep(0.5)

try:
    # Send heartbeat
    hb_req = urllib.request.Request(
        "http://127.0.0.1:8552/api/heartbeat",
        data=json.dumps({"client_id": "test_crash_m3r3", "device_name": "TestDevice"}).encode("utf-8"),
        headers={"Content-Type": "application/json"}
    )
    resp = urllib.request.urlopen(hb_req)
    print(f"Initial Heartbeat response status: {resp.status}")

    print("Waiting 17 seconds for client timeout in ClientCleanupThread...")
    time.sleep(17)

    # Check if process is still running
    poll_res = p_server.poll()
    if poll_res is None:
        print("Server process is STILL RUNNING after 17s timeout!")
        # Try sending another request
        apps_resp = urllib.request.urlopen("http://127.0.0.1:8552/api/apps")
        if apps_resp.status == 200:
            print("[PASS] Cross-Thread Logging Crash Fix verified - Server alive and healthy!")
        else:
            print(f"[FAIL] Server responded with status {apps_resp.status}")
    else:
        print(f"[FAIL] Server CRASHED! Exit code: {poll_res}")
finally:
    if p_server.poll() is None:
        p_server.terminate()
        p_server.wait()

print("\n=== Verification Complete ===")
