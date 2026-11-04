# Changelog

All notable changes to the PortPilot project are documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

---

## [2.0.0] - 2026-11-04

### Overview
PortPilot v2.0.0 represents a major milestone, transforming PortPilot from a prototype checker into a production-grade, evidence-backed hardware compatibility platform. All compatibility verdicts remain 100% deterministic, grounded in verifiable manufacturer documentation with strict separation from natural language setup parsing.

### Highlights
- **Canonical Capability Registry:** Governs all hardware specifications, publication criteria, and rule engine inputs across laptops and accessories.
- **Traceable Manufacturer Evidence & Review System:** Full audit tracking of source citations, excerpts, conflict resolutions, and duplicate warning detection.
- **Advanced Display Mode & Topology Modeling:** Deterministic evaluation of simultaneous multi-monitor setups, DisplayPort Alt Mode bandwidth, and resolution matching (including 4K, 5K, and 6K Retina aliases).
- **Automated Preview Deployment Verification:** Non-destructive 11-gate verification suite integrated into CI workflows with automated GitHub Step Summary reporting.
- **Screen-Reader & ARIA Contract Test Suite:** Automated 5-scenario Playwright E2E suite guaranteeing live region announcements, heading hierarchies, error alerts, and focus management.
- **Catalogue Expansion:** Curated high-demand devices including the Apple MacBook Air 13-inch (M2, 2022) with 100% verified manufacturer evidence.

---

### Added

#### Core Engine & Capabilities
- **Capability Registry (`api/app/capabilities.py`):** Central source of truth defining owner entities, data types, units, required fields, and rule mappings.
- **Simultaneous Display Modeling:** Evaluates aggregate display topology, DisplayPort lane limits, and manufacturer-documented multi-monitor modes without guessing.
- **Resolution Alias Normalization:** Added native support for `4K`, `UHD`, `1440p`, `1080p`, `5K` (`5120x2880`), and `6K` (`6016x3384`).
- **Catalogue Admin & Evidence API:** Endpoints for creating/updating devices, logging evidence conflicts, resolving discrepancies, and inspecting stale records with admin authentication.

#### Device Catalogue
- **Apple MacBook Air 13-inch (M2, 2022) (`A2681`):** Complete verified hardware profile with official Apple citations, 2x Thunderbolt/USB 4 ports, 6K single external display limit, and 30W-67W charging specifications.
- **Curated Verified Devices:** 16 verified laptops and 15 accessories with exact manufacturer model codes and capability-specific evidence excerpts.

#### Accessibility & Frontend
- **ARIA Live Region Announcements:** Polite live announcements for setup interpretation progress, check completion verdicts, and status updates (`.sr-only[role="status"][aria-live="polite"]`).
- **Screen-Reader Contract Test Suite (`web/e2e/accessibility-contracts.spec.ts`):** 5 automated scenarios validating page landmarks, model code distinction in selects, review confirmation gating, error alerts, and 360px keyboard navigation.
- **Automated Axe-Core Audits:** Zero WCAG 2.1 A/AA violations across `/` and `/coverage`.
- **Responsive Mobile Layouts:** Collapsible setup disclosures, zero horizontal overflow at 320px/360px viewports, and compliant touch targets ($\ge 44 \times 44$ px).
- **Share Link Query Parameter Contract:** URL sharing via `?laptop={id}&accessory={id}&displays={n}&resolution={res}&refresh={hz}` that transparently restores user selections and reruns checks without preserving stale snapshots.

#### Quality, CI & Tooling
- **CI Preview Verification (`.github/workflows/ci.yml`, `release-confidence.yml`):** Automatically boots isolated preview services in containerized E2E jobs and executes `verify_preview_deployment.py` to enforce all 11 technical gates.
- **Workflow Step Summaries:** Directly renders verification markdown tables and latency diagnostics into GitHub Actions run summaries.
- **Optimized Server Lifecycle:** Configured Playwright `reuseExistingServer: true` to eliminate redundant server spin-ups.
- **Structured Release Reports (`docs/reports/`):** Permanent audit archive storing release candidate evaluation records, smoke test logs, and raw probe JSON outputs.

---

### Changed
- Replaced ambiguous option text with model codes (`{brand} {name} · {model_code}`) to prevent misidentification of regional variants.
- Darkened text colors in result metadata, evidence headers, and requirement labels to exceed WCAG AA contrast thresholds.
- Isolated unverified draft records (`needs_review`) so they are suppressed from public `/devices` endpoints while remaining inspectable via Admin APIs.
- Migrated Playwright test runner to dynamically resolve Windows venv Python paths and enforce `FRONTEND_ORIGIN` CORS bindings.

---

### Fixed
- Fixed URL parameter reconstruction where complex query strings could fail to restore secondary setup inputs.
- Resolved race conditions in asynchronous setup parsing and older response handling.
- Corrected Starlette test client deprecation warnings and improved error boundaries for offline AI provider fallbacks.

---

### Documentation & Runbooks
- **[`CONTRIBUTING.md`](CONTRIBUTING.md):** Comprehensive contributor guide outlining local setup, architecture principles, and 5 clear contribution tracks.
- **[`docs/preview-and-release-playbook.md`](docs/preview-and-release-playbook.md):** 8 technical gates, disposable preview isolation rules, automated smoke verification, and disaster rollback runbooks.
- **[`docs/database-operations-runbook.md`](docs/database-operations-runbook.md):** Pre-deployment backup procedures, non-destructive migration policies, and database outage recovery.
- **[`docs/source-review-playbook.md`](docs/source-review-playbook.md):** Protocol for selecting manufacturer sources, resolving conflicting claims, and auditing stale specs.
- **[`docs/accessibility-screen-reader-test-plan.md`](docs/accessibility-screen-reader-test-plan.md):** Manual screen-reader verification protocol and automated testing logs.
- **[`docs/reports/release-candidate-v2.0.0-rc1.md`](docs/reports/release-candidate-v2.0.0-rc1.md):** Formal Release Candidate Evaluation Record with verified **GO** decision.
