# PortPilot

PortPilot checks whether a laptop and accessory support a requested setup. Verdicts come from deterministic rules over documented specifications; missing required facts produce **Insufficient data**.

## Current vertical slice

- Laptop: Lenovo IdeaPad Slim 3 14IRH10R
- Accessory: Anker 364 USB-C Hub (10-in-1, Dual 4K HDMI)
- Setup: one 1080p external display plus laptop charging

The manufacturer sources confirm USB-C DisplayPort 1.2 and USB Power Delivery on the laptop, and HDMI plus up to 85 W pass-through on the hub. They do not establish every requirement for this setup, so PortPilot deliberately reports **Insufficient data** rather than guessing. The catalogue is currently in memory and contains only this starter pair.

## Prerequisites

- Python 3.12 or later
- Node.js 20 or later and npm
- Docker Desktop with Compose (optional, for the combined workflow)

## Run locally

### API

```powershell
cd api
Copy-Item .env.example .env
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements-dev.txt
uvicorn app.main:app --reload
```

The API is at http://localhost:8000, its health endpoint is http://localhost:8000/health, and interactive API docs are at http://localhost:8000/docs.

### Frontend

In another terminal:

```powershell
cd web
Copy-Item .env.example .env.local
npm ci
npm run dev
```

Open http://localhost:3000. Set `NEXT_PUBLIC_API_URL` in `web/.env.local` to point the browser to a different API origin.

## Run both with Docker Compose

From the project root:

```powershell
docker compose up --build
```

Open http://localhost:3000. Compose waits for the API health check before starting the frontend. Stop the services with `Ctrl+C`, then run `docker compose down`.

## Quality commands

Run these from the indicated directory:

```powershell
# api/
ruff check app
ruff format --check app

# web/
npm run lint
npm run format:check
npm run build
```

CI runs these checks on pushes and pull requests. Format code with `ruff format app` and `npm run format`.

## Project structure

```text
api/     FastAPI service and deterministic compatibility rules
web/     Next.js user interface
.github/ GitHub Actions checks
```

## Scope and limitations

PortPilot is an early compatibility checker, not a retailer search or recommendation service. It does not scrape marketplace listings, infer unsupported capabilities, or diagnose hardware faults. PostgreSQL persistence, catalogue administration, broader device coverage, and deployment are planned for later phases.
