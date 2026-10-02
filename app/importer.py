"""CSV import: validate the whole file, then write it in one transaction."""
import csv
import hashlib
import io
import re
import sqlite3
from datetime import date, datetime, timezone

from . import errors
from .errors import AppError

REQUIRED = ["deployment_id", "service_name", "status", "duration_seconds",
            "error_message", "deployment_date", "environment"]
MAX_ERRORS = 20
IMPORTED = "imported"  # import_batch_status
_DATE = re.compile(r"\d{4}-\d{2}-\d{2}")
_POSITIVE_INT = re.compile(r"[1-9]\d*")


def _open(content: bytes) -> csv.reader:
    try:
        text = content.decode("utf-8-sig")
    except UnicodeDecodeError:
        raise AppError(errors.INVALID_FILE, ["File is not valid UTF-8"])
    reader = csv.reader(io.StringIO(text, newline=""))
    try:
        header = [h.strip() for h in next(reader)]
    except StopIteration:
        raise AppError(errors.INVALID_FILE, ["File is empty"])
    problems = []
    missing = [c for c in REQUIRED if c not in header]
    if missing:
        problems.append(f"Missing required column(s): {', '.join(missing)}")
    extra = sorted({h for h in header if h not in REQUIRED})
    if extra:
        problems.append(f"Unexpected column(s): {', '.join(extra) or '(blank)'}")
    dupes = sorted({h for h in header if header.count(h) > 1})
    if dupes:
        problems.append(f"Duplicate column(s): {', '.join(dupes)}")
    if problems:
        raise AppError(errors.INVALID_FILE, problems)
    return reader, header


def validate(reader, header: list[str]) -> list[dict]:
    problems: list[str] = []
    rows: list[dict] = []
    first_seen: dict[str, int] = {}

    def err(line: int, msg: str):
        if len(problems) < MAX_ERRORS:
            problems.append(f"Row {line}: {msg}")

    bad = False
    prev_line = 1
    for fields in reader:
        line = prev_line + 1  # 1-based, header is line 1
        prev_line = reader.line_num
        if not fields:  # blank line (e.g. trailing newline): not a record
            continue
        if len(fields) != len(header):
            err(line, f"expected {len(header)} fields, got {len(fields)}")
            bad = True
            continue
        r = {k: v.strip() for k, v in zip(header, fields)}
        n_before = len(problems)
        ok = True

        def fail(msg):
            nonlocal ok
            ok = False
            err(line, msg)

        did = r["deployment_id"]
        if not did:
            fail("deployment_id is required")
        elif did in first_seen:
            fail(f"duplicate deployment_id {did} (first seen at row {first_seen[did]})")
        else:
            first_seen[did] = line
        if not r["service_name"]:
            fail("service_name is required")
        if not r["environment"]:
            fail("environment is required")
        if r["status"] not in ("success", "failed"):
            fail(f"status must be 'success' or 'failed', got '{r['status']}'")
        elif r["status"] == "failed" and not r["error_message"]:
            fail("error_message is required for failed deployments")
        elif r["status"] == "success" and r["error_message"]:
            fail("error_message must be empty for successful deployments")
        if _POSITIVE_INT.fullmatch(r["duration_seconds"]):
            r["duration_seconds"] = int(r["duration_seconds"])
        else:
            fail(f"duration_seconds must be a positive integer, got '{r['duration_seconds']}'")
        valid_date = False
        if _DATE.fullmatch(r["deployment_date"]):
            try:
                date.fromisoformat(r["deployment_date"])
                valid_date = True
            except ValueError:
                pass
        if not valid_date:
            fail(f"deployment_date must be ISO YYYY-MM-DD, got '{r['deployment_date']}'")
        if not ok:
            bad = True
        rows.append(r)
    if not rows and not bad:
        raise AppError(errors.INVALID_FILE, ["File contains no data rows"])
    if bad:
        raise AppError(errors.VALIDATION_FAILED, problems)
    return rows


def import_csv(conn: sqlite3.Connection, filename: str, content: bytes) -> dict:
    """Order of checks follows API_SPEC.md; stops at the first failing step."""
    reader, header = _open(content)                                        # INVALID_FILE
    sha = hashlib.sha256(content).hexdigest()
    if conn.execute("SELECT 1 FROM import_batches WHERE sha256=?", (sha,)).fetchone():
        raise AppError(errors.DUPLICATE_FILE, ["This exact file was already imported"])
    rows = validate(reader, header)                                        # VALIDATION_FAILED

    try:
        conn.execute("BEGIN IMMEDIATE")
    except sqlite3.OperationalError:
        raise AppError(errors.IMPORT_BUSY,
                       ["Another import is in progress. Try again shortly."])
    try:
        ids = [r["deployment_id"] for r in rows]
        existing: list[str] = []
        for i in range(0, len(ids), 500):
            chunk = ids[i:i + 500]
            marks = ",".join("?" * len(chunk))
            existing += [x[0] for x in conn.execute(
                f"SELECT deployment_id FROM deployments WHERE deployment_id IN ({marks})", chunk)]
        if existing:
            raise AppError(errors.DUPLICATE_DEPLOYMENT, [
                f"{len(existing)} deployment_id(s) already exist, e.g. {existing[0]}. "
                "Existing deployments are never overwritten."])
        failed = sum(1 for r in rows if r["status"] == "failed")
        try:
            cur = conn.execute(
                "INSERT INTO import_batches(original_filename,sha256,imported_at,row_count,"
                "success_count,failed_count,status) VALUES (?,?,?,?,?,?,?)",
                (filename, sha, datetime.now(timezone.utc).isoformat(timespec="seconds"),
                 len(rows), len(rows) - failed, failed, IMPORTED))
        except sqlite3.IntegrityError:  # same file imported concurrently
            raise AppError(errors.DUPLICATE_FILE, ["This exact file was already imported"])
        batch_id = cur.lastrowid
        conn.executemany(
            "INSERT INTO deployments(deployment_id,service_name,status,duration_seconds,"
            "error_message,deployment_date,environment,batch_id) VALUES (?,?,?,?,?,?,?,?)",
            [(r["deployment_id"], r["service_name"], r["status"], r["duration_seconds"],
              r["error_message"], r["deployment_date"], r["environment"], batch_id)
             for r in rows])
        conn.execute("COMMIT")
    except BaseException:
        conn.execute("ROLLBACK")
        raise
    return {"batch_id": batch_id, "rows": len(rows), "failed_deployments": failed}
