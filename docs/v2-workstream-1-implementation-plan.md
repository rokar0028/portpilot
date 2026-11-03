# V2 Workstream 1 implementation plan

## Goal

Improve catalog trust by distinguishing exact device identities, surfacing likely duplicates for human review, and documenting when a device is ready to publish.

## Scope and decisions

- Keep the manufacturer model code as the primary identity when the source provides one.
- Store region variant and hardware revision separately from the display name.
- Duplicate detection is advisory: it must not merge or reject records automatically.
- A published device must have a model code and the existing category-specific required specifications, each backed by verified manufacturer evidence.
- Do not add seed models just to increase catalog size. Add only entries whose exact identity and required capabilities are documented by a manufacturer source.

## Implementation steps

1. Add hardware revision as an optional, evidence-backed identity field.
2. Add normalized identity matching for same-type devices using brand, model code, name, region, and hardware revision.
3. Return reviewable duplicate warnings from create and update operations, excluding the record being edited.
4. Document the evidence threshold and identity requirements for contributors.
5. Inspect existing seeded records for missing or ambiguous identity data; record cases that need source review rather than guessing.

## Acceptance criteria

- Regional variants and hardware revisions can be represented explicitly.
- Duplicate candidates are returned with matching reasons and IDs, without silent merging or blocking a save.
- Create and edit checks behave consistently.
- Exact manufacturer identity and verified evidence remain required for publication.
- Contributor guidance explains which source evidence is acceptable and how to handle unresolved variants.

## Progress

- [x] Add hardware revision to database, API, and capability registry.
- [x] Add advisory duplicate warnings to admin create/edit responses.
- [x] Document evidence threshold, identity fields, and review workflow.
- [x] Audit current seeded model identities and record follow-up sourcing needs.
- [x] Run API checks and update the V2 roadmap.

## Seed identity audit

All 15 laptop seeds and 14 of 15 accessory seeds have an evidenced manufacturer model code. The Anker 364 hub entry has no exact manufacturer model code in its current source record, so it is now `needs_review` and is excluded from public checks until exact identity evidence is added. The Anker Nano Hub 6-in-1 remains held for the pre-existing model-code conflict. No regional variant or hardware revision was inferred where manufacturer documentation does not establish one.

No new product records were added in this workstream: the existing evidence set did not include a candidate with reviewed manufacturer sources for exact identity and required capabilities. This follows the V2 rule against expanding coverage without sufficient evidence.
