import os
import json
from flask import Flask, request, jsonify, send_from_directory
from werkzeug.utils import secure_filename

app = Flask(__name__)
PORT = 8443
HOST = '0.0.0.0'

# Setup directories and db
BASE_DIR = os.path.dirname(os.path.abspath(__name__))
APK_DIR = os.path.join(BASE_DIR, 'apks')
IMG_DIR = os.path.join(BASE_DIR, 'images')
DB_FILE = os.path.join(BASE_DIR, 'db.json')

os.makedirs(APK_DIR, exist_ok=True)
os.makedirs(IMG_DIR, exist_ok=True)

# Initialize DB if not exists
if not os.path.exists(DB_FILE):
    with open(DB_FILE, 'w') as f:
        json.dump({"apps": []}, f)

def load_db():
    with open(DB_FILE, 'r') as f:
        return json.load(f)

def save_db(data):
    with open(DB_FILE, 'w') as f:
        json.dump(data, f, indent=4)

@app.route('/api/apps', methods=['GET'])
def list_apps():
    search_query = request.args.get('q', '').lower()
    db = load_db()
    
    if search_query:
        filtered_apps = [app for app in db['apps'] if search_query in app.get('name', '').lower() or search_query in app.get('description', '').lower()]
        return jsonify({"apps": filtered_apps})
    
    return jsonify(db)

@app.route('/api/upload', methods=['POST'])
def upload_app():
    if 'apk' not in request.files:
        return jsonify({"error": "No APK file provided"}), 400
    
    apk_file = request.files['apk']
    name = request.form.get('name', 'Unknown App')
    description = request.form.get('description', 'No description provided')
    version = request.form.get('version', '1.0')
    package_name = request.form.get('package_name', 'com.unknown.app')
    
    if apk_file.filename == '':
        return jsonify({"error": "No selected APK file"}), 400

    apk_filename = secure_filename(apk_file.filename)
    apk_save_path = os.path.join(APK_DIR, apk_filename)
    apk_file.save(apk_save_path)
    
    # Handle Icon
    icon_filename = ""
    if 'icon' in request.files and request.files['icon'].filename != '':
        icon_file = request.files['icon']
        icon_filename = secure_filename(package_name + "_icon.png")
        icon_file.save(os.path.join(IMG_DIR, icon_filename))
        
    # Handle Screenshots (multiple files)
    screenshots = []
    if 'screenshots' in request.files:
        files = request.files.getlist('screenshots')
        for f in files:
            if f.filename != '':
                s_name = secure_filename(f.filename)
                f.save(os.path.join(IMG_DIR, s_name))
                screenshots.append(s_name)
    
    db = load_db()
    existing_app = next((a for a in db['apps'] if a['package_name'] == package_name), None)
    
    if existing_app:
        # Check if version already exists to avoid duplicates
        if not any(v['version'] == version for v in existing_app['versions']):
            existing_app['versions'].append({"version": version, "file": apk_filename})
        existing_app['description'] = description
        if icon_filename:
            existing_app['icon'] = icon_filename
        if screenshots:
            existing_app['screenshots'].extend(screenshots)
            existing_app['screenshots'] = list(set(existing_app['screenshots'])) # remove dupes
    else:
        new_app = {
            "name": name,
            "package_name": package_name,
            "description": description,
            "versions": [{"version": version, "file": apk_filename}],
            "icon": icon_filename,
            "screenshots": screenshots
        }
        db['apps'].append(new_app)
        
    save_db(db)
    return jsonify({"message": "App uploaded successfully"}), 201

@app.route('/download/<filename>')
def download_apk(filename):
    return send_from_directory(APK_DIR, filename)

@app.route('/images/<filename>')
def download_image(filename):
    return send_from_directory(IMG_DIR, filename)

if __name__ == '__main__':
    print(f"Local APK Store Server running on {HOST}:{PORT}")
    app.run(host=HOST, port=PORT, debug=False)
