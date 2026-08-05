import socket
import subprocess
import time
import os

LOG_FILE = r"C:\EliteSoftware\Logs\LocalAPKStore.log"
SERVER_EXE = r"C:\Users\Administrator\Desktop\Local_APK_Store\Manager_App\Elite_App_Marketplace-Server.exe"
SERVER_DIR = r"C:\Users\Administrator\Desktop\Local_APK_Store\Manager_App"

def test_bind_conflict():
    print("Step 1: Occupying port 8552 on IPv4 (0.0.0.0) and IPv6 (::)...")
    s4 = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        s4.setsockopt(socket.SOL_SOCKET, socket.SO_EXCLUSIVEADDRUSE, 1)
    except Exception:
        pass
    s4.bind(('0.0.0.0', 8552))
    s4.listen(1)

    s6 = socket.socket(socket.AF_INET6, socket.SOCK_STREAM)
    try:
        s6.setsockopt(socket.SOL_SOCKET, socket.SO_EXCLUSIVEADDRUSE, 1)
    except Exception:
        pass
    try:
        s6.bind(('::', 8552))
        s6.listen(1)
        print("Both IPv4 and IPv6 sockets bound successfully to port 8552.")
    except Exception as e:
        print("IPv6 bind notice:", e)

    # Read current size of log file
    init_size = 0
    if os.path.exists(LOG_FILE):
        init_size = os.path.getsize(LOG_FILE)

    print("Step 2: Launching Elite_App_Marketplace-Server.exe...")
    proc = subprocess.Popen([SERVER_EXE], cwd=SERVER_DIR)
    time.sleep(3)

    new_log = ""
    if os.path.exists(LOG_FILE):
        with open(LOG_FILE, 'r', encoding='utf-8', errors='ignore') as f:
            f.seek(init_size)
            new_log = f.read()

    print("=== NEW LOG OUTPUT ===")
    print(new_log)
    print("======================")

    proc.terminate()
    proc.wait(timeout=2)
    s4.close()
    if 's6' in locals(): s6.close()

if __name__ == '__main__':
    test_bind_conflict()
