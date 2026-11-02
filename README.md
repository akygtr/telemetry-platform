# Machine Telemetry Platform

Small FastAPI service that takes readings from CNC machines and stores them in Postgres. A simulator stands in for the OPC-UA side for now.

The app is deliberately tiny. The point of this repo is everything around it: containers, CI/CD, Kubernetes, Terraform and monitoring.

## Status

- [x] Step 1: App, Docker, compose
- [ ] Step 2: CI (GitHub Actions)
- [ ] Step 3: Kubernetes on kind
- [ ] Step 4: Helm
- [ ] Step 5: Terraform on AWS
- [ ] Step 6: CD and rollback
- [ ] Step 7: Prometheus, Grafana, Loki
- [ ] Step 8: Failure drills and runbooks

## Layout

```
app/            FastAPI service (main.py, db.py, models.py, schemas.py)
simulator/      fake machines posting readings every few seconds
tests/          pytest, runs on SQLite so CI doesn't need Postgres
runbooks/       one file per failure I've caused and fixed
Dockerfile      multi-stage, non-root, healthcheck
docker-compose.yml  api + postgres + simulator
```

## Run it

From WSL2 Ubuntu, not PowerShell.

```bash
cp .env.example .env          # change the password
docker compose up --build
```

Then:

```bash
curl localhost:8000/health    # process is alive
curl localhost:8000/ready     # process can reach the DB
curl "localhost:8000/readings?machine_id=cnc-01&limit=5"
curl localhost:8000/metrics | grep readings_ingested
```

API docs at http://localhost:8000/docs

## Run tests without Docker

```bash
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements-dev.txt
pytest -q
flake8
```

## Endpoints

| Method | Path | What it's for |
|---|---|---|
| GET | /health | Liveness. Never touches the DB |
| GET | /ready | Readiness. Returns 503 if Postgres is unreachable |
| GET | /metrics | Prometheus scrape target |
| POST | /readings | Store one reading |
| GET | /readings | Latest readings, filter by `machine_id` |

`/health` and `/ready` are split on purpose. If the DB goes down, Kubernetes should stop sending traffic to the pod but not restart it. Restarting won't fix a dead database.

## Design notes

- Image is multi-stage so build tooling doesn't ship. Target is under 150MB.
- Container runs as uid 10001, not root.
- Compose waits for `pg_isready` before starting the API, so no startup race.
- Metric labels use the route template (`/readings`), not the raw URL. Raw URLs would blow up Prometheus cardinality.
- Tables are created on startup. That's fine until the schema changes, then it needs Alembic.
