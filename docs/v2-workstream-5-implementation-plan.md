# V2 Workstream 5 implementation plan

## Goal

Help users select the exact laptop model, use the checker on a phone, and report questionable results with the least useful context necessary. Document the sharing contract explicitly.

## Findings and decisions

- The checker is a Next.js client page backed by the FastAPI `/devices` and `/checks` endpoints. Evidence and result details render inline on the same page; existing Playwright coverage exercises result sharing and validation.
- Exact model codes are already shown in the laptop selector, with a link to catalogue coverage. Add a concise, expandable model-finding guide with physical label and OS-specific paths.
- Keep report submission low-data: result verdict, selected catalogue IDs, setup requirements, rule engine version, and optional short explanation. Do not send contact details, setup prose, browser/device identifiers, IP addresses, or evidence excerpts. Persist reports through a narrowly scoped submission endpoint for maintainers to review from the database.
- Shared results remain current-catalogue reruns. The URL contains the selected catalogue IDs and setup parameters; it does not preserve a catalogue or rule snapshot. State that behavior in the UI and docs.
- Improve small-screen layout through responsive typography, wrapping, controls, and evidence cards without changing desktop information architecture.

## Implementation steps

1. Inspect the roadmap, prior workstream plans, current checker/API flow, and existing uncommitted changes.
2. Add this plan before implementation.
3. Add model-number instructions for physical labels and Windows, macOS, and ChromeOS settings/help surfaces.
4. Refine mobile styles for selection, evidence, and result content.
5. Add a low-data result-report endpoint and a user-facing report form with validation and safe context; add representative API and browser coverage.
6. Explain current-data reruns for share links in the checker and contributor/product documentation.
7. Update the V2 roadmap and acceptance checklist, then run relevant API and web checks.

## Acceptance criteria

- Users can find where to look for the exact laptop model and model code, including device labels and platform settings.
- Selection, evidence, and result content remain readable and operable on narrow viewports.
- A user can report a suspicious result with useful deterministic context and a short optional note, without collecting unnecessary personal or machine data.
- Share-link behavior is stated clearly: selections are restored and evaluated against current catalogue/rule data.
- Representative tests cover report validation/persistence and the main UI flow; relevant project checks pass.

## Progress

- [x] Inspect existing roadmap, plans, checker/API architecture, and working-tree changes.
- [x] Create this implementation plan before implementation.
- [x] Implement model-finding help and mobile readability improvements.
- [x] Implement low-data reporting and representative coverage.
- [x] Document share-link semantics and update roadmap/checklists.
- [x] Run API lint/format checks and the full API test suite; run web lint/format checks.

## Verification notes

API checks pass: Ruff check/format and pytest (95 passed, 11 skipped). Web ESLint and Prettier checks pass. Production and dedicated E2E builds compile and type-check, then fail while Next.js copies standalone traced files with Windows `EPERM` errors creating nested `node_modules/next/dist/...` directories. Browser E2E execution therefore could not start in this environment.
