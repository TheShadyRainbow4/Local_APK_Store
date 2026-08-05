"""
Local APK Store - E2E Test Suite Runner
Discovers and executes all Tier 1-4 test modules.
Outputs test count breakdown and pass/fail status per tier.
Exits code 0 on full suite completion/pass.
"""

import unittest
import sys
import os
import time

# Ensure project root is on sys.path
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

def run_suite():
    print("=" * 80)
    print("       LOCAL APK STORE - OPAQUE-BOX E2E TEST SUITE RUNNER       ")
    print("=" * 80)
    print(f"Project Directory: {PROJECT_ROOT}\n")

    loader = unittest.TestLoader()

    tiers = [
        ("Tier 1: Feature Coverage (R1, R2, R3)", "tests.test_tier1_feature_coverage"),
        ("Tier 2: Boundary & Corner Cases", "tests.test_tier2_boundary_corner"),
        ("Tier 3: Pairwise Cross-Feature Interactions", "tests.test_tier3_cross_feature"),
        ("Tier 4: Real-World Workflow Scenarios", "tests.test_tier4_real_world"),
    ]

    total_tests = 0
    total_passed = 0
    total_failed = 0

    results_summary = []
    start_time = time.time()

    for tier_name, module_path in tiers:
        print(f"--- Running {tier_name} [{module_path}] ---")
        try:
            suite = loader.loadTestsFromName(module_path)
        except Exception as e:
            print(f"ERROR: Failed to load module {module_path}: {e}")
            sys.exit(1)

        runner = unittest.TextTestRunner(verbosity=2)
        result = runner.run(suite)

        count = result.testsRun
        failures = len(result.failures) + len(result.errors)
        passed = count - failures

        total_tests += count
        total_passed += passed
        total_failed += failures

        status = "PASSED" if failures == 0 else "FAILED"
        results_summary.append({
            "tier": tier_name,
            "count": count,
            "passed": passed,
            "failed": failures,
            "status": status
        })
        print(f"-> {tier_name}: {passed}/{count} Passed [{status}]\n")

    elapsed = time.time() - start_time

    print("=" * 80)
    print("                    E2E TEST SUITE SUMMARY                    ")
    print("=" * 80)
    print(f"{'Tier':<45} | {'Passed':<8} | {'Failed':<8} | {'Status':<8}")
    print("-" * 80)
    for r in results_summary:
        print(f"{r['tier']:<45} | {r['passed']:<8} | {r['failed']:<8} | {r['status']:<8}")
    print("-" * 80)
    print(f"Total Execution Time: {elapsed:.2f} seconds")
    print(f"Total Tests Executed: {total_tests}")
    print(f"Total Passed:         {total_passed}")
    print(f"Total Failed:         {total_failed}")
    print("=" * 80)

    if total_failed == 0:
        print(">>> ALL TIERS PASSED SUCCESSFULLY! Exit Code 0 <<<")
        sys.exit(0)
    else:
        print(f">>> {total_failed} TESTS FAILED! Exit Code 1 <<<")
        sys.exit(1)

if __name__ == "__main__":
    run_suite()
