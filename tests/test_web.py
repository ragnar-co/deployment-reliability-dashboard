import json
import logging

import pytest

from conftest import FIXTURE, SAMPLE, post, rows


# TST-009 / FR-10 / AC-09
def test_health_ok(client):
    assert client.get("/health").json() == {"status": "ok"}


def test_health_unavailable_when_db_cannot_open(client, monkeypatch, tmp_path):
    monkeypatch.setenv("DB_PATH", str(tmp_path))  # a directory, not a file
    r = client.get("/health")
    assert r.status_code == 503 and r.json() == {"status": "unavailable"}


# TST-017 empty state
def test_empty_state(client):
    page = client.get("/").text
    assert "No data yet" in page and "By service" not in page
    assert client.get("/api/failures").json() == {"total": 0, "items": []}


# E2E-01..04 over the HTML form
def test_upload_form_flow(client):
    r = post(client, FIXTURE, path="/upload")
    assert r.status_code == 200 and "Imported 10 deployments (6 successful, 4 failed)." in r.text
    page = client.get("/?service=alpha").text
    assert "db connection refused" in page and "missing APP_CONFIG" not in page
    # all services stay selectable while one is selected (TST-021)
    for s in ("alpha", "beta", "gamma", "delta"):
        assert f'<option value="{s}"' in page
    first_row = client.get("/").text.split("<tbody>")[1]
    assert first_row.index("delta") < first_row.index("beta") < first_row.index("alpha")  # CP-03


def test_upload_form_rejection_shows_reasons_and_saves_nothing(client, db_count):
    r = post(client, "a,b\n1,2\n", path="/upload")
    assert r.status_code == 422 and "nothing was saved" in r.text and "Missing required column" in r.text
    assert db_count() == 0
    dup = post(client, FIXTURE, path="/upload"); again = post(client, FIXTURE, path="/upload")
    assert again.status_code == 409 and "already imported" in again.text


# TST-012 / SC-02 / THR-04: every field rendered from the CSV is escaped
def test_html_escaping_of_every_displayed_field(client):
    x = "<script>alert(1)</script>"
    post(client, rows(f"{x}1,{x}svc,failed,5,{x}err,2026-07-01,{x}env"))
    page = client.get("/").text + client.get("/", params={"service": x + "svc"}).text
    assert x not in page and "&lt;script&gt;" in page


# TST-013 / TC-06
def test_sql_metacharacters_in_filters_are_harmless(client):
    post(client, FIXTURE)
    for v in ["'", "'; DROP TABLE deployments;--", "alpha' OR '1'='1", "%", "_"]:
        assert client.get("/api/services", params={"service": v}).json()["overall"]["total"] == 0
        assert client.get("/api/failures", params={"environment": v}).json()["total"] == 0
    assert client.get("/api/services").json()["overall"]["total"] == 10


# TST-014 / SC-03
def test_garbage_binary_file_rejected(client):
    r = post(client, bytes(range(256)) * 4)
    assert r.status_code == 422 and r.json()["code"] == "INVALID_FILE"


# TST-020 / TC-07 / NFR-03
def test_size_limit_boundary(client, db_count, monkeypatch):
    limit = 10 * 1024 * 1024
    head = rows("")  # header only
    def padded(size):
        line = "Z1,svc,success,5,,2026-07-01,staging"
        base = (head.rstrip("\n") + "\n" + line + "\n").encode()
        assert size >= len(base)
        return base + b"\n" * (size - len(base))  # blank lines are ignored by the parser
    assert post(client, padded(limit)).status_code == 200  # exactly 10 MiB passes
    too_big = post(client, padded(limit + 1))
    assert too_big.status_code == 413 and too_big.json()["code"] == "FILE_TOO_LARGE"
    assert "10 MB" in too_big.json()["errors"][0] and db_count() == 1


def test_size_limit_via_form_shows_error_box_and_saves_nothing(client, db_count, monkeypatch):
    monkeypatch.setenv("MAX_UPLOAD_BYTES", "100")
    r = post(client, FIXTURE, path="/upload")
    assert r.status_code == 413 and "nothing was saved" in r.text and "File exceeds the maximum" in r.text
    assert db_count() == 0


