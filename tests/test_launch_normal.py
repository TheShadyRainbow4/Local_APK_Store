import subprocess
import time
import os

LOG_FILE = r"C:\EliteSoftware\Logs\LocalAPKStore.log"
SERVER_EXE = r"C:\Users\Administrator\Desktop\Local_APK_Store\Manager_App\Elite_App_Marketplace-Server.exe"
SERVER_DIR = r"C:\Users\Administrator\Desktop\Local_APK_Store\Manager_App"

def test_launch_normal():
    init_size = 0
    if os.path.exists(LOG_FILE):
        init_size = os.path.getsize(LOG_FILE)

    print("Launching server without occupied port...")
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

if __name__ == '__main__':
    test_launch_normal()
