# V2 Workstream 7 implementation plan

## Goal

Make API latency measurable against a documented, representative target and give maintainers recovery instructions that match PortPilot's actual local and preview database environments.

This plan supports [Workstream 7 in the V2 plan](v2-implementation-plan.md#7-reliability-and-operations). It defines implementation work only; no Workstream 7 implementation or verification is claimed here.

## Findings and decisions

- The API is FastAPI/SQLAlchemy. Direct local development defaults to SQLite; Docker Compose runs PostgreSQL 16 in a named `postgres_data` volume. The Render Blueprint defines an API web service and a free PostgreSQL database in Singapore, but the README and prior deployment plan say this Blueprint is not deployed.
- Render Free PostgreSQL expires after 30 days and has no backups. It is suitable only for a disposable preview and cannot satisfy a recoverable/persistent-data requirement. Before storing user or operationally important data on Render, select a durable database plan with provider-supported backups/PITR or move to a database with equivalent recovery guarantees. No production host or provider backup schedule is currently established.
- API startup runs `alembic upgrade head`, then `python -m app.seed`, then Uvicorn. Alembic has a linear history through `20261103_0006`; several migrations add data-bearing fields or tables, so downgrades can discard evidence review history, display configurations, result reports, identity fields, and capability values. Existing [migration rollout notes](v2-migration-rollout.md) identify the data loss but do not yet give executable backup/restore steps for each actual environment.
- Middleware measures elapsed time with `perf_counter`, logs method, route template, status, elapsed milliseconds, request ID, and exception type, and does not log query strings, headers, bodies, or client addresses. `/metrics` currently exposes process-local request counters and compatibility verdict counters only. It has no duration histogram; counters reset at process restart and are not aggregated across workers. `/metrics` itself is included in request counting.
- The natural-language setup parser can call an external provider, so its latency is materially different from deterministic database/API routes. Keep it visible as its own route in distributions and slow-route logs, but exclude it from the core deterministic API SLO and report it separately rather than allowing provider latency to hide regressions in catalogue/check operations.
- Proposed initial service objective: during a 30-minute steady-state measurement window at 5 requests/second, p95 server-observed response duration for the weighted deterministic mix is at most 500 ms. Use 40% `GET /devices`, 30% `POST /checks` (mix supported, unsupported, and insufficient-data outcomes), 10% laptop detail, 10% accessory detail, 5% `GET /ready`, and 5% `POST /result-reports`. Use a fixed seeded PostgreSQL fixture/catalogue and realistic response serialization; exclude `/health`, `/metrics`, admin routes, and `POST /setup-requests/parse` from the weighted objective. Measure parse latency separately by route and provider outcome. This is an initial API-server target, not an end-user browser or cold-start target; validate its feasibility against the existing k6 harness before adopting it as a release gate.
- Duration observations and slow-route records must use normalized route templates and bounded labels; never add request/response content, query strings, authorization values, IP/client identifiers, or user-supplied text to metrics or latency logs. Keep request IDs only in structured logs for correlation.

## Scope

- [ ] Define and verify the response-time SLO, request mix, database/catalogue fixture, load, warm-up, and measurement window, using the existing k6 release-confidence workflow where practical.
- [ ] Add route-template duration distributions to `/metrics` (histogram buckets/sum/count or equivalent Prometheus-compatible representation) while preserving useful existing counters and keeping label cardinality bounded.
- [ ] Make slow routes discoverable through aggregate metrics and structured logs with a documented threshold; preserve the existing low-data logging policy.
- [ ] Document backup, restore, migration failure/partial-application response, and rollback for local SQLite, Compose PostgreSQL, and the currently configured Render Free preview. Identify the Render Free durability limitation as a release/data-handling constraint and define the prerequisite for a durable hosted environment.
- [ ] Keep current API contracts and deterministic compatibility verdict behavior unchanged.

## Sequenced implementation steps

- [ ] 1. Inspect and reconcile this plan with the existing k6 release-confidence workflow, current `/metrics` and logging behavior, Alembic revisions, Compose startup, Render Blueprint, README, and migration rollout notes. Confirm the proposed workload can run reproducibly against disposable PostgreSQL.
- [ ] 2. Add a reproducible k6 scenario and result recording for the stated request mix. Separate setup-parser measurements; record dataset/revision, concurrency/rate, warm-up, measurement window, environment, p50/p95/p99, throughput, and error rate. Adjust only if measured baseline evidence shows the proposal is infeasible, and record the reason and revised target in this plan and roadmap.
- [ ] 3. Extend API metrics with HTTP request-duration distributions by method, normalized route template, and bounded status class/code as appropriate. Ensure all requests, including exceptions, are observed once; avoid raw paths for unmatched/parameterized routes. Keep metrics process-local limitations explicit and use the existing provider scrape/collector path rather than silently claiming cross-instance aggregation.
- [ ] 4. Add threshold-based slow-request structured events (initial threshold 500 ms, configurable if appropriate) using the same safe fields as request logs. Do not emit a second event for ordinary requests, and do not record request payloads, query strings, credentials, addresses, or setup descriptions.
- [ ] 5. Write environment-specific operational runbooks. For SQLite, stop the API and copy the configured DB file plus any required WAL/SHM state, or use SQLite's online backup API. For Compose PostgreSQL, demonstrate `pg_dump`/`pg_restore` against the named service/volume, verify the dump, and document restore to an isolated database before replacement. For Render, name the exact supported snapshot/export/restore controls for the selected plan; on Free, explicitly document that no provider backup exists and treat the database as disposable. Never imply a free-tier snapshot exists.
- [ ] 6. Document migration operations: confirm `DATABASE_URL` target and current revision, take/verify a recoverable pre-migration backup, pause writes/deployment retries after failure, capture logs and `alembic current/history`, inspect partial DDL/data state, recover on an isolated restored copy first, and choose restore versus downgrade based on known data loss and app/schema compatibility. Include post-recovery revision, readiness, catalogue, and representative check verification. Address automatic migrations at API startup and its retry behavior.
- [ ] 7. Update README operational notes, migration rollout notes, this plan's progress, and V2 roadmap/release checklist with only verified outcomes. Keep Workstream 7 open until all acceptance criteria are met.

## Acceptance criteria

- [ ] A maintainer can state and reproduce the API objective: p95 at or below 500 ms over a 30-minute steady-state window at 5 requests/second with the documented request proportions, against seeded PostgreSQL. The published result includes environment, candidate revision, sample count, percentiles, throughput, and error rate. Provider-backed parser latency is reported separately.
- [ ] `/metrics` reports request-duration distributions at bounded method/route/status cardinality, including routes that return errors, and slow routes can be identified without inspecting sensitive request data. Restart/multi-worker limitations are explicit unless aggregation is actually implemented.
- [ ] Slow-request logs identify request ID, method, route template, status, duration, and safe error category only. Tests or inspection demonstrate that query values, authorization material, bodies/setup prose, and client identifiers do not appear in metrics/logs.
- [ ] A maintainer can follow distinct, tested backup and recovery instructions for SQLite and Compose PostgreSQL. Hosted instructions match the selected Render plan and do not promise unavailable backups; use of non-disposable data is blocked until durable backups/recovery are available.
- [ ] The migration runbook covers preflight revision/target checks, backup verification, failed and partially applied migrations, safe recovery, destructive downgrade consequences, and post-recovery checks aligned with the actual startup command and migration history.
- [ ] V2 roadmap and release checklist link this plan and reflect completed evidence accurately; Workstream 7 is not marked complete before all preceding criteria are met.

## Verification approach

- [ ] Run the existing k6 workflow and a deterministic API request mix against a disposable PostgreSQL database after migrations and seeding. Preserve the raw k6 summary/artifact and the exact command/configuration with the recorded result. Do not run load against Render or shared data.
- [ ] Add focused observability tests for histogram buckets/count/sum, route-template labels, statuses/errors, and scrape format; confirm a request updates exactly one observation.
- [ ] Review captured JSON logs and rendered metrics using sentinel query/body/authorization values; assert they are absent. Exercise threshold crossings and exception paths.
- [ ] Exercise SQLite backup/restore and Compose PostgreSQL dump/restore against isolated copies, then verify Alembic revision, `/ready`, catalogue visibility, and a representative `/checks` result. Rehearse a failed/partial migration on a disposable database, not a shared or hosted database.
- [ ] Review the Render Free limitation against the checked-in Blueprint and current README. Validate any future durable provider procedure against that provider's current controls before documenting it as available.

## Dependencies and environment constraints

- Depends on the existing FastAPI middleware/metrics implementation, SQLAlchemy/Alembic migration chain, Compose PostgreSQL 16 configuration, `render.yaml`, and the scheduled/manual k6 Release confidence workflow.
- Render is not deployed, no production host or durable database plan is selected, and the configured Render Free database expires after 30 days without backups. Therefore an actual hosted backup/restore drill and host-level latency observation cannot be completed until an appropriate persistent environment is provisioned. Local disposable PostgreSQL can validate application and procedure behavior, but cannot establish provider recovery guarantees.
- The API's metrics are in-memory per process. A hosted multi-worker or multi-instance service needs a scrape/aggregation arrangement that preserves histogram semantics; do not treat independent process-local metrics as a fleet-wide SLO.
- External setup parsing depends on provider configuration and availability, so its performance baseline requires a configured provider/model and must be reported separately from the core API mix.

## Progress

- [x] Inspect the V2 roadmap, Workstream 6 plan, earlier workstream plans, current API observability, migration chain, database configuration, hosting Blueprint, and release-confidence workflow.
- [x] Create this implementation plan before beginning Workstream 7 implementation.
- [x] Update the V2 roadmap and release checklist to link the plan while leaving Workstream 7 incomplete.
- [ ] Verify the proposed latency mix against the existing k6 harness and record a reproducible baseline.
- [ ] Implement and verify duration distributions and safe slow-route visibility.
- [ ] Add and rehearse SQLite and PostgreSQL backup/restore and migration recovery procedures; document hosted-plan limits.
- [ ] Update operational docs and roadmap with verified results; keep any unavailable hosted drill explicit.
