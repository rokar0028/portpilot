# V2 migration and rollout notes

This note records the database and API changes made by V2 workstreams. It describes the migrations present in the repository; it does not imply they have been applied to a shared or production database.

## Changes and rollout behavior

| Alembic revision | Change | Existing data impact | Rollout note |
| --- | --- | --- | --- |
| `20261102_0001` | Creates laptop, accessory, and source-evidence tables and indexes. | Creates the catalogue schema; no pre-existing PortPilot catalogue tables are transformed. | Baseline for a fresh database. |
| `20261102_0002` | Adds nullable `laptops.usb_c_video_supported`. | Existing laptop rows receive `NULL`, preserving unknown video support. | API exposes an optional boolean; clients must handle `null` as unknown. |
| `20261102_0003` | Adds nullable laptop `hardware_revision` and accessory `region_variant` and `hardware_revision`. | Existing rows receive `NULL`; identity is not inferred. | API reads/writes the optional identity fields. |
| `20261103_0004` | Creates evidence-conflict and catalogue-correction history tables and indexes. | Existing catalogue/evidence rows remain intact; history starts empty. | Adds protected admin review routes. Existing public checks remain available. |
| Workstream 3 | Extends the in-code capability registry and adds consistency checks. | No database or public API shape change. | Deploy the API code; no migration is needed. |
| `20261103_0005` | Adds nullable JSON `display_configurations` fields to laptops and accessories. | Existing records receive `NULL`; no combined modes or topology are inferred from individual maxima. | Apply after `20261103_0004`; API clients may optionally submit and receive documented simultaneous configurations. |
| Workstream 4 | Adds optional per-display setup modes and topology plus deterministic documented-configuration matching. | Existing scalar request fields and verdict logic for single display requests remain in use. | Rule engine version is `0.3.0`; combined requests without exact evidence return insufficient data. |
| `20261103_0006` | Creates the `result_reports` table for user correction reports. | Starts empty; stores selected IDs, setup, verdict/rules version, optional note (max 1,000 chars), and timestamp. No contact details, browser/device identifiers, IP address, setup prose, or evidence excerpts. | Deploy the API migration before exposing report submission. Reports remain available if catalogue rows are later removed. |

The API image runs `alembic upgrade head` before seeding and starting the server. For a manual rollout, take a database snapshot using the provider’s supported backup procedure, inspect the current revision, apply migrations, seed if required by the environment, and then verify readiness and representative catalogue/API behavior:

```powershell
cd api
alembic current
alembic upgrade head
python -m app.seed
```

`python -m app.seed` is idempotent for the curated seed records. Do not run it against an unintended database; confirm `DATABASE_URL` first. In Compose, the API service performs migration and seed as part of its startup command.

## Failure recovery and rollback

Detailed, environment-specific operational instructions for SQLite, Docker Compose PostgreSQL, and Render Free/durable hosting are documented in the [Database Operations and Migration Recovery Runbook](database-operations-runbook.md).

If migration fails, stop application writes and deployment retries immediately. In containerized environments (`Dockerfile`, `render.yaml`), API startup commands run `alembic upgrade head && python -m app.seed`. If an upgrade fails, the container crashes and enters a restart loop; pause deployment retries to avoid lock contention or repeated failed mutations.

Record the failing revision and database error, inspect `alembic current` and `alembic history`, and compare the database against a restorable snapshot before retrying. Do not assume a failed multi-statement migration left the database untouched on every backend (PostgreSQL supports transactional DDL for most statements; SQLite has non-transactional DDL). Always rehearse recovery against an isolated restored copy before resuming writes.

Downgrades remove data as well as schema:

- Downgrading `20261103_0006` drops `result_reports` and all submitted user reports.
- Downgrading `20261103_0005` drops the laptop and accessory simultaneous display configurations entered after upgrade.
- Downgrading `20261103_0004` drops evidence-conflict and catalogue-correction history.
- Downgrading `20261102_0003` drops the identity columns and any values entered in them.
- Downgrading `20261102_0002` drops `usb_c_video_supported` values.
- Downgrading `20261102_0001` drops the catalogue and evidence tables.

Prefer restoring a verified pre-migration snapshot if rollback is needed. Use Alembic downgrade only when the data loss is understood and the restored data/API contract is compatible with the application version being run. On Render Free, note that **no provider backups exist**; any rollback on Render Free requires a manual export taken prior to deployment or re-seeding a disposable database. After recovery, confirm `alembic current`, readiness, catalogue visibility, and a representative compatibility check before reopening writes.

## API compatibility

The identity columns and video-support field are nullable, additive schema/API fields. Evidence-review routes are additive and protected by admin authentication. Workstream 3 changes registry enforcement and adapter construction internally; it preserves existing endpoints and verdict behavior. Clients should continue to treat absent or `null` capability values as unknown where the API already represents them that way.
## Workstream 5 result reports

Revision `20261103_0006` creates the `result_reports` table for user-submitted correction reports. It stores selected catalogue IDs, structured setup, verdict and rules version, an optional note capped at 1,000 characters, and submission time. It intentionally stores no contact details, browser/device identifiers, IP address, free-form setup description, or evidence excerpt. The table has no catalogue foreign keys so a report remains useful if a catalogue entry is later removed. Deploy the API migration before exposing the report form. Downgrade drops submitted reports and is destructive.

