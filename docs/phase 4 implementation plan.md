# PortPilot — Phase 4 Implementation Plan

## Goal

Let an authorized maintainer create and edit catalogue records through a protected API, keep unreviewed records out of public compatibility checking, and publish records only after required specifications and capability-linked evidence have been validated. Expand the catalogue from five to fifteen laptops and fifteen accessories using official manufacturer sources.

## Starting point

Phase 2 supplies SQLAlchemy catalogue models and capability-linked evidence. Phase 3 consumes those models in the check endpoint and has 35 passing rule/API-handler scenarios. There is no catalogue write API, authentication setting, or source review workflow beyond the database status fields. The seed file currently contains five laptops and five accessories.

## Plan review

- Start with a protected API rather than a separate admin UI; it delivers catalogue maintenance without duplicating the existing frontend.
- Require a non-empty `ADMIN_API_TOKEN` and compare bearer credentials in constant time. If the token is not configured, admin routes stay disabled.
- New records default to `draft`; only an explicit publish status can make a record public.
- Preserve nullable values as unknown. Publishing verifies record identity, a minimum set of category-specific capabilities, and verified evidence for every populated capability; it does not require the manufacturer to document every possible field.
- Public catalogue and check endpoints should expose/use only `verified` records. Admin endpoints can read and edit drafts and records needing review.
- Add new seed devices only after matching exact model codes and capability claims to official manufacturer documentation. Do not fill missing fields by analogy with another model in the same family.

## Work plan

### 1. Define write schemas and publish validation

- Add strict laptop, accessory, and evidence input schemas with bounded strings, non-negative counts/wattage, and valid review statuses.
- Require exact model identity and category-specific minimum capability fields to publish.
- Require verified evidence linked to the model code, required publication fields, and every populated capability field.
- Keep draft and needs-review records editable even when incomplete.

### 2. Add protected catalogue API

- Read `ADMIN_API_TOKEN` from the environment and require HTTP bearer authentication on every `/admin/*` route.
- Add list, create, and full-update endpoints for laptops and accessories.
- Replace a record's evidence atomically during updates and preserve database constraints.
- Return typed catalogue records, 404 for missing records, 409 for duplicate IDs, and 422 with field-specific publish errors.
- Keep drafts and needs-review records out of public device lists and `/checks` lookups.

### 3. Document administration workflow

- Add the token to `.env.example` and allow Compose to pass it through without committing secrets.
- Document issuing a token, drafting a record, linking evidence, and publishing only after review.
- Keep public checking usable when admin auth is not configured.

### 4. Grow the evidence-backed catalogue

- Add ten laptops and ten accessories with exact model identifiers and official sources.
- Record capability-specific excerpts and review dates for populated values.
- Add test fixtures for publishable records, missing required evidence, known limits, and unknown values.

## Acceptance criteria

- Admin reads and writes reject missing, incorrect, or unconfigured credentials.
- Draft records can be saved while incomplete; attempts to publish invalid records receive clear validation errors.
- Verified publication requires the category's minimum specifications and verified evidence for every populated capability.
- Public catalogue and compatibility checks exclude non-verified records.
- API tests cover create, update, authorization, publishing, review statuses, and public visibility.
- Catalogue count reaches fifteen laptops and fifteen accessories, each with official capability-linked evidence.
- Contributor documentation explains secure setup and the review workflow.

## Exit condition

Phase 4 is complete when a maintainer can securely draft, edit, review, and publish sourced devices through the API, public users see only verified items, and the catalogue contains fifteen laptops and fifteen accessories meeting the evidence policy.

## Progress

- [x] Reviewed the Phase 4 roadmap scope against the existing models, API, seed data, and Phase 3 rules.
- [x] Implement protected list/create/update API routes for laptops and accessories.
- [x] Add fail-closed bearer-token authentication and publish-time evidence/specification validation.
- [x] Add API tests for auth, draft editing, publication, evidence replacement, and public visibility.
- [x] Document token setup and the review workflow, and pass the token through Compose.
- [x] Expand to fifteen laptops and fifteen accessories with official sources and capability-linked excerpts.

Current validation: `python -m pytest tests -q` passes all 48 API tests after the catalogue expansion; Ruff checks, frontend lint/build, and the earlier Compose configuration check pass. The seed contains fifteen laptops and fifteen accessories; new records use exact manufacturer model identifiers, official source URLs, and evidence for each populated capability. Phase 4 implementation work is complete.
