import os
import tempfile

# À définir AVANT d'importer l'application
_db = os.path.join(tempfile.mkdtemp(), "test.db")
os.environ.setdefault("SECRET_KEY", "test-secret-key-test-secret-key-test-secret-key")
os.environ["DATABASE_URL"] = f"sqlite:///{_db}"
os.environ["PRELOAD_MODELS"] = "False"
os.environ["RATELIMIT_ENABLED"] = "False"
os.environ["AUTO_CREATE_TABLES"] = "True"

import pytest  # noqa: E402


@pytest.fixture(scope="session")
def client():
    from fastapi.testclient import TestClient

    from main import app

    with TestClient(app) as c:
        yield c
