# PortPilot — Phase 8 Implementation Plan

## Goal

Let a user describe the setup they want in plain language, review and correct the extracted requirements, and submit those requirements to PortPilot's existing deterministic compatibility checker. The model only interprets requested setup intent; it never chooses devices, supplies device capabilities, or returns a compatibility verdict.

## Scope and architecture

- Use one typed `SetupRequest` contract for manual checks and parsed setup results. Its nullable fields represent explicitly unknown requirements; a review-ready request may be corrected before submission.
- Add `POST /setup-requests/parse`. A provider adapter uses a configurable OpenAI-compatible chat-completions endpoint, model, optional API key, and timeout. No provider SDK is required. Provider access is disabled unless configured.
- Ask the provider for JSON matching the setup contract plus clarification/unsupported-request metadata. Validate it locally, reject malformed or out-of-range values, and never treat model prose as trusted instructions.
- Keep the manual selectors usable at all times. Parsed values populate the same selectors; the user must explicitly confirm review before submitting a compatibility check.
- Unknown requirements are represented as null and cause the rules engine to report insufficient data if they are required. Ambiguous or unsupported requests return explicit clarification metadata; provider/configuration failures return safe, actionable API errors.
- Send only the user's setup description to the configured provider. Do not include device IDs, catalogue records, evidence, account identifiers, or compatibility results. Do not log prompt text or provider response content.
- Add deterministic tests with a mocked provider, and a small versioned evaluation set with field-level expected values and an evaluation report. Evaluation measures parsing only; compatibility remains separately tested by the existing rules suite.

## Ordered work plan and progress

1. [x] Inspect Phase 8 requirements, Phase 7 decisions, current schemas, API/rules flow, frontend manual form, dirty working tree, and available dependency paths.
2. [x] Create this implementation plan before code changes.
3. [x] Add the shared typed setup-request contract, provider configuration/adapter, parse endpoint, bounded failures, and rules behavior for unknown fields.
4. [x] Add a reviewable natural-language input flow that fills the existing manual selectors and retains manual fallback.
5. [x] Add focused parsing tests and a small prompt evaluation set/report.
6. [x] Document provider configuration, privacy behavior, limitations, and test/evaluation commands.
7. [x] Run focused Phase 8 tests and appropriate available checks; record unavailable checks and finish status here.

## Acceptance criteria

- Manual check input and parsed output use the same typed setup contract.
- An unconfigured or unavailable provider does not break manual compatibility checks.
- The parse API validates model output and explicitly exposes unknown fields, clarification needs, unsupported asks, and provider failures.
- The frontend displays editable requirements and does not check automatically after parsing.
- The model receives no device specifications and cannot influence verdict generation.
- Focused tests cover valid, ambiguous/unknown, malformed, unsupported, provider-unavailable, and prompt privacy behavior.
- A repeatable, small evaluation set and report show per-field parsing results and failure cases without claiming compatibility accuracy.

## Privacy and provider behavior

The provider URL, model name, API key, and timeout are environment configuration (`SETUP_PARSER_BASE_URL`, `SETUP_PARSER_MODEL`, `SETUP_PARSER_API_KEY`, `SETUP_PARSER_TIMEOUT_SECONDS`). The API key is optional for local compatible endpoints. The parser submits only the natural-language setup text. Operators must review the selected provider's retention and processing terms before enabling it. PortPilot does not promise provider-side deletion or zero retention. Parsing is optional and should be disabled by leaving the endpoint/model unset. Manual selection remains available.

## Evaluation approach

Maintain a compact JSON fixture set with direct, underspecified, ambiguous, and unsupported requests. Compare each extracted known field with the expected field value, count unknown/clarification behavior, and separately record invalid or unsafe inference. Report the denominator per field, exact-match rate, and notable errors. Keep deterministic mock-provider tests as the CI-stable behavioral gate; live-provider evaluation is opt-in and is not a deployment gate.

## Progress notes

- Repository already has a manual `Setup` schema and deterministic `/checks` endpoint. Current rules consume complete numeric/boolean setup fields, so nullable requirements need explicit unknown handling.
- The frontend already controls all manual fields and share URLs; Phase 8 will layer parsing on top of these controls.
- `api/.venv` contains only pip under Python 3.14.5. No installed FastAPI/pytest or cached package artifacts were found in the inspected local pip cache. Check system Python/other approved environments before deciding test availability; do not attempt network installs.
- The system Python 3.14.5 environment already contains the required runtime/test packages and Ruff; no package installation was attempted.
- Implemented `SetupRequest`, `POST /setup-requests/parse`, an OpenAI-compatible standard-library provider adapter, explicit bounded provider errors, and unknown-aware rules. Parser output must include every requirement field; unknown intent is represented by explicit null values.
- Added a natural-language input, editable review state, and explicit review confirmation to the existing setup form. Parsing does not trigger `/checks`; manual selectors remain usable when parsing is disabled or fails.
- Added five evaluation prompts and an opt-in live evaluation script. A provider is not configured here, so no live model accuracy is claimed. See [the parser guide](phase%208%20setup%20parser.md).
- Verification: all 81 API tests pass; Ruff check passes for Phase 8 and directly affected API files; Ruff formatting check passes for the new/modified files other than `main.py` (whose existing untouched sections have formatting drift); frontend ESLint and `npx tsc --noEmit` pass. No live-provider evaluation was run.

Current status: Phase 8 local implementation and deterministic verification are complete. Live-provider evaluation remains unmeasured until an operator configures a provider and runs the documented opt-in evaluation.
