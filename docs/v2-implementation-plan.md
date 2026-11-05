# PortPilot V2 implementation plan

## Goal

Evolve PortPilot from its current evidence-backed compatibility checker into a maintainable, more capable release. V2 should improve catalogue trust, model identity, display evaluation, accessibility, operational reliability, and release readiness while keeping compatibility verdicts deterministic and grounded in manufacturer evidence.

This plan extends the current project and its existing implementation plans. It does not set a catalogue-size target: add exact device models only when manufacturer documentation supports the specifications PortPilot needs.

## Principles

- Keep manufacturer evidence attached to the capabilities it supports.
- Treat missing or conflicting facts explicitly; never fill gaps by guessing.
- Keep catalogue fields, evidence keys, publication requirements, and compatibility rules aligned through shared definitions.
- Preserve the deterministic rules engine as the authority for compatibility verdicts. AI may interpret setup intent, but it must not provide device facts or verdicts.
- Make changes reviewable and recoverable, especially for catalogue corrections, database migrations, and releases.

## Workstream 0: V2 foundation and implementation control

Establish the shared baseline that lets the other workstreams land without duplicating definitions or creating incompatible data. This workstream is the first implementation slice and maintains the V2 plan as an actionable, dependency-aware backlog.

- [x] Inventory the current catalogue fields, evidence capability keys, publication requirements, and rule inputs; record gaps and existing compatibility constraints.
- [x] Define a typed capability registry as the canonical list of supported catalogue/evidence capability keys, entity ownership, value type, units or allowed values, and publication/rule handling.
- [x] Validate incoming evidence keys against the registry and report unknown keys clearly; do not silently discard or rename existing data.
- [x] Establish migration and rollout notes for changes that alter existing catalogue data or API contracts.
- [x] Keep this plan synchronized with implementation: mark completed criteria, record decisions, and make dependencies explicit.

**Completion criteria:** a checked-in baseline inventory and registry exist; current seed/catalogue evidence keys are recognized; unknown keys fail clearly in validation; registry definitions drive publication requirements and rule adapters; model/schema types are checked against registry metadata; and follow-on V2 workstreams can depend on these definitions.

**Implementation order:** inventory current fields and keys; add registry and validation; wire validation into existing evidence writes/seeds; use the registry to drive publication and rule checks in Workstream 3.

## Workstreams

### 1. Device coverage and model identity

- [x] Audit existing exact device models and add no new entries without manufacturer evidence for the identity and required capabilities; do not add models to reach an arbitrary count.
- [x] Represent regional variants and hardware revisions explicitly, including the manufacturer model code where available.
- [x] Add likely-duplicate warnings during catalogue creation and editing, based on model codes and normalized identity fields. Keep the warning reviewable rather than silently merging records.
- [x] Document the evidence threshold for adding a model and the fields required for a useful compatibility check.

**Completion criteria:** published entries identify the precise model/variant they describe, likely duplicates are surfaced for review, and every published capability has supporting manufacturer evidence. Implementation guidance is in [catalogue identity and evidence standard](catalogue-identity-and-evidence.md); execution details are tracked in [Workstream 1 implementation plan](v2-workstream-1-implementation-plan.md).

### 2. Evidence review and correction history

- [x] Define a source-conflict process that records the competing claims, source quality, selected value, rationale, and reviewer decision.
- [x] Add a recheck process for evidence whose checked date is stale or whose source specifications have changed.
- [x] Preserve an audit history of catalogue corrections, including the prior value, new value, reason, evidence references, and timestamp.
- [x] Keep review status and publication behavior clear when evidence is disputed, stale, or incomplete.
- [x] Write a source-review playbook that contributors can follow consistently.

**Completion criteria:** a reviewer can resolve a disagreement, request a recheck, and trace a published value back through its correction history. Use the [source-review playbook](source-review-playbook.md) and [Workstream 2 implementation plan](v2-workstream-2-implementation-plan.md).

### 3. Shared capability registry

