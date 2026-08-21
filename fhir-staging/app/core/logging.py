"""Structured logging setup.

Emits one JSON object per line by default — `logging.format: json` in
configs/config.yaml — so log aggregators can index every field without regex.
A flat `console` format is available for local development.

The correlation id (request_id) is injected automatically from
app.core.request_context's ContextVar, so no layer below the router has to
accept or forward it. See that module's docstring for why.

Conventions for callers:
  - one line per meaningful event, not per function call
  - pass structured data via `extra={...}`, never f-string it into the message
  - name events dotted and resource-first: "staging_medical_record.created",
    "db.slow_query"
  - `extra` keys must not collide with LogRecord attributes (`args`, `name`,
    `module`, …) — logging.makeRecord() raises KeyError on a collision. That's
    why the trace decorator below emits `call_args`, not `args`. The full list
    is _RESERVED_ATTRS.
"""

import functools
import inspect
import json
import logging
import re
import sys
import time
from typing import Any

from app.core.config import settings
from app.core.request_context import get_log_context

# Attributes the stdlib puts on every LogRecord. Anything NOT in here came from
# a caller's extra={...} and gets merged into the emitted object.
_RESERVED_ATTRS = {
    "name",
    "msg",
    "args",
    "levelname",
    "levelno",
    "pathname",
    "filename",
    "module",
    "exc_info",
    "exc_text",
    "stack_info",
    "lineno",
    "funcName",
    "created",
    "msecs",
    "relativeCreated",
    "thread",
    "threadName",
    "processName",
    "process",
    "taskName",
}

_REDACTED = "***REDACTED***"


class JsonFormatter(logging.Formatter):
    RESERVED_ATTRS = _RESERVED_ATTRS

    def format(self, record: logging.LogRecord) -> str:
        log_record: dict[str, Any] = {
            "timestamp": self.formatTime(record),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }

        # request_id, if set.
        log_record.update(get_log_context())

        # Everything the caller passed via extra={...}.
        for key, value in record.__dict__.items():
            if key not in self.RESERVED_ATTRS and key not in log_record:
                log_record[key] = value

        if record.exc_info:
            log_record["traceback"] = self.formatException(record.exc_info)

        return json.dumps(log_record, default=str)


class ConsoleFormatter(logging.Formatter):
    """Human-readable single line for local development. Same data as the JSON
    formatter, just laid out for eyes instead of for an indexer."""

    def __init__(self) -> None:
        super().__init__("%(asctime)s %(levelname)-8s %(name)s | %(message)s")

    # Set by logging.Formatter.format() itself (record.message = getMessage(),
    # record.asctime = formatTime()) — already rendered in `base`, so they must
    # not be repeated in the key=value suffix.
    _FORMATTER_SET = {"message", "asctime"}

    def format(self, record: logging.LogRecord) -> str:
        base = super().format(record)

        ctx = get_log_context()
        request_id = ctx.get("request_id")
        prefix = f"[{request_id[:8]}] " if request_id else ""

        extras = {
            k: v
            for k, v in record.__dict__.items()
            if k not in _RESERVED_ATTRS
            and k not in self._FORMATTER_SET
            and k not in ctx
        }
        suffix = ""
        if extras:
            suffix = " " + " ".join(f"{k}={v}" for k, v in extras.items())

        line = f"{prefix}{base}{suffix}"
        if record.exc_info:
            line += "\n" + self.formatException(record.exc_info)
        return line


def setup_logging() -> None:
    """Configure the root logger from settings.logging. Idempotent — replaces
    any previously installed handlers rather than stacking another one."""
    log_settings = settings.logging

    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(
        ConsoleFormatter() if log_settings.format == "console" else JsonFormatter()
    )

    root = logging.getLogger()
    root.setLevel(log_settings.level)
    root.handlers.clear()
    root.addHandler(handler)

    # Uvicorn ships its own plaintext access log. Off by default: it duplicates
    # app.middleware.access_log's richer `http.request` line, and since the
    # uvicorn.access logger sets propagate=False and keeps its own handler, it
    # bypasses the formatter installed above — so it stays plain text even with
    # format: json, which breaks anything parsing the stream. Set
    # logging.uvicorn_access: true in configs/config.yaml to see both effects.
    logging.getLogger("uvicorn.access").setLevel(
        logging.INFO if log_settings.uvicorn_access else logging.WARNING
    )

    # SQLAlchemy's own engine logger is driven explicitly by logging.sql_echo
    # (see app.core.database) rather than inherited from the root level, so
    # setting level: DEBUG doesn't accidentally dump every statement twice.
    logging.getLogger("sqlalchemy.engine").setLevel(logging.WARNING)


def get_logger(name: str) -> logging.Logger:
    return logging.getLogger(name)


# ── Debug-mode payload logging ────────────────────────────────────────────────


def _redact(value: Any, redact_keys: set[str]) -> Any:
    """Recursively mask configured field names, matched case-insensitively at
    any nesting depth."""
    if isinstance(value, dict):
        return {
            k: (_REDACTED if str(k).lower() in redact_keys else _redact(v, redact_keys))
            for k, v in value.items()
        }
    if isinstance(value, (list, tuple)):
        return [_redact(v, redact_keys) for v in value]
    return value


