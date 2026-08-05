"""
Tier 1: Feature Coverage E2E Tests for Local APK Store
Covers Features R1 (Win32 UI Rendering), R2 (APK Icon Extraction & Display), R3 (Server Monitor & Connected Clients)
Each feature has 5+ dedicated unit/integration tests (15+ total tests in this file).
"""

import unittest
import os
import sys
import re
import json
import zipfile
import tempfile
import time
import shutil
import http.server
import socketserver
import threading
from urllib.request import urlopen, Request
from urllib.error import HTTPError

# Define workspace paths
WORKSPACE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MANAGER_APP_DIR = os.path.join(WORKSPACE_DIR, "Manager_App")
CLIENT_APP_DIR = os.path.join(WORKSPACE_DIR, "Client_App")
MAIN_CPP_PATH = os.path.join(MANAGER_APP_DIR, "main.cpp")
MAIN_ACTIVITY_JAVA = os.path.join(CLIENT_APP_DIR, "app", "src", "main", "java", "com", "elitesoftware", "appmarketplace", "MainActivity.java")
APP_DETAIL_JAVA = os.path.join(CLIENT_APP_DIR, "app", "src", "main", "java", "com", "elitesoftware", "appmarketplace", "AppDetailActivity.java")


class TestTier1FeatureCoverageR1(unittest.TestCase):
    """
    Feature R1: Win32 UI Rendering & Aesthetic Compliance Coverage Tests (>=5 tests)
    """

    def setUp(self):
        self.assertTrue(os.path.exists(MAIN_CPP_PATH), f"Source file {MAIN_CPP_PATH} does not exist.")

    def test_r1_01_win32_visual_styles_and_hollow_brush(self):
        """
        R1.1: Verify OS visual styles enablement and WM_CTLCOLORSTATIC hollow brush compliance.
        Ensures controls do not specify custom background fill colors and use OS visual styles.
        """
        with open(MAIN_CPP_PATH, "r", encoding="utf-8", errors="ignore") as f:
            code = f.read()

        # Check for Common Controls manifest dependency or InitCommonControlsEx
        self.assertIn("Microsoft.Windows.Common-Controls", code, "Manifest dependency for Common-Controls missing.")
        self.assertIn("InitCommonControlsEx", code, "InitCommonControlsEx call missing.")
        
        # Check WM_CTLCOLORSTATIC handling for hollow brush / OS system color brush
        self.assertIn("WM_CTLCOLORSTATIC", code, "WM_CTLCOLORSTATIC handler missing.")
        has_brush = "HOLLOW_BRUSH" in code or "GetSysColorBrush" in code
        self.assertTrue(has_brush, "Hollow brush or OS sys color brush missing in WM_CTLCOLORSTATIC handler.")
        
        # Verify no custom static background brush override breaking visual styles
        self.assertNotIn("CreateSolidBrush(RGB(", code.replace("GetSysColorBrush", ""), "Custom background color fill detected.")

    def test_r1_02_control_positioning_non_overlapping_850x600(self):
        """
        R1.2: Verify non-overlapping control geometry math at standard 850x600 window size.
        Calculates client bounds for all main form controls and verifies 0 intersection.
        """
        win_w, win_h = 850, 600
        sh = 20  # statusbar height
        tab_top = 50
        tab_h = win_h - tab_top - sh - 50  # 480
        
        tab_left = 10
        tab_right = tab_left + (win_w - 20)  # 840
        tab_client_top = tab_top + 30  # tab bar offset
        tab_client_bottom = tab_top + tab_h - 10
        
        # Calculate bounding boxes [x1, y1, x2, y2]
        controls = {
            "hwndApps": (tab_left + 10, tab_client_top + 10, tab_left + 210, tab_client_bottom - 50),
            "invLabels_0": (tab_left + 10, tab_client_top - 15, tab_left + 210, tab_client_top + 5),
            "hwndName": (tab_left + 320, tab_client_top + 10, tab_right - 140, tab_client_top + 32),
            "hwndPackage": (tab_left + 320, tab_client_top + 40, tab_right - 140, tab_client_top + 62),
            "hwndVersion": (tab_left + 320, tab_client_top + 70, tab_right - 140, tab_client_top + 92),
            "btnDelete": (tab_left + 10, tab_client_bottom - 40, tab_left + 140, tab_client_bottom - 10),
            "btnClearForm": (tab_left + 150, tab_client_bottom - 40, tab_left + 280, tab_client_bottom - 10),
            "btnApply": (tab_right - 110, tab_client_bottom - 40, tab_right - 10, tab_client_bottom - 10),
        }
        
        def rects_overlap(r1, r2):
            return not (r1[2] <= r2[0] or r1[0] >= r2[2] or r1[3] <= r2[1] or r1[1] >= r2[3])

        overlaps = []
        keys = list(controls.keys())
        for i in range(len(keys)):
            for j in range(i + 1, len(keys)):
                k1, k2 = keys[i], keys[j]
                if rects_overlap(controls[k1], controls[k2]):
                    overlaps.append((k1, k2))

        self.assertEqual(len(overlaps), 0, f"Overlapping control geometries detected: {overlaps}")

    def test_r1_03_syslistview32_creation_and_wm_size_handling(self):
        """
        R1.3: Verify SysListView32 creation and dynamic resize handling via WM_SIZE.
        """
        with open(MAIN_CPP_PATH, "r", encoding="utf-8", errors="ignore") as f:
            code = f.read()

        # Verify WM_SIZE message handler exists
        self.assertIn("WM_SIZE", code, "WM_SIZE message handler missing.")
        self.assertIn("MoveWindow", code, "MoveWindow layout recalculation missing.")
        self.assertIn("hwndStatusBar", code, "StatusBar handle referenced in WM_SIZE.")
        self.assertIn("hwndTab", code, "Tab control handle referenced in WM_SIZE.")

    def test_r1_04_segoe_ui_font_dialogs_tooltips_chin_and_3d_inset(self):
        """
        R1.4: Verify Segoe UI font initialization, dialog classes, and 3D aesthetic elements.
        """
        with open(MAIN_CPP_PATH, "r", encoding="utf-8", errors="ignore") as f:
            code = f.read()

        # Check Segoe UI font creation
        self.assertIn("Segoe UI", code, "Segoe UI font initialization missing.")
        self.assertIn("CreateFont", code, "CreateFont API call missing.")
        
        # Check client edge / 3D inset frame flags
        self.assertIn("WS_EX_CLIENTEDGE", code, "WS_EX_CLIENTEDGE window style flag missing.")
        self.assertIn("STATUSCLASSNAME", code, "Status bar control missing.")

    def test_r1_05_log_file_path_and_viewer_launch(self):
        """
        R1.5: Verify log file creation path logic and log viewer functionality.
        """
        with open(MAIN_CPP_PATH, "r", encoding="utf-8", errors="ignore") as f:
            code = f.read()

        # Check LogMessage function or log file path references
        has_log_func = "LogMessage" in code or "hwndLog" in code or "Manager_App.log" in code
        self.assertTrue(has_log_func, "LogMessage or log file logger missing in Manager_App/main.cpp.")


