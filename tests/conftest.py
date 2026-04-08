import pytest
from fastapi.testclient import TestClient


@pytest.fixture
def app(tmp_path, monkeypatch):
    """Yields (TestClient, db_path_str). Each test gets a fresh SQLite file."""
    db_path = str(tmp_path / "test.db")
    monkeypatch.setenv("DATABASE_PATH", db_path)
    from backend.server import Server
    with TestClient(Server.app) as c:
        yield c, db_path
