import logging
import os
import time
from contextlib import asynccontextmanager

from fastapi import Depends, FastAPI, HTTPException, Request, Response
from prometheus_client import CONTENT_TYPE_LATEST, Counter, Histogram, generate_latest
from sqlalchemy import select, text
from sqlalchemy.orm import Session

from app.db import Base, engine, get_db
from app.models import Reading
from app.schemas import ReadingIn, ReadingOut

logging.basicConfig(
    level=os.getenv("LOG_LEVEL", "INFO"),
    format="%(asctime)s %(levelname)s %(name)s %(message)s",
)
log = logging.getLogger("telemetry")

# Metrics you'll graph in Grafana later (step 7)
REQUESTS = Counter("http_requests_total", "HTTP requests", ["method", "path", "status"])
LATENCY = Histogram("http_request_duration_seconds", "Request latency", ["path"])
READINGS = Counter("readings_ingested_total", "Readings stored", ["machine_id"])


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Fine for now. Swap for Alembic migrations once the schema starts changing.
    Base.metadata.create_all(bind=engine)
    log.info("startup complete")
    yield


app = FastAPI(title="Machine Telemetry API", version=os.getenv("APP_VERSION", "dev"), lifespan=lifespan)


@app.middleware("http")
async def track_requests(request: Request, call_next):
    start = time.perf_counter()
    response = await call_next(request)
    route = request.scope.get("route")
    path = route.path if route else "unmatched"  # avoid label explosion from random URLs
    LATENCY.labels(path).observe(time.perf_counter() - start)
    REQUESTS.labels(request.method, path, response.status_code).inc()
    return response


@app.get("/health")
def health():
    """Liveness: is the process up. Never touches the DB."""
    return {"status": "ok", "version": app.version}


@app.get("/ready")
def ready(db: Session = Depends(get_db)):
    """Readiness: can we actually serve traffic. Fails if the DB is unreachable."""
    try:
        db.execute(text("SELECT 1"))
    except Exception as exc:
        log.error("readiness check failed: %s", exc)
        raise HTTPException(status_code=503, detail="database unavailable")
    return {"status": "ready"}


@app.get("/metrics")
def metrics():
    return Response(generate_latest(), media_type=CONTENT_TYPE_LATEST)


@app.post("/readings", response_model=ReadingOut, status_code=201)
def create_reading(payload: ReadingIn, db: Session = Depends(get_db)):
    reading = Reading(**payload.model_dump())
    db.add(reading)
    db.commit()
    db.refresh(reading)
    READINGS.labels(reading.machine_id).inc()
    return reading


@app.get("/readings", response_model=list[ReadingOut])
def list_readings(machine_id: str | None = None, limit: int = 50, db: Session = Depends(get_db)):
    limit = max(1, min(limit, 500))
    stmt = select(Reading).order_by(Reading.recorded_at.desc()).limit(limit)
    if machine_id:
        stmt = stmt.where(Reading.machine_id == machine_id)
    return db.scalars(stmt).all()
