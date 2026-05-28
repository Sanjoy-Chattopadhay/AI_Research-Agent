import os
import tempfile

os.environ.setdefault("SECRET_KEY", "test-secret-key-must-be-at-least-thirty-two-chars-long")
_tmp = tempfile.mkdtemp()
os.environ["DATABASE_URL"] = f"sqlite:///{_tmp}/test.db"
os.environ["VECTOR_STORE_DIR"] = f"{_tmp}/vectors"
os.environ["UPLOAD_DIR"] = f"{_tmp}/uploads"

import pytest
from fastapi.testclient import TestClient

from app.config import get_settings
from app.database import init_db
from app.main import app


@pytest.fixture(scope="session", autouse=True)
def _setup():
    get_settings.cache_clear()
    init_db()


@pytest.fixture
def client():
    return TestClient(app)
