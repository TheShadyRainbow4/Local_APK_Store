## 2026-08-04T20:40:50Z

OBJECTIVE:
Build a comprehensive, opaque-box, requirement-driven E2E test suite for Local APK Store covering features R1 (UI Rendering), R2 (APK Icon Extraction & Display), and R3 (Server Monitor & Connected Clients) across Tiers 1-4.

REQUIREMENTS:
1. Directory Structure:
   Create test files inside `C:\Users\Administrator\Desktop\Local_APK_Store\tests`:
   - `tests/test_tier1_feature_coverage.py` (or ps1/py): >=5 tests per feature (R1: 5+, R2: 5+, R3: 5+ -> total >=15 tests)
   - `tests/test_tier2_boundary_corner.py`: >=5 tests per feature (R1: 5+, R2: 5+, R3: 5+ -> total >=15 tests)
   - `tests/test_tier3_cross_feature.py`: >=4 tests for pairwise feature interactions (R1+R2, R2+R3, R1+R3, R1+R2+R3)
   - `tests/test_tier4_real_world.py`: >=5 realistic end-to-end workflow scenarios
   - `tests/run_e2e_tests.ps1` (and `tests/run_e2e_tests.py`): Test runner that discovers and executes all Tier 1-4 tests, reports test counts and pass/fail status per tier, and exits with code 0.

2. Test Coverage Breakdown:
   - Feature R1 (Win32 UI Rendering & Aesthetic Compliance):
     * Test OS visual styles / background brush compliance in Win32 C++ source code & window styling flags
     * Test control positioning and non-overlapping geometry at 850x600 size
     * Test SysListView32 control creation and dynamic resize handling (WM_SIZE)
     * Test Segoe UI font initialization, Menubar, Toolbar, About/Help/Settings dialog classes/resources, Tooltips, Chin panel, 3D inset frame
     * Test log file creation path (`%SystemDrive%\EliteSoftware\Logs\Manager_App.log`) and log viewer link launch
   - Feature R2 (APK Icon Extraction & Display):
     * Test automatic extraction of valid PNG internal icon from standard APK ZIP archive
     * Test extraction fallback for adaptive XML icons / missing icons / default fallback PNG
     * Test HTTP endpoint `GET /images/<icon>` returns correct image bytes and headers
     * Test Win32 HIMAGELIST image loading logic and SysListView32 icon assignment
     * Test Android client Intent extra alignment and HTTP icon URL loading logic
   - Feature R3 (Server Monitor & Connected Clients):
     * Test `POST /api/heartbeat` with client_id and device_name registers client IP and device name
     * Test repeat heartbeat updates last_active timestamp without creating duplicate client entries
     * Test `POST /api/disconnect` immediately removes client from connected clients map
     * Test 15-second inactive client automatic timeout cleanup thread logic
     * Test Server Monitor SysListView32 UI updating client list (IP Address, Device Name, Last Active) on WM_TIMER tick

3. Documentation:
   - Create `C:\Users\Administrator\Desktop\Local_APK_Store\TEST_INFRA.md` documenting test philosophy, feature inventory matrix, architecture, runner invocation, and coverage thresholds.
   - Run the test suite runner script to verify execution.
   - Create `C:\Users\Administrator\Desktop\Local_APK_Store\TEST_READY.md` containing the E2E test suite status, runner command (`powershell -ExecutionPolicy Bypass -File tests\run_e2e_tests.ps1`), coverage table breakdown across Tiers 1-4, and feature checklist.
