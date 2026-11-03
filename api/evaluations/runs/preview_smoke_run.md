# PortPilot Preview Deployment Verification Report

- **Execution Timestamp:** `2026-11-03T12:15:37.520033+00:00`
- **API Endpoint:** `http://127.0.0.1:18000`
- **Web Endpoint:** `N/A`
- **Overall Outcome:** **`PASS`**
- **Score:** `9/12 passed (3 skipped, 0 failed)`

## Check Details

| Check Name | Category | Status | Latency (ms) | Details |
| --- | --- | :---: | :---: | --- |
| API Liveness Check (GET /health) | Liveness & Readiness | ✅ PASS | 68.8 | API responded status: ok |
| Database Readiness Check (GET /ready) | Liveness & Readiness | ✅ PASS | 32.0 | Database connectivity confirmed status: ready |
| Catalogue Data Integrity & Filtering (GET /devices) | Catalogue Integrity | ✅ PASS | 41.1 | Verified 15 laptops and 13 accessories. Zero leaks detected. |
| Device Details & Evidence (GET /devices/{category}/{id}) | Catalogue Integrity | ✅ PASS | 33.7 | Fetched laptop 'lenovo-ideapad-slim-3-14irh10r' and accessory 'anker-555-usb-c-hub' details with valid schema structure. |
| Deterministic Compatibility Evaluation (POST /checks) | Compatibility Rules | ✅ PASS | 34.8 | Evaluated lenovo-ideapad-slim-3-14irh10r + anker-555-usb-c-hub -> 'insufficient_data' (engine: 0.3.0) |
| Simultaneous Multi-Display Evaluation (POST /checks) | Compatibility Rules | ✅ PASS | 11.1 | Dual-display check evaluated successfully with verdict: 'incompatible' and explicit limits. |
| Share Link Query Parameter Contract | Shared Links | ✅ PASS | 0.1 | Share URL parameters '?laptop=lenovo-ideapad-slim-3-14irh10r&accessory=anker-555-usb-c-hub' conform to Next.js query parameter restoration spec. |
| Result Report Ingestion (POST /result-reports) | Reporting & Ingestion | ✅ PASS | 47.9 | Successfully ingested low-data result report (report id: report-aa4bcc7cb99845998150fb02c7617f5c). |
| AI Setup Parser Endpoint (POST /setup-requests/parse) | Setup Parser | ⚠️ SKIP | 28.7 | External provider offline (Provider unavailable in preview (HTTP 503): {'detail': {'code': 'setup_parser_unavailable', 'message': 'Setup parsing is not configured. Use the manual setup fields.'}}). Deterministic checks remain unblocked. |
| Observability & Duration Distributions (GET /metrics) | Observability & Metrics | ✅ PASS | 26.8 | Exposed Prometheus request counters and duration histograms without credential leaks. |
| Frontend Shell Rendering (GET /) | Frontend Smoke | ⚠️ SKIP | 0.0 | No --web-url provided |
| Frontend Coverage Page (GET /coverage) | Frontend Smoke | ⚠️ SKIP | 0.0 | No --web-url provided |
