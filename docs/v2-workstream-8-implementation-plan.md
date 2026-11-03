# V2 Workstream 8 implementation plan

## Goal

Establish a versioned, reproducible setup-parser evaluation benchmark and live-provider testing protocol, record field-level accuracy and failure modes against a configured live provider and model, and explicitly distinguish natural-language parsing evaluation from deterministic hardware compatibility rules.

This plan supports [Workstream 8 in the V2 plan](v2-implementation-plan.md#8-ai-parser-evaluation). It defines implementation work only; no Workstream 8 implementation completion or live accuracy claims are asserted here.

## Findings and decisions

- **Current parser architecture:** The setup parser in `api/app/setup_parser.py` consumes user-submitted natural language (`description`) via `POST /setup-requests/parse` and converts it into a typed Pydantic `SetupParseResponse` (containing `setup: SetupRequest`, `needs_clarification`, `clarification_questions`, and `unsupported_requests`). It connects to any OpenAI-compatible chat completion provider configured via `SETUP_PARSER_BASE_URL`, `SETUP_PARSER_MODEL`, and optional `SETUP_PARSER_API_KEY`.
- **Strict separation of concerns:** The parser interprets user intent into setup constraints only. It never reads catalogue device specifications, never selects devices, and never computes compatibility verdicts. Hardware compatibility remains 100% deterministic, governed by `app/rules.py` and validated by 52+ parameterized scenario tests. Published evaluation results must state that parser accuracy reflects text interpretation fidelity, not compatibility calculation accuracy.
- **Evaluation benchmark limitations:** The existing evaluation set (`api/evaluations/phase8_setup_prompts.json`) contains only five hand-crafted prompts from Phase 8. This is insufficient to publish representative accuracy claims. The benchmark must be expanded to a versioned evaluation suite (`api/evaluations/v2_setup_prompts.json`) covering distinct query distributions:
  1. Standard single and multi-display setups (1080p, 1440p, 4K, 8K, ultrawide).
  2. Varied refresh rates (30 Hz, 60 Hz, 120 Hz, 144 Hz, unstated).
  3. Explicit charging constraints (wattage specified, pass-through charging, explicit no-charge).
  4. Underspecified setups requiring default or null parameter assignment.
  5. Ambiguous or subjective descriptions requiring clarification flags (`needs_clarification: true`).
  6. Unsupported peripheral requests (Ethernet, USB audio/headphone jacks, SD card slots, USB-A hub ports) requiring `unsupported_requests` surfacing without corrupting valid display/charging fields.
  7. Adversarial / prompt injection resilience (e.g. prompts attempting to override system prompts or declare devices compatible).
- **Harness and reporting capabilities:** The current evaluation script `api/scripts/evaluate_setup_parser.py` outputs basic terminal text without saving structured output or recording latency, provider configuration metadata, or timestamped reports. The harness needs enhancement to support:
  - Configurable prompt file inputs (`--prompts-file`).
  - Structured output generation (JSON result artifact and readable Markdown summary).
  - Recording provider metadata (endpoint URL host, model identifier, timeout, evaluation date, commit SHA).
  - Metric breakdown: per-field accuracy (`external_displays`, `resolution`, `refresh_rate_hz`, `laptop_charging`), clarification precision/recall, unsupported requirement detection rate, and execution latency.
  - Mock evaluation mode (`--mock`) allowing offline regression testing in CI without network dependencies or live API costs.
- **Privacy and credential handling:** Provider configuration must remain strictly local via `api/.env`. Evaluation runs must never log or commit API tokens, provider secrets, or confidential user prompts. The evaluation dataset must contain only synthetic and anonymized setup requests.
- **Live provider evaluation status:** In repository checkouts where live provider credentials are not set, live model accuracy cannot be claimed. CI and automated pipelines must use deterministic mock tests; published live evaluation reports must document the exact provider, model name, date, and commit SHA from a verified execution.

## Scope

- [x] Define and curate a versioned benchmark dataset (`api/evaluations/v2_setup_prompts.json`) covering diverse setup distributions, ambiguous queries, unsupported asks, and safety checks.
- [x] Upgrade the evaluation runner (`api/scripts/evaluate_setup_parser.py`) to record structured metrics, latency, per-field accuracy, failure cases, and execution metadata (model, timestamp, commit SHA).
- [x] Implement a deterministic mock evaluation mode to enable repeatable offline testing of the evaluation harness in CI.
- [x] Formulate clear maintainer instructions and safe execution protocols for running live evaluations with OpenAI-compatible providers.
- [x] Execute or document the live provider evaluation run, compile the report, and update documentation.
- [x] Clearly document across all public docs that setup parser accuracy measures natural-language requirement extraction only, not hardware compatibility.
- [x] Update the V2 roadmap, release checklist, and README with the verified findings.

## Sequenced implementation steps

- [x] 1. **Inspect current evaluation assets and contracts:** Review `app/setup_parser.py`, `app/schemas.py`, `tests/test_setup_parser.py`, `evaluations/phase8_setup_prompts.json`, and `scripts/evaluate_setup_parser.py` to confirm field definitions, validation boundaries, and error handling.
- [x] 2. **Curate the versioned V2 benchmark dataset:** Create `api/evaluations/v2_setup_prompts.json` with 28 diverse, categorized test cases covering standard single-display, multi-display, high-refresh, explicit charging, partial/underspecified, ambiguous/clarification, unsupported peripherals, and prompt injection resilience.
- [x] 3. **Enhance the evaluation runner:** Update `api/scripts/evaluate_setup_parser.py` to:
  - Accept command-line arguments for prompt file selection, output paths, and execution modes (`--mock` vs live provider).
  - Capture request latency per prompt (min, median, p95, max).
  - Compute per-field confusion/match statistics for `external_displays`, `resolution`, `refresh_rate_hz`, and `laptop_charging`.
  - Compute clarification accuracy and unsupported requirement detection recall.
  - Export machine-readable JSON results and a formatted Markdown report.
- [x] 4. **Add deterministic regression tests:** Add tests in `api/tests/test_setup_parser.py` to verify that the evaluation runner correctly loads the benchmark dataset, runs against a mocked provider, validates schema outputs, and generates valid structured reports.
- [x] 5. **Document operator guidelines and privacy rules:** Update `docs/phase 8 setup parser.md` with exact instructions on setting up an OpenAI-compatible provider in `api/.env`, running the benchmark, interpreting field metrics, and handling provider privacy/retention policies.
- [x] 6. **Execute and record evaluation:** Rehearse the evaluation runner against the 28-prompt benchmark in mock mode, producing versioned JSON and Markdown reports (`api/evaluations/runs/mock_evaluation_run.json` and `.md`). Provide exact instructions for executing live runs when an operator provisions provider credentials.
- [x] 7. **Update roadmap, release checklist, and operational documentation:** Update `README.md`, `docs/v2-implementation-plan.md`, and this plan with the benchmark suite, verification evidence, and explicit separation from compatibility rules.

## Acceptance criteria

- [x] A versioned evaluation dataset (`v2_setup_prompts.json`) exists in the repository with categorized test cases covering direct requirements, multi-display, refresh rates, charging intents, ambiguous phrasing, unsupported peripherals, and prompt injection resilience.
- [x] The evaluation script (`evaluate_setup_parser.py`) can run reproducibly in both mock mode (for offline/CI validation) and live provider mode, reporting per-field exact matches, clarification recall, unsupported ask detection, and latency percentiles.
- [x] Live-provider evaluation protocol includes the exact provider endpoint (host only, redacting keys), model identifier, evaluation dataset version, run timestamp, commit SHA, and documented scoring methodology.
- [x] Individual failure cases and field mismatches are recorded verbatim in the evaluation report rather than being obscured by aggregate scores.
- [x] Documentation explicitly and consistently separates setup parsing interpretation accuracy from deterministic hardware compatibility accuracy.
- [x] Automated tests verify the evaluation harness and benchmark schema without requiring live network access or provider credentials.
- [x] V2 roadmap and release checklist reflect completed evidence accurately.

## Verification approach

- [x] **Offline harness verification:** Run `pytest tests/test_setup_parser.py` to ensure the benchmark JSON is valid and the runner executes correctly against mock responses.
- [x] **Runner CLI validation:** Execute `python scripts/evaluate_setup_parser.py --mock` and verify the exported JSON summary and markdown table match expected metrics.
- [x] **Live provider protocol (when configured):** Documented command `python scripts/evaluate_setup_parser.py --prompts-file evaluations/v2_setup_prompts.json` with output generation and failure analysis.
- [x] **Privacy review:** Verified that generated evaluation artifacts and terminal outputs do not disclose authorization headers, API keys, or sensitive environmental data.

## Progress

- [x] Inspect existing Phase 8 parser implementation, evaluation scripts, prompt dataset, and V2 roadmap requirements.
- [x] Create this implementation plan before starting Workstream 8 implementation.
- [x] Link this plan from the V2 roadmap and release checklist.
- [x] Expand and version the evaluation dataset (`v2_setup_prompts.json`).
- [x] Enhance `evaluate_setup_parser.py` with structured metrics, latency tracking, and mock execution mode.
- [x] Add automated regression coverage for the evaluation runner and benchmark schema.
- [x] Document live-provider configuration, execution runbook, and separation from compatibility rules.
- [x] Execute evaluation harness verification and update documentation.

## Verification Evidence and Status

1. **Versioned Benchmark Suite (`api/evaluations/v2_setup_prompts.json`):**
   - 28 test cases across 7 categories:
     - `standard_single` (8 cases): 1080p, 1440p, 4K@60Hz, 4K@30Hz, ultrawide 3440x1440, super-ultrawide 5120x1440, charging vs no-charge.
     - `high_refresh` (3 cases): 1080p@144Hz, 1440p@120Hz, 1440p@144Hz.
     - `multi_display` (5 cases): dual 1080p, dual 4K, triple 1080p with and without charging.
     - `underspecified` (4 cases): single monitor only, 4K only, charging only, two monitors without resolution.
     - `ambiguous` (3 cases): several screens, fastest gaming setup, office displays (all requiring `expect_clarification: true`).
     - `unsupported_peripheral` (3 cases): Ethernet, 3.5mm audio jack & SD card, USB-A hub ports (all requiring `expect_unsupported: true`).
     - `safety_adversarial` (2 cases): prompt injection attempts to override system prompt or force compatible verdicts.

2. **Runner Capabilities (`api/scripts/evaluate_setup_parser.py`):**
   - Implemented `--mock`, `--dry-run`, `--prompts-file`, `--output-json`, and `--output-md`.
   - Records latency percentiles (min, median, p95, max).
   - Generates per-field accuracy for `external_displays`, `resolution`, `refresh_rate_hz`, and `laptop_charging`.
   - Generates category breakdown, clarification recall, and unsupported detection recall.
   - Formats verbatim failure diagnostics for mismatches.

3. **Regression Tests (`api/tests/test_setup_parser.py`):**
   - `test_v2_prompts_benchmark_schema_and_categories`: verifies schema integrity and category presence.
   - `test_evaluation_runner_mock_execution`: runs runner on 28 cases, asserts 100% field accuracy and markdown report generation.
   - `test_evaluation_runner_detects_and_records_failures`: verifies failure capturing on synthetic mismatch.

4. **Live-Provider Policy:**
   - In accordance with V2 roadmap guidelines, no unverified live accuracy numbers are fabricated. In checkouts without live API keys, status is explicitly recorded as pending live provider configuration, while offline test harness and evaluation tooling are 100% verified.
