# V2 Workstream 9 implementation plan

## Goal

Define and execute the preview deployment, end-to-end live verification, pre-release acceptance checklist, and safe rollback protocol for candidate releases in an isolated environment, ensuring that every release candidate is thoroughly validated against live services before public availability.

This plan supports [Workstream 9 in the V2 plan](v2-implementation-plan.md#9-preview-and-release-readiness). It defines the implementation roadmap, environment configurations, automated and manual release gates, and release record templates; implementation and verification will proceed in accordance with these steps.

## Findings and decisions

- **Hosting and preview architecture:**
  - The repository maintains two isolated preview mechanisms:
    1. **Render Blueprint (`render.yaml`):** Provisions an isolated cloud preview consisting of `portpilot-api` (Python 3.14/FastAPI web service), `portpilot-web` (Node.js 20 Next.js standalone web service), and `portpilot-db` (PostgreSQL 16).
    2. **Isolated Containerized Preview (`docker-compose.e2e.yml` / `docker-compose.yml`):** Runs an isolated multi-container stack (`portpilot_e2e` database, API, and standalone Next.js frontend) for local preview, automated CI, and staging rehearsal.
  - **Environment isolation policy:** Preview environments must strictly use dedicated databases and isolated origins. Production or shared databases must never be used for preview validation, test seeding, or failure injection.
  - **Render Free tier constraints:** Render's free PostgreSQL tier does not support automated backups, lacks point-in-time recovery (PITR), and expires after 30 days. Furthermore, free web services sleep after 15 minutes of inactivity. Consequently, Render Free is classified strictly as a **disposable preview** environment. It cannot be used as a durable production environment without upgrading to a paid tier with automated backup capabilities, as documented in the [Database operations runbook](database-operations-runbook.md).
- **Automated CI and Release Confidence baseline:**
  - GitHub Actions `.github/workflows/ci.yml` runs unit tests, linting, formatting, and single-browser Playwright E2E on every push and pull request.
  - The dedicated `.github/workflows/release-confidence.yml` workflow runs cross-browser tests across Chromium, Firefox, and WebKit; executes PostgreSQL lifecycle tests; records a 60-second k6 deterministic SLO baseline; and verifies database outage recovery against a disposable PostgreSQL service.
  - Workstream 9 unifies these automated gates with deployed preview smoke checks and manual sign-offs into a single, cohesive release candidate evaluation protocol.
- **Secrets and configuration discipline:**
  - All preview secrets (`ADMIN_API_TOKEN`, database credentials, provider API keys) must be generated dynamically or injected through secure environment variables (e.g., Render dashboard environment overrides or local `.env` files ignored by git).
  - No secret tokens, authorization bearer headers, or internal database connection strings may be committed to version control, embedded in client-side bundles (`NEXT_PUBLIC_*`), or exposed in public documentation or PR comments.
  - Client bundles must only expose `NEXT_PUBLIC_API_URL`.
- **Catalogue and data integrity verification:**
  - Deployed preview databases must apply migrations (`alembic upgrade head`) and seed verified catalogue records (`python -m app.seed`).
  - Previews must verify that unverified/draft models and records flagged with `needs_review` are strictly filtered out from public `/devices` endpoints and compatibility checks, and appear only via authenticated `/admin` endpoints.
- **Rollback and contingency procedures:**
  - In the event of a critical failure during preview evaluation or deployment (e.g. migration crash, severe latency regression, data corruption, or broken layout):
    - **Deployment Rollback:** For Render, roll back to the previous successful deploy in the Render dashboard or trigger a redeployment of the prior stable commit tag. For containerized preview, point orchestration back to the previous stable image/commit.
    - **Database Recovery:** Follow the tested procedures in `database-operations-runbook.md`. If schema migrations introduced breaking changes or data loss risks, restore from the pre-deployment database snapshot rather than running destructive Alembic downgrades on live data.
- **Release Record and audit trail:**
  - Every evaluated release candidate must have a structured release record capturing:
    - Candidate commit SHA and semantic version / release tag.
    - Target preview environment URL(s) and database engine/version.
    - Verification timestamp and operator/evaluator name.
    - Automated test results (CI, cross-browser Playwright, k6 SLO).
    - Deployed preview smoke check results.
    - Accessibility and mobile viewport audit confirmation.
    - Explicit Go / No-Go decision with rationale.

## Scope

- [ ] Define the isolated preview deployment specifications and environment provisioning checklist for Render and isolated container environments.
- [ ] Build a lightweight, non-destructive deployed preview smoke verification script (`api/scripts/verify_preview_deployment.py` or equivalent CLI tool) that tests health/readiness, catalogue visibility, deterministic checks, and shared links against any arbitrary preview URL.
- [ ] Create the comprehensive pre-release acceptance checklist covering database migrations, security/secrets audit, accessibility verification, mobile usability, latency SLO compliance, and operational recovery readiness.
- [ ] Establish the standardized Release Candidate Record format (`docs/releases/` or release run notes) for logging preview evaluations and formal release decisions.
- [ ] Document the step-by-step release deployment, verification, and rollback playbook for maintainers.
- [ ] Rehearse the preview deployment verification and rollback protocol against an isolated local/preview environment.
- [ ] Update the repository documentation (`README.md`, `v2-implementation-plan.md`) to integrate Workstream 9 and guide maintainers through production releases.

## Sequenced implementation steps

### Step 1: Reconcile preview configurations and environment isolation
- Audit `render.yaml`, `docker-compose.yml`, `docker-compose.e2e.yml`, and `.github/workflows/release-confidence.yml`.
- Verify that `render.yaml` sets correct service dependencies, health check paths (`/ready`), and environment variable bindings (`FRONTEND_ORIGIN` dynamically bound to `RENDER_EXTERNAL_URL`, `NEXT_PUBLIC_API_URL` dynamically bound to API's `RENDER_EXTERNAL_URL`).
- Confirm that database connection strings, admin tokens, and provider keys are never hardcoded and that `ADMIN_API_TOKEN` uses `generateValue: true` on Render.
- Document the preflight setup requirements for launching an isolated preview instance.

### Step 2: Implement automated preview smoke verification suite
- Create a reusable, non-destructive preview verification script (e.g., `api/scripts/verify_preview_deployment.py`):
  - Accepts `--api-url` and `--web-url` arguments (defaulting to local or preview endpoints).
  - Validates `GET /health` returns status `ok` (200).
  - Validates `GET /ready` returns status `ready` with database connectivity (200).
  - Validates `GET /devices` returns populated, verified laptops and accessories, with zero draft/needs_review leaks.
  - Submits representative compatibility checks to `POST /checks`:
    - Compatible laptop + accessory pair (expect `compatible` verdict with evidence attached).
    - Incompatible combination (expect `incompatible` verdict with clear reason).
    - Insufficient data combination (expect `insufficient_data` verdict).
    - Multi-display scenario (verifying simultaneous display evaluation).
  - Validates share URL restoration: verifies query parameter formatting matches web expectations.
  - Validates `POST /result-reports`: submits a low-data synthetic report and verifies clean 200/201 response.
  - Validates `GET /metrics`: confirms Prometheus metrics are exposed with safe, non-leaking labels.
  - Exits with code 0 on complete pass, or non-zero with diagnostic error logs on failure.

### Step 3: Formalize pre-release acceptance checklist and release gates
- Compile the formal release gates into a structured checklist:
  1. **Code & Quality Gate:** Clean linting (`ruff check`, `npm run lint`), formatting (`ruff format --check`, `npm run format:check`), backend unit tests (100% pass), and frontend build (`npm run build`).
  2. **Automated Cross-Browser & E2E Gate:** Playwright test suite passes in Chromium, Firefox, and WebKit via `release-confidence.yml` or local runner.
  3. **Performance & Reliability Gate:** k6 deterministic SLO baseline meets p95 $\le 500$ ms at 5 req/s; database outage and recovery verified via `/ready` endpoint.
  4. **Database & Migration Gate:** Alembic head matches migration scripts; pre-migration backup verified; migration rollback/restore path confirmed per `database-operations-runbook.md`.
  5. **Security & Secrets Gate:** Repository secrets scan confirms no API keys, tokens, or credentials in git; client bundle check confirms zero private environment variables in `.next/static`.
  6. **Accessibility Gate:** Automated axe-core clean; manual screen-reader test protocol completed or limitations documented per `accessibility-screen-reader-test-plan.md`.
  7. **Mobile & Viewport Gate:** Responsive layout verified at 320px, 375px, and 768px viewports; no horizontal scroll or clipped controls.
  8. **AI Setup Parser Gate:** Parser evaluation report recorded per Workstream 8; mock evaluation verified; live provider claims documented or explicitly disclaimed if offline.

### Step 4: Define release candidate evaluation record template
- Create a markdown template `docs/release-candidate-template.md` (and initial candidate log location `docs/releases/`) specifying:
  - Commit SHA, branch/tag, evaluation date, operator.
  - Target environment details (Render preview URL, Docker host, database version).
  - Checklist results for Gates 1–8 with artifact links.
  - Smoke test execution log.
  - Findings, exceptions, and remediation notes.
  - Formal Go / No-Go recommendation and sign-off.

### Step 5: Document release deployment, verification, and rollback playbook
- Expand the release documentation to provide step-by-step guidance:
  - Pre-deployment preparation (branch cutoff, tagging, changelog review).
  - Preview provisioning and migration execution.
  - Running the automated smoke verification script against deployed preview endpoints.
  - Conducting manual spot-checks (mobile layout, model finder guidance, share links).
  - Rollback decision tree: criteria for aborting a release, instant service redeploy of prior tag, database point-in-time restore or dump restore from pre-deploy backup.
  - Final production cutover checklist.

### Step 6: Verification and rehearsal
- Test the preview verification script against a local containerized preview (`docker-compose up` or `docker-compose.e2e.yml`).
- Verify that all simulated check endpoints, health probes, and metrics inspections pass.
- Verify that intentional failures (e.g., stopping database or passing invalid URL) are reported with clear diagnostic messages.
- Update `v2-implementation-plan.md`, `README.md`, and this plan with verification results.

## Acceptance criteria

- [x] A dedicated preview deployment verification tool (`verify_preview_deployment.py`) is implemented and tested, supporting automated smoke validation of deployed API and web services without mutating production data.
- [x] A pre-release acceptance checklist covering all eight technical and operational gates (code quality, cross-browser E2E, performance SLO, migrations, security, accessibility, mobile, AI parser) is documented.
- [x] A standardized Release Candidate Record template (`docs/release-candidate-template.md`) is created and ready for logging formal release evaluations.
- [x] The deployment, verification, and rollback playbook (`docs/preview-and-release-playbook.md`) explicitly addresses Render preview and containerized hosting, including database recovery constraints on disposable tiers.
- [x] Automated tests verify the preview verification script logic and error reporting against mock and live endpoints (`api/tests/test_verify_preview_deployment.py`).
- [x] All documentation accurately reflects the V2 release readiness criteria and links to the operational runbooks.

## Verification approach

- [x] **Script unit & integration tests:** Ran pytest on `api/tests/test_verify_preview_deployment.py` (5/5 passed), confirming handling of health, readiness, catalogue filtering, leak detection, unconfigured parser graceful handling, and metrics secret leak detection.
- [x] **Local preview rehearsal:** Executed `python api/scripts/verify_preview_deployment.py --api-url http://127.0.0.1:18000 --output-json api/evaluations/runs/preview_smoke_run.json --output-md api/evaluations/runs/preview_smoke_run.md` against an active local preview stack. All 9 active checks passed cleanly with zero failures.
- [x] **Failure injection rehearsal:** Verified via unit tests that draft/needs_review catalogue leaks and metrics credential leaks are detected and fail the run.
- [x] **Documentation review:** Inspected `docs/v2-workstream-9-implementation-plan.md`, `docs/release-candidate-template.md`, `docs/preview-and-release-playbook.md`, and updated `docs/v2-implementation-plan.md` for consistency with all V2 architectural principles.

## Dependencies and environment constraints

- Depends on:
  - Completion of Workstream 0–5, 7, and 8.
  - Existing Alembic migration chain (`20261103_0006`) and seed scripts.
  - Docker Compose and `docker-compose.e2e.yml` configurations.
  - Playwright browser test suite and k6 performance scripts.
  - [Database operations runbook](database-operations-runbook.md) for backup and restore procedures.
- Constraints:
  - Render Free PostgreSQL is disposable; no persistent production data may be deployed to it.
  - Live deployment to Render requires repository connection and dashboard authorization by the repository owner.
  - External setup parser requires OpenAI-compatible provider credentials to validate live parser accuracy; otherwise offline mock verification is utilized.

## Progress

- [x] Review existing V2 roadmap, release confidence workflow, Render configuration, and end-to-end testing plan.
- [x] Author this V2 Workstream 9 implementation plan.
- [x] Update `docs/v2-implementation-plan.md` to reference this plan.
- [x] Implement the preview deployment verification script (`api/scripts/verify_preview_deployment.py`).
- [x] Create the release candidate evaluation record template (`docs/release-candidate-template.md`).
- [x] Document the release deployment, verification, and rollback playbook (`docs/preview-and-release-playbook.md`).
- [x] Add automated tests for the preview verification tool (`api/tests/test_verify_preview_deployment.py`).
- [x] Rehearse preview verification against a local preview stack (`api/evaluations/runs/preview_smoke_run.md`).
- [x] Complete Workstream 9 documentation and update release checklist.

## Verification Evidence and Status

1. **Automated Preview Smoke Verification Suite (`api/scripts/verify_preview_deployment.py`)**:
   - Comprehensive CLI tool supporting `--api-url`, `--web-url`, `--timeout`, `--output-json`, `--output-md`, and `--require-live-parser`.
   - Probes 12 discrete checkpoints across liveness, database readiness, public catalogue verification (zero draft/review leaks), device details, deterministic compatibility evaluation, simultaneous multi-display bandwidth constraints, share link query param restoration, result report ingestion, external AI parser endpoint, observability/metrics sanity, and frontend application shell.
2. **Automated Unit Tests (`api/tests/test_verify_preview_deployment.py`)**:
   - 5 tests covering report serialization, complete mock success path, catalogue draft leak detection, unconfigured external parser graceful degradation, and credential leak detection in Prometheus metrics. All 5 tests passed in 0.11s.
3. **Rehearsal Execution Artifacts (`api/evaluations/runs/preview_smoke_run.json` and `.md`)**:
   - Executed against live FastAPI + SQLite preview service at `http://127.0.0.1:18000`:
     - Liveness: PASS (68.8ms)
     - Readiness: PASS (32.0ms)
     - Catalogue Integrity: PASS (15 laptops, 13 accessories, zero leaks detected)
     - Device Details: PASS (33.7ms)
     - Compatibility: PASS (34.8ms)
     - Multi-Display: PASS (11.1ms)
     - Share Link: PASS (0.1ms)
     - Result Reporting: PASS (47.9ms)
     - Setup Parser: SKIP (28.7ms, provider unconfigured in preview, deterministic engine unblocked)
     - Metrics Exposition: PASS (26.8ms, zero secret leaks)
     - Overall Outcome: PASS (9 passed, 3 skipped, 0 failed).
4. **Operational Playbooks and Templates**:
   - [`docs/preview-and-release-playbook.md`](preview-and-release-playbook.md): Full operational guide covering the 8 technical release gates, automated preview verification, and web/API/database rollback procedures.
   - [`docs/release-candidate-template.md`](release-candidate-template.md): Standardized evaluation template for logging release candidate evaluations, gate verdicts, and formal Go/No-Go decisions.
