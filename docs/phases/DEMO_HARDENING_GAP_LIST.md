# DEMO HARDENING GAP LIST
**Project:** SIH 26059

| Current Issue | Severity | Impact on Demo | Proposed Fix | Verification |
| :--- | :--- | :--- | :--- | :--- |
| **PostgreSQL Unavailable** | High (Architectural) | Demo lacks live DB inserts | Isolate `DEMO_MODE` to synthetic arrays | Route API fallback yields 201 Created |
| **Browser UI Automation Unavailable** | Medium (Test Coverage) | E2E playwright tests fail in CI | Rely on manual operator script for UI | React rendering of FastAPI JSON verified statically |
| **Missing Risk Fallback** | Critical (Safety) | UI might draw a 0-risk route on failure | Enforce 400 Error on `Safest` objective | Test script yields HTTP 400 |
| **Scattered Demo Checks** | Low (Tech Debt) | Complex maintenance | RouteOrchestrator centralizes injection | Code review of `route_orchestrator.py` |
