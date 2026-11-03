# PortPilot — Phase 3 Implementation Plan

## Goal

Make `POST /checks` evaluate a requested laptop and accessory setup with deterministic, explainable rules. Every required fact must be supported by catalogue data; unknown facts produce `insufficient_data`, while documented limits produce `compatible_with_limits`.

## Starting point

Phase 2 added the database-backed catalogue and evidence links. The check endpoint already returns verdict, summary, limits, requirement details, evidence, and a rule-engine version. Its current evaluator covers only USB-C video, display count, an exact display mode, and a deliberately unknown charging result. Catalogue fields already store laptop USB-C/HDMI mode maxima, accessory HDMI mode maxima, host connection requirements, and Power Delivery values. The request supports display count, resolution, refresh rate, and laptop charging.

## Plan review

- Preserve the existing request and response contract; the current UI consumes its field names.
- Compare requested modes against maximum supported modes instead of string equality. A documented maximum is a bound, not a single exact mode.
- Keep unknown distinct from unsupported. Only an explicit `false` or an exceeded documented limit can fail a requirement.
- Use only stored/manual manufacturer evidence; do not infer support from connector names or product category.
- The current catalogue has no separate monitor capability, laptop charging demand, or USB bandwidth model. Do not invent these facts; call out the data gap and return unknown where it is required.
- Keep rule logic pure so scenarios can be tested without a database or web server.

## Work plan

### 1. Normalize catalogue inputs for rule evaluation

- Pass the model's documented HDMI and USB-C maximum modes, display limit, connector facts, and Power Delivery ranges to the evaluator.
- Represent missing values as `None`; retain explicit `False` values.
- Keep rule evidence attached to the selected devices in the existing API response.

### 2. Implement deterministic requirements

- Check the accessory host connection against the laptop's documented ports where the catalogue can establish a match.
- For video setups, check the accessory's USB-C DP Alt Mode requirement against laptop video support.
- Check requested display count against the laptop limit and known accessory output count.
- Check requested resolution and refresh against the applicable documented laptop and accessory maxima.
- Check charging only from documented laptop input and accessory output values; report a limit when available power falls below the laptop's documented maximum but meets its documented minimum.
- Report unknown for unsupported-to-evaluate combinations or missing required facts.

### 3. Determine verdict and explanation

- `incompatible` when any required capability is explicitly unsupported or the requested setup exceeds a documented maximum.
- `insufficient_data` when no failure is established but at least one required fact is unknown.
- `compatible_with_limits` when requirements are established and a documented limitation applies.
- `compatible` when all requested requirements are established without a known limitation.
- Keep requirement records stable as `{name, status, detail}` and populate `limits` with user-readable constraints.

### 4. Add scenario coverage

- Cover compatible, limited, incompatible, and insufficient-data outcomes.
- Cover resolution/refresh boundary behavior, display counts, charging thresholds, video-required vs not-required, and no-requested-feature behavior.
- Keep API integration changes limited to wiring normalized fields through the existing endpoint.

## Acceptance criteria

- Requested display modes are checked against maxima for both laptop path and accessory output.
- Explicitly unsupported requirements fail; missing specifications remain unknown.
- Charging can pass or report a limit only when stored values justify that result.
- Verdict precedence is deterministic: failure, then unknown, then known limitation, then compatible.
- Response contract and evidence references remain compatible with the existing frontend.
- Pure rule tests exercise all four verdicts and key boundaries.

## Exit condition

Phase 3 is complete when representative documented scenarios produce stable verdicts and explanations through `POST /checks`, with unknown data never reported as support. Missing catalogue fields that prevent a safe decision are recorded for Phase 4 catalogue expansion.

## Progress

- [x] Reviewed Phase 2 schema and current API contract against the seven-phase roadmap.
- [x] Wired persisted connection, display mode, output count, and charging values into rule evaluation.
- [x] Implemented mode maxima, conservative unknown handling, charging thresholds, verdict precedence, and limits.
- [x] Added six pure evaluator scenarios covering the four verdicts and important display-mode boundaries.
- [x] Expand scenarios beyond the roadmap target of at least 20 and cover additional combinations.
- [x] Review rule inputs against seeded mode and charging fields, including charger output vs hub pass-through.
- [x] Validate the API check handler against an isolated SQLite catalogue, including evidence output and structured 404 behavior.
- [x] Run frontend lint and production build to confirm the existing check UI contract remains valid.

Current validation: `ruff check app tests`, `ruff format --check app tests`, `pytest tests -q` (35 passed), `npm run lint`, and `npm run build` pass. The seeded Lenovo + Anker request returns `insufficient_data`, preserving the source-backed unknown USB-C video requirement instead of assuming a path. An HTTP-server smoke check was blocked because the workspace sandbox denied socket access; the isolated FastAPI handler and database path are covered directly.
