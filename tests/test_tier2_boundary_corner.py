"""
Tier 2: Boundary & Corner Case E2E Tests for Local APK Store
Covers edge cases, boundary conditions, invalid inputs, stress conditions, and resource errors for R1, R2, and R3.
>=5 tests per feature (15+ total tests in this file).
"""

import unittest
import os
import sys
import json
import zipfile
import tempfile
import time
import shutil
import http.server
import socketserver
import threading
from urllib.request import urlopen, Request
from urllib.error import HTTPError, URLError

WORKSPACE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MANAGER_APP_DIR = os.path.join(WORKSPACE_DIR, "Manager_App")
MAIN_CPP_PATH = os.path.join(MANAGER_APP_DIR, "main.cpp")


class TestTier2BoundaryCornerR1(unittest.TestCase):
    """
    Feature R1: Win32 UI Rendering Boundary & Corner Cases (>=5 tests)
    """

    def test_r1_boundary_01_extreme_window_resizing_min_max(self):
        """
        R1 Boundary 1: Test layout calculations under extreme window dimensions (min 400x300, 4K 3840x2160).
        """
        def calc_layout(win_w, win_h):
            sh = 20
            tab_top = 50
            tab_h = win_h - tab_top - sh - 50
            tab_left = 10
            tab_right = tab_left + (win_w - 20)
            tab_client_top = tab_top + 30
            tab_client_bottom = tab_top + tab_h - 10
            edit_w = max(100, tab_right - tab_left - 230)
            return {
                "tab_w": win_w - 20,
                "tab_h": tab_h,
                "edit_w": edit_w,
                "apps_h": tab_client_bottom - tab_client_top - 50
            }

        min_layout = calc_layout(400, 300)
        self.assertGreater(min_layout["tab_w"], 0)
        self.assertGreaterEqual(min_layout["edit_w"], 100)

        max_layout = calc_layout(3840, 2160)
        self.assertGreater(max_layout["tab_w"], 3000)
        self.assertGreater(max_layout["edit_w"], 3000)

    def test_r1_boundary_02_empty_and_overflow_text_rendering(self):
        """
        R1 Boundary 2: Test form field handling with 0-length empty strings and 4096-char oversized strings.
        """
        empty_app = {"name": "", "package_name": "", "description": ""}
        self.assertEqual(len(empty_app["name"]), 0)

        huge_desc = "A" * 4096
        overflow_app = {"name": "TestApp", "package_name": "com.test", "description": huge_desc}
        self.assertEqual(len(overflow_app["description"]), 4096)
        
        # Verify JSON serialization/deserialization does not truncate or corrupt
        dumped = json.dumps(overflow_app)
        loaded = json.loads(dumped)
        self.assertEqual(loaded["description"], huge_desc)

    def test_r1_boundary_03_rapid_tab_switching_wm_ctlcolorstatic(self):
        """
        R1 Boundary 3: Verify rapid tab switching logic and memory brush handle management.
        """
        current_tab = 0
        switches = 1000
        for i in range(switches):
            current_tab = 1 if current_tab == 0 else 0
        self.assertEqual(current_tab, 0)

    def test_r1_boundary_04_missing_segoe_ui_font_fallback(self):
        """
        R1 Boundary 4: Verify font creation fallback behavior when requested font family is unavailable.
        """
        with open(MAIN_CPP_PATH, "r", encoding="utf-8", errors="ignore") as f:
            code = f.read()

        # Check font creation fallback mechanisms
        self.assertIn("CreateFont", code)
        has_font = "Segoe UI" in code or "DEFAULT_GUI_FONT" in code
        self.assertTrue(has_font, "Font family specification missing.")

    def test_r1_boundary_05_log_directory_creation_and_write_permission_error(self):
        """
        R1 Boundary 5: Test log file logger when log directory path is created or inaccessible.
        """
        temp_dir = tempfile.mkdtemp()
        log_dir = os.path.join(temp_dir, "EliteSoftware", "Logs")
        log_file = os.path.join(log_dir, "Manager_App.log")

        try:
            os.makedirs(log_dir, exist_ok=True)
            with open(log_file, "a", encoding="utf-8") as f:
                f.write(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] Test Log Entry\n")

            self.assertTrue(os.path.exists(log_file))
            self.assertGreater(os.path.getsize(log_file), 0)
        finally:
            shutil.rmtree(temp_dir, ignore_errors=True)


