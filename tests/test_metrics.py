import pytest

from conftest import FIXTURE, HDR, post, rows


@pytest.fixture
def loaded(client):
    assert post(client, FIXTURE).status_code == 200
    return client


# TST-002 / FR-06 / AC-05 (hand-computed from tests/fixtures/small.csv)
def test_per_service_formulas_and_order(loaded):
    s = loaded.get("/api/services").json()["services"]
    assert [x["service_name"] for x in s] == ["delta", "beta", "alpha", "gamma"]  # lowest rate first
    by = {x["service_name"]: x for x in s}
    assert by["alpha"] == {"service_name": "alpha", "total": 3, "successes": 2, "failures": 1,
                           "success_rate": 66.67, "avg_success_seconds": 150.0}
    assert by["beta"]["success_rate"] == 33.33 and by["beta"]["avg_success_seconds"] == 300.0
    assert by["gamma"]["success_rate"] == 100.0 and by["gamma"]["avg_success_seconds"] == 100.0
    assert by["delta"]["success_rate"] == 0.0 and by["delta"]["avg_success_seconds"] is None  # no success: no avg


def test_failed_durations_excluded_from_average(loaded):
    assert loaded.get("/api/services?service=beta").json()["overall"]["avg_success_seconds"] == 300.0


def test_ties_break_on_failures_then_name(client):
    post(client, rows("A1,b,failed,5,e,2026-07-01,staging", "A2,a,failed,5,e,2026-07-01,staging",
                      "A3,a,failed,5,e,2026-07-01,staging", "A4,c,failed,5,e,2026-07-01,staging"))
    assert [x["service_name"] for x in client.get("/api/services").json()["services"]] == ["a", "b", "c"]


def test_rounding_is_half_up(client):
    # 1 success of 800 -> 0.125% : half-up gives 0.13, banker's rounding gives 0.12
    lines = ["S0,x,success,5,,2026-07-01,staging"] + [f"F{i},x,failed,5,e,2026-07-01,staging" for i in range(799)]
    assert post(client, rows(*lines)).status_code == 200
    assert client.get("/api/services").json()["overall"]["success_rate"] == 0.13


def test_average_rounding_is_half_up_to_two_decimals(client):
    # 199 x 1s + 1 x 2s = 201/200 = 1.005 s : half-up gives 1.01, banker's rounding gives 1.00
    lines = [f"A{i},x,success,1,,2026-07-01,staging" for i in range(199)] + ["B,x,success,2,,2026-07-01,staging"]
    post(client, rows(*lines))
    assert client.get("/api/services").json()["overall"]["avg_success_seconds"] == 1.01


# TST-003 / TST-021 / FR-07 / AC-06
def test_service_filter_changes_numbers_and_list(loaded):
    j = loaded.get("/api/services?service=alpha").json()
    assert j["overall"]["total"] == 3 and [x["service_name"] for x in j["services"]] == ["alpha"]
    f = loaded.get("/api/failures?service=alpha").json()
    assert f["total"] == 1 and f["items"][0]["error_message"] == "db connection refused"


def test_every_service_view_matches_independent_calculation(loaded):
    import csv, io
    data = list(csv.DictReader(io.StringIO(FIXTURE)))
    for svc in {r["service_name"] for r in data}:
        mine = [r for r in data if r["service_name"] == svc]
        ok = [int(r["duration_seconds"]) for r in mine if r["status"] == "success"]
        o = loaded.get(f"/api/services?service={svc}").json()["overall"]
        assert o["total"] == len(mine) and o["successes"] == len(ok) and o["failures"] == len(mine) - len(ok)
        assert o["success_rate"] == pytest.approx(len(ok) * 100 / len(mine), abs=0.005)


def test_unknown_service_is_empty_not_an_error(loaded):
    r = loaded.get("/api/services?service=nope")
    assert r.status_code == 200
    assert r.json() == {"overall": {"total": 0, "successes": 0, "failures": 0, "success_rate": None,
                                    "avg_success_seconds": None}, "services": []}
    assert loaded.get("/?service=nope").status_code == 200


# TST-010 / FR-11 / AC-10 (P1)
def test_environment_filter(loaded):
    o = loaded.get("/api/services?environment=staging").json()["overall"]
    assert (o["total"], o["successes"], o["failures"], o["avg_success_seconds"]) == (5, 3, 2, 83.33)
    f = loaded.get("/api/failures?environment=staging&service=alpha").json()
    assert f["total"] == 1


# TST-004 / FR-08 / AC-07
def test_failure_list_content_and_order(loaded):
    f = loaded.get("/api/failures").json()
    assert [i["deployment_id"] for i in f["items"]] == ["D010", "D006", "D004", "D003"]
    assert f["items"][1] == {"deployment_id": "D006", "service_name": "beta", "environment": "production",
                             "deployment_date": "2026-07-06", "duration_seconds": 20,
                             "error_message": "health-check timeout"}


def test_failure_ids_sort_as_text_on_same_date(client):
    post(client, rows("D9,a,failed,5,e,2026-07-01,staging", "D10,a,failed,5,e,2026-07-01,staging"))
    assert [i["deployment_id"] for i in client.get("/api/failures").json()["items"]] == ["D9", "D10"]


# TST-016
def test_pagination(client):
    post(client, rows(*[f"F{i:04d},a,failed,5,err {i},2026-07-01,staging" for i in range(250)]))
    assert client.get("/api/failures?limit=100&offset=200").json()["total"] == 250
    assert len(client.get("/api/failures?limit=100&offset=200").json()["items"]) == 50
    p1, p3 = client.get("/").text, client.get("/?page=3").text
    assert "Page 1 / 3" in p1 and "Next ›" in p1 and "Prev" not in p1
    assert "Page 3 / 3" in p3 and "Prev" in p3 and "Next" not in p3
    assert client.get("/?page=abc").status_code == 200 and "Page 1 / 3" in client.get("/?page=0").text
    far = client.get("/?page=99")
    assert far.status_code == 200 and "No failed deployments on this page" in far.text and "Prev" in far.text


@pytest.mark.parametrize("q", ["limit=0", "limit=1001", "limit=x", "offset=-1", "offset=1.5"])
def test_invalid_query_parameters(loaded, q):
    r = loaded.get(f"/api/failures?{q}")
    assert r.status_code == 422 and r.json()["code"] == "INVALID_PARAMETER"


# TST-008 / FR-09 / AC-08: numbers come from SQLite, never from the CSV
def test_numbers_do_not_depend_on_the_csv_file(loaded, tmp_path):
    assert list(tmp_path.glob("*.csv")) == []  # nothing retained
    assert loaded.get("/api/services").json()["overall"]["total"] == 10
