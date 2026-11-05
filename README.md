# PortPilot

PortPilot checks whether a laptop and accessory support a requested setup. Verdicts come from deterministic rules over documented specifications; missing required facts produce **Insufficient data**.

## Current vertical slice

- Laptop: Lenovo IdeaPad Slim 3 14IRH10R
- Accessory: Anker Nano Hub (7-in-1, A83D2)
- Setup: one 1080p external display plus laptop charging

The manufacturer sources confirm USB-C DisplayPort 1.2 and USB Power Delivery (45–65 W) on the laptop, and HDMI plus 85 W pass-through on the hub, confirming compatibility for this setup. The API catalogue is database-backed and currently publishes 19 laptops and 17 accessories; three accessories are held for model-identity and evidence review. Missing required specifications or unverified claims produce **Insufficient data** rather than guessing.

The checker lets you select a laptop, accessory, display mode, and charging requirement. After a check, **Share this result** copies a URL containing an immutable result snapshot (`?snapshot=<id>`) that preserves the verified verdict, summary, limitations, and citations, while also providing a fallback rerun mode when opened. Quick-filter search boxes let you quickly narrow down laptops and accessories by model name or code. A quick-reference glossary on the page explains USB-C, DisplayPort Alt Mode, USB Power Delivery, USB4, and Thunderbolt. Users can report a questionable result with its selected models, requested setup, verdict, rules version, and an optional note. Reports omit contact details and device/browser identifiers.

The [coverage and limitations page](/coverage) reports live verified catalogue counts and explains how PortPilot handles manufacturer evidence and unknown specifications.

## Implementation plans

- [PortPilot implementation plan](docs/portpilot-implementation-plan.md) — product scope and original implementation direction.
- [V2 implementation plan](docs/v2-implementation-plan.md) — follow-on workstreams and V2 release acceptance criteria.
- [Workstream 0 implementation plan](docs/v2-workstream-0-implementation-plan.md) — V2 baseline inventory, capability registry, and implementation control.
- [Workstream 1 implementation plan](docs/v2-workstream-1-implementation-plan.md) — device identity, duplicate review, and evidence threshold.
- [Workstream 2 implementation plan](docs/v2-workstream-2-implementation-plan.md) — evidence conflicts, rechecks, and correction history.
- [Workstream 3 implementation plan](docs/v2-workstream-3-implementation-plan.md) — capability registry integration and consistency checks.
- [Workstream 4 implementation plan](docs/v2-workstream-4-implementation-plan.md) — simultaneous display configurations, modes, and topology.
- [Workstream 5 implementation plan](docs/v2-workstream-5-implementation-plan.md) — model-finding help, mobile readability, low-data reporting, and sharing behavior.
- [Workstream 6 implementation plan](docs/v2-workstream-6-implementation-plan.md) — screen-reader manual audit plan and accessibility checks.
- [Workstream 7 implementation plan](docs/v2-workstream-7-implementation-plan.md) — latency target, duration distributions, and migration recovery.
- [Workstream 8 implementation plan](docs/v2-workstream-8-implementation-plan.md) — live-provider parser evaluation, versioned benchmarks, and accuracy reporting.
- [Workstream 9 implementation plan](docs/v2-workstream-9-implementation-plan.md) — preview deployment verification and release checklist.
- [Workstream 10 implementation plan](docs/v2-workstream-10-implementation-plan.md) — contributor guide, playbooks, and hand-off.
- [Workstream 11 implementation plan](docs/v2-workstream-11-implementation-plan.md) — hardware protocol fidelity, physical bus constraints, and catalogue depth.
- [Capability registry contributor guide](docs/capability-registry.md) — how to add a capability across catalogue, evidence, publication, and rules.
- [V2 migration and rollout notes](docs/v2-migration-rollout.md) — revision history, data impact, rollout, and rollback guidance.
- [Database operations and migration recovery runbook](docs/database-operations-runbook.md) — tested backup, restore, and failure recovery instructions for SQLite, Compose PostgreSQL, and hosted preview.
- [Source-review playbook](docs/source-review-playbook.md) — review, recheck, and correction process.
- [Catalogue identity and evidence standard](docs/catalogue-identity-and-evidence.md) — contributor guidance for exact device identity and publication.
- [Phase 0 implementation plan](docs/implementation%20plan.md) — initial scope and vertical-slice decisions.

