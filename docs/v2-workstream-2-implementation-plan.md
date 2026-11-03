# V2 Workstream 2 implementation plan

## Goal

Make evidence disputes, rechecks, and catalogue corrections traceable. Open or unresolved evidence issues must keep affected devices out of public checks until maintainers resolve and republish them.

## Scope

- Record competing source claims, URLs, source quality, capability, and review state.
- Record a reviewer’s selected value and rationale when resolving a conflict.
- Surface stale evidence for recheck and record the outcome and checked date.
- Keep an append-only correction trail with prior/new values, reason, evidence references, actor, and timestamp.
- Make review/publication behavior explicit: open conflicts or failed rechecks move the device to `needs_review`; resolution alone does not republish it.
- Provide a source review playbook.

## Implementation steps

1. Add persistent conflict and correction-history records.
2. Add authenticated admin endpoints to list/create/resolve conflicts and inspect/recheck stale evidence.
3. Capture field and evidence changes on catalogue edits, requiring a reason when changes are made.
4. Gate public catalogue/check responses on review status and document the resolution-to-republication flow.
5. Add source-review guidance and focused tests for lifecycle, auditability, and visibility.

## Acceptance criteria

- Conflicts retain both claims and source quality, selected value, reviewer, and rationale.
- Stale evidence is discoverable and recheck outcomes are persisted.
- Corrections are append-only and include before/after values, reason, evidence references, actor, and time.
- Open conflicts and failed rechecks prevent public use; resolving an issue requires an explicit reviewed catalogue update before republishing.
- API checks and migrations pass.

## Progress

- [x] Add conflict and correction persistence with migration.
- [x] Add protected review, stale-evidence, and recheck endpoints.
- [x] Capture changes during catalogue edits and require reasons.
- [x] Add source-review playbook and tests.
- [x] Update the V2 roadmap and verify the complete API suite.

## Rollout and behavior

Migration `20261103_0004` is additive and creates the conflict and correction history tables. Existing device/evidence rows remain intact. Stale evidence is surfaced by the admin queue using a default age threshold of 365 days; age alone does not unpublish a device, while a failed or uncertain recheck sets the device to `needs_review` and removes it from public results. Recheck outcomes are recorded in correction history. Open conflicts also set `needs_review`. Resolving a conflict does not republish a device; a maintainer must recheck the selected evidence and explicitly update the catalogue to `verified` with a correction reason.
