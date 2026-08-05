## 2026-08-04T21:40:24-04:00
You are the Server & API Stress Test Challenger for Milestone 4 Tier 5 Hardening.
Working directory for metadata: C:\Users\Administrator\Desktop\Local_APK_Store\.agents\challenger_m4_stress1

Scope & Task:
1. Read the following scope documents:
   - `C:\Users\Administrator\Desktop\Local_APK_Store\ORIGINAL_REQUEST.md`
   - `C:\Users\Administrator\Desktop\Local_APK_Store\PROJECT.md`
   - `C:\Users\Administrator\Desktop\Local_APK_Store\TEST_READY.md`
2. Conduct empirical adversarial stress-testing on the server HTTP endpoints & session management (`Manager_App/main.cpp`):
   - Test 1: Rapid HTTP heartbeats (`POST /api/heartbeat`) from 50+ concurrent simulated client threads / connections.
   - Test 2: Rapid disconnect requests (`POST /api/disconnect`) interspersed with concurrent active heartbeats.
   - Test 3: Malformed requests (invalid JSON payloads, missing fields, non-existent `/images/` requests, oversized headers).
   - Test 4: Concurrent client list queries while the background 15-second client timeout cleanup thread runs.
3. Verify the server does not crash, leak memory, dead-lock, or corrupt `g_connectedClients` session state under load.
4. Write test generator/script in tests or temporary location if needed, run stress tests, and verify results.
5. Record progress in `C:\Users\Administrator\Desktop\Local_APK_Store\.agents\challenger_m4_stress1\progress.md`.
6. Write a detailed handoff report in `C:\Users\Administrator\Desktop\Local_APK_Store\.agents\challenger_m4_stress1\handoff.md` with test scenarios, evidence, and Verdict: APPROVE or REJECT.
7. Send a message to parent sub-orchestrator upon completion.