## Prerequisites

- Python 3.12 or later
- Node.js 20 or later and npm
- Docker Desktop with Compose (optional, for the combined workflow)

## Run locally

### API

```powershell
cd api
Copy-Item .env.example .env
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements-dev.txt
alembic upgrade head
python -m app.seed
uvicorn app.main:app --reload --port 8001
```

The direct workflow uses a local SQLite file by default. The API is at http://localhost:8001, its health endpoint is http://localhost:8001/health, the evidence-backed catalogue is at http://localhost:8001/devices, and interactive API docs are at http://localhost:8001/docs. PortPilot uses 8001 locally to avoid clashes with other common services on port 8000.

### Catalogue evidence

Each source record identifies the capability it supports, with a manufacturer URL, short factual excerpt, and checked date. Evidence review status is `draft`, `verified`, or `needs_review`. A capability that is not documented stays null; it is not treated as unsupported.

### Catalogue administration and seeding

Catalogue writes use the protected API. Set a long random `ADMIN_API_TOKEN` in `api/.env` for local API development. For Docker Compose, set the same variable in the shell before starting Compose; if it is absent, catalogue administration stays disabled. For example in PowerShell:

```powershell
$env:ADMIN_API_TOKEN = python -c "import secrets; print(secrets.token_urlsafe(32))"
docker compose up --build
```

In `/docs`, authorize with the value as a bearer token, then use `GET`, `POST`, and `PUT` under `/admin/laptops` and `/admin/accessories`. New records default to `draft`, and drafts remain editable while incomplete. To publish, set `review_status` to `verified`, provide the category's required specifications, and attach verified manufacturer evidence for the model code and each populated capability. Updates replace the evidence list for that device. Only verified records appear in the public catalogue and can be used in checks. Do not commit API tokens or place them in request examples.

#### Declarative JSON Seed Ingestion

You can also seed or update device records declaratively from specification JSON files:

```powershell
# Dry-run validation against Pydantic schema and capability registry
python scripts/seed_from_spec.py specs/examples/plugable-ud-6950z.json --dry-run

# Ingest into local SQLite or configured DATABASE_URL
python scripts/seed_from_spec.py specs/examples/plugable-ud-6950z.json

# Or ingest via authenticated API endpoint
python scripts/seed_from_spec.py specs/examples/plugable-ud-6950z.json --api-url http://127.0.0.1:8001 --token $env:ADMIN_API_TOKEN
```

#### Evidence Staleness Audits

To audit manufacturer citations and ensure evidence remains fresh:

```powershell
# Audit local database for verified evidence older than 180 days
python scripts/check_evidence_staleness.py --max-age-days 180

# Or audit a running API deployment
python scripts/check_evidence_staleness.py --api-url http://127.0.0.1:8001 --token $env:ADMIN_API_TOKEN
```

### Frontend

In another terminal:

```powershell
cd web
Copy-Item .env.example .env.local
npm ci
npm run dev
```

Open http://localhost:3000. Set `NEXT_PUBLIC_API_URL` in `web/.env.local` to point the browser to a different API origin.

## Run both with Docker Compose

From the project root, Docker Compose starts PostgreSQL, applies migrations, seeds the catalogue, then starts the API and frontend:

```powershell
docker compose up --build
```

Open http://localhost:3000. Compose waits for PostgreSQL health before starting the API and waits for the API health check before starting the frontend. PostgreSQL data is stored in a named volume. Stop the services with `Ctrl+C`, then run `docker compose down`.

## Free Render preview configuration

[`render.yaml`](render.yaml) defines the API, Next.js frontend, and PostgreSQL database as free Render resources in Singapore. It is configuration only; PortPilot is not deployed yet. Render Free web services sleep after 15 minutes without traffic, and Free Postgres expires after 30 days with no backups. Use this only as a temporary preview and do not store user data there. The API runs migrations and seeds the catalogue when it starts. Deployment still requires this private GitHub repository to be connected to Render. See [Preview and release playbook](docs/preview-and-release-playbook.md) for pre-release verification, smoke testing, and rollback procedures.

## Quality commands

Run these from the indicated directory:

