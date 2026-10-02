import sqlite3
import time
import uuid
from pathlib import Path
from urllib.parse import urlencode

from fastapi import FastAPI, Request, UploadFile
from fastapi.responses import JSONResponse
from fastapi.templating import Jinja2Templates

from . import config, db, errors, importer, logging_setup, metrics
from .errors import AppError
from .logging_setup import correlation_id, log

logging_setup.setup()
app = FastAPI(title="Deployment Reliability Dashboard")
templates = Jinja2Templates(directory=str(Path(__file__).parent / "templates"))


@app.middleware("http")
async def request_context(request: Request, call_next):
    cid = request.headers.get("x-request-id") or str(uuid.uuid4())
    token = correlation_id.set(cid)
    started = time.perf_counter()
    try:
        response = await call_next(request)
    finally:
        correlation_id.reset(token)
    response.headers["X-Request-ID"] = cid
    token = correlation_id.set(cid)
    try:
        log("request", method=request.method, path=request.url.path,
            status=response.status_code, ms=round((time.perf_counter() - started) * 1000, 1))
    finally:
        correlation_id.reset(token)
    return response


def _int_param(raw: str | None, name: str, default: int, lo: int, hi: int | None = None) -> int:
    if raw is None or raw == "":
        return default
    try:
        value = int(raw)
    except ValueError:
        raise AppError(errors.INVALID_PARAMETER, [f"{name} must be an integer"])
    if value < lo or (hi is not None and value > hi):
        bound = f"between {lo} and {hi}" if hi is not None else f"at least {lo}"
        raise AppError(errors.INVALID_PARAMETER, [f"{name} must be {bound}"])
    return value


def _dashboard(conn: sqlite3.Connection, service: str | None, environment: str | None,
               page: int, messages=None, problems=None) -> dict:
    page_size = config.PAGE_SIZE
    rows, fail_total = metrics.failures(conn, service, environment, page_size, (page - 1) * page_size)
    pages = max(1, -(-fail_total // page_size))

    def page_url(p: int) -> str:
        q = {k: v for k, v in (("service", service), ("environment", environment)) if v}
        q["page"] = p
        return "/?" + urlencode(q)

    limit = config.max_upload_bytes()
    return {
        "has_data": metrics.total_count(conn) > 0,
        "services": metrics.list_services(conn), "environments": metrics.list_environments(conn),
        "selected": service, "selected_env": environment,
        "overall": metrics.overall(conn, service, environment),
        "by_service": metrics.by_service(conn, service, environment),
        "failures": rows, "fail_total": fail_total,
        "page": page, "pages": pages, "page_url": page_url,
        "max_bytes": limit, "max_label": config.mb_label(limit),
        "message": messages or "", "problems": problems or [],
    }


async def _receive(file: UploadFile | None) -> tuple[str, bytes]:
    if file is None or not file.filename:
        raise AppError(errors.INVALID_FILE, ["No file was provided"])
    limit = config.max_upload_bytes()
    content = await file.read(limit + 1)  # stop reading once past the limit
    if len(content) > limit:
        raise AppError(errors.FILE_TOO_LARGE,
                       [f"File exceeds the maximum of {config.mb_label(limit)}."])
    return file.filename, content


def _json_error(e: AppError) -> JSONResponse:
    return JSONResponse({"code": e.code, "errors": e.errors}, status_code=e.status_code)


@app.exception_handler(AppError)
async def app_error_handler(request: Request, e: AppError):
    return _json_error(e)


@app.get("/health")
def health():
    try:
        conn = db.connect()
        try:
            conn.execute("SELECT 1")
        finally:
            conn.close()
    except Exception:
        return JSONResponse({"status": "unavailable"}, status_code=503)
    return {"status": "ok"}


@app.get("/")
def index(request: Request, service: str = "", environment: str = "", page: str = "1"):
    try:
        page_no = max(int(page), 1)
    except ValueError:
        page_no = 1
    conn = db.connect()
    try:
        ctx = _dashboard(conn, service or None, environment or None, page_no)
    finally:
        conn.close()
    return templates.TemplateResponse(request, "index.html", ctx)


@app.post("/upload")
async def upload(request: Request, file: UploadFile | None = None):
    conn = db.connect()
    status = 200
    try:
        try:
            name, content = await _receive(file)
            res = importer.import_csv(conn, name, content)
            log("import_accepted", batch_id=res["batch_id"], rows=res["rows"])
            ctx = _dashboard(conn, None, None, 1, messages=(
                f"Imported {res['rows']:,} deployments "
                f"({res['successful_deployments']:,} successful, {res['failed_deployments']:,} failed)."))
        except AppError as e:
            log("import_rejected", code=e.code, error_count=len(e.errors))
            ctx = _dashboard(conn, None, None, 1, problems=e.errors)
            status = e.status_code
    finally:
        conn.close()
    return templates.TemplateResponse(request, "index.html", ctx, status_code=status)


@app.post("/api/import")
async def api_import(file: UploadFile | None = None):
    conn = db.connect()
    try:
        name, content = await _receive(file)
        try:
            res = importer.import_csv(conn, name, content)
        except AppError as e:
            log("import_rejected", code=e.code, error_count=len(e.errors))
            raise
        log("import_accepted", batch_id=res["batch_id"], rows=res["rows"])
        return res
    finally:
        conn.close()


@app.get("/api/services")
def api_services(service: str = "", environment: str = ""):
    conn = db.connect()
    try:
        s, env = service or None, environment or None
        return {"overall": metrics.overall(conn, s, env), "services": metrics.by_service(conn, s, env)}
    finally:
        conn.close()


@app.get("/api/failures")
def api_failures(service: str = "", environment: str = "",
                 limit: str | None = None, offset: str | None = None):
    lim = _int_param(limit, "limit", 100, 1, 1000)
    off = _int_param(offset, "offset", 0, 0)
    conn = db.connect()
    try:
        items, total = metrics.failures(conn, service or None, environment or None, lim, off)
        return {"total": total, "items": items}
    finally:
        conn.close()
