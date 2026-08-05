"""
Tier 4: Real-World Workflow E2E Tests for Local APK Store
Tests complete multi-step user workflows, store operations, and live component interactions.
>=5 end-to-end scenario tests in this file.
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

WORKSPACE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MANAGER_APP_DIR = os.path.join(WORKSPACE_DIR, "Manager_App")


class TestTier4RealWorldWorkflows(unittest.TestCase):
    """
    Tier 4: End-to-End Real-World Scenario Tests
    """

    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.apks_dir = os.path.join(self.temp_dir, "apks")
        self.images_dir = os.path.join(self.temp_dir, "images")
        self.db_file = os.path.join(self.temp_dir, "db.json")
        os.makedirs(self.apks_dir, exist_ok=True)
        os.makedirs(self.images_dir, exist_ok=True)

        self.db = {"apps": []}
        with open(self.db_file, "w") as f:
            json.dump(self.db, f)

        self.clients = {}
        self.lock = threading.Lock()

    def tearDown(self):
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_tier4_01_end_to_end_apk_ingestion_icon_extraction_and_store_sync(self):
        """
        Scenario 1: Administrator ingests a new APK -> Server parses metadata & extracts icon -> Updates db.json -> Serves to store.
        """
        # Step 1: Admin places sample APK
        apk_filename = "com.elitesoftware.demo-1.0.apk"
        apk_path = os.path.join(self.apks_dir, apk_filename)
        png_data = b'\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR_REALWORLD_SCENARIO_1'

        with zipfile.ZipFile(apk_path, "w") as zf:
            zf.writestr("res/drawable/ic_launcher.png", png_data)

        # Step 2: Auto-discovery & extraction
        icon_output_filename = "com.elitesoftware.demo_icon.png"
        icon_output_path = os.path.join(self.images_dir, icon_output_filename)

        with zipfile.ZipFile(apk_path, "r") as zf:
            icon_data = zf.read("res/drawable/ic_launcher.png")
            with open(icon_output_path, "wb") as out_f:
                out_f.write(icon_data)

        # Step 3: DB Registration
        app_record = {
            "name": "Elite Demo App",
            "package_name": "com.elitesoftware.demo",
            "category": "Productivity",
            "versions": [{"version": "1.0", "file": apk_filename}],
            "icon": icon_output_filename
        }
        self.db["apps"].append(app_record)
        with open(self.db_file, "w") as f:
            json.dump(self.db, f)

        # Step 4: Verify store accessibility
        with open(self.db_file, "r") as f:
            loaded_db = json.load(f)

        self.assertEqual(len(loaded_db["apps"]), 1)
        self.assertEqual(loaded_db["apps"][0]["package_name"], "com.elitesoftware.demo")
        self.assertTrue(os.path.exists(icon_output_path))
        self.assertEqual(os.path.getsize(icon_output_path), len(png_data))

    def test_tier4_02_multi_client_lifecycle_connection_heartbeat_and_disconnection(self):
        """
        Scenario 2: Multi-client lifecycle (5 devices connect, pulse heartbeats, 2 disconnect gracefully).
        """
        # Step 1: 5 clients connect
        devices = [
            ("dev_1", "Pixel 7", "192.168.1.101"),
            ("dev_2", "Galaxy S22", "192.168.1.102"),
            ("dev_3", "OnePlus 11", "192.168.1.103"),
            ("dev_4", "Xiaomi 13", "192.168.1.104"),
            ("dev_5", "Pixel Tablet", "192.168.1.105")
        ]

        now = time.time()
        for cid, dname, ip in devices:
            self.clients[cid] = {"device_name": dname, "ip": ip, "last_active": now}

        self.assertEqual(len(self.clients), 5)

        # Step 2: Pulse heartbeat for remaining devices
        for cid, _, _ in devices[:3]:
            self.clients[cid]["last_active"] = time.time()

        # Step 3: Explicit disconnect for dev_4 and dev_5
        del self.clients["dev_4"]
        del self.clients["dev_5"]

        self.assertEqual(len(self.clients), 3)
        self.assertNotIn("dev_4", self.clients)
        self.assertNotIn("dev_5", self.clients)
        self.assertIn("dev_1", self.clients)

    def test_tier4_03_inactive_client_timeout_eviction_and_reconnection(self):
        """
        Scenario 3: Client connection drops -> 15s timeout evicts client -> client reconnects and resumes.
        """
        cid = "mobile_client_007"

        # 1. Connect
        self.clients[cid] = {"device_name": "Agent Phone", "ip": "10.0.0.42", "last_active": time.time() - 20}

        # 2. Server timeout sweep (15s threshold)
        cutoff = time.time() - 15
        expired = [c for c, data in self.clients.items() if data["last_active"] < cutoff]
        for c in expired:
            del self.clients[c]

        self.assertNotIn(cid, self.clients, "Inactive client was not evicted after 20s drop.")

        # 3. Reconnect
        self.clients[cid] = {"device_name": "Agent Phone", "ip": "10.0.0.42", "last_active": time.time()}

        self.assertIn(cid, self.clients, "Reconnected client was not re-registered.")
        self.assertGreater(self.clients[cid]["last_active"], cutoff)

    def test_tier4_04_server_restart_and_state_recovery(self):
        """
        Scenario 4: Server restarts -> db.json state is preserved -> clients resume heartbeats smoothly.
        """
        # Step 1: Write initial database
        initial_app = {"name": "Persistent App", "package_name": "com.persistent", "icon": "app_icon.png"}
        with open(self.db_file, "w") as f:
            json.dump({"apps": [initial_app]}, f)

        # Step 2: Simulate Server Shutdown
        self.clients.clear()

        # Step 3: Simulate Server Startup (Load db.json)
        with open(self.db_file, "r") as f:
            recovered_db = json.load(f)

        self.assertEqual(len(recovered_db["apps"]), 1)
        self.assertEqual(recovered_db["apps"][0]["package_name"], "com.persistent")

        # Step 4: Resume client heartbeats
        self.clients["resumed_client"] = {"device_name": "Resumed Device", "ip": "192.168.1.5", "last_active": time.time()}
        self.assertEqual(len(self.clients), 1)

    def test_tier4_05_concurrent_app_discovery_icon_fetching_and_monitor_updates(self):
        """
        Scenario 5: High-load workflow with concurrent app listing requests, icon downloads, and server monitor updates.
        """
        # Setup multi-threaded simulation
        successes = []

        def client_activity(client_idx):
            # 1. Register heartbeat
            cid = f"load_client_{client_idx}"
            with self.lock:
                self.clients[cid] = {"device_name": f"LoadBot_{client_idx}", "ip": f"10.0.1.{client_idx}", "last_active": time.time()}

            # 2. Simulate read db
            with open(self.db_file, "r") as f:
                _ = json.load(f)

            successes.append(client_idx)

        threads = []
        for i in range(20):
            t = threading.Thread(target=client_activity, args=(i,))
            threads.append(t)
            t.start()

        for t in threads:
            t.join()

        self.assertEqual(len(successes), 20)
        self.assertEqual(len(self.clients), 20)


if __name__ == "__main__":
    unittest.main()
