# V2 Workstream 4 implementation plan

## Goal

Represent manufacturer-documented combinations of external displays and evaluate requested multi-display modes without extrapolating from single-output maxima.

## Evidence review and decisions

The current laptop catalogue has individual USB-C maximum resolution/refresh and an overall external display count. Accessory records have HDMI output count and a per-output maximum. The current seed excerpts support individual HDMI modes and some single-path laptop modes; they do not establish combined resolution/refresh combinations, MST behavior, lane allocation, or per-output interactions. Those combinations must remain unknown unless an exact manufacturer source documents them.

The existing scalar capability registry remains authoritative. Add an explicit structured display-configuration value type to represent each documented simultaneous mode set, any documented per-display output connection, and its stated topology. Preserve all existing scalar fields and behavior for legacy single-mode requests. No seed combination will be inferred from independent maxima.

## Scope

- Accept a setup containing requested external display modes, optional output connections, and optional requested topology, while retaining the existing count/resolution/refresh request form.
- Add nullable, evidence-backed combined-display configuration fields to laptop and accessory catalogue records. A documented entry contains the simultaneous display modes, any documented output connection per display, and optional topology exactly as the source establishes them.
- Compare multi-display requests only against an explicitly documented configuration. An explicit count or individual maximum may still establish a specific limitation, but cannot establish an undocumented combined mode.
- Return precise insufficient-data explanations when the catalogue does not establish the requested combination or topology.
- Add no seed configuration unless existing manufacturer evidence explicitly establishes it; the current reviewed seed evidence does not.

## Implementation steps

1. Add this plan before implementation and preserve all existing working-tree changes.
2. Extend the capability registry and model/write/read schemas with a JSON-backed structured capability for documented simultaneous display configurations, plus an additive migration.
3. Extend setup requests with per-display resolution/refresh and an optional topology, preserving existing fields and defaults.
4. Extend deterministic rules: retain count and per-output checks; match combined requests only against exact documented configurations; report missing combined-mode or topology evidence as unknown.
5. Add tests for exact supported combinations, documented count/mode limits, mismatched topology, absent combination evidence, API serialization, and old request compatibility.
6. Update contributor/evidence documentation, migration notes, and the V2 roadmap/checklist; run the API checks.

## Acceptance criteria

- A catalogue editor can record a source-backed simultaneous display configuration without changing old scalar maxima.
- A multi-display setup is compatible only when laptop and accessory evidence establish the requested combination and topology (where requested).
- A documented count/output limit can yield a specific incompatibility; undocumented aggregate bandwidth or lane allocation remains insufficient data with an explanation naming the gap.
- Existing single-display requests retain their current request shape and deterministic behavior.
- Registry consistency checks cover the new structured field and rule input.
- API checks pass and existing uncommitted changes remain intact.

## Progress

- [x] Inspect roadmap, Workstreams 0–3 plans, capability registry/contributor guide, current catalogue, manufacturer excerpts, and compatibility rules.
- [x] Create this plan before implementation.
- [x] Implement structured combined-mode catalogue/request modeling and compatibility evaluation.
- [x] Add representative tests and migration/rollout notes if required.
- [x] Update contributor guidance, V2 roadmap, and acceptance checklist.
- [x] Run API checks (Ruff lint/format and the API pytest suite: 94 passed, 11 skipped).
