# PortPilot

PortPilot checks whether a laptop and accessory support a requested setup. Verdicts come from deterministic rules over documented specifications; missing required facts produce **Insufficient data**.

## Current vertical slice

- Laptop: Lenovo IdeaPad Slim 3 14IRH10R
- Accessory: Anker 364 USB-C Hub (10-in-1, Dual 4K HDMI)
- Setup: one 1080p external display plus laptop charging

The manufacturer sources confirm USB-C DisplayPort 1.2 and USB Power Delivery on the laptop, and HDMI plus up to 85 W pass-through on the hub. They do not establish every requirement for this setup, so PortPilot deliberately reports **Insufficient data** rather than guessing. The API catalogue is database-backed and currently publishes 15 laptops and 14 accessories; one accessory is held for model-identity review.

The checker lets you select a laptop, accessory, display mode, and charging requirement. After a check, **Share this result** copies a URL that restores those selections and reruns the check when opened. A quick-reference glossary on the page explains USB-C, DisplayPort Alt Mode, USB Power Delivery, USB4, and Thunderbolt.

The [coverage and limitations page](/coverage) reports live verified catalogue counts and explains how PortPilot handles manufacturer evidence and unknown specifications.

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
uvicorn app.main:app --reload
```

The direct workflow uses a local SQLite file by default. The API is at http://localhost:8000, its health endpoint is http://localhost:8000/health, the evidence-backed catalogue is at http://localhost:8000/devices, and interactive API docs are at http://localhost:8000/docs.

### Catalogue evidence

Each source record identifies the capability it supports, with a manufacturer URL, short factual excerpt, and checked date. Evidence review status is `draft`, `verified`, or `needs_review`. A capability that is not documented stays null; it is not treated as unsupported.

### Catalogue administration

Catalogue writes use the protected API. Set a long random `ADMIN_API_TOKEN` in `api/.env` for local API development. For Docker Compose, set the same variable in the shell before starting Compose; if it is absent, catalogue administration stays disabled. For example in PowerShell:

```powershell
$env:ADMIN_API_TOKEN = python -c "import secrets; print(secrets.token_urlsafe(32))"
docker compose up --build
```

In `/docs`, authorize with the value as a bearer token, then use `GET`, `POST`, and `PUT` under `/admin/laptops` and `/admin/accessories`. New records default to `draft`, and drafts remain editable while incomplete. To publish, set `review_status` to `verified`, provide the category's required specifications, and attach verified manufacturer evidence for the model code and each populated capability. Updates replace the evidence list for that device. Only verified records appear in the public catalogue and can be used in checks. Do not commit API tokens or place them in request examples.

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

[`render.yaml`](render.yaml) defines the API, Next.js frontend, and PostgreSQL database as free Render resources in Singapore. It is configuration only; PortPilot is not deployed yet. Render Free web services sleep after 15 minutes without traffic, and Free Postgres expires after 30 days with no backups. Use this only as a temporary preview and do not store user data there. The API runs migrations and seeds the catalogue when it starts. Deployment still requires this private GitHub repository to be connected to Render.

## Quality commands

Run these from the indicated directory:

```powershell
# api/
ruff check app migrations tests
ruff format --check app migrations tests
python -m pytest tests -q

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
```

In a second terminal, use the same `NEXT_PUBLIC_API_URL` and run the built browser suite:

```powershell
cd web
$env:NEXT_PUBLIC_API_URL = "http://127.0.0.1:18000"
npm run build:standalone
npm run e2e:install
npm run e2e
```

The Playwright config starts the API and standalone frontend against that database. When finished, stop the disposable database from the repository root with `docker compose -p portpilot-e2e -f docker-compose.e2e.yml down`.

CI runs these checks on pushes and pull requests. Apply database migrations with `alembic upgrade head`, and seed the curated devices with `python -m app.seed`. Format code with `ruff format app migrations` and `npm run format`.

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
- The Python rules engine calculates every verdict. It does not infer device specifications; missing required values produce **Insufficient data**.
- Catalogue capabilities link to manufacturer URLs, factual excerpts, and checked dates. The seed workflow and protected admin API require evidence for populated published fields.
- PostgreSQL is used in the combined Compose workflow; direct local API development defaults to SQLite.
- The verified catalogue currently contains 15 laptops and 14 accessories: USB-C hubs and USB-C chargers. One accessory remains in `needs_review`; other accessory categories remain future coverage, not a promise that a compatible result is available for every product.
- The evaluator test file defines 52 distinct scenarios when parameterized inputs are counted. The API suite passes 75 tests; API lint/format, frontend lint/format, and the production build also pass.

The Render Free preview configuration is prepared but not deployed. The default `onrender.com` hostnames can be used without buying a domain. No portfolio destination has been selected. Phase 6 evidence review, desktop/mobile browser checks, and quality checks are complete.

## Operations and monitoring

- `GET /health` is a database-independent liveness check. `GET /ready` checks database connectivity and returns only a generic not-ready response on failure.
- `GET /metrics` exposes Prometheus text metrics for HTTP request counts by method, route template, and status, plus compatibility verdict counts by rule-engine version. It is process-local: counts reset on restart and are not aggregated across multiple workers.
- API request logs are structured JSON and include a server-generated request ID, method, route template, status, and elapsed time. Compatibility logs include verdict and rule-engine version. Request bodies, query strings, credentials, and device identifiers are not logged.
- Configure the hosting provider to retain and alert on API error logs and service availability. The application does not send metrics to an external monitoring service; a provider-side scraper or collector can read `/metrics`.

## Demo preparation

See [the 90-second demo outline](demo-outline.md) for candidate compatible and incompatible checks, the result details to show, and the recording sequence.

## Project structure

```text
api/     FastAPI service, SQLAlchemy models, Alembic migrations, and device seeds
web/     Next.js user interface
.github/ GitHub Actions checks
```

## Scope and limitations

PortPilot is an early compatibility checker, not a retailer search or recommendation service. It does not scrape marketplace listings, infer unsupported capabilities, or diagnose hardware faults. The catalogue is manually curated from manufacturer sources. PostgreSQL persistence, evidence-linked device records, and a protected catalogue administration API are in place; broader device coverage and the public deployment remain incomplete.
