"""FEATURE_CHECKLIST.md section 5: the two supplied files in test_data/."""
from pathlib import Path

import pytest

from conftest import post

DATA = Path(__file__).parent.parent / "test_data"


@pytest.mark.skipif(not (DATA / "deployments_valid.csv").exists(), reason="test_data not present")
def test_valid_file_matches_checklist_totals(client, db_count):
    r = post(client, (DATA / "deployments_valid.csv").read_bytes(), name="deployments_valid.csv")
    assert r.status_code == 200 and r.json()["rows"] == 1000
    o = client.get("/api/services").json()["overall"]
    assert (o["successes"], o["failures"], o["success_rate"], o["avg_success_seconds"]) == (851, 149, 85.1, 325.11)
    assert "Imported 1,000 deployments (851 successful, 149 failed)." in post(
        client, (DATA / "deployments_valid.csv").read_bytes().replace(b"TST-", b"TSX-"), path="/upload").text


@pytest.mark.skipif(not (DATA / "deployments_invalid.csv").exists(), reason="test_data not present")
def test_invalid_file_rejected_with_no_partial_import(client, db_count):
    r = post(client, (DATA / "deployments_invalid.csv").read_bytes(), name="deployments_invalid.csv")
    assert r.status_code == 422 and r.json()["code"] == "VALIDATION_FAILED"
    assert db_count() == 0 and db_count("import_batches") == 0
