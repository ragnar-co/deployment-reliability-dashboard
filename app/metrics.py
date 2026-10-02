"""Every dashboard number is read from SQLite (CONSTRAINTS TC-05); filters are parameterized."""
import sqlite3
from decimal import ROUND_HALF_UP, Decimal


def _where(service: str | None, environment: str | None, extra: str = ""):
    clauses, params = [], []
    if service:
        clauses.append("service_name = ?")
        params.append(service)
    if environment:
        clauses.append("environment = ?")
        params.append(environment)
    if extra:
        clauses.append(extra)
    return (" WHERE " + " AND ".join(clauses)) if clauses else "", params


def _rate(successes: int, total: int):
    if not total:
        return None
    return float((Decimal(successes) * 100 / Decimal(total)).quantize(Decimal("0.01"), ROUND_HALF_UP))


def _avg(duration_sum, count):
    if not count:
        return None
    return float((Decimal(duration_sum) / Decimal(count)).quantize(Decimal("0.1"), ROUND_HALF_UP))


def list_services(conn: sqlite3.Connection) -> list[str]:
    return [r[0] for r in conn.execute(
        "SELECT DISTINCT service_name FROM deployments ORDER BY service_name")]


def list_environments(conn: sqlite3.Connection) -> list[str]:
    return [r[0] for r in conn.execute(
        "SELECT DISTINCT environment FROM deployments ORDER BY environment")]


def total_count(conn: sqlite3.Connection) -> int:
    return conn.execute("SELECT COUNT(*) FROM deployments").fetchone()[0]


_AGG = ("COUNT(*) AS total, COALESCE(SUM(status='success'),0) AS successes,"
        " COALESCE(SUM(status='failed'),0) AS failures,"
        " COALESCE(SUM(CASE WHEN status='success' THEN duration_seconds END),0) AS ok_seconds")


def _shape(r) -> dict:
    return {"total": r["total"], "successes": r["successes"], "failures": r["failures"],
            "success_rate": _rate(r["successes"], r["total"]),
            "avg_success_seconds": _avg(r["ok_seconds"], r["successes"])}


def overall(conn, service=None, environment=None) -> dict:
    w, p = _where(service, environment)
    return _shape(conn.execute(f"SELECT {_AGG} FROM deployments{w}", p).fetchone())


def by_service(conn, service=None, environment=None) -> list[dict]:
    w, p = _where(service, environment)
    rows = conn.execute(
        f"SELECT service_name, {_AGG} FROM deployments{w} GROUP BY service_name", p).fetchall()
    out = [{"service_name": r["service_name"], **_shape(r)} for r in rows]
    # lowest success rate first = where to start; ties: more failures, then name
    out.sort(key=lambda x: (x["success_rate"], -x["failures"], x["service_name"]))
    return out


def failures(conn, service=None, environment=None, limit=100, offset=0):
    w, p = _where(service, environment, "status = 'failed'")
    total = conn.execute(f"SELECT COUNT(*) FROM deployments{w}", p).fetchone()[0]
    rows = conn.execute(
        "SELECT deployment_id, service_name, environment, deployment_date,"
        " duration_seconds, error_message FROM deployments" + w +
        " ORDER BY deployment_date DESC, deployment_id DESC LIMIT ? OFFSET ?",
        p + [limit, offset]).fetchall()
    return [dict(r) for r in rows], total