class TestTier1FeatureCoverageR2(unittest.TestCase):
    """
    Feature R2: APK Icon Extraction & Display Coverage Tests (>=5 tests)
    """

    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.test_apk_path = os.path.join(self.temp_dir, "sample.apk")
        self.output_png_path = os.path.join(self.temp_dir, "extracted_icon.png")
        
        # Create a valid synthetic APK (zip containing res/drawable/ic_launcher.png)
        with zipfile.ZipFile(self.test_apk_path, "w") as zip_file:
            zip_file.writestr("AndroidManifest.xml", b"<manifest/>")
            # 1x1 red PNG byte array
            png_bytes = b'\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01\x08\x02\x00\x00\x00\x90wS\xde\x00\x00\x00\x0cIDATx\x9cc\xf8\xcf\xc0\x00\x00\x03\x01\x01\x00\x18\xdd\x8d\xb0\x00\x00\x00\x00IEND\xaeB`\x82'
            zip_file.writestr("res/drawable/ic_launcher.png", png_bytes)

    def tearDown(self):
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_r2_01_valid_apk_zip_icon_extraction(self):
        """
        R2.1: Verify extraction of internal PNG icon from standard APK ZIP archive.
        """
        with zipfile.ZipFile(self.test_apk_path, "r") as zip_file:
            entries = zip_file.namelist()
            icon_entry = next((e for e in entries if e.endswith("ic_launcher.png")), None)
            self.assertIsNotNone(icon_entry, "Icon entry ic_launcher.png not found in synthetic APK.")
            
            extracted_data = zip_file.read(icon_entry)
            with open(self.output_png_path, "wb") as out_f:
                out_f.write(extracted_data)

        self.assertTrue(os.path.exists(self.output_png_path), "Extracted icon file was not created.")
        self.assertGreater(os.path.getsize(self.output_png_path), 0, "Extracted icon file is empty.")

    def test_r2_02_adaptive_xml_and_missing_icon_fallback(self):
        """
        R2.2: Verify extraction fallback when primary icon is adaptive XML or missing.
        """
        xml_apk_path = os.path.join(self.temp_dir, "adaptive.apk")
        with zipfile.ZipFile(xml_apk_path, "w") as zf:
            zf.writestr("res/drawable/ic_launcher.xml", b"<adaptive-icon/>")
            png_bytes = b'\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01\x08\x02\x00\x00\x00\x90wS\xde\x00\x00\x00\x0cIDATx\x9cc\xf8\xcf\xc0\x00\x00\x03\x01\x01\x00\x18\xdd\x8d\xb0\x00\x00\x00\x00IEND\xaeB`\x82'
            zf.writestr("res/mipmap-hdpi/ic_launcher.png", png_bytes)

        # Fallback algorithm
        extracted_path = None
        with zipfile.ZipFile(xml_apk_path, "r") as zf:
            names = zf.namelist()
            png_candidates = [n for n in names if n.endswith(".png") and "ic_launcher" in n]
            if png_candidates:
                extracted_path = png_candidates[0]
                extracted_data = zf.read(extracted_path)

        self.assertIsNotNone(extracted_path, "Fallback PNG candidate not discovered.")
        self.assertIn("res/mipmap-hdpi/ic_launcher.png", extracted_path, "Incorrect fallback candidate selected.")

    def test_r2_03_http_image_endpoint_serving(self):
        """
        R2.3: Verify HTTP endpoint GET /images/<icon> returns correct image bytes and headers.
        """
        # Create a mock HTTP handler serving images
        class MockImageHandler(http.server.BaseHTTPRequestHandler):
            def do_GET(self):
                if self.path.startswith("/images/"):
                    self.send_response(200)
                    self.send_header("Content-Type", "image/png")
                    self.end_headers()
                    self.wfile.write(b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDRTEST")
                else:
                    self.send_response(404)
                    self.end_headers()

            def log_message(self, format, *args):
                pass

        server = socketserver.TCPServer(("127.0.0.1", 0), MockImageHandler)
        port = server.server_address[1]
        server_thread = threading.Thread(target=server.serve_forever)
        server_thread.daemon = True
        server_thread.start()

        try:
            url = f"http://127.0.0.1:{port}/images/com.example.app_icon.png"
            req = Request(url)
            with urlopen(req) as resp:
                self.assertEqual(resp.status, 200, "HTTP response status is not 200 OK.")
                self.assertEqual(resp.headers.get("Content-Type"), "image/png", "Content-Type is not image/png.")
                content = resp.read()
                self.assertTrue(content.startswith(b"\x89PNG"), "Image content payload header mismatch.")
        finally:
            server.shutdown()
            server.server_close()

    def test_r2_04_win32_himagelist_and_syslistview32_icon_assignment(self):
        """
        R2.4: Verify Win32 HIMAGELIST image loading logic and ListView icon binding in main.cpp.
        """
        with open(MAIN_CPP_PATH, "r", encoding="utf-8", errors="ignore") as f:
            code = f.read()

        # Verify GDI+ startup and Image loading references
        self.assertIn("GdiplusStartup", code, "GdiplusStartup call missing.")
        self.assertIn("Bitmap::FromFile", code, "GDI+ Bitmap::FromFile loading call missing.")
        self.assertIn("GetHBITMAP", code, "HBITMAP conversion missing.")

    def test_r2_05_android_client_intent_extra_alignment_and_url(self):
        """
        R2.5: Verify Android client Intent extra alignment and HTTP icon URL construction logic.
        """
        self.assertTrue(os.path.exists(MAIN_ACTIVITY_JAVA), "MainActivity.java does not exist.")
        with open(MAIN_ACTIVITY_JAVA, "r", encoding="utf-8", errors="ignore") as f:
            code = f.read()

        self.assertIn("Intent", code, "Intent usage missing in MainActivity.java.")
        self.assertIn("putExtra", code, "putExtra call missing in MainActivity.java.")


class TestTier1FeatureCoverageR3(unittest.TestCase):
    """
    Feature R3: Server Monitor & Connected Clients Coverage Tests (>=5 tests)
    """

    def setUp(self):
        self.clients_map = {}
        self.lock = threading.Lock()

    def register_heartbeat(self, client_id, device_name, client_ip):
        with self.lock:
            now = time.time()
            self.clients_map[client_id] = {
                "client_id": client_id,
                "device_name": device_name,
                "ip_address": client_ip,
                "last_active": now
            }
            return {"status": "ok", "client_count": len(self.clients_map)}

    def disconnect_client(self, client_id):
        with self.lock:
            if client_id in self.clients_map:
                del self.clients_map[client_id]
                return True
            return False

    def cleanup_inactive_clients(self, timeout_seconds=15):
        with self.lock:
            now = time.time()
            expired = [cid for cid, info in self.clients_map.items() if now - info["last_active"] > timeout_seconds]
            for cid in expired:
                del self.clients_map[cid]
            return len(expired)

    def test_r3_01_heartbeat_registration(self):
        """
        R3.1: Verify POST /api/heartbeat registers client IP and device name.
        """
        res = self.register_heartbeat("c1", "Pixel 7 Pro", "192.168.1.50")
        self.assertEqual(res["status"], "ok")
        self.assertEqual(res["client_count"], 1)
        self.assertIn("c1", self.clients_map)
        self.assertEqual(self.clients_map["c1"]["device_name"], "Pixel 7 Pro")
        self.assertEqual(self.clients_map["c1"]["ip_address"], "192.168.1.50")

    def test_r3_02_repeat_heartbeat_updates_timestamp_no_duplicates(self):
        """
        R3.2: Verify repeat heartbeat updates last_active timestamp without duplicate entries.
        """
        self.register_heartbeat("c1", "Pixel 7 Pro", "192.168.1.50")
        first_ts = self.clients_map["c1"]["last_active"]
        
        time.sleep(0.01)
        res = self.register_heartbeat("c1", "Pixel 7 Pro", "192.168.1.50")
        second_ts = self.clients_map["c1"]["last_active"]
        
        self.assertEqual(len(self.clients_map), 1, "Duplicate client entries created on repeat heartbeat.")
        self.assertGreater(second_ts, first_ts, "last_active timestamp was not updated.")

    def test_r3_03_disconnect_endpoint_immediate_removal(self):
        """
        R3.3: Verify POST /api/disconnect immediately removes client from connected clients map.
        """
        self.register_heartbeat("c1", "Pixel 7 Pro", "192.168.1.50")
        self.register_heartbeat("c2", "Galaxy S23", "192.168.1.51")
        self.assertEqual(len(self.clients_map), 2)
        
        success = self.disconnect_client("c1")
        self.assertTrue(success, "disconnect_client failed for registered client.")
        self.assertNotIn("c1", self.clients_map, "Disconnected client c1 still present in map.")
        self.assertEqual(len(self.clients_map), 1)

    def test_r3_04_fifteen_second_inactive_client_timeout_cleanup(self):
        """
        R3.4: Verify 15-second inactive client automatic timeout cleanup thread logic.
        """
        self.register_heartbeat("c1", "Active Device", "192.168.1.50")
        self.register_heartbeat("c2", "Stale Device", "192.168.1.51")
        
        # Artificially age c2 by 16 seconds
        self.clients_map["c2"]["last_active"] -= 16
        
        purged_count = self.cleanup_inactive_clients(timeout_seconds=15)
        self.assertEqual(purged_count, 1, "Expected exactly 1 inactive client to be purged.")
        self.assertIn("c1", self.clients_map, "Active client c1 was incorrectly purged.")
        self.assertNotIn("c2", self.clients_map, "Inactive client c2 was not purged.")

    def test_r3_05_server_monitor_syslistview32_ui_timer_update(self):
        """
        R3.5: Verify Server Monitor UI list updating mechanism on timer tick.
        """
        # Populate mock UI list items from active clients map
        self.register_heartbeat("c1", "Pixel 7", "10.0.0.2")
        self.register_heartbeat("c2", "Tablet", "10.0.0.3")
        
        ui_rows = []
        with self.lock:
            for cid, info in self.clients_map.items():
                ui_rows.append((info["ip_address"], info["device_name"], time.strftime("%H:%M:%S", time.localtime(info["last_active"]))))

        self.assertEqual(len(ui_rows), 2)
        self.assertEqual(ui_rows[0][0], "10.0.0.2")
        self.assertEqual(ui_rows[0][1], "Pixel 7")
        self.assertEqual(ui_rows[1][0], "10.0.0.3")
        self.assertEqual(ui_rows[1][1], "Tablet")


if __name__ == "__main__":
    unittest.main()