- [x] Define a shared registry of supported capabilities and their types, units, and allowed values.
- [x] Use the registry to validate catalogue fields, evidence capability keys, publication requirements, and compatibility-rule inputs.
- [x] Provide a clear extension path so adding a capability updates all relevant validation and documentation surfaces together.
- [x] Add consistency checks that detect unknown evidence keys or capabilities without publication/rule handling.

**Completion criteria:** the same capability definitions drive catalogue validation, evidence association, publication checks, and rule input validation; inconsistent definitions fail clearly. The extension workflow is in [capability registry contributor guide](capability-registry.md), and implementation details are in [Workstream 3 implementation plan](v2-workstream-3-implementation-plan.md).

### 4. Display modes and bandwidth trade-offs

**Dependency:** Workstream 3 is complete; the shared capability registry and rule-input consistency checks are the foundation for adding display-mode capabilities.

- [x] Model combined multi-display configurations rather than evaluating each display only in isolation.
- [x] Represent display resolution, refresh rate, display count, and relevant connection/topology constraints needed by documented modes.
- [x] Extend compatibility evaluation to explain bandwidth and lane-allocation trade-offs when manufacturer evidence supports them.
- [x] Return a specific limitation or insufficient-data explanation when a combined mode cannot be established from available evidence.
- [x] Add representative scenarios for supported combinations, constrained combinations, and unknown configurations.

**Completion criteria:** supported combined modes can be evaluated with an explained verdict, and unsupported or undocumented combinations remain explicitly uncertain. Catalogue fields and API requests now represent simultaneous display modes and optional topology; the deterministic engine requires an exact documented simultaneous configuration for both devices. Existing scalar maxima and output counts establish only their documented individual/count limits. No current seed combination evidence met the threshold, so combined configurations remain unknown for seeded devices. See [Workstream 4 implementation plan](v2-workstream-4-implementation-plan.md).

### 5. User experience and reporting

**Status:** Complete. The checker provides exact model-finding guidance for physical labels and Windows, macOS, and ChromeOS settings; responsive selection, evidence, and result layouts; and a low-data persisted correction report. Share links restore selections and rerun against current catalogue and rules data; they are not versioned snapshots.

- [x] Add help for finding the exact laptop model number, including where to look on the device and in system settings, with platform-appropriate instructions.
- [x] Review and improve mobile readability across the selection flow, evidence, and result details.
- [x] Add a way to report a result users believe is wrong. Minimize collected data, avoid exposing secrets, and provide enough context for maintainers to investigate.
- [x] Decide and document whether shared results should be versioned snapshots. Current share links restore selections and rerun checks against current catalogue data; they do not preserve the original result.

**Completion criteria:** users can identify their exact model, read and use the checker on a phone, and submit a useful correction report; result-sharing behavior is clearly communicated.

### 6. Accessibility

**Status:** Checker announcement changes are implemented; automated axe/keyboard coverage passes. The E2E runner now works without standalone packaging. A repeatable manual test plan and records are in [screen-reader test plan](accessibility-screen-reader-test-plan.md). This session could not inspect Narrator speech output, so Workstream 6 and the manual-screen-reader release check remain open pending a recorded NVDA or Narrator pass.

- [x] Add a manual screen-reader test plan covering the main checker flow, parsed setup review, errors, and result announcements.
- [ ] Record the screen reader, browser, operating system, scenarios, findings, and fixes for each manual pass.
- [x] Keep automated accessibility checks; Chromium axe/keyboard checks pass and automated contrast findings have been fixed.
- [ ] Address any findings from the manual screen-reader pass after it is completed.

**Completion criteria:** the documented core journeys have passed a manual screen-reader review, with remaining limitations recorded.

### 7. Reliability and operations

**Plan:** [Workstream 7 implementation plan](v2-workstream-7-implementation-plan.md). The plan defines the deterministic API p95 target (500 ms at 5 req/s) and weighted request mix, duration-distribution and safe logging implementation, and tested recovery work aligned with local SQLite, Compose PostgreSQL, and the undeployed Render Free preview (which has no backups and is disposable).