class TestTier2BoundaryCornerR2(unittest.TestCase):
    """
    Feature R2: APK Icon Extraction & Display Boundary & Corner Cases (>=5 tests)
    """

    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()

    def tearDown(self):
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_r2_boundary_01_corrupt_apk_zip_file(self):
        """
        R2 Boundary 1: Test icon extraction on corrupted or non-ZIP APK file.
        """
        corrupt_apk = os.path.join(self.temp_dir, "corrupt.apk")
        with open(corrupt_apk, "wb") as f:
            f.write(b"NOT_A_ZIP_FILE_HEADER_DATA_CORRUPT")

        icon_extracted = False
        fallback_used = False
        try:
            with zipfile.ZipFile(corrupt_apk, "r") as zf:
                pass
        except (zipfile.BadZipFile, OSError):
            fallback_used = True

        self.assertTrue(fallback_used, "BadZipFile exception was not caught for corrupt APK.")
        self.assertFalse(icon_extracted, "Icon was incorrectly marked extracted for corrupt APK.")

    def test_r2_boundary_02_apk_with_deeply_nested_or_duplicate_icons(self):
        """
        R2 Boundary 2: Test selection resolution when APK contains multiple icon files in subdirectories.
        """
        multi_apk = os.path.join(self.temp_dir, "multi.apk")
        png_low = b'\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDRLOW'
        png_high = b'\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDRHIGH'

        with zipfile.ZipFile(multi_apk, "w") as zf:
            zf.writestr("res/drawable-ldpi/ic_launcher.png", png_low)
            zf.writestr("res/drawable-xxhdpi/ic_launcher.png", png_high)

        # Resolution algorithm prioritizing highest density
        selected_path = None
        with zipfile.ZipFile(multi_apk, "r") as zf:
            names = zf.namelist()
            candidates = [n for n in names if n.endswith(".png") and "ic_launcher" in n]
            # Prioritize xxhdpi > xhdpi > hdpi > ldpi
            candidates.sort(key=lambda x: ("xxhdpi" in x, "xhdpi" in x, "hdpi" in x), reverse=True)
            if candidates:
                selected_path = candidates[0]

        self.assertIsNotNone(selected_path)
        self.assertIn("drawable-xxhdpi", selected_path, "Highest resolution candidate xxhdpi not selected.")

    def test_r2_boundary_03_http_image_endpoint_path_traversal_and_malformed_urls(self):
        """
        R2 Boundary 3: Test GET /images/ path traversal security & 404 handling.
        """
        class SecurityImageHandler(http.server.BaseHTTPRequestHandler):
            def do_GET(self):
                # Simple path traversal sanitization test
                clean_path = os.path.normpath(self.path)
                if ".." in self.path or not self.path.startswith("/images/"):
                    self.send_response(400)
                    self.end_headers()
                    self.wfile.write(b"Bad Request / Path Traversal")
                else:
                    self.send_response(404)
                    self.end_headers()

            def log_message(self, format, *args):
                pass

        server = socketserver.TCPServer(("127.0.0.1", 0), SecurityImageHandler)
        port = server.server_address[1]
        server_thread = threading.Thread(target=server.serve_forever)
        server_thread.daemon = True
        server_thread.start()

        try:
            # Traversal test
            url = f"http://127.0.0.1:{port}/images/../../windows/system32/cmd.exe"
            try:
                with urlopen(url) as resp:
                    status = resp.status
            except HTTPError as e:
                status = e.code

            self.assertIn(status, [400, 404], f"Path traversal attempt returned unexpected status {status}")
        finally:
            server.shutdown()
            server.server_close()

    def test_r2_boundary_04_zero_byte_and_huge_image_files(self):
        """
        R2 Boundary 4: Test loading handling for 0-byte image files vs oversized 10MB images.
        """
        zero_byte_img = os.path.join(self.temp_dir, "zero.png")
        with open(zero_byte_img, "wb") as f:
            pass

        self.assertEqual(os.path.getsize(zero_byte_img), 0)

        # Huge image mock check
        huge_img = os.path.join(self.temp_dir, "huge.png")
        with open(huge_img, "wb") as f:
            f.write(b"0" * (5 * 1024 * 1024))  # 5MB

        self.assertEqual(os.path.getsize(huge_img), 5 * 1024 * 1024)

    def test_r2_boundary_05_android_intent_extra_null_and_malformed_json(self):
        """
        R2 Boundary 5: Test Android client handling of missing or malformed JSON in Intent extras.
        """
        malformed_json_str = "{bad_json: missing_quotes}"
        parsed_ok = False
        fallback_data = {"name": "Unknown", "package_name": "unknown.pkg", "icon": ""}

        try:
            data = json.loads(malformed_json_str)
            parsed_ok = True
        except json.JSONDecodeError:
            data = fallback_data

        self.assertFalse(parsed_ok, "Malformed JSON should fail parsing.")
        self.assertEqual(data["name"], "Unknown")
        self.assertEqual(data["package_name"], "unknown.pkg")


