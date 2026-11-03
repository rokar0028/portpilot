# Screen-reader test plan

## Purpose

Manually review the core PortPilot checker journeys with a screen reader. Automated axe and Playwright checks supplement this review; they cannot confirm spoken output, announcement timing, or whether users can follow the information.

## Supported combinations

Run at least one current Windows combination before release:

- NVDA with Firefox or Chrome, or
- Windows Narrator with Microsoft Edge.

Record exact versions and the operating system build. Repeat important journeys on another supported combination when available. Use keyboard only during the pass, then optionally repeat with pointer input to compare.

## Scenarios

1. **Open and select devices**
   - Load the checker and navigate by headings, landmarks, and form controls.
   - Confirm the laptop and accessory selects have clear names and option text distinguishes exact models/model codes.
   - Select both devices and open verified details. Confirm evidence links have useful names and disclosure state is understandable.
2. **Setup fields and parsed setup review**
   - Open “Adjust screen or charging needs”; navigate all fields and confirm names, values, and instructions.
   - Enter a short setup description and activate “Interpret setup”.
   - Confirm a concise completion announcement, then navigate to the parsed review. Hear clarification, unsupported requests, and unknown-field messages where present.
   - Confirm the review checkbox is named and that checking remains unavailable until the user confirms review. Change a parsed field and confirm review is required again.
3. **Errors**
   - Simulate an unavailable device catalogue and an unavailable setup/check service.
   - Confirm each error is announced once, identifies the issue, and leaves retry or manual entry available.
   - Confirm focus remains in a sensible location after the error and recovery.
4. **Result announcements and details**
   - Run a supported check and an insufficient-data or incompatible check.
   - Confirm one concise completion announcement includes the verdict and summary.
   - Navigate headings and requirements to inspect the verdict, limitations, evidence disclosures and source links. Confirm icons do not create redundant speech.
   - Change an input and verify the stale result is cleared; rerun and confirm the next verdict is announced.
5. **Report and responsive keyboard use**
   - Open the result report, submit a short note and confirm the success or failure status is announced.
   - At a narrow viewport, tab through controls; confirm focus is visible, order is logical, and no horizontal page scrolling is needed.

## Findings and fixes

For each finding, record the scenario, actual spoken behavior, expected behavior, severity/impact, and fix (or linked issue). Re-run the affected scenario after a fix. Do not mark a combination passed based only on DOM inspection or axe.

## Manual pass records

| Date | Screen reader and version | Browser and version | Operating system and version | Scenarios completed | Findings | Fixes / outcome |
| --- | --- | --- | --- | --- | --- | --- |
| 2026-11-03 — attempt only, not a pass | Windows Narrator was launched; Narrator version and speech output were not available for inspection | None; no screen-reader browser journey completed | Windows 10 Pro 25H2, build 26200.9711 | Attempted to start Narrator; no checklist scenario completed | Narrator opened its update/startup UI, but the available automation could not expose or inspect spoken output | No screen-reader findings or fixes can be claimed. A human must complete and record the scenarios above using Narrator or NVDA before release. |

## Separate automated browser run

| Date | Screen reader | Browser and version | Operating system and version | Scenarios | Findings and fixes |
| --- | --- | --- | --- | --- | --- |
| 2026-11-03 | Not applicable; automated test only | Playwright 1.64.1, Chromium 156.0.8078.4 | Windows 10 Pro 25H2, build 26200.9711 | Empty checker, parsed setup review, supported result, service error, coverage page, 360px keyboard navigation | Axe found low contrast in result metadata, requirement labels, and evidence heading; colors were darkened. Fixed outdated test locators. Final automated run: 4/4 passed. This does not verify spoken output. |

