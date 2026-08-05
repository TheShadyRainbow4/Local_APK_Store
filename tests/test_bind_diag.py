import socket
import subprocess
import time
import os

LOG_FILE = r"C:\EliteSoftware\Logs\LocalAPKStore.log"

def test_bind_both():
    print("Binding IPv4 0.0.0.0:8552...")
    s4 = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        s4.setsockopt(socket.SOL_SOCKET, socket.SO_EXCLUSIVEADDRUSE, 1)
    except Exception:
        pass
    s4.bind(('0.0.0.0', 8552))
    s4.listen(1)

    print("Binding IPv6 :::8552...")
    s6 = socket.socket(socket.AF_INET6, socket.SOCK_STREAM)
    try:
        s6.setsockopt(socket.SOL_SOCKET, socket.SO_EXCLUSIVEADDRUSE, 1)
    except Exception:
        pass
    try:
        s6.bind(('::', 8552))
        s6.listen(1)
        print("IPv6 bound successfully.")
    except Exception as e:
        print("IPv6 bind error:", e)

    print("Launching server process while port 8552 is occupied on both IPv4 & IPv6...")
    SERVER_EXE = r"C:\Users\Administrator\Desktop\Local_APK_Store\Manager_App\Elite_App_Marketplace-Server.exe"
    SERVER_DIR = r"C:\Users\Administrator\Desktop\Local_APK_Store\Manager_App"

    # Save log file size
    init_size = 0
    if os.path.exists(LOG_FILE):
        init_size = os.path.getsize(LOG_FILE)

    proc = subprocess.Popen([SERVER_EXE], cwd=SERVER_DIR)
    time.sleep(3)

    if os.path.exists(LOG_FILE):
        with open(LOG_FILE, 'r', encoding='utf-8', errors='ignore') as f:
            f.seek(init_size)
            new_logs = f.read()
        print("New log entries produced by server:")
        print(new_logs)

    proc.terminate()
    proc.wait()
    s4.close()
    if 's6' in locals(): s6.close()

if __name__ == '__main__':
    test_bind_both()
