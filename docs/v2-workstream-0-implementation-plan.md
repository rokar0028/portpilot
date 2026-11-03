# V2 Workstream 0 implementation plan

## Goal

Create the shared foundation for V2 work: inventory the current catalogue and rule surfaces, then establish a typed capability registry that keeps catalogue fields, evidence keys, publication requirements, and rule inputs aligned.

This is a supporting implementation plan for [Workstream 0 in the V2 plan](v2-implementation-plan.md#workstream-0-v2-foundation-and-implementation-control).

## Scope

- Preserve current API behavior and existing stored catalogue data while introducing validation.
- Recognize capabilities already represented in laptop and accessory models, API schemas, evidence, and compatibility rules.
- Keep this first slice internal to the API; it does not change database schema or expose a new endpoint.
- The initial registry intentionally landed before it controlled every validation surface; Workstream 3 completed that rollout and recorded the extension contract.

## Implementation steps

1. Inventory model/schema fields, evidence keys in seeds, publication requirements, and rule inputs.
2. Add a typed registry with entity ownership and basic value metadata.
3. Add a validation helper that rejects unknown evidence keys with a useful error.
4. Wire the helper into incoming evidence validation and verify existing seed keys are covered.
5. Record follow-up gaps before making registry definitions drive publication or rule logic.

## Acceptance criteria

- Every currently seeded evidence key has a registry entry.
- Every entry identifies its owning entity and value type; constrained categorical values and units are documented where applicable.
- Unknown evidence keys are rejected with a message that names the key.
- Existing seed data and evidence keys remain unchanged.
- No migration or public API shape change is required for this slice.

## Current inventory

The catalog currently models laptop and accessory capability values in `api/app/models.py` and write/read contracts in `api/app/schemas.py`. Evidence stores a `capability_key` string. Publication rules live in `api/app/catalog_admin.py`; compatibility inputs are read in `api/app/rules.py`; seeded catalog evidence is in `api/app/seed.py`.

The initial implementation registered the capability keys observed in the seed data. Workstream 3 reconciled the registry with every persisted capability field, made publication and rule-input handling registry-driven, and added startup consistency validation.

## Progress

- [x] Add Workstream 0 to the V2 roadmap.
- [x] Document the implementation plan and current code locations.
- [x] Add and wire the typed capability registry for incoming catalogue evidence.
- [x] Register the capability keys used by the current seed catalog.
- [x] Verify registry coverage against every persisted laptop and accessory capability field and make publication requirements registry-driven.
- [x] Use the registry to define rule adapter inputs and verify schema/model type metadata consistency.

Workstream 3 completed the registry rollout: catalogue fields, entity-scoped evidence keys, publication handling, and compatibility adapter inputs now share startup consistency validation. See the [Workstream 3 plan](v2-workstream-3-implementation-plan.md) and [capability registry contributor guide](capability-registry.md).

## Migration and rollout notes

The initial Workstream 0 registry introduced no database migration or public API shape change. The subsequent identity work added nullable identity columns in `20261102_0003`; evidence-review and correction history added tables in `20261103_0004`. Workstream 3 changed only API code and required no migration. The [V2 migration and rollout notes](v2-migration-rollout.md) record the data impact, rollout sequence, compatibility notes, and destructive downgrade behavior for these revisions.

## Workstream 0 completion

- [x] Record migration and rollout notes for schema/API changes made by the dependent workstreams.
- [x] Synchronize the V2 roadmap with completed Workstreams 1–3 and make Workstream 3 an explicit prerequisite for Workstream 4.