def log_payload(logger: logging.Logger, event: str, payload: Any) -> None:
    """Log a full request/response payload — debug mode only.

    No-op unless BOTH `logging.debug_payloads` is on AND the logger is enabled
    for DEBUG, so the (potentially expensive) model_dump + redaction walk never
    runs in production.

    ⚠️ PHI: this is what writes staged medical-record metadata and extracted
    Observation values into the log stream. `logging.redact` masks obvious
    secrets; it is not a PHI safeguard. Local development only.
    """
    if not settings.logging.debug_payloads:
        return
    if not logger.isEnabledFor(logging.DEBUG):
        return

    dump = getattr(payload, "model_dump", None)
    data = dump(mode="json", exclude_unset=True) if callable(dump) else payload

    redact_keys = {k.lower() for k in settings.logging.redact}
    logger.debug(event, extra={"event": event, "payload": _redact(data, redact_keys)})


# ── Flow tracing ──────────────────────────────────────────────────────────────
#
# `logging.level: DEBUG` turns on an entry + exit line for EVERY public async
# method of every traced service and repository, so a single request produces a
# complete top-to-bottom trace: route -> service method -> repository method(s)
# -> SQL. At INFO those lines disappear and only the access log plus the
# hand-placed business events remain.
#
# Applied as a class decorator on the composed service/repository classes (see
# app/services/<resource>/__init__.py). It walks the full MRO, so methods that
# live on per-sub-resource mixins are covered too — adding a new mixin method
# needs no logging code of its own.


def _snake(name: str) -> str:
    """StagingMedicalRecordService -> staging_medical_record.service"""
    s = re.sub(r"(?<!^)(?=[A-Z])", "_", name).lower()
    return s.replace("_service", ".service").replace("_repository", ".repository")


def _describe(value: Any) -> Any:
    """Render one call argument for a log line. Pydantic models are dumped only
    when debug_payloads is on (they're request bodies — PHI); otherwise just
    the type name, so the flow is still traceable without the contents."""
    dump = getattr(value, "model_dump", None)
    if callable(dump):
        if not settings.logging.debug_payloads:
            return f"<{type(value).__name__}>"
        return dump(mode="json", exclude_unset=True)
    if isinstance(value, (str, int, float, bool)) or value is None:
        return value
    if isinstance(value, (list, tuple, set)):
        return f"<{type(value).__name__}[{len(value)}]>"
    return f"<{type(value).__name__}>"


def _traced(fn, logger: logging.Logger, prefix: str, component: str):
    """Wrap one method so it announces itself.

    INFO  — a single line naming what is being called, e.g.
            "StagingMedicalRecordService.list_staging_medical_records". No arguments, no
            result, no timing. Reading the log top to bottom gives you the
            call chain: route -> service -> repository.
    DEBUG — the same entry line, now carrying call_args, plus a completion
            line with duration_ms and the result type (or the exception).
    """
    method = fn.__name__
    label = f"{component}.{method}"
    event = f"{prefix}.{method}"

    # Positional parameter names, read straight off the code object (`self`
    # dropped). Deliberately NOT inspect.signature(): under PEP 649 (Python
    # 3.14) that forces evaluation of the function's annotations, and a
    # repository method named `list` whose own parameters are annotated
    # `list[str]` resolves `list` to the method inside the class body, not the
    # builtin — evaluating raises "TypeError: 'function' object is not
    # subscriptable". co_varnames needs no annotations at all, and is far
    # cheaper per call besides.
    _code = fn.__code__
    _pos_names = _code.co_varnames[1 : _code.co_argcount]

    @functools.wraps(fn)
    async def wrapper(self, *args, **kwargs):
        debug = logger.isEnabledFor(logging.DEBUG)

        extra = {"event": event, "component": component, "method": method}
        if debug:
            redact_keys = {k.lower() for k in settings.logging.redact}
            bound = dict(zip(_pos_names, args))
            bound.update(kwargs)
            # NB: key is "call_args", not "args" — LogRecord reserves "args"
            # and logging.makeRecord raises KeyError on a collision.
            extra["call_args"] = _redact(
                {k: _describe(v) for k, v in bound.items()}, redact_keys
            )

        logger.info(label, extra=extra)

        if not debug:
            return await fn(self, *args, **kwargs)

        started = time.perf_counter()
        try:
            result = await fn(self, *args, **kwargs)
        except Exception as exc:
            logger.debug(
                f"{label} raised {type(exc).__name__}",
                extra={
                    "event": f"{event}.error",
                    "component": component,
                    "method": method,
                    "error_type": type(exc).__name__,
                    "duration_ms": round((time.perf_counter() - started) * 1000, 2),
                },
            )
            raise
        logger.debug(
            f"{label} ok",
            extra={
                "event": f"{event}.ok",
                "component": component,
                "method": method,
                "duration_ms": round((time.perf_counter() - started) * 1000, 2),
                "result": _describe(result),
            },
        )
        return result

    return wrapper


def trace_methods(cls):
    """Class decorator — makes every public async method announce itself.

    INFO gives one line per call (`StagingMedicalRecordService.list_staging_medical_records`),
    so the log reads as the call chain. DEBUG adds arguments, timing and
    results. See _traced().

    Walks the whole MRO so mixin-provided methods are covered, and binds the
    wrapper onto `cls` itself (shadowing the mixin's original). Underscore-
    prefixed methods are skipped deliberately: they're internal helpers like
    `_to_plain`/`_apply_list_filters` that run per row and would bury the
    actual flow in noise.
    """
    prefix = _snake(cls.__name__)
    seen: set[str] = set()
    for klass in cls.__mro__:
        if klass is object:
            continue
        for name, attr in list(vars(klass).items()):
            if name in seen or name.startswith("_"):
                continue
            if not inspect.iscoroutinefunction(attr):
                continue
            seen.add(name)
            setattr(
                cls,
                name,
                _traced(attr, get_logger(klass.__module__), prefix, cls.__name__),
            )
    return cls
