# PortPilot: Hardware Protocol & Compatibility Verification Engine

[![CI](https://github.com/rokar0028/portpilot/actions/workflows/ci.yml/badge.svg)](https://github.com/rokar0028/portpilot/actions/workflows/ci.yml)
[![Python 3.12](https://img.shields.io/badge/Python-3.12-3776AB.svg?logo=python&logoColor=white)](https://www.python.org/)
[![Next.js 15](https://img.shields.io/badge/Next.js-15-000000.svg?logo=next.js&logoColor=white)](https://nextjs.org/)
[![TypeScript 5.7](https://img.shields.io/badge/TypeScript-5.7-3178C6.svg?logo=typescript&logoColor=white)](https://www.typescriptlang.org/)
[![Tests](https://img.shields.io/badge/Pytest-163%20passed-success.svg?logo=pytest&logoColor=white)](https://docs.pytest.org/)
[![Accessibility](https://img.shields.io/badge/WCAG%202.1-AA%20Compliant-brightgreen.svg)](https://www.w3.org/WAI/standards-guidelines/wcag/)
[![License MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)

> 🎓 **Academic Capstone Project**  
> This project was designed and developed as an **Academic Final Year Major Project** for the Bachelor of Technology (B.Tech) degree in Computer Science & Engineering. It addresses real-world hardware protocol verification, physical bus constraints modeling, evidence-backed knowledge systems, and accessible engineering.

---

PortPilot is a deterministic compatibility and protocol verification engine that assesses whether a given laptop host and peripheral accessory (hubs, docks, chargers, displays) reliably support a requested hardware setup. Unlike heuristic tools or retail product descriptions, PortPilot calculates verdicts through deterministic mathematical and protocol rules based strictly on verified manufacturer specifications and physical bus standards. Missing required facts produce **Insufficient data** rather than speculative assertions.

## Problem Statement: Real-World Hardware Traps Solved

Online marketplaces (Amazon, Best Buy) and general LLMs frequently provide false-positive compatibility answers because they treat USB-C as a uniform standard. In reality, USB-C is merely a physical form factor concealing divergent protocols, alternate modes, bandwidth limits, and operating system quirks. PortPilot models real-world physical bus constraints to prevent expensive hardware mismatches:

1. **The macOS Multi-Stream Transport (MST) Trap:** Standard USB-C multi-display docks rely on DisplayPort MST to extend separate desktop spaces to 2+ monitors over a single cable. macOS operating systems intentionally omit MST support over standard USB-C, forcing all connected external monitors to mirror each other. PortPilot flags this architectural constraint before users purchase an incompatible dock.
2. **The High-Speed Lane Bifurcation Bottleneck:** Driving 4K at 60 Hz over DisplayPort 1.2 requires all 4 high-speed differential lanes on a USB-C connector. Connecting a hub that provides USB 3.0 data (5 Gbps+) steals 2 lanes for data traffic, capping display output to 4K at 30 Hz or 1080p. PortPilot identifies and warns about these hardware bandwidth trade-offs.
3. **Net Power Delivery Pass-Through Deficits:** Multi-port USB-C hubs reserve 15W–30W of input power to energize internal chipsets and charging ports. If a 65W wall charger is plugged into a hub with a 15W reservation, it delivers only 50W to a laptop requiring 65W, causing slow-charge warnings or battery drain under CPU load. PortPilot calculates net power margins ($W_{\text{net}} = W_{\text{input}} - W_{\text{reservation}}$) against host requirements.
4. **GPU Display Limits & DisplayLink Software Routing:** Base Apple Silicon processors (M1, M2, M3, M4) natively support only one external display engine. PortPilot models whether multi-display docks rely on native DisplayPort Alt Mode (which fails on base Macs) or DisplayLink USB software compression (which bypasses native GPU limits using virtual framebuffer drivers).

## Two-Tier Compatibility Architecture

PortPilot operates on an auditable two-tier evaluation model that guarantees mathematical transparency:

- **Tier 1: Verified Manufacturer Evidence (🛡️ Verified):** Exact hardware model matching where every capability is backed by an active manufacturer specification URL citation, verbatim excerpt, and checked date. Missing required fields produce **Insufficient data**.
- **Tier 2: Theoretical Protocol Evaluation (⚙️ Theoretical):** Standard hardware protocol profiles (such as *Thunderbolt 4 Host*, *USB-C 3.2 Gen 2 DP 1.4 Host*, *Apple Silicon Base Architecture*, *Universal Thunderbolt 4 Dock*, and *Dual HDMI MST Dock*). This allows users whose exact laptop or accessory is not yet curated to evaluate their setup against official USB-IF, VESA, and Intel protocol standards.

## Core Capabilities & Features

- **Multi-Device Compatibility Checking:** Evaluate combinations across 22 verified laptops and 24 accessories spanning Apple, Dell, Lenovo, Anker, Belkin, Ugreen, and Plugable, alongside standard protocol profiles.
- **Auditable Evidence Citations:** Every compatibility assertion links directly to an active manufacturer specification URL, verbatim quote, and verification timestamp.
- **Immutable Result Snapshots:** Share checks via persistent URL snapshots (`?snapshot=<id>`) preserving the exact verdict, requirements, limitations, and citations.
- **Reverse Accessory Search:** Lookup all compatible docks and chargers for a given laptop via `GET /devices/laptops/{device_id}/compatible-accessories`.
- **WCAG 2.1 AA Accessibility:** Full screen-reader support with polite ARIA live announcements, high-contrast UI, keyboard navigation, and zero automated axe violations.
- **Natural Language Parsing:** LLM-assisted setup parser (`POST /setup-requests/parse`) that converts freeform queries (e.g., *"dual 4K displays and 65W charging"*) into structured schema with fallback rules.

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

## System Architecture & Engineering Design

```mermaid
flowchart TD
  subgraph ClientTier["Frontend Layer (Next.js 15 App Router / React 19)"]
    UI["Checker Interface & Quick-Filter Search"]
    A11y["WCAG 2.1 AA Compliant ARIA Live Regions"]
    Snap["Immutable Result Snapshots (?snapshot=id)"]
  end

  subgraph ServiceTier["Backend API Service (FastAPI / Python 3.12)"]
    API["FastAPI REST Endpoints"]
    Auth["Protected Admin API (Bearer Token Auth)"]
    NLParser["Natural Language Setup Parser"]
  end

  subgraph EngineTier["Deterministic Rule Engine (v0.6.0)"]
    Tier1["Tier 1: Verified Manufacturer Evidence"]
    Tier2["Tier 2: Theoretical Protocol Evaluation"]
    Rules["Hardware Rules (macOS MST, Bifurcation, Net PD, DisplayLink)"]
  end

  subgraph DataTier["Data & Specification Storage Layer"]
    DB[("PostgreSQL 16 / SQLite Engine")]
    Specs["Declarative JSON Device Specs (api/specs/)"]
    Audit["Automated Evidence Freshness & Staleness Tracker"]
  end

  subgraph OpsTier["Observability & Reliability Infrastructure"]
    Metrics["Prometheus /metrics Endpoint"]
    Logs["Structured JSON Request & Latency Logging"]
    Health["Liveness (/health) & DB Readiness (/ready) Probes"]
  end

  UI -->|HTTP / JSON| API
  NLParser -->|Extracted Setup| API
  API --> Rules
  Rules --> Tier1
  Rules --> Tier2
  API --> DB
  Specs -->|Declarative Ingestion| DB
  DB --> Audit
  API --> Metrics
  API --> Logs
```

- **Separation of Concerns:** The API serves as the single source of truth for verified hardware devices and protocol baselines. Unreviewed drafts remain private.
- **Deterministic Evaluation:** The Python rules engine (`v0.6.0`) computes verdicts deterministically across both evaluation tiers. It directly models DisplayPort Alternate Mode, DP Multi-Stream Transport (MST) vs. macOS SST mirroring, Thunderbolt bandwidth tunneling, DisplayLink software routing, and USB-C lane bifurcation. Specifications are never guessed; absent data results in **Insufficient data**.
- **Evidence-Linked Catalogue:** Every published capability links directly to a verified manufacturer citation URL, verbatim excerpt, and validation timestamp. Specifications are declared as structured JSON documents under `api/specs/laptops/` and `api/specs/accessories/`.
- **Database Flexibility:** Production deployments utilize PostgreSQL 16 (with connection pooling via `psycopg3`), while local and test workflows leverage isolated SQLite engines.
- **Reverse Lookup & Instant Search:** Includes reverse capability search via `GET /devices/laptops/{device_id}/compatible-accessories` with dynamic display and power filters, alongside full-text instant search via `GET /devices/search`.
- **Comprehensive Quality Gates:** 163 backend unit and integration tests, strict Ruff linting and formatting, Playwright end-to-end browser journeys across desktop and mobile viewports, automated WCAG 2.1 AA accessibility assertions, and production Next.js builds.

## Operations and monitoring

- **Public reporting and privacy:** `POST /result-reports` accepts only the selected device IDs, setup, verdict, rules version, and an optional note of up to 1,000 characters. Reports are unauthenticated, rate-limited per process, and retained in the configured database for operational review. Do not submit names, contact details, secrets, or other personal information. Production deployments should add durable rate limiting, abuse monitoring, and a documented retention/deletion policy at the edge or database layer.
- **Metrics access:** `GET /metrics` is intentionally unauthenticated for local and simple preview monitoring. In production, expose it only through a private network, authenticated monitoring gateway, or equivalent access control.

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

## Documentation & Methodology

Key engineering specifications and operational runbooks are maintained in [`docs/`](docs/):

- [PortPilot Architecture & Core Plan](docs/portpilot-implementation-plan.md) — Product requirements and foundational protocol rules.
- [V2 Capability & Evaluation Architecture](docs/v2-implementation-plan.md) — Follow-on capabilities, snapshots, and release acceptance criteria.
- [Capability Registry Guide](docs/capability-registry.md) — How capabilities are registered, verified, and mapped to deterministic rules.
- [Database Operations & Recovery Runbook](docs/database-operations-runbook.md) — Tested backup, migration recovery, and failure response procedures.
- [Accessibility Screen-Reader Test Plan](docs/accessibility-screen-reader-test-plan.md) — WCAG 2.1 AA manual and automated test matrices.

<details>
<summary><strong>View All 20 Detailed Workstream Plans & Historical Specs</strong></summary>

- [Workstream 0: Baseline Inventory & Capability Registry](docs/v2-workstream-0-implementation-plan.md)
- [Workstream 1: Device Identity & Evidence Threshold](docs/v2-workstream-1-implementation-plan.md)
- [Workstream 2: Evidence Conflicts & Recheck History](docs/v2-workstream-2-implementation-plan.md)
- [Workstream 3: Registry Integration & Consistency Checks](docs/v2-workstream-3-implementation-plan.md)
- [Workstream 4: Display Configurations & Topology](docs/v2-workstream-4-implementation-plan.md)
- [Workstream 5: Model-Finding, Mobile UX & Low-Data Reports](docs/v2-workstream-5-implementation-plan.md)
- [Workstream 6: Screen-Reader & Accessibility Audit](docs/v2-workstream-6-implementation-plan.md)
- [Workstream 7: Latency SLO, Metrics & Migration Recovery](docs/v2-workstream-7-implementation-plan.md)
- [Workstream 8: LLM Setup Parser Evaluation Benchmark](docs/v2-workstream-8-implementation-plan.md)
- [Workstream 9: Deployment Verification Checklist](docs/v2-workstream-9-implementation-plan.md)
- [Workstream 10: Contributor Hand-off & Architecture Runbooks](docs/v2-workstream-10-implementation-plan.md)
- [Workstream 11: Hardware Protocol Fidelity & Bus Constraints](docs/v2-workstream-11-implementation-plan.md)
- [Workstream 12: Reverse Lookup & Declarative Seeder](docs/v2-workstream-12-implementation-plan.md)
- [Source Review Playbook](docs/source-review-playbook.md)
- [Catalogue Identity Standard](docs/catalogue-identity-and-evidence.md)
- [Preview & Release Playbook](docs/preview-and-release-playbook.md)
- [Phase 0 Original Plan](docs/implementation%20plan.md)
</details>

## Project structure

```text
api/
  app/            FastAPI service, models, rules engine (0.6.0), and observability
  specs/          Declarative JSON device specs (laptops/ and accessories/)
  migrations/     Alembic database schema migrations
  tests/          Pytest test suite (163 passing unit and integration tests)
  scripts/        Spec validation, evaluation benchmarks, and staleness audits
web/
  src/
    components/   Modular UI components (DeviceSelector, SetupForm, ResultPanel, etc.)
    types/        Canonical TypeScript checker contracts
    utils/        Evidence grouping and helper utilities
    app/          Next.js App Router (root checker and /coverage)
  e2e/            Playwright browser test suite
.github/          GitHub Actions CI and release confidence workflows
```

## Scope, Limitations & Future Work

### Current Project Scope
- PortPilot is a deterministic compatibility and protocol verification engine, not an e-commerce affiliate or recommendation service.
- It operates strictly over verified technical specifications and established hardware protocols, intentionally avoiding unverified inferences or marketplace scraping.
- Hardware coverage is backed by an auditable manual and declarative JSON evidence pipeline across major device ecosystems (Apple, Dell, Lenovo, Anker, Belkin, Ugreen, Plugable).

### Future Work & Extensions
- **Expanded Hardware Catalogue:** Broaden declarative spec coverage across additional OEM manufacturers and next-generation protocols (USB4 2.0 80 Gbps / 120 Gbps and Thunderbolt 5).
- **Automated Evidence Verification Bot:** Implement scheduled headless scrapers to re-verify manufacturer specification URL liveness, detect document changes, and automatically flag stale evidence.
- **Crowdsourced Review Pipeline:** Provide a cryptographically signed community submission pipeline allowing contributors to submit manufacturer specification PDFs/links with automated schema checks.

---

## Academic Project Attribution

- **Project Title:** PortPilot — Deterministic Hardware Protocol & Peripheral Compatibility Verification Engine
- **Academic Context:** Final Year Major Project / Capstone Project (B.Tech in Computer Science & Engineering)
- **Technologies:** Python 3.12, FastAPI, SQLAlchemy, Alembic, PostgreSQL, Next.js 15, TypeScript 5.7, Playwright, Docker, Prometheus
- **Repository:** [github.com/rokar0028/portpilot](https://github.com/rokar0028/portpilot)
- **License:** [MIT License](LICENSE)
