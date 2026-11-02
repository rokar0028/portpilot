# PortPilot — Phase 6 Implementation Plan

## Goal

Increase confidence in PortPilot's decisions and make its catalogue boundaries visible. Expand device coverage only when exact-model manufacturer evidence supports the published fields; never fill the target count by inference.

## Starting point

- Phase 5 is marked complete. The single-page checker supports shareable URLs and has an inline glossary.
- The seed contains 15 laptops and 15 accessories; public catalogue endpoints expose verified records only.
- The deterministic evaluator covers connection, video, display count and mode, charging, unknown data, and verdict precedence.
- The Phase 5 plan records 48 passing API tests. The Phase 6 roadmap calls for 50 compatibility-engine scenarios, desktop/mobile browser journey coverage, a public coverage and limitations page, and a review of every compatible verdict.
- There is no dedicated public page summarizing catalogue coverage, evidence policy, and supported scope.

## Plan review

- Keep the deterministic evaluator and its fail-closed handling of unknown specifications as the release's trust boundary.
- Count distinct compatibility scenarios, including parametrized cases, rather than relying on the total API suite count to satisfy the 50-rule-scenario target.
- Audit all seeded, verified device capabilities and all possible `compatible` verdict paths for evidence alignment before adding products.
- Add catalogued devices only where primary manufacturer sources identify the exact model/variant and substantiate each populated field. Retain unknown values when source material is incomplete.
- Build a public coverage page from the live verified catalogue where practical, and explain the evidence policy and limits in user-facing language.
- Treat browser journey checks and final verification as explicit remaining work; do not claim Phase 6 complete until every acceptance criterion has evidence.

## Work plan

### 1. Strengthen compatibility-rule coverage

- [x] Inventory existing evaluator tests and count distinct scenario cases.
- [x] Add focused boundary and missing-data scenarios until there are at least 50 compatibility-engine scenarios.
- [x] Cover all verdicts, display mode parsing/bounds, display counts, charging thresholds, optional requirements, malformed/unknown values, and failure/unknown precedence.
- [x] Review each `compatible` result path to ensure every required fact is supported by inputs that have capability-linked evidence.

### 2. Audit catalogue evidence and grow coverage responsibly

- [x] Review every seeded laptop/accessory and each populated capability against its exact-model official source.
- [x] Record discrepancies as `needs_review` or remove unsupported populated fields; do not silently substitute family-level specifications.
- [x] Add devices toward 30 laptops and 30 accessories only when exact model and capability evidence are available; the reviewed sources did not justify filling the remaining slots.
- [x] Keep catalogue totals and verified counts observable for the coverage page.

### 3. Publish catalogue coverage and limitations

- [x] Add a public page explaining supported categories, evidence/review policy, verdict meanings, and known coverage limits.
- [x] Show current verified laptop and accessory counts from the API rather than hard-coded totals.
- [x] Make unavailable API data and empty catalogue states understandable.
- [x] Link to the page from the checker and README.

### 4. Verify the main user journey

- [x] Exercise the primary journey on desktop and mobile, including shared-URL restoration and an insufficient-data result.
- [x] Check keyboard navigation, visible focus, labels, responsive layout, and readable evidence links.
- [x] Run the API and frontend quality commands and resolve regressions.
- [x] Update this plan and the README with verified scenario counts, catalogue coverage, and remaining limitations.

## Acceptance criteria

- At least 50 distinct compatibility-engine scenarios cover boundary, missing-data, and verdict behavior.
- Every route to a `compatible` verdict is based on known required capability values with corresponding evidence.
- Every verified populated catalogue capability is supported by exact-model official evidence, or is corrected/reviewed before the release is called trustworthy.
- The catalogue grows only when evidence supports the added records; any shortfall from 30/30 is clearly reported.
- The public coverage page reports live verified counts and explains the evidence policy and limitations.
- The desktop/mobile main journey and the documented API/frontend quality commands pass.

## Exit condition

Phase 6 is complete: the evaluator has at least 50 meaningful scenarios, compatible verdict paths and published catalogue evidence have been reviewed, a public page reports live scope and limitations, the desktop/mobile main journey has passed, and project quality checks pass. Unsupported expansion remains explicitly tracked rather than guessed.

## Progress

- [x] Reviewed the roadmap's Phase 6 scope against the completed Phase 5 plan and current repository.
- [x] Created and reviewed this Phase 6 plan.
- [x] Added 20 evaluator scenarios, bringing the rule suite to 52 distinct cases by counting parametrized inputs; the API suite passes 68 tests.
- [x] Added a public coverage page with live verified totals, accessory categories, evidence policy, and scope limits; linked it from the checker and README.
- [x] Review the seeded laptop/accessory records for capability-to-evidence links and confirm that every populated checker input has a corresponding evidence key.
- [x] Review compatible-verdict input paths: public checks use only verified records; catalogue publication requires verified evidence for every populated field; seeded records now get the same fail-closed evidence check.
- [x] Finish source-by-source review of every seeded model and correct or flag discrepancies. Three mixed-port DP summaries now use DP 1.4; the Anker Prime output claim is unknown; Anker A83C3 is held as `needs_review` because the manufacturer uses that code for conflicting products.
- [x] Add additional devices only after exact-model source review. No unsupported rows were added to chase the 30/30 target.
- [x] Run API checks (ruff lint/format, 68 tests) and web checks (lint, Prettier, production build); all pass.
- [x] Exercise desktop/mobile journeys and shared URL restoration in headless Chrome. At a true 390 px mobile viewport, the document width is 390 px, the insufficient-data result renders, and the form controls do not overflow. Keyboard Tab reaches the coverage link with visible focus; all select controls have labels; all 22 evidence records render as readable HTTPS links. The coverage page displays 15 verified laptops and 14 verified accessories.

Current status: Phase 6 is complete. The seeded database reports 15 verified laptops, 14 verified accessories, and one accessory awaiting identity review. Seed validation fails closed when a populated field lacks evidence and reseeding removes stale capability evidence. The shared URL restored the selected pair and returned **Insufficient data** on desktop and mobile; responsive width, keyboard focus, labels, evidence links, and live coverage counts were reviewed in headless Chrome. API and web quality commands pass. No catalogue expansion was made without exact-model source support.
