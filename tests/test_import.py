import pytest

from conftest import FIXTURE, HDR, post, rows

# TST-001 / AC-01 / AC-04
def test_valid_import_and_totals(client):
    r = post(client, FIXTURE)
    assert r.status_code == 200
    assert r.json() == {"batch_id": 1, "rows": 10, "successful_deployments": 6, "failed_deployments": 4}
    assert client.get("/api/services").json()["overall"] == {
        "total": 10, "successes": 6, "failures": 4, "success_rate": 60.0, "avg_success_seconds": 150.0}


# TST-005 / AC-02 / FR-02 / FR-03
BAD = [
    (FIXTURE.replace("D001,alpha,success", "D001,alpha,ok"), "status must be"),
    (FIXTURE.replace("D001,alpha,success", "D001,alpha,Success"), "status must be"),
    (FIXTURE.replace("2026-07-01", "2026-13-40"), "ISO YYYY-MM-DD"),
    (FIXTURE.replace("2026-07-01", "2026-7-1"), "ISO YYYY-MM-DD"),
    (FIXTURE.replace(",100,", ",0,"), "positive integer"),
    (FIXTURE.replace(",100,", ",-5,"), "positive integer"),
    (FIXTURE.replace(",100,", ",1.5,"), "positive integer"),
    (FIXTURE.replace("db connection refused", ""), "error_message is required"),
    (FIXTURE.replace("D001,alpha,success,100,", "D001,alpha,success,100,oops"), "must be empty"),
    (FIXTURE.replace("D001,alpha", "D001,"), "service_name is required"),
    (FIXTURE.replace(",2026-07-01,staging", ",2026-07-01,"), "environment is required"),
    (FIXTURE.replace("D001,alpha,success,100,,2026-07-01,staging", "D001,alpha,success"), "expected 7 fields"),
]


@pytest.mark.parametrize("bad,needle", BAD)
def test_invalid_rows_rejected_without_partial_data(client, db_count, bad, needle):
    r = post(client, bad)
    assert r.status_code == 422 and r.json()["code"] == "VALIDATION_FAILED"
    assert needle in " ".join(r.json()["errors"])
    assert db_count() == 0 and db_count("import_batches") == 0


# TST-018 / LC-01 / API_SPEC file format
@pytest.mark.parametrize("bad", [
    "deployment_id,service_name\nD1,a\n",                                    # missing columns
    FIXTURE.replace("environment", "environment,extra", 1).replace("staging", "staging,x"),  # extra column
    FIXTURE.replace("deployment_id", "Deployment_ID", 1),                    # wrong case
    FIXTURE.replace("environment", "environment,service_name", 1),           # duplicate column
    HDR,                                                                     # no data rows
    "",                                                                      # empty file
])
def test_invalid_file_rejected(client, db_count, bad):
    r = post(client, bad)
    assert r.status_code == 422 and r.json()["code"] == "INVALID_FILE"
    assert db_count() == 0


def test_non_utf8_rejected(client, db_count):
    r = post(client, FIXTURE.replace("alpha", "café", 1).encode("latin-1"))
    assert r.status_code == 422 and r.json()["code"] == "INVALID_FILE"
    assert db_count() == 0


def test_bom_crlf_reordered_columns_and_whitespace_accepted(client):
    text = ("﻿" + "environment,deployment_id,status,service_name,error_message,duration_seconds,deployment_date\r\n"
            " staging , D1 ,failed, alpha , boom ,7,2026-07-01\r\n")
    r = post(client, text)
    assert r.status_code == 200, r.text
    item = client.get("/api/failures").json()["items"][0]
    assert (item["deployment_id"], item["service_name"], item["environment"], item["error_message"]) == \
        ("D1", "alpha", "staging", "boom")


def test_in_file_duplicate_is_validation_error_with_row_numbers(client):
    r = post(client, rows("D1,a,success,5,,2026-07-01,staging", "D2,a,success,5,,2026-07-01,staging",
                          "D1,a,success,5,,2026-07-01,staging"))
    j = r.json()
    assert r.status_code == 422 and j["code"] == "VALIDATION_FAILED"
    assert j["errors"] == ["Row 4: duplicate deployment_id D1 (first seen at row 2)"]


def test_error_list_capped_at_20_in_file_order(client):
    r = post(client, rows(*[f"D{i},a,bogus,5,,2026-07-01,staging" for i in range(30)]))
    errs = r.json()["errors"]
    assert len(errs) == 20 and errs[0].startswith("Row 2:") and errs[-1].startswith("Row 21:")


# TST-006 / FR-04 / AC-03
def test_exact_repeat_upload_detected(client, db_count):
    assert post(client, FIXTURE).status_code == 200
    r = post(client, FIXTURE)
    assert r.status_code == 409 and r.json()["code"] == "DUPLICATE_FILE"
    msg = r.json()["errors"][0]  # tells the user the data is already there and nothing changed
    assert "already imported on" in msg and "batch #1" in msg and "10 deployments" in msg
    assert msg.endswith("Nothing was changed.") and msg.split(" on ")[1][:4] == "2026"
    assert db_count() == 10 and db_count("import_batches") == 1


# TST-007
def test_existing_deployment_id_rejects_whole_file_and_rolls_back(client, db_count):
    post(client, FIXTURE)
    r = post(client, rows("D900,gamma,success,5,,2026-08-01,staging", "D001,alpha,failed,1,x,2026-08-01,staging"))
    assert r.status_code == 409 and r.json()["code"] == "DUPLICATE_DEPLOYMENT"
    assert db_count() == 10 and db_count("import_batches") == 1


def test_check_order_duplicate_file_before_row_validation(client):
    post(client, FIXTURE)
    r = post(client, FIXTURE)  # identical content: must say DUPLICATE_FILE, not DUPLICATE_DEPLOYMENT
    assert r.json()["code"] == "DUPLICATE_FILE"


def test_check_order_invalid_file_before_duplicate_file(client):
    assert post(client, "x,y\n1,2\n").json()["code"] == "INVALID_FILE"


def test_import_busy_when_database_locked(client, tmp_path):
    import sqlite3
    from app import db
    post(client, FIXTURE)
    blocker = sqlite3.connect(tmp_path / "t.db", isolation_level=None)
    blocker.execute("BEGIN IMMEDIATE")
    try:
        r = post(client, rows("Z1,z,success,5,,2026-07-01,staging"))
    finally:
        blocker.execute("ROLLBACK"); blocker.close()
    assert r.status_code == 503 and r.json()["code"] == "IMPORT_BUSY"


def test_missing_file_part(client):
    r = client.post("/api/import")
    assert r.status_code == 422 and r.json()["code"] == "INVALID_FILE"


def test_blank_lines_are_ignored_and_row_numbers_still_count_them(client):
    assert post(client, FIXTURE + "\n\n").status_code == 200
    r = post(client, rows("D1,a,success,5,,2026-07-01,staging", "", "D2,a,bogus,5,,2026-07-01,staging"))
    assert r.json()["errors"] == ["Row 4: status must be 'success' or 'failed', got 'bogus'"]
