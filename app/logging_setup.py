import contextvars
import json
import logging
import time

correlation_id: contextvars.ContextVar[str] = contextvars.ContextVar("correlation_id", default="-")
logger = logging.getLogger("app")


class JsonFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        data = {"ts": time.strftime("%Y-%m-%dT%H:%M:%S", time.gmtime(record.created)) + "Z",
                "level": record.levelname, "correlation_id": correlation_id.get(),
                "event": record.getMessage()}
        data.update(getattr(record, "fields", {}))
        return json.dumps(data, ensure_ascii=False)


def setup() -> None:
    if logger.handlers:
        return
    handler = logging.StreamHandler()
    handler.setFormatter(JsonFormatter())
    logger.addHandler(handler)
    logger.setLevel(logging.INFO)
    logger.propagate = True


def log(event: str, **fields) -> None:
    logger.info(event, extra={"fields": fields})