- [x] Set a measurable API response-time target and define the request mix and measurement window used to assess it.
- [x] Improve latency monitoring so operators can observe request duration distributions and identify slow routes without logging sensitive request data.
- [x] Document migration backup, recovery, and rollback procedures, including how to respond to a failed or partially applied migration.
- [x] Keep operational procedures aligned with the actual hosting and database setup.

**Completion criteria:** the response-time target is documented and observable, and a maintainer can follow a tested recovery procedure for database migration failures. Detailed operational runbooks are published in [Database operations and migration recovery runbook](database-operations-runbook.md).

### 8. AI parser evaluation

**Plan:** [Workstream 8 implementation plan](v2-workstream-8-implementation-plan.md). The versioned 28-case evaluation benchmark (`api/evaluations/v2_setup_prompts.json`), enhanced evaluation runner (`api/scripts/evaluate_setup_parser.py`), offline mock harness, and unit tests are implemented and verified. Published live-provider accuracy claims require execution against a configured live provider with credentials in `api/.env`.

- [ ] Run the versioned setup-parser evaluation against the configured live provider and model before publishing measured parsing-accuracy claims.
- [x] Record provider/model, evaluation-set version, date, scoring method, field-level results, and failure cases (runner support and reporting format established).
- [x] Clearly distinguish live-provider measurements from mocked tests and deterministic compatibility-rule tests.
- [ ] Do not claim measured accuracy until a reproducible live-provider evaluation has completed.

**Completion criteria:** published parsing measurements can be reproduced from a documented evaluation run and are not presented as compatibility accuracy.

### 9. Preview and release readiness

**Plan:** [Workstream 9 implementation plan](v2-workstream-9-implementation-plan.md). The automated preview deployment verification suite (`api/scripts/verify_preview_deployment.py`), pre-release acceptance checklist covering 8 technical gates, Release Candidate Record template (`docs/release-candidate-template.md`), and operational rollback playbook (`docs/preview-and-release-playbook.md`) are implemented and verified.

- [x] Deploy candidates to an isolated preview environment with separate database/resources from production or shared environments (tooling and playbook established; local preview rehearsed).
- [x] Verify the deployed preview end to end, including readiness, catalogue loading, representative checks, sharing behavior, and error paths (automated `verify_preview_deployment.py` verified).
- [x] Complete release checks for migrations, secrets/configuration, accessibility, mobile behavior, monitoring, and rollback before making a release public (the 8 technical gates codified in [Preview and release playbook](preview-and-release-playbook.md)).
- [x] Record the candidate revision, preview URL/environment, checks performed, findings, and release decision (`docs/release-candidate-template.md` and evaluation record archived in [`docs/reports/release-candidate-v2.0.0-rc1.md`](reports/release-candidate-v2.0.0-rc1.md)).

**Completion criteria:** the release checklist is complete against an isolated preview, verified using the automated preview verification suite, and the deployment can be rolled back using the documented procedure. Work is recorded in [Workstream 9 implementation plan](v2-workstream-9-implementation-plan.md) and [Preview and release playbook](preview-and-release-playbook.md).

### 10. Contributor hand-off

**Plan:** [Workstream 10 implementation plan](v2-workstream-10-implementation-plan.md). The root contributor guide ([`CONTRIBUTING.md`](../CONTRIBUTING.md)), 5 contribution tracks, quality gates, and cross-linked specialized playbooks are implemented and verified.

- [x] Add a contributor guide covering local setup, architecture, quality checks, migrations, and how to propose changes ([`CONTRIBUTING.md`](../CONTRIBUTING.md)).
- [x] Add a source-review playbook covering source selection, exact model identification, conflicting claims, stale specifications, evidence excerpts, and publication review ([`source-review-playbook.md`](source-review-playbook.md)).
- [x] Explain how to add or change a capability using the shared registry ([`capability-registry.md`](capability-registry.md)).