```powershell
# api/
ruff check app migrations tests scripts
ruff format --check app migrations tests scripts
python -m pytest tests -q
python scripts/evaluate_setup_parser.py --mock
python scripts/verify_preview_deployment.py --api-url http://127.0.0.1:8001
python scripts/check_evidence_staleness.py --warn-only

# web/
npm run lint
npm run format:check
npm run build
```

## End-to-end tests

Browser tests use a disposable PostgreSQL database named `portpilot_e2e`, synthetic fixture records, and the production standalone frontend. They refuse to seed unless `PORTPILOT_E2E=1` and the database URL points to the local test database. They do not use Render or any shared deployment.

Start the isolated database from the repository root:

```powershell
docker compose -p portpilot-e2e -f docker-compose.e2e.yml up -d --wait
```

In an API terminal, set the test environment and prepare the database:

```powershell
cd api
$env:PORTPILOT_E2E = "1"
$dbPort = (docker compose -p portpilot-e2e -f ../docker-compose.e2e.yml port e2e-db 5432).Split(":")[-1]
$env:DATABASE_URL = "postgresql+psycopg://portpilot_e2e:portpilot_e2e@127.0.0.1:$dbPort/portpilot_e2e"
$env:FRONTEND_ORIGIN = "http://127.0.0.1:13000"
$env:ADMIN_API_TOKEN = "local-e2e-only-token"
alembic upgrade head
python -m app.seed
python -m e2e_fixtures
$env:PORTPILOT_POSTGRES_TESTS = "1"
python -m pytest tests/test_postgres_api.py -q
```

In a second terminal, use the same `NEXT_PUBLIC_API_URL` and run the built browser suite:

```powershell
cd web
$env:NEXT_PUBLIC_API_URL = "http://127.0.0.1:18000"
npm run build:e2e
npm run e2e:install
npm run e2e
```

The Playwright config starts the API and standalone frontend against that database. When finished, stop the disposable database from the repository root with `docker compose -p portpilot-e2e -f docker-compose.e2e.yml down`.

CI runs these checks on pushes and pull requests. Apply database migrations with `alembic upgrade head`, and seed the curated devices with `python -m app.seed`. Format code with `ruff format app migrations` and `npm run format`.

The scheduled **Release confidence** workflow runs the same browser journeys in Chromium, Firefox, and WebKit, repeats PostgreSQL policy/API checks, and records a low-rate k6 baseline plus database readiness recovery against job-local disposable databases. Run it manually with a candidate commit SHA before a release. It does not target Render or any shared deployment; deployment smoke requires a separately provisioned isolated preview.

## Architecture and design choices

```mermaid
flowchart LR
  User[User] --> Web[Next.js checker]
  Web -->|catalogue and checks| API[FastAPI]
  API --> Rules[Deterministic rules]
  API --> DB[(PostgreSQL)]
  DB --> Evidence[Capability-linked manufacturer evidence]
  Rules --> Result[Verdict, requirements, limits, evidence]
```

- The API is the source of truth for verified devices. Draft and review-needed records stay private.
- The Python rules engine (version 0.5.0) calculates every verdict deterministically. It accounts for DP Alt Mode, DisplayPort MST vs. macOS SST mirroring, Thunderbolt daisy-chaining, DisplayLink software driver routing, and USB-C host bandwidth contention. It does not infer device specifications; missing required values produce **Insufficient data**.
- Catalogue capabilities link to manufacturer URLs, factual excerpts, and checked dates. The seed workflow, JSON spec ingestion CLI, and protected admin API require evidence for populated published fields.
- PostgreSQL is used in the combined Compose workflow; direct local API development defaults to SQLite.
- The verified catalogue currently publishes laptops and accessories spanning USB-C hubs, USB-C docks, Thunderbolt docks, DisplayLink docks, USB-C chargers, and portable monitors. Three accessories remain in `needs_review`; other accessory categories remain future coverage, not a promise that a compatible result is available for every product.
- Reverse lookup is supported via `GET /devices/laptops/{device_id}/compatible-accessories` with display and charging filters, alongside instant catalogue search via `GET /devices/search`.
- The evaluator test suite in `tests/test_rules.py` covers 77 distinct compatibility scenarios. The complete API test suite passes 154 unit and integration tests (with 11 PostgreSQL policy/readiness checks conditionally executed in isolated CI environments); API lint/format, frontend lint/format, and the production build also pass.

