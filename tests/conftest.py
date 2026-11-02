import os
import sys
from pathlib import Path

import pytest

# Tests run against a throwaway SQLite file, no Postgres needed in CI step 2
os.environ["DATABASE_URL"] = "sqlite:///./test_telemetry.db"
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from fastapi.testclient import TestClient  # noqa: E402

from app.db import engine  # noqa: E402
from app.main import app  # noqa: E402


@pytest.fixture(scope="session")
def client():
    # One DB for the whole run. Deleting the file between tests while the
    # connection pool still has it open gives "readonly database" errors.
    with TestClient(app) as c:
        yield c
    engine.dispose()
    Path("test_telemetry.db").unlink(missing_ok=True)
