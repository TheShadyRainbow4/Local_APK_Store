import json
import os

db_path = r'C:\Users\Administrator\Desktop\Local_APK_Store\Manager_App\db.json'

with open(db_path, 'r', encoding='utf-8') as f:
    db = json.load(f)

for app in db.get('apps', []):
    versions = app.get('versions', [])
    # Sort descending based on length of version string and then string value, or just reverse it since they were appended
    # Actually, a simple reverse is fine, or sort by version parsing
    def parse_ver(v):
        try:
            return [int(x) for x in v['version'].replace('v', '').split('.')]
        except:
            return [0]
    
    versions.sort(key=parse_ver, reverse=True)
    app['versions'] = versions

with open(db_path, 'w', encoding='utf-8') as f:
    json.dump(db, f, indent=4)
