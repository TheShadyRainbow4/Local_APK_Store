import os
import json
import time
import urllib.request
import urllib.error
import subprocess

manager_dir = r"C:\Users\Administrator\Desktop\Local_APK_Store\Manager_App"
db_path = os.path.join(manager_dir, "db.json")
img_dir = os.path.join(manager_dir, "images")
exe_path = os.path.join(manager_dir, "Elite_App_Marketplace-Server.exe")
if not os.path.exists(exe_path):
    exe_path = os.path.join(manager_dir, "LocalAPKStore.exe")

print(f"=== Step 1: Launching {os.path.basename(exe_path)} ===")
proc = subprocess.Popen([exe_path], cwd=manager_dir)
print(f"Process launched with PID: {proc.pid}")

print("Waiting 12 seconds for auto-scan cycle to complete...")
time.sleep(12)

print("\n=== Step 2 & 4: Verifying db.json and extracted .png icons ===")
with open(db_path, "r", encoding="utf-8") as f:
    db = json.load(f)

apps = db.get("apps", [])
total_apps = len(apps)
apps_with_pkg = [a for a in apps if a.get("package_name") and not a.get("package_name").startswith("unknown.package")]
apps_with_icon = [a for a in apps if a.get("icon") and os.path.exists(os.path.join(img_dir, a["icon"]))]

print(f"Total apps in db.json: {total_apps}")
print(f"Apps with valid package_name: {len(apps_with_pkg)}")
print(f"Apps with verified extracted icon file in images/: {len(apps_with_icon)}")

# List icon files in images/
img_files = os.listdir(img_dir) if os.path.exists(img_dir) else []
png_icons = [f for f in img_files if f.endswith(".png")]
print(f"Total PNG files in images/ directory: {len(png_icons)}")

print("\n=== Step 3: Specific Verification for Dark Sky Adaptive XML Vector Icon ===")
darksky_icon = "net.darksky.darksky_icon.png"
darksky_path = os.path.join(img_dir, darksky_icon)
if os.path.exists(darksky_path):
    size = os.path.getsize(darksky_path)
    with open(darksky_path, "rb") as f:
        header = f.read(8)
    header_hex = " ".join(f"{b:02X}" for b in header)
    png_magic = "89 50 4E 47 0D 0A 1A 0A"
    is_png = (header_hex == png_magic)
    print(f"Dark Sky icon file: {darksky_icon}")
    print(f"File Size: {size} bytes")
    print(f"Binary Header: {header_hex}")
    print(f"PNG Magic Match ({png_magic}): {is_png}")
else:
    print(f"ERROR: {darksky_icon} NOT FOUND!")

print("\n=== Step 5: Test HTTP Server Image Endpoint ===")
url = f"http://localhost:8552/images/{darksky_icon}"
print(f"Requesting GET {url}...")

req = urllib.request.Request(url, method='HEAD')
try:
    with urllib.request.urlopen(req) as resp:
        print(f"HTTP Status: {resp.status} {resp.reason}")
        print(f"Headers:\n{resp.headers}")
except urllib.error.HTTPError as e:
    print(f"HTTP Error: {e.code} {e.reason}")
except Exception as e:
    print(f"Connection Error: {e}")

# Now try GET request to verify content bytes
try:
    with urllib.request.urlopen(url) as resp:
        data = resp.read(8)
        data_hex = " ".join(f"{b:02X}" for b in data)
        print(f"GET Data Header: {data_hex}")
        print(f"GET Content matches PNG magic: {data_hex == '89 50 4E 47 0D 0A 1A 0A'}")
except Exception as e:
    print(f"GET Request Error: {e}")

print("\nTerminating server process...")
proc.terminate()
try:
    proc.wait(timeout=3)
except Exception:
    proc.kill()
print("Test script completed.")