# TST-022 (HTML side; selecting a large file in a browser is a manual check)
def test_page_carries_client_limit_and_hidden_warning(client, monkeypatch):
    page = client.get("/").text
    assert 'data-max-bytes="10485760"' in page and "max 10 MB" in page
    assert 'id="size-warning"' in page and 'role="alert"' in page and "hidden" in page
    monkeypatch.setenv("MAX_UPLOAD_BYTES", "2097152")
    page = client.get("/").text
    assert 'data-max-bytes="2097152"' in page and "max 2 MB" in page


@pytest.mark.parametrize("bad", ["0", "-5", "abc"])
def test_invalid_max_upload_bytes_config_fails_loudly(client, monkeypatch, bad):
    monkeypatch.setenv("MAX_UPLOAD_BYTES", bad)
    with pytest.raises(RuntimeError):
        client.get("/")


# TST-015 / ARCHITECTURE Observability
def test_json_logs_with_correlation_id(client, caplog):
    from app import logging_setup
    with caplog.at_level(logging.INFO, logger="app"):
        r = client.get("/health", headers={"X-Request-ID": "abc-123"})
        assert r.headers["X-Request-ID"] == "abc-123"
        records = [x for x in caplog.records if x.name == "app" and x.getMessage() == "request"]
        assert records
        line = json.loads(logging_setup.JsonFormatter().format(records[-1]))
        assert line["event"] == "request" and line["path"] == "/health" and line["status"] == 200
        assert {"ts", "level", "correlation_id"} <= set(line)
        assert client.get("/health").headers["X-Request-ID"]  # generated when absent


def test_rejection_log_has_code_but_not_row_content(client, caplog):
    from app import logging_setup
    with caplog.at_level(logging.INFO, logger="app"):
        post(client, rows("D1,a,success,5,secret-error-text,2026-07-01,staging"))
        rec = [x for x in caplog.records if x.getMessage() == "import_rejected"][-1]
        text = logging_setup.JsonFormatter().format(rec)
        assert "VALIDATION_FAILED" in text and "secret-error-text" not in text


# TST-011 / AC-04, AC-05: only when the real sample file is present
@pytest.mark.skipif(not SAMPLE.exists(), reason="sample CSV is not committed")
def test_supplied_sample_matches_reference_totals(client):
    r = client.post("/api/import", files={"file": ("s.csv", SAMPLE.read_bytes(), "text/csv")})
    assert r.status_code == 200 and r.json()["rows"] == 36527
    j = client.get("/api/services").json()
    o = j["overall"]
    assert (o["successes"], o["failures"], o["success_rate"], o["avg_success_seconds"]) == (33643, 2884, 92.1, 187.8)
    assert len(j["services"]) == 24
    w = j["services"][0]
    assert (w["service_name"], w["failures"], w["success_rate"]) == ("release-validator", 316, 79.29)


# TST-023 / UI_SPEC: refreshing after a successful upload must not re-submit the file
def test_successful_upload_redirects_so_refresh_is_safe(client, db_count):
    r = client.post("/upload", files={"file": ("x.csv", FIXTURE.encode(), "text/csv")}, follow_redirects=False)
    assert r.status_code == 303 and r.headers["location"].startswith("/?imported=10&successful=6&failed=4")
    page = client.get(r.headers["location"])
    assert page.status_code == 200 and "Imported 10 deployments (6 successful, 4 failed)." in page.text
    again = client.get(r.headers["location"])  # what a browser refresh does now
    assert again.status_code == 200 and "already imported" not in again.text
    assert db_count() == 10 and db_count("import_batches") == 1


def test_forged_import_message_params_are_ignored_unless_numeric(client):
    page = client.get("/", params={"imported": "<b>x</b>", "successful": "1", "failed": "1"}).text
    assert "<b>x</b>" not in page and "Imported" not in page