The Render Free preview configuration is prepared but not deployed. The default `onrender.com` hostnames can be used without buying a domain. No portfolio destination has been selected. Core V2 evidence reviews, desktop/mobile browser checks, quality checks, and protocol fidelity rules are complete.

## Operations and monitoring

- **Health and readiness:** `GET /health` is a database-independent liveness check. `GET /ready` checks database connectivity and returns only a generic not-ready response (`503 not_ready`) on failure without exposing credentials or internal database errors.
- **Service Level Objective (SLO):** PortPilot's API response-time objective is p95 server duration $\le 500$ ms at 5 requests/second over a 30-minute steady-state window for the weighted deterministic request mix (40% `GET /devices`, 30% `POST /checks`, 10% `GET /devices/laptops/{id}`, 10% `GET /devices/accessories/{id}`, 5% `GET /ready`, 5% `POST /result-reports`) against seeded PostgreSQL. In local load validation, the mix measured p50 of 23.8 ms, p95 of 50.5 ms, p99 of 92.9 ms, throughput of 5.01 req/s, and 0.00% error rate. Natural language parsing (`POST /setup-requests/parse`) is backed by an external AI provider and is tracked and evaluated separately from this deterministic SLO.
- **Duration distributions and metrics:** `GET /metrics` exposes Prometheus text metrics covering:
  - Total HTTP requests (`portpilot_http_requests_total`) by method, route template, and status.
  - Duration distributions (`portpilot_http_request_duration_seconds`) as standard histogram buckets (`le="0.005"` through `le="+Inf"`, plus sum and count) by method, route template, and status.
  - Compatibility checks (`portpilot_compatibility_checks_total`) by verdict and rule-engine version.
  - Metrics are process-local: observations reset on process restart and are not aggregated across multi-worker deployments without an external Prometheus scraper.
- **Safe logging and slow-route detection:** Structured JSON logs record `http_request` events with request ID, method, normalized route template, status code, and elapsed milliseconds. If elapsed time meets or exceeds `SLOW_REQUEST_THRESHOLD_MS` (default 500 ms), a warning event `http_slow_request` is emitted. Ordinary requests under threshold do not produce duplicate events. Sensitive values—including query parameters, authorization tokens, request/response bodies, client IP addresses, and setup text—are strictly excluded from logs and metrics.
- **Database operations and migration recovery:** Tested backup, restore, migration failure response, and rollback runbooks for local SQLite, Compose PostgreSQL, and Render Free are documented in the [Database Operations and Migration Recovery Runbook](docs/database-operations-runbook.md). Storing persistent user data on Render Free is blocked until a durable database tier with automated backups and point-in-time recovery is provisioned.

## Demo preparation

See [the 90-second demo outline](docs/demo-outline.md) for candidate compatible and incompatible checks, the result details to show, and the recording sequence.

## Contributing

We welcome contributions! Please review [CONTRIBUTING.md](CONTRIBUTING.md) for local environment setup, contribution tracks (catalogue curation, capability extension, rules engine, frontend), quality commands, and pull request guidelines. Key contributor references:
- [Catalogue Identity and Evidence Standard](docs/catalogue-identity-and-evidence.md)
- [Source Review Playbook](docs/source-review-playbook.md)
- [Capability Registry Contributor Guide](docs/capability-registry.md)
- [Database Operations and Migration Recovery Runbook](docs/database-operations-runbook.md)
- [Preview and Release Playbook](docs/preview-and-release-playbook.md)
- [Accessibility Screen-Reader Test Plan](docs/accessibility-screen-reader-test-plan.md)

## Project structure

```text
api/     FastAPI service, SQLAlchemy models, Alembic migrations, and device seeds
web/     Next.js user interface
.github/ GitHub Actions checks
```

## Scope and limitations

PortPilot is an early compatibility checker, not a retailer search or recommendation service. It does not scrape marketplace listings, infer unsupported capabilities, or diagnose hardware faults. The catalogue is manually curated from manufacturer sources. PostgreSQL persistence, evidence-linked device records, and a protected catalogue administration API are in place; broader device coverage and the public deployment remain incomplete.
