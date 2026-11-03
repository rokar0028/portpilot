# PortPilot — Phase 7 Implementation Plan

## Goal

Prepare PortPilot for a credible public portfolio release: deploy the frontend, API, and database; monitor service and check failures; and provide clear project documentation and a short demonstration.

## Starting point

- Phase 6 is complete: the catalogue source review, desktop/mobile journey validation, and quality commands passed.
- The application has a Next.js frontend, FastAPI API, SQLAlchemy/Alembic persistence, PostgreSQL in Docker Compose, and an existing `/health` endpoint.
- Compose already waits for PostgreSQL and API health before starting dependent services.
- The README documents local and Compose workflows but lacks a concise architecture/design section and an interview-ready demo script.
- The workspace has a connected Render assistant integration, but no Render workspace has been selected for inspection. No production host, public domain, or portfolio destination is configured in the repository.
- The user requires a zero-cost path for now. Render Free can support a preview with limitations; its free PostgreSQL database expires after 30 days, so it does not meet the plan's persistent-database criterion.
- Supabase is now installed and its organization is accessible. Vercel account tools also respond, though the earlier screenshot showed its plugin panel still requesting connection. Existing Vercel and Supabase projects are unrelated to PortPilot; none were changed.

## Plan review

- Treat Phase 6 completion as the release gate for public deployment. Phase 7 preparation can proceed locally, but do not publish an unreviewed catalogue or claim passing checks that have not been run.
- Keep the Dockerized deployment portable until the user/project context establishes a hosting target. Record platform-specific choices and required secrets before adding provider configuration.
- Keep public health checks free of credentials and database details. Monitoring must make API errors and failed/uncertain checks observable without logging secrets or user-submitted sensitive data.
- Document architecture, key decisions, sources policy, verified check-scenario count, and limitations from confirmed repository state.
- Prepare a demo around existing seeded cases: a fully documented compatible setup and a documented incompatible display-count setup. Recheck their exact outputs before recording.
- Keep all deployment choices within free tiers while the user requires zero cost. Disclose host sleep, storage, inactivity, and usage limits before relying on a free tier for the public demo.
- Treat public deployment and portfolio publication as separate actions requiring an inspected/selected provider workspace and a portfolio destination.

## Work plan

### 1. Prepare project documentation and demo

- [x] Add a concise architecture diagram and design decisions to the README.
- [x] Document the sources policy, verified catalogue scope, test/quality status, and known limitations accurately.
- [x] Create a 90-second demo outline with setup instructions, candidate compatible/incompatible scenarios, and evidence to show.
- [x] Reconfirm scenario outputs and source links before recording.

### 2. Add portable operational monitoring

- [x] Add structured API request/error logs with request path, status, elapsed time, and request correlation ID.
- [x] Record compatibility verdict counts and rule-engine version without logging request bodies or credentials.
- [x] Preserve a simple public liveness endpoint and add a readiness check for the configured database.
- [x] Document log fields, retention expectations, and provider-neutral monitoring integration points.

### 3. Select and configure deployment target

- [x] Compare viable free frontend, API, and PostgreSQL hosting options against cost, region, environment variables, persistence, and Docker support.
- [ ] Confirm the deployment target, public origins, domain, and required secrets before committing provider-specific manifests.
- [x] Prepare a free Render preview Blueprint with database references, generated admin token, CORS origin wiring, health checks, migrations, and seeding.
- [x] Create the private GitHub repository and push the phase-wise commit history.
- [ ] Connect the private repository to Render so it can read the Blueprint and deploy it.
- [ ] Deploy the three components and verify public health, catalogue reads, compatibility checks, and shared result URLs.

### 4. Release and portfolio handoff

- [ ] Configure provider-side alerting/retention for API errors and service availability after a provider workspace is selected; application metrics endpoint is implemented.
- [ ] Record and review a 90-second demo with compatible and incompatible scenarios.
- [ ] Add verified live app, repository, and demo links to the chosen portfolio destination.
- [ ] Update README and this plan with deployment architecture, check results, and operational limitations.

## Acceptance criteria

- The Phase 6 release gate is complete before public release.
- A public deployment runs the frontend, API, and persistent database with migrations and secure configuration.
- Service errors and compatibility verdict outcomes can be monitored without storing request bodies or secrets in logs.
- README explains architecture, key design choices, evidence policy, verified validation status, and known limitations.
- A reviewed demo shows one supported setup and one incompatible setup with manufacturer evidence.
- Public links and deployment behavior are verified before portfolio publication.

## Exit condition

Phase 7 is complete when the reviewed application is deployed, operational monitoring is active, project documentation is accurate, a concise demo is recorded, and the live/repository/demo links are present in the portfolio.

## Progress

- [x] Reviewed Phase 7 roadmap scope against the current repository and Phase 6 status.
- [x] Created and reviewed this plan, including a Phase 6 release gate.
- [x] Added README architecture/design notes, evidence policy, current catalogue scope, scenario count caveat, Phase 6 status, and operations/monitoring notes.
- [x] Prepared a 90-second demo outline and revalidated compatible/incompatible scenarios and evidence links.
- [x] Added portable operational monitoring: structured logs, request IDs, `/ready`, `/metrics`, and safe failure responses.
- [x] Completed and verified the Phase 6 release gate.
- [x] Compared free hosting options and inspected the selected Render workspace through the connected assistant integration; it contains two unrelated Free web services and no PortPilot services.
- [x] Prepared the Render free preview Blueprint and documented the 30-day database expiry and spin-down behavior.
- [x] Create the private GitHub repository and push the phase-wise commit history.
- [ ] Connect the private repository to Render and verify Blueprint deployment eligibility.
- [ ] Record and review the 90-second demo.
- [ ] Deploy, verify public behavior, configure provider-side monitoring, and publish verified links to the chosen portfolio destination.

Current status: Phase 7's local implementation is prepared. The README and demo outline are current, portable health/metrics/logging are implemented, and the Render preview Blueprint parses as YAML. The private GitHub repository and phase-wise commit history are available; a Render connection remains unconfirmed. Phase 7 is not complete: no public deployment, provider-side alerts, recorded video, or portfolio publication exists yet. Supabase is installed and accessible; Vercel account tools respond, but the earlier panel screenshot indicated that its plugin setup may still need completion. Existing Vercel and Supabase projects belong to unrelated apps and were left untouched.
