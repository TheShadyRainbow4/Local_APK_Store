import socket
import subprocess
import time
import os
import urllib.request

LOG_FILE = r"C:\EliteSoftware\Logs\LocalAPKStore.log"

print("--- DIAGNOSTIC START ---")

# Step 1: Check if port 8552 is free right now
def is_port_free(port=8552):
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        s.bind(('0.0.0.0', port))
        s.close()
        return True
    except Exception as e:
        print(f"Port {port} bind error: {e}")
        return False

print("Is port 8552 free right now?", is_port_free(8552))

# Clear log file or record size
if os.path.exists(LOG_FILE):
    with open(LOG_FILE, 'r', encoding='utf-8', errors='ignore') as f:
        lines = f.readlines()
    print(f"Log file exists, last 5 lines:")
    for l in lines[-5:]:
        print("  ", l.strip())

print("--- TEST BINDING WITH EXCLUSIVE ACCESS ---")
s_occ = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
# On Windows, SO_EXCLUSIVEADDRUSE is -5 or 0x8000 in C, socket.SO_EXCLUSIVEADDRUSE
try:
    s_occ.setsockopt(socket.SOL_SOCKET, socket.SO_EXCLUSIVEADDRUSE, 1)
except Exception:
    pass
s_occ.bind(('0.0.0.0', 8552))
s_occ.listen(1)
print("Occupied port 8552 exclusively.")

# Launch server
SERVER_EXE = r"C:\Users\Administrator\Desktop\Local_APK_Store\Manager_App\Elite_App_Marketplace-Server.exe"
SERVER_DIR = r"C:\Users\Administrator\Desktop\Local_APK_Store\Manager_App"

proc = subprocess.Popen([SERVER_EXE], cwd=SERVER_DIR)
time.sleep(3)

if os.path.exists(LOG_FILE):
    with open(LOG_FILE, 'r', encoding='utf-8', errors='ignore') as f:
        lines = f.readlines()
    print(f"Log file after launch (last 10 lines):")
    for l in lines[-10:]:
        print("  ", l.strip())

proc.terminate()
proc.wait()
s_occ.close()
print("Closed occupied socket.")
time.sleep(1)
print("--- DIAGNOSTIC END ---")
