# Release Candidate Evaluation Record

- **Release Candidate Version / Tag:** `v2.0.0-rcX`
- **Candidate Commit SHA:** `<git-commit-sha>`
- **Evaluation Date & Time (UTC):** `YYYY-MM-DDTHH:MM:SSZ`
- **Lead Evaluator / Maintainer:** `@<username>`
- **Target Preview Environment:** `Render Preview` / `Local Isolated Container Preview`
  - **API Preview URL:** `https://portpilot-api-<hash>.onrender.com` (or `http://127.0.0.1:18000`)
  - **Web Preview URL:** `https://portpilot-web-<hash>.onrender.com` (or `http://127.0.0.1:13000`)
  - **Database Instance:** Isolated PostgreSQL 16 (disposable preview)

---

## Technical Gates Evaluation

| # | Gate Name | Required Criteria | Result | Notes & Artifacts |
|---|---|---|:---:|---|
| **1** | **Code & Quality** | `ruff check`, `ruff format --check`, backend pytest (100% pass), `npm run lint`, `npm run format:check`, `npm run build` | `[PASS / FAIL]` | Clean codebase baseline |
| **2** | **Cross-Browser & E2E** | Playwright test suite passes in Chromium, Firefox, WebKit (`.github/workflows/release-confidence.yml`) | `[PASS / FAIL]` | Browser compatibility confirmed |
| **3** | **Performance & Reliability SLO** | Deterministic API p95 $\le 500$ ms at 5 req/s over 30-min window against seeded PostgreSQL; `/ready` returns 503 during DB outage and recovers | `[PASS / FAIL]` | SLO baseline recorded |
| **4** | **Database & Migrations** | Alembic current equals head revision; pre-migration dump verified; rollback consequence reviewed per `database-operations-runbook.md` | `[PASS / FAIL]` | No destructive unrecoverable migrations |
| **5** | **Security & Secrets** | Zero secrets in git history; zero credentials in `.next/static` bundles; no credentials logged in `/metrics` or slow-request logs | `[PASS / FAIL]` | Clean secrets audit |
| **6** | **Accessibility & Screen Reader** | Automated axe-core clean; manual screen-reader test protocol completed or documented limitations noted (`accessibility-screen-reader-test-plan.md`) | `[PASS / FAIL]` | Screen reader announcement verified |
| **7** | **Mobile & Responsive** | Responsive layouts verified across 320px, 375px, 768px viewports; touch targets $\ge 44 \times 44$ px; zero horizontal overflows | `[PASS / FAIL]` | Mobile readability confirmed |
| **8** | **AI Parser Evaluation** | 28-prompt benchmark run recorded (`v2_setup_prompts.json`); mock mode verified; live provider claims documented or explicitly disclaimed if offline | `[PASS / FAIL]` | Text parsing strictly separated from deterministic compatibility |

---

## Deployed Preview Verification Smoke Log

```text
# Command executed:
python api/scripts/verify_preview_deployment.py --api-url <API_URL> --web-url <WEB_URL> --output-json <report.json> --output-md <report.md>
```

- **Checks Run:** `<total>`
- **Passed:** `<passed>`
- **Failed:** `<failed>`
- **Skipped:** `<skipped>` (e.g. external AI provider if offline in preview)
- **Preview Verification Outcome:** `[PASS / FAIL]`

---

## Discovered Anomalies & Findings

1. *None / list any observed warnings, latency spikes, or cosmetic layout defects.*

---

## Formal Release Decision

- **Recommendation:** `[GO / NO-GO]`
- **Decision Rationale:**
  - *Summary of gate evaluation and verification confidence.*
- **Sign-off By:** `@<evaluator>` on `<date>`
