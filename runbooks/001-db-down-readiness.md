# Postgres down, API stays alive but not ready

**Date:** fill in when you reproduce it yourself
**Where:** compose

## Symptom

`/ready` returns 503 `database unavailable`. `/health` still returns 200. Simulator logs `send failed`.

I saw nothing.

## Impact

No readings stored. API process is up, so a naive health check would say everything is fine.

## How I found it

```bash
docker compose ps                 # db container exited or unhealthy
curl -i localhost:8000/ready      # 503
docker compose logs api | tail    # "readiness check failed: ... connection refused"
```

## Root cause

Postgres container stopped (`docker compose stop db` to reproduce).

## Fix

`docker compose start db`. API recovers on its own because `pool\_pre\_ping=True` throws away dead connections.

## Prevention

* Kubernetes readiness probe on `/ready`, liveness on `/health` (step 3)
* Alert on readiness failures and on `readings\_ingested\_total` going flat (step 7)

