# V2 Workstream 10 implementation plan

## Goal

Provide comprehensive contributor documentation and hand-off materials—unifying local developer setup, architectural guidelines, evidence-backed catalogue curation, capability registry extensions, deterministic compatibility rules modification, quality gates, and pull request procedures—so that external maintainers and contributors can autonomously and safely develop, test, and propose changes to PortPilot.

This plan supports [Workstream 10 in the V2 plan](v2-implementation-plan.md#10-contributor-hand-off). It defines the implementation roadmap, document specifications, and hand-off verification criteria.

## Findings and decisions

- **Current documentation baseline:**
  - `README.md` provides high-level system overview, quick-start commands, Docker Compose instructions, and operational notes.
  - Specialized contributor guidance documents exist across `docs/`:
    - [`catalogue-identity-and-evidence.md`](catalogue-identity-and-evidence.md): Requirements for model codes, variants, and evidence citations.
    - [`source-review-playbook.md`](source-review-playbook.md): Procedures for conflict resolution, rechecks, and correction history.
    - [`capability-registry.md`](capability-registry.md): Protocol for extending the typed capability registry in `app/capabilities.py`.
    - [`database-operations-runbook.md`](database-operations-runbook.md): Database migrations, backups, and rollback procedures.
    - [`preview-and-release-playbook.md`](preview-and-release-playbook.md): Pre-release gates, preview verification, and release checklists.
    - [`accessibility-screen-reader-test-plan.md`](accessibility-screen-reader-test-plan.md): Accessibility testing methodology.
- **Identified documentation gaps:**
  - **No root `CONTRIBUTING.md`:** The repository lacks a standard GitHub entry point (`CONTRIBUTING.md`) for new contributors.
  - **Fragmented onboarding path:** A new contributor currently has to discover and stitch together multiple individual markdown files in `docs/` to understand how to propose a catalogue addition, a rule modification, or a schema migration.
  - **Explicit architectural guardrails needed:** PortPilot relies on strict separation of concerns (deterministic rule evaluation vs. natural-language setup interpretation; manufacturer evidence required for published fields; zero guessing). These core principles must be prominent in the contributor onboarding guide so contributors do not introduce speculative heuristic logic or bypass evidence validation.
  - **PR and change submission standards:** Clear pull request templates and conventions (commit message style, pre-submission checklist, evidence verification requirements) need to be documented.
- **Design decisions for Workstream 10:**
  1. Author a comprehensive root [`CONTRIBUTING.md`](../CONTRIBUTING.md) that serves as the single clear front door for all contributors.
  2. Index and integrate the existing specialized playbooks (`source-review-playbook.md`, `capability-registry.md`, `database-operations-runbook.md`, `preview-and-release-playbook.md`) into structured contribution tracks:
     - **Track A: Adding or Updating Device Models** (evidence threshold, model codes, review status).
     - **Track B: Extending Capabilities & Fields** (capability registry, schemas, migrations).
     - **Track C: Modifying Compatibility Rules** (deterministic engine, parameterized tests, explainability).
     - **Track D: Frontend & UX Improvements** (Next.js, Tailwind/CSS, accessibility, mobile layout).
     - **Track E: Tooling, Infrastructure & CI** (Playwright E2E, k6 SLO, preview verification).
  3. Provide a clear Pre-Submission Quality Checklist mapping directly to automated CI checks and quality commands.

## Scope

- [ ] Create the repository root [`CONTRIBUTING.md`](../CONTRIBUTING.md) with comprehensive local setup instructions, architectural principles, contribution tracks, and pull request guidelines.
- [ ] Review and refine existing playbooks ([`source-review-playbook.md`](source-review-playbook.md), [`capability-registry.md`](capability-registry.md), [`catalogue-identity-and-evidence.md`](catalogue-identity-and-evidence.md)) to ensure bidirectional linking and consistency with V2 standards.
- [ ] Document clear change workflows for:
  - Curating exact manufacturer device models with evidence citations.
  - Adding or modifying capabilities in the typed registry.
  - Adding or modifying deterministic rules with parameterized test scenarios.
  - Safely creating and testing database migrations.
- [ ] Establish a Pull Request checklist and review guide covering code formatting, unit tests, secrets audits, and evidence standards.
- [ ] Verify that a contributor following only checked-in documentation can install dependencies, run tests, verify formatting, and run the preview verification tool from a clean checkout.
- [ ] Update `v2-implementation-plan.md` and `README.md` to reference the contributor guide and mark Workstream 10 complete upon verification.

## Sequenced implementation steps

### Step 1: Reconcile and organize contributor documentation assets
- Review existing documentation across `README.md`, `docs/`, and configuration files to catalog all required developer actions, quality commands, and environmental nuances.
- Ensure consistent terminology across all guides (`review_status`: `draft`, `verified`, `needs_review`; `verdict`: `compatible`, `compatible_with_limits`, `incompatible`, `insufficient_data`).

### Step 2: Author the root `CONTRIBUTING.md`
- Draft `CONTRIBUTING.md` at the repository root covering:
  - **Welcome & Core Philosophy:** Deterministic compatibility authority, manufacturer evidence requirement, zero guessing, reviewable and recoverable changes.
  - **Local Development Environment Setup:**
    - Python backend setup with venv, dependencies (`requirements-dev.txt`), and SQLite vs. Compose PostgreSQL.
    - Node.js frontend setup with `npm ci` and `npm run dev`.
    - Docker Compose full-stack startup (`docker compose up --build`).
  - **Contribution Tracks:**
    - *Track 1: Catalogue Curation & Evidence:* Step-by-step instructions for finding manufacturer specifications, extracting model codes, formulating excerpts, adding records to `api/app/seed.py` or via admin API, and resolving duplicate warnings.
    - *Track 2: Capability Registry Extension:* How to add a capability key to `app/capabilities.py`, map publication requirements, configure rule adapters, update SQLAlchemy models and Pydantic schemas, and write migration scripts.
    - *Track 3: Compatibility Rules:* How to modify `app/rules.py`, write parameterized test scenarios in `tests/test_rules.py`, and preserve explainable verdicts (summary, limits, requirements, evidence).
    - *Track 4: Frontend Development & Accessibility:* Working with Next.js, accessibility standards (axe-core, keyboard, ARIA live regions), and responsive mobile layouts.
  - **Quality Gates & Pre-Submission Commands:**
    - Backend linting, formatting, and unit tests (`ruff check`, `ruff format`, `pytest`).
    - Frontend linting, formatting, and type-checks (`npm run lint`, `npm run format:check`, `npm run build`).
    - Playwright browser E2E tests (`npm run build:e2e`, `npm run e2e`).
    - Preview deployment verification (`python scripts/verify_preview_deployment.py`).
  - **Database Migration Guidelines:**
    - Running `alembic revision --autogenerate`.
    - Data safety: avoiding destructive downgrades, preserving pre-migration dumps per `database-operations-runbook.md`.
  - **Pull Request Process:**
    - Branch naming conventions (`feat/`, `fix/`, `docs/`).
    - Commit message style.
    - PR description requirements and review expectations.
    - Zero secrets policy (no API tokens, database connection strings, or private keys).

### Step 3: Align specialized contributor playbooks
- Ensure `docs/source-review-playbook.md`, `docs/capability-registry.md`, and `docs/catalogue-identity-and-evidence.md` cross-reference `CONTRIBUTING.md` and reflect current V2 conventions.
- Verify all file paths, script names, and CLI commands mentioned in contributor docs exist and execute cleanly.

### Step 4: Validate contributor onboarding experience
- Rehearse the contributor onboarding workflow against the checked-in instructions:
  - Verify Python virtual environment setup and dependency installation.
  - Verify execution of quality commands listed in `CONTRIBUTING.md`.
  - Verify execution of test suites (`pytest tests -q`).
  - Verify preview verification CLI execution.

### Step 5: Update project tracking and release checklists
- Update `docs/v2-implementation-plan.md` to reference Workstream 10 completion.
- Update `README.md` to prominently link to `CONTRIBUTING.md`.
- Mark the final item on the V2 Release Acceptance Checklist (`Contributor and source-review guidance supports hand-off`) as completed.

## Acceptance criteria

- [x] A root `CONTRIBUTING.md` exists, providing a complete, self-contained guide for new contributors and maintainers.
- [x] All four primary contribution pathways (catalogue curation, capability extension, rules modification, frontend development) are documented with exact file references and validation steps.
- [x] Architectural principles—including deterministic rule evaluation, manufacturer evidence mandates, and zero guessing—are clearly articulated.
- [x] Quality commands and pre-submission validation gates are clearly documented and match CI workflows.
- [x] All cross-references between `README.md`, `CONTRIBUTING.md`, and `docs/` playbooks are valid and navigable.
- [x] A new developer can set up the project, run test suites, and understand how to propose a change using only repository documentation.

## Verification approach

- [x] **Documentation link and command audit:** Verified all referenced file paths, scripts (`scripts/verify_preview_deployment.py`, `scripts/evaluate_setup_parser.py`), and documentation links in `CONTRIBUTING.md`, `README.md`, and specialized playbooks exist and match repository structure.
- [x] **Workflow verification:** Executed the documented contributor quality commands (`ruff check`, `ruff format --check`, `pytest tests -q`, `npm run lint`, `npm run format:check`, `npm run build`), confirming 100% clean passes.
- [x] **Review against V2 acceptance criteria:** Confirmed that contributor hand-off, source review, and capability extension criteria are fully satisfied.

## Dependencies and environment constraints

- Depends on all prior workstreams (Workstreams 0–9) being finalized so that architectural definitions, capability registries, observability, testing harnesses, and release playbooks are stable and accurately documented.
- No external infrastructure required; relies solely on repository checkouts and standard developer environments.

## Progress

- [x] Review existing contributor documentation assets and identify gaps.
- [x] Author this V2 Workstream 10 implementation plan.
- [x] Author root `CONTRIBUTING.md`.
- [x] Align and cross-link specialized playbooks in `docs/` (`source-review-playbook.md`, `capability-registry.md`, `catalogue-identity-and-evidence.md`, `README.md`).
- [x] Rehearse and verify documented commands and quality gates.
- [x] Update `v2-implementation-plan.md`, `README.md`, and close the V2 release acceptance checklist.

## Verification Evidence and Status

1. **Root Contributor Guide ([`CONTRIBUTING.md`](../CONTRIBUTING.md))**:
   - Comprehensive contributor onboarding document at the repository root.
   - Articulates foundational principles: deterministic rules engine as sole authority, mandatory manufacturer evidence, strict natural-language parser isolation, and typed capability registry.
   - Provides exact virtualenv, SQLite, and Docker Compose setup steps.
   - Establishes 5 structured contribution tracks:
     - Track 1: Catalogue Curation & Evidence (linking [`catalogue-identity-and-evidence.md`](catalogue-identity-and-evidence.md) and [`source-review-playbook.md`](source-review-playbook.md)).
     - Track 2: Capability Registry Extension (linking [`capability-registry.md`](capability-registry.md)).
     - Track 3: Compatibility Rules & Parameterized Tests (`app/rules.py` and `tests/test_rules.py`).
     - Track 4: Frontend & Accessibility (`web/src/`, axe-core, mobile viewports).
     - Track 5: Tooling, Observability & SLO Benchmarks (`verify_preview_deployment.py`, `deterministic-slo-mix.js`).
   - Details database migration procedures and data rollback rules linking [`database-operations-runbook.md`](database-operations-runbook.md).
   - Establishes pull request conventions, verification checklists, and zero-secrets policy.
2. **Cross-Linked Playbooks**:
   - `docs/source-review-playbook.md`, `docs/capability-registry.md`, `docs/catalogue-identity-and-evidence.md`, and `README.md` updated with bidirectional links to `CONTRIBUTING.md`.
3. **Command Verification**:
   - Backend: `ruff check` (passed), `ruff format --check` (29 files formatted), `pytest tests -q` (106 passed).
   - Frontend: `npm run lint` (0 errors), `npm run format:check` (clean), `npm run build` (successful production build).
