"""
Codec between nested FHIR datatypes (as snake_case dicts) and the flat `<prefix>_<field>` columns used by
the PlanDefinition tables.

  pack(prefix, kind, data)   -> {column_name: value}      (used when creating rows)
  unpack(prefix, kind, row)  -> nested dict | None        (used by the plain mapper; None when nothing is set)
  camel(obj)                 -> same structure with lowerCamelCase keys (used by the FHIR mapper)

Supported kinds: ratio, quantity, simple_quantity, period, range, expression, attachment, cc, coding, timing.
"""

from __future__ import annotations

from datetime import date, datetime
from typing import Any, Dict, Optional

_FLAT_FIELDS = {
    "quantity": ("value", "comparator", "unit", "system", "code"),
    "simple_quantity": ("value", "unit", "system", "code"),
    "period": ("start", "end"),
    "expression": ("description", "name", "language", "expression", "reference"),
    "attachment": ("content_type", "language", "data", "url", "size", "hash", "title", "creation"),
    "cc": ("system", "code", "display", "text"),
    "coding": ("system", "code", "display"),
}

# Timing.repeat scalar fields and the 0..* primitives stored comma-separated.
_REPEAT_SCALARS = (
    "count", "count_max", "duration", "duration_max", "duration_unit", "frequency", "frequency_max",
    "period", "period_max", "period_unit", "offset",
)
_REPEAT_LISTS = ("day_of_week", "time_of_day", "when")


def _iso(v: Any) -> Any:
    return v.isoformat() if isinstance(v, (datetime, date)) else v


def _csv(values) -> Optional[str]:
    items = [str(_iso(v)) for v in (values or [])]
    return ",".join(items) if items else None


def _split(text: Optional[str]) -> list:
    return [t for t in (text or "").split(",") if t]


def _get(data: Any, key: str) -> Any:
    if data is None:
        return None
    return data.get(key) if isinstance(data, dict) else getattr(data, key, None)


def pack(prefix: str, kind: str, data: Any) -> Dict[str, Any]:
    """Flatten one nested datatype value into `<prefix>_<field>` column values (empty dict when data is None)."""
    if data is None:
        return {}
    if kind in _FLAT_FIELDS:
        return {f"{prefix}_{f}": _get(data, f) for f in _FLAT_FIELDS[kind]}
    if kind == "ratio":
        out = {}
        out.update(pack(f"{prefix}_numerator", "quantity", _get(data, "numerator")))
        out.update(pack(f"{prefix}_denominator", "quantity", _get(data, "denominator")))
        return out
    if kind == "range":
        out = {}
        out.update(pack(f"{prefix}_low", "simple_quantity", _get(data, "low")))
        out.update(pack(f"{prefix}_high", "simple_quantity", _get(data, "high")))
        return out
    if kind == "timing":
        out: Dict[str, Any] = {f"{prefix}_event": _csv(_get(data, "event"))}
        out.update(pack(f"{prefix}_code", "cc", _get(data, "code")))
        repeat = _get(data, "repeat")
        if repeat is not None:
            rp = f"{prefix}_repeat"
            out.update(pack(f"{rp}_bounds_duration", "quantity", _get(repeat, "bounds_duration")))
            out.update(pack(f"{rp}_bounds_range", "range", _get(repeat, "bounds_range")))
            out.update(pack(f"{rp}_bounds_period", "period", _get(repeat, "bounds_period")))
            for f in _REPEAT_SCALARS:
                out[f"{rp}_{f}"] = _get(repeat, f)
            for f in _REPEAT_LISTS:
                out[f"{rp}_{f}"] = _csv(_get(repeat, f))
        return out
    raise ValueError(f"unknown kind {kind}")


def unpack(prefix: str, kind: str, row: Any) -> Optional[dict]:
    """Rebuild the nested datatype from columns; None when every column is empty."""
    if kind in _FLAT_FIELDS:
        out = {f: _iso(getattr(row, f"{prefix}_{f}", None)) for f in _FLAT_FIELDS[kind]}
    elif kind == "ratio":
        out = {
            "numerator": unpack(f"{prefix}_numerator", "quantity", row),
            "denominator": unpack(f"{prefix}_denominator", "quantity", row),
        }
    elif kind == "range":
        out = {
            "low": unpack(f"{prefix}_low", "simple_quantity", row),
            "high": unpack(f"{prefix}_high", "simple_quantity", row),
        }
    elif kind == "timing":
        rp = f"{prefix}_repeat"
        repeat = {
            "bounds_duration": unpack(f"{rp}_bounds_duration", "quantity", row),
            "bounds_range": unpack(f"{rp}_bounds_range", "range", row),
            "bounds_period": unpack(f"{rp}_bounds_period", "period", row),
            **{f: getattr(row, f"{rp}_{f}", None) for f in _REPEAT_SCALARS},
            **{f: (_split(getattr(row, f"{rp}_{f}", None)) or None) for f in _REPEAT_LISTS},
        }
        out = {
            "event": _split(getattr(row, f"{prefix}_event", None)) or None,
            "code": unpack(f"{prefix}_code", "cc", row),
            "repeat": _prune(repeat) or None,
        }
    else:
        raise ValueError(f"unknown kind {kind}")
    return _prune(out) or None


def _prune(d: dict) -> dict:
    """Drop None values and empty containers (keeps 0 / False)."""
    return {k: v for k, v in d.items() if v is not None and v != {} and v != []}


def _camel_key(key: str) -> str:
    head, *rest = key.split("_")
    return head + "".join(p.capitalize() for p in rest)


def camel(obj: Any) -> Any:
    """Recursively convert dict keys from snake_case to lowerCamelCase (FHIR spelling)."""
    if isinstance(obj, dict):
        return {_camel_key(k): camel(v) for k, v in obj.items()}
    if isinstance(obj, list):
        return [camel(v) for v in obj]
    return obj
