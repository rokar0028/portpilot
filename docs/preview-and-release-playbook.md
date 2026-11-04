# Preview and Release Playbook

This playbook defines how to provision an isolated preview environment, evaluate a candidate release against all technical quality gates, verify live services non-destructively, make an evidence-backed release decision, and roll back safely if an issue arises.

It operationalizes [Workstream 9](v2-workstream-9-implementation-plan.md) and aligns with PortPilot's architectural principles and [Database operations runbook](database-operations-runbook.md).

---

## 1. Preview Architecture and Environment Isolation

PortPilot supports two isolated preview mechanisms. Production or shared databases must **never** be used for preview validation, test data seeding, or failure rehearsal.

### Option A: Render Cloud Preview (`render.yaml`)

- Provisions an isolated stack on Render:
  - `portpilot-api`: Python 3.14/FastAPI web service running Uvicorn.
  - `portpilot-web`: Node.js 20 Next.js standalone web service.
  - `portpilot-db`: PostgreSQL 16 database.
- **Environmental Constraints (Render Free):**
  - Render Free PostgreSQL expires after 30 days and provides **no automated backups** or point-in-time recovery.
  - Free web services sleep after 15 minutes of inactivity (causing cold-start delays on initial requests).
  - Treat Render Free strictly as a **disposable preview** environment. Storing persistent user data or relying on it as a production host is prohibited until upgraded to a durable plan.
- **Configuration & Secrets:**
  - `DATABASE_URL` is bound automatically by Render from the database instance.
  - `FRONTEND_ORIGIN` is dynamically bound to `portpilot-web`'s `RENDER_EXTERNAL_URL`.
  - `NEXT_PUBLIC_API_URL` is dynamically bound to `portpilot-api`'s `RENDER_EXTERNAL_URL`.
  - `ADMIN_API_TOKEN` is generated dynamically using `generateValue: true`.

### Option B: Isolated Containerized Preview (`docker-compose.e2e.yml`)

- Runs locally or on staging runners:
  - Isolated PostgreSQL container on a dynamic host port.
  - Fresh Alembic migration (`alembic upgrade head`) and seed execution (`python -m app.seed`).
  - Standalone Next.js production build (`npm run build:e2e`).
  - Isolated database `portpilot_e2e` destroyed upon test completion.

---

## 2. Pre-Release Verification Protocol (The 8 Technical Gates)

Before deploying a candidate release to production or publishing release claims, the candidate commit SHA must pass all eight gates:

### Gate 1: Code Quality and Build
Run in `api/`:
```bash
ruff check app migrations tests scripts
ruff format --check app migrations tests scripts
python -m pytest tests -q
```
Run in `web/`:
```bash
npm run lint
npm run format:check
npm run build
```
*Criteria:* 100% test pass (zero errors), clean formatting, and production build succeeds without warnings.

### Gate 2: Cross-Browser & E2E Verification
Trigger the GitHub Actions workflow `.github/workflows/release-confidence.yml` with the candidate commit SHA, or execute Playwright locally across Chromium, Firefox, and WebKit:
```bash
cd web
npm run build:e2e
npx playwright test --project=chromium --project=firefox --project=webkit
```
*Criteria:* All critical user journeys (model selection, check execution, result display, share link copy, coverage view) pass across all three rendering engines.

### Gate 3: Performance & Reliability SLO
Execute the deterministic k6 SLO test against seeded PostgreSQL:
```bash
cd api
k6 run --summary-export=k6-summary.json -e WARMUP_DURATION=10s -e STEADY_STATE_DURATION=60s perf/deterministic-slo-mix.js
```
*Criteria:*
- Server-observed p95 response duration $\le 500$ ms at 5 req/s.
- 0.00% HTTP 5xx error rate on deterministic endpoints.
- Database outage recovery verified: `GET /ready` returns HTTP 503 during outage and recovers to HTTP 200 upon database restart.

### Gate 4: Database Migrations & Backup Verification
Follow the preflight steps in [Database operations runbook](database-operations-runbook.md):
- Confirm current database revision equals `alembic heads` (`alembic current`).
- Ensure pre-deployment database dump is taken and tested before applying new migrations.
- Verify downgrade consequences: confirm that if a rollback is needed, the pre-migration backup restore is executed rather than a destructive downgrade that drops review history or capability data.

### Gate 5: Security and Secrets Audit
- Verify that `ADMIN_API_TOKEN`, database passwords, and external API keys are not present in git history or committed `.env` files.
- Inspect the frontend build output (`web/.next/static`) to ensure no sensitive environment variables leaked into client bundles (only `NEXT_PUBLIC_API_URL` permitted).
- Check `GET /metrics` and API logs to ensure no authorization headers, bearer tokens, or database connection strings are exposed.

### Gate 6: Accessibility & Screen Reader Audit
- Verify automated axe-core scans pass cleanly with zero critical or serious accessibility violations.
- Review or conduct the manual screen-reader test protocol documented in [Accessibility Screen-Reader Test Plan](accessibility-screen-reader-test-plan.md) covering device selectors, live region announcements, and result cards.

### Gate 7: Mobile Viewport & Responsive Usability
- Test candidate UI in mobile viewports (320px, 375px, 414px) using Chrome DevTools or physical mobile devices.
- Confirm that:
  - Model finding instructions are readable and collapsible.
  - Result cards and evidence lists do not produce horizontal page scroll.
  - Interactive touch targets are at least $44 \times 44$ px.

