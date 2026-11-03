# PortPilot — Phase 1 Implementation Plan

## Goal

Make the current Next.js frontend and FastAPI backend a reliable local development foundation. A new developer should be able to clone the repository, follow the README, start both applications, and see a clear service-health check.

## Current starting point

- [x] A project README describes the product, initial vertical slice, and local start commands.
- [x] A Next.js frontend scaffold and FastAPI backend scaffold exist in separate `web/` and `api/` directories.
- [x] The API has a health route, catalogue route, check endpoint, and deterministic starter rules.
- [ ] The workspace is not yet a Git repository.
- [ ] Dependencies have not been installed or the run instructions verified.
- [ ] Docker Compose, environment examples, lint/format configuration, and CI are not yet present.

## Work plan

### 1. Establish repository and project conventions

- [ ] Initialize Git in the project root and make the initial foundation commit.
- [ ] Keep the `api/` and `web/` applications independently installable.
- [ ] Add root-level contribution notes for naming, formatting, and how to run each app.
- [ ] Confirm `.gitignore` covers Python environments/cache, Node dependencies, Next build output, and local secrets.

**Output:** a clean repository with a first commit and no generated or secret files tracked.

### 2. Make local startup reproducible

- [ ] Verify the backend install and run commands from a clean Python environment.
- [ ] Verify the frontend install and run commands from a clean Node environment.
- [ ] Add `api/.env.example` and `web/.env.example` for configurable service URLs and future database settings.
- [ ] Configure the frontend API URL through `NEXT_PUBLIC_API_URL`, with the local API URL as the documented default.
- [ ] Add a root `docker-compose.yml` to start the frontend and API together for local development.
- [ ] Add container definitions and health checks if needed for reliable Compose startup.

**Output:** one documented local workflow works both with direct commands and Docker Compose.

### 3. Align API and frontend development settings

- [ ] Add backend formatting and lint configuration, such as Ruff, with a small set of consistent rules.
- [ ] Add frontend lint and formatting configuration compatible with the selected Next.js version.
- [ ] Update package scripts so lint and format commands use supported tooling.
- [ ] Restrict CORS to the configured local frontend origin and document how to change it for deployment.
- [ ] Ensure API errors are returned in a predictable shape that the frontend can display.

**Output:** contributors can run the same formatter and linter locally and get useful, consistent API errors.

### 4. Add basic continuous integration

- [ ] Add a GitHub Actions workflow triggered on pushes and pull requests.
- [ ] Install backend dependencies and run formatting/lint checks.
- [ ] Install frontend dependencies and run lint plus a production build.
- [ ] Keep CI limited to quick quality checks; add test suites with the later compatibility-engine phase.

**Output:** a pull request reports whether both applications pass their foundation checks.

### 5. Clarify setup and troubleshooting documentation

- [ ] Update the README with prerequisites, exact setup commands, both local workflows, and expected local URLs.
- [ ] Document how to reach FastAPI's `/docs` and `/health` routes.
- [ ] Add a short troubleshooting section for missing dependencies, ports in use, and frontend-to-API connection errors.
- [ ] Explain that the catalogue is currently in memory and that its conservative verdicts are limited to the starter records.

**Output:** a first-time contributor can start both services without relying on undocumented steps.

## Suggested implementation order

1. Initialize Git and review the ignore rules.
2. Add environment examples and make API URL configuration explicit.
3. Verify and document direct local startup.
4. Add lint/format tools and supported package scripts.
5. Add Docker Compose and health checks.
6. Add CI and finish README setup/troubleshooting notes.

## Phase 1 acceptance criteria

- [ ] The project is a Git repository with a clean initial foundation commit.
- [ ] The API starts locally and responds successfully at `/health`.
- [ ] The frontend starts locally and can reach the API using its environment setting.
- [ ] Docker Compose starts both services using documented commands.
- [ ] No credentials or machine-specific environment files are committed.
- [ ] Backend and frontend lint/format commands are documented and operational.
- [ ] CI runs the foundation checks on pushes and pull requests.
- [ ] The README accurately reflects what is implemented and how to run it.

## Exit condition

Phase 1 is complete when a clean checkout can be started through the documented workflow and CI confirms that the frontend and backend foundation checks pass. The in-memory catalogue and narrow compatibility rules remain the Phase 2 and Phase 3 work surface.
