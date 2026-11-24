# PortPilot Frontend Refactor Implementation Plan

## Objective

Reduce frontend complexity while preserving the current user journey, visual language, API contracts, accessibility behavior, and compatibility results.

## Scope

- Refactor the Next.js frontend only.
- Keep the backend and endpoint contracts unchanged.
- Preserve device selection, filtering, setup interpretation, checks, snapshots, sharing, reporting, evidence, limitations, and mobile behavior.

## Workstreams

1. **Extract API access**
   - [x] Add a typed frontend API module for catalogue loading, checks, setup parsing, compatible accessories, snapshots, and reports.
   - [x] Keep error messages and request payloads compatible with the current UI.

2. **Extract URL and snapshot restoration**
   - [x] Move query-string parsing and setup normalization into pure functions.
   - [x] Keep invalid values on the same safe defaults currently used by the page.
   - [x] Preserve snapshot-first restoration and fallback to regular URL parameters.

3. **Reduce page-controller duplication**
   - [ ] Centralize result/error/loading cleanup after device or setup changes.
   - [x] Preserve stale-request protection for compatibility checks.
   - [x] Keep `page.tsx` responsible for composition and feature coordination.

4. **Improve failure states**
   - [x] Keep catalogue retry behavior.
   - [ ] Distinguish compatible-accessory request failure from an empty result list.
   - [x] Preserve accessible alert and status announcements.

5. **Styling cleanup**
   - [ ] Replace repeated inline styles with focused classes only where this can be done without visual changes.

## Verification gates

- [x] `npm run lint`
- [x] `npm run format:check`
- [x] `npm run build`
- [ ] Relevant Playwright journeys
- [x] Manual successful check with the seeded Lenovo and Anker records
- [ ] Manual URL restoration, sharing, report submission, and API failure checks

## Delivery sequence

1. [x] Add pure helpers and API wrappers.
2. [ ] Add focused tests for URL parsing and API error behavior.
3. [x] Integrate helpers into `page.tsx` in small patches.
4. [x] Run lint, format, build, and browser checks.
5. [ ] Review the diff for unintended behavior or copy changes.
