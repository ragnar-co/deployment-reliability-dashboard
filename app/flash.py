"""One-time notices shown after a redirect (Post/Redirect/Get).

Held in process memory, which is fine because the app runs as a single instance
(ARCHITECTURE.md Scalability). A notice is read once, so refreshing the page
clears it. No cookie is set (TRACKING_PLAN.md).
"""
import secrets
import threading
import time

_TTL_SECONDS = 120
_MAX_ENTRIES = 200
_store: dict[str, tuple[float, dict]] = {}
_lock = threading.Lock()


def put(message: str = "", problems: list[str] | None = None) -> str:
    token = secrets.token_urlsafe(16)
    now = time.monotonic()
    with _lock:
        for key in [k for k, (expires, _) in _store.items() if expires < now]:
            del _store[key]
        while len(_store) >= _MAX_ENTRIES:
            del _store[min(_store, key=lambda k: _store[k][0])]
        _store[token] = (now + _TTL_SECONDS, {"message": message, "problems": problems or []})
    return token


def pop(token: str) -> dict | None:
    """Return the notice once; unknown, used or expired tokens give None."""
    with _lock:
        entry = _store.pop(token, None)
    if entry is None or entry[0] < time.monotonic():
        return None
    return entry[1]
