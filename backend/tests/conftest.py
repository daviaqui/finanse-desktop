import os
import tempfile
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

_test_directory = tempfile.TemporaryDirectory(prefix="finanse-tests-")
os.environ["FINANSE_DATA_DIR"] = _test_directory.name
os.environ["FINANSE_TOKEN"] = "test-credential-" + "a" * 48

from app.core.config import TOKEN  # noqa: E402
from app.db.migrations import initialize  # noqa: E402
from app.db.session import engine  # noqa: E402
from app.main import app  # noqa: E402


@pytest.fixture(autouse=True)
def reset_database():
    engine.dispose()
    for path in Path(_test_directory.name).glob("*.sqlite3*"):
        path.unlink()
    initialize()
    yield
    engine.dispose()


@pytest.fixture
def client():
    with TestClient(app) as client:
        yield client


@pytest.fixture
def auth_headers():
    return {"Authorization": f"Bearer {TOKEN}"}
