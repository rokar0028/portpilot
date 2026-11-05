# Contributing to PortPilot

Welcome, and thank you for contributing to PortPilot!

PortPilot is an evidence-backed compatibility checker for USB-C laptops, monitors, docks, and chargers. It provides deterministic, fact-grounded compatibility verdicts directly tied to manufacturer documentation.

This guide outlines our development philosophy, environment setup, contribution workflows, quality standards, and pull request procedures.

---

## 1. Core Principles & Architecture

Before proposing any changes, please review the foundational principles governing PortPilot:

1. **Deterministic Rule Authority:**
   Compatibility verdicts are calculated exclusively by our deterministic evaluation engine in [`api/app/rules.py`](api/app/rules.py). We do not guess, extrapolate, or use AI to infer hardware compatibility. Missing or conflicting facts always produce an explicit **`insufficient_data`** verdict.
2. **Mandatory Manufacturer Evidence:**
   Every published device capability must link to verifiable manufacturer documentation (manual, technical specification sheet, support page). Retailer listings, forums, and anecdotal claims are not accepted as published evidence.
3. **Strict Separation of Natural Language Parsing:**
   Our natural-language setup parser ([`api/app/setup_parser.py`](api/app/setup_parser.py)) translates user requests into structured constraints only (e.g. "dual 4K at 60Hz"). It never touches device facts or compatibility calculations.
4. **Shared Capability Registry:**
   All device capabilities, database models, schemas, publication requirements, and rule inputs are governed by the canonical capability registry in [`api/app/capabilities.py`](api/app/capabilities.py).
5. **Reviewable & Recoverable Changes:**
   Catalogue updates, schema migrations, and operational procedures must maintain a traceable audit history and tested rollback path.

---

## 2. Local Development Setup

### Prerequisites
- **Python:** 3.12 or newer (3.14 supported).
- **Node.js:** 20.x or newer (with `npm` 10+).
- **Docker & Docker Compose:** Optional for local SQLite development; required for PostgreSQL integration and containerized preview testing.

---

### Backend Setup (FastAPI & SQLAlchemy)

Direct local API development defaults to a local SQLite database (`sqlite:///./portpilot.db`).

1. Navigate to the `api` directory:
   ```bash
   cd api
   ```
2. Create and activate a Python virtual environment:
   ```bash
   # Linux / macOS
   python3 -m venv .venv
   source .venv/bin/activate

   # Windows (PowerShell)
   python -m venv .venv
   .venv\Scripts\Activate.ps1
   ```
3. Install development dependencies:
   ```bash
   pip install -r requirements-dev.txt
   ```
4. Set up the local database:
   ```bash
   alembic upgrade head
   python -m app.seed
   ```
5. Start the FastAPI development server:
   ```bash
   uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
   ```
   - API endpoints: http://127.0.0.1:8000
   - Interactive OpenAPI docs: http://127.0.0.1:8000/docs
   - Health check: http://127.0.0.1:8000/health
   - Database readiness: http://127.0.0.1:8000/ready
   - Prometheus metrics: http://127.0.0.1:8000/metrics

---

### Frontend Setup (Next.js)

1. Open a new terminal and navigate to the `web` directory:
   ```bash
   cd web
   ```
2. Install dependencies:
   ```bash
   npm ci
   ```
3. Configure environment variables (points to the local API by default):
   ```bash
   # Linux / macOS
   cp .env.example .env.local

   # Windows (PowerShell)
   Copy-Item .env.example .env.local
   ```
4. Start the Next.js development server:
   ```bash
   npm run dev
   ```
   Open http://localhost:3000 to interact with the PortPilot interface.

---

### Running with Docker Compose (Full Stack with PostgreSQL)

To run the complete production-like stack (PostgreSQL 16, API, and Next.js):

```bash
docker compose up --build
```
- Frontend: http://localhost:3000
- API: http://localhost:8001
- Compose automatically waits for PostgreSQL health before starting the API, and waits for API readiness before launching the web service.
- To shut down: `docker compose down`.

---

## 3. Contribution Tracks

PortPilot contributions typically fall into one of five tracks:

### Track 1: Adding or Updating Device Models
- **Standard:** Follow the [Catalogue Identity and Evidence Standard](docs/catalogue-identity-and-evidence.md).
- **Process:**
  1. Locate the exact manufacturer product specification or manual.
  2. Extract the precise manufacturer model code (e.g. `83DH000AUS`), regional variant, and hardware revision.
  3. Extract factual quotes for each populated capability with source URLs and checked dates.
  4. Add the record to [`api/app/seed.py`](api/app/seed.py) using `validate_seed_record()`, ingest a JSON specification file via `python scripts/seed_from_spec.py <spec.json>` (see templates in `api/specs/examples/`), or submit via the authenticated Admin API (`/admin/laptops` or `/admin/accessories`).
  5. If competing or conflicting claims exist, follow the [Source Review Playbook](docs/source-review-playbook.md).

### Track 2: Extending Capabilities & Data Fields
- **Standard:** Follow the [Capability Registry Contributor Guide](docs/capability-registry.md).
- **Process:**
  1. Add the capability entry to `CAPABILITIES` in [`api/app/capabilities.py`](api/app/capabilities.py) specifying owner entity, type, and units.
  2. Map publication rules (`required_for` or `PUBLICATION_OPTIONAL`).
  3. Map rule engine adapters (`RULE_INPUTS`, `RULE_DERIVED_INPUTS`, or `RULE_UNUSED`).
  4. Add matching columns in [`api/app/models.py`](api/app/models.py) and schemas in [`api/app/schemas.py`](api/app/schemas.py).
  5. Generate and verify the database migration (`alembic revision --autogenerate`).