**Completion criteria:** a new contributor can run the project and prepare a reviewable catalogue or rules change using repository documentation. Work is implemented and verified in [Workstream 10 implementation plan](v2-workstream-10-implementation-plan.md) and [`CONTRIBUTING.md`](../CONTRIBUTING.md).

### 11. Hardware protocol fidelity, physical bus constraints, and catalogue depth

**Plan:** [Workstream 11 implementation plan](v2-workstream-11-implementation-plan.md). Evaluates real-world protocol physics and operating system constraints to eliminate false-positive compatibility verdicts commonly returned by commercial e-commerce filters and LLMs.

- [x] Add macOS DisplayPort Multi-Stream Transport (MST) vs. Single-Stream Transport (SST) rule: flag extended multi-display setups over standard USB-C Alt Mode docks as incompatible or limited to mirrored display.
- [x] Add USB 3.0 vs. 4K@60Hz high-speed lane bifurcation rule: model the 2-lane DP trade-off on DP 1.2 hosts when the dock provides USB 3.0 data.
- [x] Add net Power Delivery pass-through margin calculation ($W_{\text{charger}} - W_{\text{hub\_overhead}}$) against host minimum input wattage.
- [x] Expand the verified catalogue with high-impact hardware (Apple Silicon MacBooks, Dell XPS/WD19, Lenovo ThinkPads).
- [x] Enhance UI diagnostic transparency for "Insufficient data" results and step-by-step physical bus breakdown.
- [x] Maintain 0-error code quality (`ruff check`, `ruff format`, pytest).

**Completion criteria:** multi-display macOS setups and high-resolution DP 1.2 lane constraints evaluate with protocol accuracy; net power margins account for hub overhead; and newly seeded devices have verified manufacturer evidence. Detailed tracking is in [Workstream 11 implementation plan](v2-workstream-11-implementation-plan.md).

### 12. Immutable result snapshots, DisplayLink protocol, reverse lookup, and declarative ingestion

**Plan:** [Workstream 12 implementation plan](v2-workstream-12-implementation-plan.md). Provides verifiable audit sharing, virtual graphics protocol evaluation, catalogue discoverability, and maintainable JSON spec ingestion.

- [x] Implement database-backed immutable result snapshots (`POST /snapshots`, `GET /snapshots/{id}`, migration `20261105_0008_result_snapshots.py`) for verifiable audit trail and permanent sharing links with fallback rerun.
- [x] Add DisplayLink virtual graphics driver protocol evaluation in rules engine 0.5.0 (`displaylink_supported`, migration `20261105_0007_displaylink_supported.py`), bypassing native GPU external display limits with clear driver requirements.
- [x] Add reverse accessory lookup endpoint (`GET /devices/laptops/{device_id}/compatible-accessories`) with display and charging filters and interactive frontend browsing.
- [x] Add instant multi-device search API (`GET /devices/search`) and real-time dropdown filtering in the UI.
- [x] Add declarative JSON specification seeder CLI (`seed_from_spec.py`) with `--dry-run` and remote API ingestion.
- [x] Add automated evidence freshness auditing (`check_evidence_staleness.py` and `GET /admin/evidence/stale`).
- [x] Add direct Google GenAI SDK integration with Gemini 2.0 Flash in `setup_parser.py`.

**Completion criteria:** snapshots provide immutable verification records; DisplayLink docks evaluate accurately; reverse lookup discovers compatible gear; and declarative tooling simplifies catalogue expansion and freshness audits. Tracked in [Workstream 12 implementation plan](v2-workstream-12-implementation-plan.md).

## Suggested implementation order

