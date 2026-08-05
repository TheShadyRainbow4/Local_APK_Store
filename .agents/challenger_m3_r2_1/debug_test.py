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

# Kill existing processes
subprocess.run(["powershell", "-Command", "Get-Process -Name 'Elite_App_Marketplace-Server', 'LocalAPKStore' -ErrorAction SilentlyContinue | Stop-Process -Force -ErrorAction SilentlyContinue"], capture_output=True)
time.sleep(1)

print("Starting server process...")
proc = subprocess.Popen([EXE_PATH], cwd=CWD, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

# Wait for server ready
start_t = time.time()
ready = False
while time.time() - start_t < 15:
    try:
        req = urllib.request.Request(f"{SERVER_URL}/api/apps", method='GET')
        with urllib.request.urlopen(req, timeout=1) as resp:
            if resp.status == 200:
                print("Server is listening.")
                ready = True
                break
    except Exception:
        time.sleep(0.5)

if not ready:
    print("Server failed to start!")
    sys.exit(1)

# Send heartbeat
print("Sending heartbeat...")
data = json.dumps({"client_id": "crash_test", "device_name": "Pixel 8"}).encode('utf-8')
req = urllib.request.Request(f"{SERVER_URL}/api/heartbeat", data=data, headers={'Content-Type': 'application/json'}, method='POST')
with urllib.request.urlopen(req) as resp:
    print(f"Heartbeat resp: {resp.status}")

# Wait 20s and monitor process state
for i in range(20):
    time.sleep(1)
    ret = proc.poll()
    if ret is not None:
        print(f"CRASH DETECTED at t={i+1}s! Exit code: {ret}")
        stdout, stderr = proc.communicate()
        print(f"STDOUT: {stdout.decode('utf-8', errors='ignore')}")
        print(f"STDERR: {stderr.decode('utf-8', errors='ignore')}")
        break
    else:
        print(f"t={i+1}s: Server still running...")

if proc.poll() is None:
    print("Server survived 20 seconds without crashing!")
    proc.terminate()
