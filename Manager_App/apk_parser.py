import sys
import json
import os
from pyaxmlparser import APK

def main():
    if len(sys.argv) < 2:
        print(json.dumps({"error": "No APK path provided"}))
        return
    
    apk_path = sys.argv[1]
    if not os.path.exists(apk_path):
        print(json.dumps({"error": "File does not exist"}))
        return

    try:
        apk = APK(apk_path)
        icon_path = ""
        # Try to extract icon
        try:
            icon_data = apk.icon_data
            if icon_data:
                icon_path = os.path.join(os.path.dirname(apk_path), apk.package + "_icon.png")
                with open(icon_path, 'wb') as f:
                    f.write(icon_data)
        except Exception:
            pass
            
        data = {
            "name": apk.application,
            "package": apk.package,
            "version": apk.version_name,
            "icon": icon_path
        }
        print(json.dumps(data))
    except Exception as e:
        print(json.dumps({"error": str(e)}))

if __name__ == "__main__":
    main()
