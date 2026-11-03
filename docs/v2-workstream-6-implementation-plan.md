# V2 Workstream 6 implementation plan

## Goal

Make the checker’s primary journeys understandable and operable with screen readers, retain automated accessibility checks, and record manual assistive-technology reviews in a repeatable way.

This plan supports [Workstream 6 in the V2 plan](v2-implementation-plan.md#6-accessibility).

## Findings and decisions

- The checker is a Next.js client page. Its primary journeys include device selection, optional natural-language setup parsing and review, validation/service errors, and an inline compatibility result with requirements and evidence.
- Playwright already runs axe against the checker and coverage page, plus a narrow-screen keyboard reachability check.
- The checker currently puts the entire changing result panel inside a polite live region. That can cause large, unpredictable announcements as interactive result details are inserted. Use a small dedicated status region for concise state changes, while leaving result content navigable by headings and landmarks.
- Parsed setup review, service errors, and successful results need distinct, concise announcements. Existing alert/status roles should remain purposeful and should not be duplicated by the new announcement region.
- Manual records must identify screen reader, browser, operating system, scenarios, findings, and fixes. A browser automation assertion is not a screen-reader pass; if no actual screen reader is available, record that limitation without claiming a manual pass.

## Implementation steps

1. Inspect the V2 roadmap, earlier workstream plans, current working-tree changes, checker UI, and accessibility tests.
2. Create this plan before implementation.
3. Refine live announcements and accessible names/structure for loading, parsed setup review, errors, and result updates based on code review.
4. Expand automated axe coverage across representative checker states and test concise announcement content and keyboard access.
5. Add a repeatable manual screen-reader test plan and dated pass record template/entries that state the actual screen reader, browser, OS, scenarios, findings, and fixes.
6. Update the V2 roadmap and release checklist with completion state and any remaining manual-test limitation.
7. Run relevant web lint, formatting, and accessibility/browser checks available in this environment.

## Acceptance criteria

- Main checker controls and the parsed setup review can be reached and understood through semantic labels, headings, and keyboard operation.
- Loading, success, parsed review, and failures receive concise, non-duplicated announcements.
- Automated axe checks cover representative checker states and report no WCAG 2.1 A/AA violations.
- The manual test plan covers device selection, setup parsing/review, validation or service errors, and result announcements. Each performed pass records screen reader, browser, OS, scenarios, findings, and fixes; unavailable manual runs are explicitly labeled and not claimed as passed.
- The V2 roadmap and release checklist reflect verified work and remaining limitations.

## Progress

- [x] Inspect roadmap, prior workstream plans, working-tree changes, checker flow, and existing accessibility checks.
- [x] Create this plan before implementation.
- [x] Improve accessible announcements and semantics across checker states.
- [x] Add representative automated accessibility/state coverage for parsed review, results, and service errors.
- [x] Document manual screen-reader scenarios and this session’s actual verification limits in [screen-reader test plan](accessibility-screen-reader-test-plan.md).
- [x] Update the V2 roadmap and release checklist with the pending manual pass.
- [ ] Complete manual screen-reader scenarios and record actual screen reader/browser/OS versions, findings, and fixes.
- [x] Run the browser accessibility suite and confirm the expanded axe checks pass.

## Verification notes

- `npm run lint` passes.
- `npm run format:check` passes.
- `npm run build:e2e` passes after the E2E server was changed to run the regular Next.js build directly, avoiding unnecessary Windows standalone dependency copying for tests.
- `npx playwright test e2e/accessibility.spec.ts --project=chromium` passes (4 tests) against a freshly migrated and seeded disposable SQLite database. This includes the axe scans for empty, parsed-review, result, error, and coverage states and the narrow-screen keyboard check.
- The result-state axe scan initially found serious color-contrast issues in version metadata, requirement status labels, and evidence headings. Darker accessible colors fixed those findings. The first test attempt also exposed stale “Laptop” locators; these now match the actual “Your laptop” label.
- Windows Narrator is installed and launched, but its startup/update UI did not expose an inspectable speech-viewer path through the available automation. No manual spoken-output scenario was completed. A real manual pass is still required before Workstream 6 can be called complete.

## Browser automation record

| Date | Screen reader | Browser | Operating system | Scenarios | Findings and fixes |
| --- | --- | --- | --- | --- | --- |
| 2026-11-03 | Not applicable; automated browser run | Playwright 1.64.1, Chromium 156.0.8078.4 | Windows 10 Pro 25H2, build 26200.9711 | Empty checker, parsed setup review, supported result, check error, coverage, 360px keyboard navigation | Found three result-state contrast issues and corrected text colors. Corrected stale test label locators. Final result: 4/4 tests passed. This is not a manual screen-reader pass. |

## Manual review record

| Date | Screen reader | Browser | Operating system | Scenarios | Findings | Fixes / outcome |
| --- | --- | --- | --- | --- | --- | --- |
| 2026-11-03 — attempt only, not a pass | Windows Narrator launched; its version and speech output were not inspectable | None; no screen-reader browser scenario completed | Windows 10 Pro 25H2, build 26200.9711 | Attempted Narrator launch; no checklist scenario completed | Startup/update UI did not expose an inspectable speech-viewer path through available automation | No manual findings or fixes can be claimed. Complete the scenarios in the linked plan with NVDA or Narrator before release. |

