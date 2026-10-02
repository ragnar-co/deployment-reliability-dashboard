import sqlite3
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

HDR = "deployment_id,service_name,status,duration_seconds,error_message,deployment_date,environment\n"
FIXTURE = (Path(__file__).parent / "fixtures" / "small.csv").read_text()
SAMPLE = Path(__file__).parent.parent / "theBeth_deployments_mock.csv"


@pytest.fixture
def client(tmp_path, monkeypatch):
    monkeypatch.setenv("DB_PATH", str(tmp_path / "t.db"))
    monkeypatch.delenv("MAX_UPLOAD_BYTES", raising=False)
    from app.main import app
    return TestClient(app)


@pytest.fixture
def db_count(tmp_path):
    def count(table="deployments"):
        c = sqlite3.connect(tmp_path / "t.db")
        try:
            return c.execute(f"select count(*) from {table}").fetchone()[0]
        finally:
            c.close()
    return count


def post(client, text, path="/api/import", name="x.csv"):
    data = text if isinstance(text, bytes) else text.encode()
    return client.post(path, files={"file": (name, data, "text/csv")})


def rows(*lines):
    return HDR + "".join(l + "\n" for l in lines)
