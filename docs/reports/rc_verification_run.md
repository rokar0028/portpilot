# PortPilot Preview Deployment Verification Report

- **Associated Release Candidate Record:** [`release-candidate-v2.0.0-rc1.md`](release-candidate-v2.0.0-rc1.md)
- **Raw JSON Artifact:** [`rc_verification_run.json`](rc_verification_run.json)
- **Execution Timestamp:** `2026-11-03T13:24:49.858763+00:00`
- **API Endpoint:** `http://127.0.0.1:8001`
- **Web Endpoint:** `http://127.0.0.1:3000`
- **Overall Outcome:** **`PASS`**
- **Score:** `11/12 passed (1 skipped, 0 failed)`

## Check Details

| Check Name | Category | Status | Latency (ms) | Details |
| --- | --- | :---: | :---: | --- |
| API Liveness Check (GET /health) | Liveness & Readiness | ✅ PASS | 28.7 | API responded status: ok |
| Database Readiness Check (GET /ready) | Liveness & Readiness | ✅ PASS | 25.5 | Database connectivity confirmed status: ready |
| Catalogue Data Integrity & Filtering (GET /devices) | Catalogue Integrity | ✅ PASS | 64.1 | Verified 15 laptops and 13 accessories. Zero leaks detected. |
| Device Details & Evidence (GET /devices/{category}/{id}) | Catalogue Integrity | ✅ PASS | 27.1 | Fetched laptop 'lenovo-ideapad-slim-3-14irh10r' and accessory 'anker-555-usb-c-hub' details with valid schema structure. |
| Deterministic Compatibility Evaluation (POST /checks) | Compatibility Rules | ✅ PASS | 36.5 | Evaluated lenovo-ideapad-slim-3-14irh10r + anker-555-usb-c-hub -> 'insufficient_data' (engine: 0.3.0) |
| Simultaneous Multi-Display Evaluation (POST /checks) | Compatibility Rules | ✅ PASS | 15.0 | Dual-display check evaluated successfully with verdict: 'incompatible' and explicit limits. |
| Share Link Query Parameter Contract | Shared Links | ✅ PASS | 0.1 | Share URL parameters '?laptop=lenovo-ideapad-slim-3-14irh10r&accessory=anker-555-usb-c-hub' conform to Next.js query parameter restoration spec. |
| Result Report Ingestion (POST /result-reports) | Reporting & Ingestion | ✅ PASS | 27.1 | Successfully ingested low-data result report (report id: report-c87dd35fc41749cbab10dd34eaed73e4). |
| AI Setup Parser Endpoint (POST /setup-requests/parse) | Setup Parser | ⚠️ SKIP | 26.0 | External provider offline (Provider unavailable in preview (HTTP 503): {'detail': {'code': 'setup_parser_unavailable', 'message': 'Setup parsing is not configured. Use the manual setup fields.'}}). Deterministic checks remain unblocked. |
| Observability & Duration Distributions (GET /metrics) | Observability & Metrics | ✅ PASS | 28.4 | Exposed Prometheus request counters and duration histograms without credential leaks. |
| Frontend Shell Rendering (GET /) | Frontend Smoke | ✅ PASS | 32.7 | Web service returned valid HTML application shell. |
| Frontend Coverage Page (GET /coverage) | Frontend Smoke | ✅ PASS | 45.9 | Coverage page rendered successfully with live catalogue references. |