### Gate 8: AI Parser Evaluation
- Validate setup parser benchmark results:
  - Run `python api/scripts/evaluate_setup_parser.py --mock` for offline regression verification.
  - If live AI provider credentials are configured, execute `python api/scripts/evaluate_setup_parser.py --prompts-file api/evaluations/v2_setup_prompts.json` and attach the generated evaluation run artifact.
  - If live provider credentials are not configured in the preview environment, confirm that documentation clearly disclaims live parser accuracy while maintaining that deterministic compatibility rules remain 100% verified.

---

## 3. Automated Live Preview Deployment Verification

Once the candidate is deployed to an isolated preview environment, execute the non-destructive smoke verification script:

```bash
# Basic API-only verification
python api/scripts/verify_preview_deployment.py \
  --api-url https://portpilot-api-preview.onrender.com \
  --output-json preview_verification_report.json \
  --output-md preview_verification_report.md

# Full API + Web preview verification
python api/scripts/verify_preview_deployment.py \
  --api-url https://portpilot-api-preview.onrender.com \
  --web-url https://portpilot-web-preview.onrender.com \
  --output-json preview_verification_report.json \
  --output-md preview_verification_report.md
```

### What the Verification Script Probes:
1. **Liveness (`GET /health`):** Confirms FastAPI process is responsive.
2. **Readiness (`GET /ready`):** Confirms database connectivity.
3. **Catalogue Integrity (`GET /devices`):** Verifies laptop and accessory models are loaded with populated manufacturer evidence. Strictly checks that zero unverified, draft, or `needs_review` models leak into public endpoints.
4. **Device Details (`GET /devices/{category}/{id}`):** Verifies detailed device endpoints return valid schemas.
5. **Deterministic Compatibility (`POST /checks`):** Executes representative compatibility evaluation and checks verdict, explanation, requirements, and evidence fields.
6. **Simultaneous Multi-Display Evaluation:** Submits dual-display setup request to confirm multi-monitor bandwidth/lane rule handling.
7. **Share Link Query Parameter Contract:** Validates `?laptop={id}&accessory={id}` parameter reconstruction.
8. **Result Reporting (`POST /result-reports`):** Ingests a safe synthetic result report.
9. **Setup Parser Probe (`POST /setup-requests/parse`):** Probes the natural language parser endpoint; if provider is unconfigured, records an informative skip without breaking deterministic gates.
10. **Observability & Metrics (`GET /metrics`):** Validates Prometheus metrics exposition and verifies absence of credential leaks.
11. **Frontend Smoke (`GET /` & `GET /coverage`):** Validates HTML markup, branding, and coverage page response.

The script exits with code `0` on a complete pass or code `1` if any critical gate fails.

> [!NOTE]
> **Automated CI Enforcement:**
> In addition to manual execution against cloud previews, `verify_preview_deployment.py` is integrated directly into `.github/workflows/ci.yml` and `.github/workflows/release-confidence.yml` during containerized E2E jobs. Every pull request and release confidence run automatically executes all 11 technical gate probes, writes structured JSON/Markdown reports to `$GITHUB_STEP_SUMMARY`, and uploads report artifacts before browser journeys run.

---

## 4. Go / No-Go Decision Framework

Record all findings in a copy of [`docs/release-candidate-template.md`](release-candidate-template.md) and archive the completed record and artifacts in `docs/reports/` (e.g. [`docs/reports/release-candidate-v2.0.0-rc1.md`](reports/release-candidate-v2.0.0-rc1.md)).

### Hard Blocker Criteria (Mandatory NO-GO):
- Any failure in Gates 1, 2, 4, or 5.
- Failure of `GET /ready` or inability of the database to recover from interruption.
- Leakage of `draft` or `needs_review` catalogue entries into public endpoints.
- Secret or credential exposure in metrics, logs, or client-side JavaScript bundles.
- Fatal crash or unhandled 500 error during `POST /checks`.

### Permissible Informational Warnings:
- Setup parser offline in disposable preview (permitted if live provider credentials are intentionally omitted in preview, provided offline mock tests passed).
- Minor cosmetic or text formatting improvements not impacting accessibility or core workflows.

---

## 5. Deployment Rollback & Disaster Recovery

If an issue is discovered during or after preview verification:

### Web / API Service Rollback:
- **On Render:**
  1. Open the Render Dashboard for `portpilot-api` / `portpilot-web`.
  2. Under the **Deploys** tab, locate the prior stable deploy.
  3. Click **Rollback to this deploy**.
- **In Containerized Staging:**
  1. Point deployment orchestration or `docker-compose.yml` image tags back to the prior stable commit SHA.
  2. Run `docker compose up -d --build`.

### Database Recovery & Rollback:
- Consult the [Database operations runbook](database-operations-runbook.md#5-migration-failure-and-rollback-runbook).
- **CRITICAL:** Do **not** run `alembic downgrade -1` if the migration involved destructive schema changes or dropped capability tables.
- Instead, perform a clean restore from the pre-deployment database dump:
  ```bash
  # Example for Compose PostgreSQL:
  docker compose exec -T db dropdb -U portpilot portpilot
  docker compose exec -T db createdb -U portpilot portpilot
  docker compose exec -T db pg_restore -U portpilot -d portpilot /backups/pre_deploy_backup.dump
  ```
- Verify recovery:
  ```bash
  curl -fsS http://localhost:8001/ready
  curl -fsS http://localhost:8001/devices
  ```