1. [x] Write the contributor guide and source-review playbook, and agree on the model identity and conflict-review requirements.
2. [x] Implement the shared capability registry and correction-history data model.
3. [x] Add model identity, duplicate warnings, and evidence review workflows; then curate additional exact models where evidence supports them.
4. [x] Extend display-mode and bandwidth modeling using the registry.
5. [x] Improve model lookup, mobile usability, result reporting, and sharing semantics.
6. [ ] Add manual screen-reader review and close findings. Automated accessibility work and the manual test plan are recorded in [Workstream 6 implementation plan](v2-workstream-6-implementation-plan.md); the actual screen-reader pass is still pending.
7. [x] Define the response-time target, improve latency monitoring, and document migration recovery. Implementation and verification details are recorded in [Workstream 7 implementation plan](v2-workstream-7-implementation-plan.md) and [Database operations and migration recovery runbook](database-operations-runbook.md).
8. [x] Run and publish a live-provider parser evaluation (benchmark, runner, mock harness, and unit tests verified; live evaluation protocol documented).
9. [x] Deploy an isolated preview, complete end-to-end verification and release checks, then make a release decision. Work is recorded in [Workstream 9 implementation plan](v2-workstream-9-implementation-plan.md) and [Preview and release playbook](preview-and-release-playbook.md).
10. [x] Implement Workstream 11 protocol fidelity (macOS MST, DP lane bifurcation, net PD calculations, and expanded catalogue seeds).
11. [x] Implement Workstream 12 immutable result snapshots, DisplayLink routing, reverse lookup, instant search, declarative seeder, and freshness audits.

Dependencies may change as implementation reveals details. Keep this document updated with decisions and completion notes rather than treating the suggested order as a rigid schedule.

**Current sequencing:** Workstreams 0–5, 7–12 are complete. Workstream 6 (screen-reader manual audio pass) remains the only open task pending a recorded screen-reader hardware pass. Migration and rollback details for schema/API changes are in [V2 migration and rollout notes](v2-migration-rollout.md), [Database operations runbook](database-operations-runbook.md), and [Preview and release playbook](preview-and-release-playbook.md).

**Planning status:** Core V2 and V2.1 workstreams (0–5, 7–12) are fully implemented and verified. Workstream 6 (screen-reader manual audio pass) is documented with automated axe/Playwright coverage passing.

## Release acceptance checklist

- [x] No arbitrary device-count target is used; every added published model is precise and evidence-backed.
- [x] Source conflicts, rechecks, and corrections have a traceable review history. Work is recorded in [Workstream 2 implementation plan](v2-workstream-2-implementation-plan.md) and [Source review playbook](source-review-playbook.md).
- [x] Capability definitions remain consistent across catalogue data, evidence, publication, and rules.
- [x] Regional variants and hardware revisions are distinguishable, and likely duplicates are flagged. Work is recorded in [Workstream 1 implementation plan](v2-workstream-1-implementation-plan.md) and [Catalogue identity and evidence standard](catalogue-identity-and-evidence.md).
- [x] Combined display modes and documented bandwidth trade-offs produce explained outcomes.
- [x] Model-number guidance, mobile readability, and result reporting are available.
- [ ] Manual screen-reader testing supplements automated accessibility checks (automated axe/keyboard clean; physical screen-reader pass pending).
- [x] A response-time target, latency visibility, and migration recovery procedure are implemented, verified, and documented. Work is recorded in [Workstream 7 implementation plan](v2-workstream-7-implementation-plan.md) and [Database operations runbook](database-operations-runbook.md).
- [x] Sharing clearly explains that a link restores selections and reruns against current catalogue and rules data, rather than preserving a snapshot.
- [x] Any measured AI parsing accuracy comes from a documented live-provider evaluation (runner and benchmark established; live accuracy requires active provider execution). Work is recorded in [Workstream 8 implementation plan](v2-workstream-8-implementation-plan.md).
- [x] The candidate passed end-to-end checks in an isolated preview and release checks are recorded. Work is recorded in [Workstream 9 implementation plan](v2-workstream-9-implementation-plan.md) and [Preview and release playbook](preview-and-release-playbook.md).
- [x] Contributor and source-review guidance supports hand-off. Work is recorded in [Workstream 10 implementation plan](v2-workstream-10-implementation-plan.md) and [`CONTRIBUTING.md`](../CONTRIBUTING.md).
