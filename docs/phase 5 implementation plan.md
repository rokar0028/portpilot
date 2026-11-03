# PortPilot — Phase 5 Implementation Plan

## Goal

Make the compatibility checker easy to complete and easy to understand for a nontechnical user. The main journey is choosing a laptop and accessory, describing the intended display/charging setup, and reading an evidence-backed result.

## Starting point

- The Next.js page already loads verified devices from `GET /devices` and submits a setup to `POST /checks`.
- The form offers one or two displays, common resolutions, refresh rates, and an optional charging requirement.
- The result shows a verdict, summary, requirement statuses, and source excerpts.
- The selected devices and setup are not saved in the URL, the result omits a clear device-pair heading, and no glossary is present.
- Phase 4 has 15 laptops and 15 accessories in the seed catalogue; the API suite passes (48 tests).

## Plan review

- Keep the existing API request/response contract and build on the working database-driven flow.
- Make a shared URL fully reproduce a check by encoding device IDs and setup options, restoring the form, and rerunning the check when opened.
- Put the verdict and selected device pair before rule details; preserve uncertainty language and capability-specific sources.
- Define unfamiliar terms briefly in a compact glossary that does not interrupt the check flow.
- Keep the first UX iteration within the current single-page application; no separate routes or account system are needed.

## Work plan

### 1. Complete the selector-to-result flow

- [x] Keep laptop and accessory selectors connected to the verified catalogue.
- [x] Show the selected model identifier and key documented/unknown capabilities beside each selector.
- [x] Retain setup selections as controlled form state.
- [x] Make loading, API failure, and empty-catalogue states clear and accessible.

### 2. Explain and share a result

- [x] Present the chosen laptop/accessory pair with the verdict and summary.
- [x] Keep pass/fail/unknown requirement details and manufacturer evidence visible.
- [x] Encode laptop, accessory, display count, resolution, refresh, and charging in shareable query parameters.
- [x] Restore shared settings and automatically run the check when a complete shared URL is opened.
- [x] Add a copy-link action with clipboard feedback and a usable fallback.

### 3. Add a small glossary

- [x] Explain USB-C, DisplayPort Alt Mode, USB Power Delivery, USB4, and Thunderbolt in plain language.
- [x] Make glossary content keyboard-accessible and compact on desktop and mobile.

### 4. Review the experience

- [x] Keep responsive layout, visible focus, labels, and status text usable on small screens and keyboard navigation.
- [x] Run frontend lint/build and API regression checks after implementation.
- [x] Update the README and this plan to describe the user journey and sharing behavior.

## Acceptance criteria

- A user can select two catalogue devices and a requested setup, then see the verdict, requirements, and sources.
- A copied result URL reopens with the same devices and setup and reruns the same check.
- Unknown specifications remain visibly unverified and are never presented as confirmed support.
- The glossary explains the five terms without requiring the user to leave the checker.
- The page passes frontend lint and production build.

## Exit condition

Phase 5 is complete when a nontechnical user can perform and share a check, understand the result and its evidence, and look up core USB-C terminology from the page.

## Progress

- [x] Reviewed the Phase 5 roadmap against the existing selector, check API, and result panel.
- [x] Implement shareable/restorable check URLs, clearer model context, and glossary.
- [x] Run frontend lint/build and API regression checks; update contributor documentation.

Current validation: `npm run lint`, `npm run format:check`, and `npm run build` pass in `web/`; `python -m pytest tests -q` (48 passed), `ruff check app migrations tests`, and `ruff format --check app migrations tests` pass in `api/`.