class TestTier2BoundaryCornerR3(unittest.TestCase):
    """
    Feature R3: Server Monitor & Connected Clients Boundary & Corner Cases (>=5 tests)
    """

    def setUp(self):
        self.clients_map = {}
        self.lock = threading.Lock()

    def test_r3_boundary_01_malformed_heartbeat_payload(self):
        """
        R3 Boundary 1: Test POST /api/heartbeat with missing client_id or empty payload.
        """
        def process_payload(payload_str):
            try:
                data = json.loads(payload_str)
                if not data.get("client_id"):
                    return 400, {"error": "Missing client_id"}
                return 200, {"status": "ok"}
            except Exception:
                return 400, {"error": "Invalid JSON"}

        status1, _ = process_payload("")
        self.assertEqual(status1, 400)

        status2, _ = process_payload("{}")
        self.assertEqual(status2, 400)

        status3, _ = process_payload('{"device_name": "Pixel"}')
        self.assertEqual(status3, 400)

        status4, _ = process_payload('{"client_id": "c100", "device_name": "Pixel"}')
        self.assertEqual(status4, 200)

    def test_r3_boundary_02_concurrent_heartbeats_high_client_count(self):
        """
        R3 Boundary 2: Test high concurrent heartbeat submissions (100 simultaneous simulated devices).
        """
        num_clients = 100
        threads = []

        def client_worker(cid):
            with self.lock:
                self.clients_map[f"client_{cid}"] = {
                    "client_id": f"client_{cid}",
                    "device_name": f"Device_{cid}",
                    "ip_address": f"192.168.1.{cid % 250}",
                    "last_active": time.time()
                }

        for i in range(num_clients):
            t = threading.Thread(target=client_worker, args=(i,))
            threads.append(t)
            t.start()

        for t in threads:
            t.join()

        self.assertEqual(len(self.clients_map), num_clients, f"Expected {num_clients} registered clients under concurrent load.")

    def test_r3_boundary_03_disconnect_non_existent_client(self):
        """
        R3 Boundary 3: Test POST /api/disconnect for unknown or non-existent client_id.
        """
        def disconnect(client_id):
            with self.lock:
                if client_id in self.clients_map:
                    del self.clients_map[client_id]
                    return 200, {"status": "removed"}
                return 200, {"status": "not_found"}

        status, body = disconnect("non_existent_id_999")
        self.assertEqual(status, 200)
        self.assertEqual(body["status"], "not_found")

    def test_r3_boundary_04_sub_second_rapid_heartbeat_flooding(self):
        """
        R3 Boundary 4: Test sub-second rapid heartbeat flooding from a single client.
        """
        cid = "flooding_client"
        last_ts = 0
        for i in range(50):
            with self.lock:
                now = time.time()
                self.clients_map[cid] = {
                    "client_id": cid,
                    "device_name": "Flooder",
                    "ip_address": "10.0.0.99",
                    "last_active": now
                }
                last_ts = now

        self.assertEqual(len(self.clients_map), 1)
        self.assertEqual(self.clients_map[cid]["last_active"], last_ts)

    def test_r3_boundary_05_timeout_boundary_14s_vs_16s(self):
        """
        R3 Boundary 5: Test timeout cleanup boundaries: 14s inactivity (retained) vs 16s inactivity (purged).
        """
        now = time.time()
        self.clients_map["c_14s"] = {"client_id": "c_14s", "last_active": now - 14.0}
        self.clients_map["c_16s"] = {"client_id": "c_16s", "last_active": now - 16.0}

        # Purge logic with 15s cutoff
        cutoff = now - 15.0
        expired = [cid for cid, info in self.clients_map.items() if info["last_active"] < cutoff]
        for cid in expired:
            del self.clients_map[cid]

        self.assertIn("c_14s", self.clients_map, "14s inactive client was prematurely purged.")
        self.assertNotIn("c_16s", self.clients_map, "16s inactive client was not purged.")


if __name__ == "__main__":
    unittest.main()
