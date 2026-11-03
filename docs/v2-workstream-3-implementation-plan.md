# V2 Workstream 3 implementation plan

## Goal

Make the existing capability registry the checked contract for catalogue fields, evidence keys, publication requirements, and compatibility rule adapters.

## Scope and decisions

- Keep this API-only and preserve catalogue data, database schema, endpoints, and verdict behavior.
- Extend the current `api/app/capabilities.py`; do not create a second catalogue of device facts.
- A capability is either required for named publication categories or explicitly optional for publication.
- A capability is either mapped into the rule adapter or explicitly declared unused by current compatibility rules. Adapter input names must also match the fields consumed by the rules engine.
- Run registry consistency validation at API startup and in focused tests so omissions and stale mappings fail with actionable messages.
- Preserve deterministic rule logic and the current meaning of existing rule inputs.

## Implementation steps

1. Add explicit publication-optional and rule-unused declarations to registry metadata; add allowed values where the category is constrained.
2. Derive adapter mappings and capability lookups from the registry declarations.
3. Add consistency validation across SQLAlchemy fields, API write-schema fields/types, publication declarations, rule adapter mappings, and rule-engine consumption.
4. Keep evidence association and conflict/recheck key validation on the same entity-scoped registry lookup.
5. Add tests for full registry consistency and clear failures for missing/mistyped/unknown handling.
6. Document the capability extension procedure, update the V2 roadmap, and mark completed criteria.

## Acceptance criteria

- A single registry remains the source of capability ownership and value metadata.
- Every persisted capability field has a matching write-schema field and registry entry; types and constrained values agree.
- Every registry capability explicitly declares publication handling and rule handling.
- Every rule adapter input declared in the registry is consumed by the rules engine; no consumed input is unmapped.
- Evidence and conflict keys are entity-validated against the registry.
- No migration or public API shape change is needed.
- API checks pass.

## Extension path

When adding a catalogue capability, update the registry row with entity, scalar type, unit, allowed values, publication requirement categories (or add it to the explicit optional set), and rule adapter mapping (or explicit unused set). Add the model column and write-schema field, then add or update rule-engine consumption if the capability affects compatibility. Add evidence to the relevant seed or admin payload with the same key, update inventory documentation, and run the API checks. Startup consistency validation reports which layer is missing.

## Progress

- [x] Inspect Workstream 0/1/2 implementation and existing registry call sites.
- [x] Define a shared capability handling contract and startup consistency checks.
- [x] Keep catalogue validation, evidence association, publication requirements, and rule inputs registry-driven.
- [x] Add focused consistency and failure tests.
- [x] Document the extension path and update the V2 roadmap.
- [x] Run the API checks.
