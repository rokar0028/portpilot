# V2 Workstream 12 implementation plan

## Goal

Deliver advanced platform features: immutable result snapshots for verifiable audit sharing, DisplayLink virtual graphics driver protocol evaluation, reverse compatible-accessories lookup, instant multi-device catalogue search, declarative JSON seed specification tooling, and automated evidence freshness auditing.

## Real-world problem & architectural context

1. **Ephemeral vs. Immutable Share Links:**
   - Previously, sharing a check only serialized query parameters (`?laptop={id}&accessory={id}...`). If the underlying device specifications or rules engine evolved, reopening the URL months later could yield a different verdict than what the user saw.
   - For technical support, e-commerce verification, and hardware return disputes, users need an immutable snapshot (`/snapshots/{id}`) capturing the exact verdict, summary, limitations, and citations at check time, while preserving the ability to rerun the check against the latest rules.

2. **DisplayLink Virtual Graphics & Single-Display Host Limitations:**
   - Base Apple Silicon processors (M1, M2, M3 non-Pro/Max) only support one native external display over USB-C DP Alt Mode or Thunderbolt.
   - However, DisplayLink universal docks use virtual graphics drivers to compress video over standard USB 3.0/USB4 data lanes, bypassing native GPU display limits and macOS MST mirroring limits to drive dual 4K monitors.
   - The engine must accurately recognize DisplayLink accessories, evaluate them as compatible, and surface clear requirements about necessary DisplayLink software driver installation.

3. **Reverse Lookup ("What works with my laptop?"):**
   - Users frequently start with a specific laptop and want to discover all compatible docks, hubs, or chargers meeting their display and charging requirements without testing accessories one by one.

4. **Instant Multi-Device Filtering:**
   - As the catalogue grows, selecting devices from long dropdown lists becomes cumbersome. Instant filtering by model name or part number improves the selection experience.

5. **Declarative Device Ingestion & Evidence Freshness Auditing:**
   - Manually constructing SQL seeds or REST payloads is error-prone. A declarative JSON specification format with dry-run validation standardizes catalogue contributions.
   - Hardware specifications change or links rot over time; automated freshness audits flag evidence older than a defined threshold (e.g., 180 days).

---

## Scope & Components

### 1. Database Schema & Migrations
- Migration `20261105_0007_displaylink_supported.py`: Adds `displaylink_supported` boolean column to the `accessories` table.
- Migration `20261105_0008_result_snapshots.py`: Creates the `result_snapshots` table capturing immutable records with:
  - `id`: ULID-style or UUID identifier
  - `laptop_id`, `accessory_id`, `setup_json`
  - `verdict`, `summary`, `limits_json`, `requirements_json`, `evidence_json`
  - `rule_engine_version`, `created_at`

### 2. Deterministic Rules Engine Enhancements (`api/app/rules.py` v0.5.0)
- Evaluate DisplayLink-equipped docks (`displaylink_supported=True`):
  - Bypasses native USB-C DP Alt Mode requirements.
  - Bypasses macOS MST multi-display mirroring limitations.
  - Injects mandatory requirement note: *"DisplayLink driver installation required: this accessory uses DisplayLink virtual graphics over USB data."*
- Bandwidth & lane trade-off modeling:
  - 2-lane DP 1.2 host bandwidth limits on 4K@60Hz over standard USB 3.0 hubs.
  - Net Power Delivery pass-through margin checking ($W_{\text{charger}} - W_{\text{hub\_reserve}} \ge W_{\text{laptop\_min}}$).
  - Thunderbolt daisy-chaining topology verification.

### 3. API Endpoints (`api/app/main.py` & `catalog_admin.py`)
- `POST /snapshots`: Persists an evaluated check result as an immutable snapshot.
- `GET /snapshots/{snapshot_id}`: Retrieves the immutable snapshot record.
- `GET /devices/laptops/{device_id}/compatible-accessories`: Reverse compatibility search filtering by displays, resolution, refresh rate, and charging needs.
- `GET /devices/search`: Instant search across laptops and accessories matching queries by name or model code.
- `GET /admin/evidence/stale`: Admin endpoint auditing verified evidence older than `max_age_days`.

### 4. Setup Parser Native SDK Integration (`api/app/setup_parser.py`)
- Direct integration with Google GenAI SDK (`google.genai`) using Gemini 2.0 Flash when `GEMINI_API_KEY` or `GOOGLE_API_KEY` is present.
- Enforces strict JSON schema validation and clean fallback to OpenAI-compatible provider endpoints.

### 5. CLI & Operational Tooling
- `api/scripts/seed_from_spec.py`: Validates and ingests device specifications and manufacturer evidence from declarative JSON files (supports `--dry-run`, local SQLite/PostgreSQL, or authenticated API).
- `api/scripts/check_evidence_staleness.py`: CLI tool for scanning database or API for stale citations.
- `api/specs/examples/`: Sample specifications for `apple-macbook-air-m3.json` and `plugable-ud-6950z.json`.

### 6. Frontend Integration (`web/src/app/page.tsx`)
- Deep linking with immutable snapshots (`?snapshot=<id>`) displaying verified badges, original evaluation timestamps, and rerun options.
- Instant search filter boxes on laptop and accessory selects with normalized substring and part number matching.
- Modal / drawer browsing of compatible accessories for the selected laptop.
- Styled physical negotiation breakdown cards and missing manufacturer specification diagnostics.

---

## Progress & Verification

- [x] Database migrations created and verified against SQLite and PostgreSQL:
  - `20261105_0007_displaylink_supported.py`
  - `20261105_0008_result_snapshots.py`
- [x] Rules engine bumped to `0.5.0` with DisplayLink virtual graphics, macOS MST rules, and net charging calculation.
- [x] API endpoints implemented and unit/integration tested (159 pytest tests passing):
  - `tests/test_snapshots_and_search.py`
  - `tests/test_compatible_accessories.py`
  - `tests/test_seed_from_spec.py`
  - `tests/test_rules.py`
- [x] Frontend features integrated and validated:
  - Clean Next.js 15 build with 0 TypeScript/ESLint errors.
  - Zero formatting issues with Prettier.
- [x] CLI tools verified:
  - `seed_from_spec.py` tested with dry-run and database ingestion.
  - `check_evidence_staleness.py` verified against local catalogue.
- [x] E2E test assertions aligned to rule engine `0.5.0` in `checker.spec.ts` and `accessibility-contracts.spec.ts`.
