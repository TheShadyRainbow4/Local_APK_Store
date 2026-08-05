# Test Infrastructure & Strategy Documentation — Local APK Store

## 1. Test Philosophy & Design Principles
The End-to-End (E2E) testing framework for **Local APK Store** is designed around opaque-box, contract-driven, requirement-verified validation.

- **Non-Invasive Verification**: Tests validate observable APIs, network protocols, data structures, and file system states without relying on internal function mocks or fake test assertions.
- **Independence & Isolation**: Every test creates its own temporary environment (isolated ports, isolated temporary directories, synthetic APK archives, isolated mock client connections) and cleans up resources immediately after execution.
- **Strict Verification Rules**: All test cases use authoritative verification derived directly from `ORIGINAL_REQUEST.md` and `PROJECT.md`. No hardcoded dummy passing tests.
- **Multi-Tiered Coverage Layout**: Organizes test suites into Tiers 1-4, moving from individual feature requirement validation up to multi-client end-to-end real-world workflows.

---

## 2. Feature Inventory & Mapping Matrix

| Feature ID | Feature Name | Target Scope / Requirements | Test File |
|------------|--------------|-----------------------------|-----------|
| **R1** | Win32 UI Rendering & Aesthetic Compliance | R1.1 Custom Backfill Brush Removal<br>R1.2 Non-Overlapping Control Geometry<br>R1.3 SysListView32 Conversion & Dynamic WM_SIZE<br>R1.4 Segoe UI Font, Dialogs, Tooltips, Chin Panel, 3D Inset<br>R1.5 Log File Creation & Logger Link | `tests/test_tier1_feature_coverage.py`<br>`tests/test_tier2_boundary_corner.py`<br>`tests/test_tier3_cross_feature.py`<br>`tests/test_tier4_real_world.py` |
| **R2** | APK Icon Extraction & Display | R2.1 Server ZIP Internal PNG Extraction<br>R2.2 Extraction Fallback (Adaptive XML / Default Image)<br>R2.3 HTTP Endpoint `GET /images/<icon>` Serving<br>R2.4 Win32 HIMAGELIST Image Loading & ListView Binding<br>R2.5 Android Client Intent Extra Alignment & HTTP Icon URL | `tests/test_tier1_feature_coverage.py`<br>`tests/test_tier2_boundary_corner.py`<br>`tests/test_tier3_cross_feature.py`<br>`tests/test_tier4_real_world.py` |
| **R3** | Server Monitor & Connected Clients | R3.1 Client Heartbeat Registration (`POST /api/heartbeat`)<br>R3.2 Repeat Heartbeat Timestamp Updates (No Duplicates)<br>R3.3 Disconnect Protocol (`POST /api/disconnect`)<br>R3.4 15-Second Inactive Client Timeout Purge Thread<br>R3.5 Server Monitor SysListView32 UI Timer Refresh | `tests/test_tier1_feature_coverage.py`<br>`tests/test_tier2_boundary_corner.py`<br>`tests/test_tier3_cross_feature.py`<br>`tests/test_tier4_real_world.py` |

---

## 3. Architecture & Test Directory Structure

```
C:\Users\Administrator\Desktop\Local_APK_Store\
├── tests/
│   ├── __init__.py                            # Package initialization
│   ├── test_tier1_feature_coverage.py          # Tier 1: Feature Coverage (15 tests: R1=5, R2=5, R3=5)
│   ├── test_tier2_boundary_corner.py           # Tier 2: Boundary & Corner Cases (15 tests: R1=5, R2=5, R3=5)
│   ├── test_tier3_cross_feature.py             # Tier 3: Pairwise & Multi-Feature Interactions (4 tests)
│   ├── test_tier4_real_world.py               # Tier 4: Real-World Workflow Scenarios (5 tests)
│   ├── run_e2e_tests.py                       # Native Python Test Runner & Reporter
│   └── run_e2e_tests.ps1                      # PowerShell Test Execution Wrapper
├── TEST_INFRA.md                              # Test Strategy & Infrastructure Manual
└── TEST_READY.md                              # Suite Status, Execution Command & Verification Metrics
```

---

## 4. Runner Invocation & Commands

### PowerShell Invocation (Standard Windows Execution)
```powershell
powershell -ExecutionPolicy Bypass -File tests\run_e2e_tests.ps1
```

### Python Direct Invocation
```cmd
python tests/run_e2e_tests.py
```

### Individual Tier Execution
```cmd
python -m unittest tests/test_tier1_feature_coverage.py
python -m unittest tests/test_tier2_boundary_corner.py
python -m unittest tests/test_tier3_cross_feature.py
python -m unittest tests/test_tier4_real_world.py
```

---

## 5. Coverage Thresholds & Quality Gates

- **Total Test Count Minimum**: 39 Tests
  * Tier 1 (Feature Coverage): >= 15 tests (5 R1, 5 R2, 5 R3)
  * Tier 2 (Boundary & Corner Cases): >= 15 tests (5 R1, 5 R2, 5 R3)
  * Tier 3 (Cross-Feature Pairwise Interactions): >= 4 tests (R1+R2, R2+R3, R1+R3, R1+R2+R3)
  * Tier 4 (Real-World Scenarios): >= 5 tests
- **Pass Threshold**: 100% Pass Rate required (0 Failures, 0 Errors)
- **Execution Code Gate**: Runner exits with code `0` on 100% pass, `1` on any failure.
