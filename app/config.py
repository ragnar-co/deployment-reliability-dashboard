import os

DEFAULT_MAX_UPLOAD_BYTES = 10 * 1024 * 1024  # 10 MiB (CONSTRAINTS TC-07)
PAGE_SIZE = 100


def db_path() -> str:
    return os.environ.get("DB_PATH", "data/dashboard.db")


def max_upload_bytes() -> int:
    raw = os.environ.get("MAX_UPLOAD_BYTES", "").strip()
    if not raw:
        return DEFAULT_MAX_UPLOAD_BYTES
    try:
        value = int(raw)
    except ValueError:
        raise RuntimeError("MAX_UPLOAD_BYTES must be a positive integer")
    if value <= 0:
        raise RuntimeError("MAX_UPLOAD_BYTES must be a positive integer")
    return value


def mb_label(num_bytes: int) -> str:
    return f"{num_bytes / (1024 * 1024):g} MB"