### Track 3: Modifying Compatibility Rules
- **Location:** [`api/app/rules.py`](api/app/rules.py)
- **Process:**
  1. Ensure the rules engine remains 100% deterministic: do not import external network clients or AI helpers.
  2. Preserve explainability: verdicts must populate `verdict`, `summary`, `requirements`, `limits`, and `evidence`.
  3. Add or update parameterized test scenarios in [`api/tests/test_rules.py`](api/tests/test_rules.py) covering all edge cases.

### Track 4: Frontend Development & Accessibility
- **Location:** [`web/src/`](web/src/)
- **Process:**
  1. Maintain responsive mobile layouts (320px, 375px, 768px viewports).
  2. Ensure keyboard navigation and ARIA attributes conform to [Accessibility Screen-Reader Test Plan](docs/accessibility-screen-reader-test-plan.md).
  3. Keep touch targets $\ge 44 \times 44$ px.
  4. Run automated accessibility scans using Playwright + axe-core (`npm run e2e`).

### Track 5: Tooling, Observability & Infrastructure
- **Metrics & Logging:** Preserve safe, bounded logging. Never log authorization headers, passwords, request bodies, or user setup text to logs or Prometheus metrics.
- **Preview Verification:** Run [`api/scripts/verify_preview_deployment.py`](api/scripts/verify_preview_deployment.py) against live or local preview stacks.
- **SLO Performance:** Benchmark deterministic latency against [`api/perf/deterministic-slo-mix.js`](api/perf/deterministic-slo-mix.js) (target: p95 $\le 500$ ms at 5 req/s).

---

## 4. Quality Commands & Pre-Submission Gates

All pull requests must pass the following automated quality checks:

### Backend Checks (run from `api/`):
```bash
# 1. Lint code
ruff check app migrations tests scripts

# 2. Check code formatting
ruff format --check app migrations tests scripts

# 3. Run unit and integration tests
python -m pytest tests -q

# 4. Verify AI parser evaluation harness (mock mode)
python scripts/evaluate_setup_parser.py --mock
```

### Frontend Checks (run from `web/`):
```bash
# 1. Lint TypeScript and React
npm run lint

# 2. Check formatting
npm run format:check

# 3. Production build test
npm run build
```

### End-to-End Browser Testing (Playwright):
```bash
# 1. Start disposable test database
docker compose -p portpilot-e2e -f docker-compose.e2e.yml up -d --wait

# 2. In web/: build standalone assets and execute tests
cd web
npm run build:e2e
npm run e2e

# 3. Shut down disposable database
docker compose -p portpilot-e2e -f docker-compose.e2e.yml down
```

### Preview Deployment Smoke Verification:
```bash
python api/scripts/verify_preview_deployment.py --api-url http://127.0.0.1:8000
```

---

## 5. Database Migrations & Rollback Safety

When modifying database schemas:
1. Always generate migrations with Alembic:
   ```bash
   cd api
   alembic revision --autogenerate -m "describe_change"
   ```
2. Review the generated script in `api/migrations/versions/` to verify column types, nullability, and foreign key constraints.
3. Test upgrading and downgrading against a disposable database:
   ```bash
   alembic upgrade head
   alembic downgrade -1
   alembic upgrade head
   ```
4. **Data Rollback Rule:** Follow the [Database Operations Runbook](docs/database-operations-runbook.md). Never run destructive downgrades on environments containing live user or audit data; perform a database restore from pre-migration backup instead.

---

## 6. Pull Request & Review Process

1. **Create a Feature Branch:**
   ```bash
   git checkout -b feat/your-feature-name
   # or: fix/issue-description, docs/topic-name
   ```
2. **Commit Style:**
   Use clear, descriptive commit messages following the Conventional Commits style (e.g., `feat:`, `fix:`, `docs:`, `test:`, `refactor:`).
3. **Secrets Audit:**
   Ensure zero secrets, API tokens (`ADMIN_API_TOKEN`), provider keys, or database connection strings are staged or committed. Client bundles must never contain private credentials.
4. **Pull Request Description:**
   Include:
   - Summary of changes and rationale.
   - Reference to associated issues or workstreams.
   - For device additions: manufacturer source URL(s) and model codes.
   - Results of local quality verification commands (`ruff`, `pytest`, `npm run lint`, `npm run build`).
5. **Code Review:**
   Maintainers will review the PR for architectural fidelity, deterministic rule compliance, manufacturer evidence validity, and automated CI passing status.

---

## 7. Key Documentation Links

- [PortPilot V2 Implementation Plan](docs/v2-implementation-plan.md)
- [Catalogue Identity and Evidence Standard](docs/catalogue-identity-and-evidence.md)
- [Source Review Playbook](docs/source-review-playbook.md)
- [Capability Registry Contributor Guide](docs/capability-registry.md)
- [Database Operations and Migration Recovery Runbook](docs/database-operations-runbook.md)
- [Preview and Release Playbook](docs/preview-and-release-playbook.md)
- [Release Candidate Record Template](docs/release-candidate-template.md)
- [Accessibility Screen-Reader Test Plan](docs/accessibility-screen-reader-test-plan.md)
- [End-to-End Testing Plan](docs/end-to-end-testing-plan.md)
