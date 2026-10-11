"""
Parsers/clause-builders for FHIR R4 search parameter types (token, reference, date).

https://www.hl7.org/fhir/R4/search.html

Every function raises HTTP 422 on malformed input so bad search values never
reach the database.

  token      "code" | "system|code" | "|code" | "system|"   (comma = OR)
  reference  "Patient/123" | "123"                           (comma = OR)
  date       "[eq|ne|gt|lt|ge|le|sa|eb|ap]YYYY[-MM[-DD[Thh:mm[:ss][Z|+hh:mm]]]]"
"""

from __future__ import annotations

import re
from datetime import datetime, timedelta, timezone
from enum import Enum
from typing import List, Optional, Tuple, Type, TypeVar

from fastapi import HTTPException, status
from sqlalchemy import and_, not_, or_

E = TypeVar("E", bound=Enum)


def _bad(detail: str) -> HTTPException:
    return HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=detail)


def split_or(value: Optional[str]) -> List[str]:
    """Split a comma-separated OR list, dropping blanks."""
    if not value:
        return []
    return [v.strip() for v in value.split(",") if v.strip()]


# ── token ─────────────────────────────────────────────────────────────────────


def token_clause(system_col, code_col, value: Optional[str]):
    """Build a WHERE clause for a Coding/Identifier token. Returns None when no value."""
    clauses = []
    for item in split_or(value):
        if "|" in item:
            system, code = item.split("|", 1)
            parts = []
            if system:
                parts.append(system_col == system)
            else:
                parts.append(system_col.is_(None))
            if code:
                parts.append(code_col == code)
            clauses.append(and_(*parts))
        else:
            clauses.append(code_col == item)
    return or_(*clauses) if clauses else None


def enum_token_values(value: Optional[str], enum_cls: Type[E], field: str) -> List[E]:
    """Parse a comma-separated list of codes into enum members (422 on unknown code)."""
    out: List[E] = []
    for item in split_or(value):
        try:
            out.append(enum_cls(item))
        except ValueError:
            raise _bad(f"Invalid {field} '{item}'. Allowed: {[e.value for e in enum_cls]}.")
    return out


# ── reference ─────────────────────────────────────────────────────────────────


def parse_reference_param(
    value: str, enum_cls: Type[E], field: str
) -> List[Tuple[Optional[E], int]]:
    """Parse "Type/id" or bare "id" (comma = OR). Type is None when omitted."""
    out: List[Tuple[Optional[E], int]] = []
    for item in split_or(value):
        parts = item.rstrip("/").split("/")
        ref_type: Optional[E] = None
        if len(parts) >= 2:
            try:
                ref_type = enum_cls(parts[-2])
            except ValueError:
                raise _bad(
                    f"Invalid {field} reference type '{parts[-2]}'. "
                    f"Allowed: {[e.value for e in enum_cls]}."
                )
        try:
            ref_id = int(parts[-1])
        except ValueError:
            raise _bad(f"Invalid {field} reference '{item}'. Expected 'Type/id' or numeric id.")
        out.append((ref_type, ref_id))
    return out


def reference_clause(type_col, id_col, refs: List[Tuple[Optional[Enum], int]]):
    clauses = []
    for ref_type, ref_id in refs:
        parts = [id_col == ref_id]
        if ref_type is not None:
            parts.append(type_col == ref_type)
        clauses.append(and_(*parts))
    return or_(*clauses) if clauses else None


# ── date ──────────────────────────────────────────────────────────────────────

_DATE_RE = re.compile(r"^(eq|ne|gt|lt|ge|le|sa|eb|ap)?(\d.*)$")


def parse_date_param(value: str, field: str) -> Tuple[str, datetime, datetime]:
    """
    Returns (prefix, lo, hi) where [lo, hi) is the range implied by the value's
    precision (a day value covers the whole day).
    """
    value = value.strip().replace(" ", "+")  # '+' in tz offsets arrives as a space
    m = _DATE_RE.match(value)
    if not m:
        raise _bad(f"Invalid {field} value '{value}'. Expected [prefix]YYYY-MM-DD[Thh:mm:ss].")
    prefix, raw = m.group(1) or "eq", m.group(2)
    try:
        if re.fullmatch(r"\d{4}", raw):
            lo = datetime(int(raw), 1, 1, tzinfo=timezone.utc)
            hi = datetime(lo.year + 1, 1, 1, tzinfo=timezone.utc)
        elif re.fullmatch(r"\d{4}-\d{2}", raw):
            lo = datetime(int(raw[:4]), int(raw[5:7]), 1, tzinfo=timezone.utc)
            hi = (
                datetime(lo.year + 1, 1, 1, tzinfo=timezone.utc)
                if lo.month == 12
                else datetime(lo.year, lo.month + 1, 1, tzinfo=timezone.utc)
            )
        elif re.fullmatch(r"\d{4}-\d{2}-\d{2}", raw):
            lo = datetime.fromisoformat(raw).replace(tzinfo=timezone.utc)
            hi = lo + timedelta(days=1)
        else:
            lo = datetime.fromisoformat(raw.replace("Z", "+00:00"))
            if lo.tzinfo is None:
                lo = lo.replace(tzinfo=timezone.utc)
            hi = lo + timedelta(seconds=1)
    except ValueError:
        raise _bad(f"Invalid {field} value '{value}'.")
    return prefix, lo, hi


def period_date_clause(lo_expr, hi_expr, prefix: str, s_lo: datetime, s_hi: datetime):
    """
    Match a resource effective range [lo_expr, hi_expr] against a search range
    [s_lo, s_hi). A NULL hi_expr with a non-NULL lo_expr is an open-ended period.
    """
    has_lo = lo_expr.isnot(None)
    open_ended = and_(hi_expr.is_(None), has_lo)
    if prefix == "eq":
        return and_(has_lo, lo_expr >= s_lo, hi_expr < s_hi)
    if prefix == "ne":
        return and_(has_lo, not_(and_(lo_expr >= s_lo, hi_expr < s_hi)))
    if prefix == "gt":
        return or_(hi_expr >= s_hi, open_ended)
    if prefix == "ge":
        return or_(hi_expr >= s_lo, open_ended)
    if prefix == "lt":
        return lo_expr < s_lo
    if prefix == "le":
        return lo_expr < s_hi
    if prefix == "sa":
        return lo_expr >= s_hi
    if prefix == "eb":
        return hi_expr < s_lo
    # ap — approximate: any overlap
    return and_(has_lo, lo_expr < s_hi, or_(hi_expr.is_(None), hi_expr >= s_lo))


def instant_clause(col, prefix: str, s_lo: datetime, s_hi: datetime):
    """Match a single instant column (e.g. updated_at) against a search range."""
    if prefix in ("eq", "ap"):
        return and_(col >= s_lo, col < s_hi)
    if prefix == "ne":
        return not_(and_(col >= s_lo, col < s_hi))
    if prefix in ("gt", "sa"):
        return col >= s_hi
    if prefix == "ge":
        return col >= s_lo
    if prefix in ("lt", "eb"):
        return col < s_lo
    return col < s_hi  # le


# ── string ────────────────────────────────────────────────────────────────────


def string_clause(col, value: Optional[str], mode: str = "startswith"):
    """
    Build a WHERE clause for a FHIR `string` search parameter.

    mode: "startswith" (default per spec — case-insensitive prefix match),
          "contains" (`:contains` — case-insensitive substring), or
          "exact" (`:exact` — case-sensitive full match).
    Comma-separated values are OR. Returns None when there is no value.
    """
    clauses = []
    for item in split_or(value):
        if mode == "exact":
            clauses.append(col == item)
        elif mode == "contains":
            clauses.append(col.ilike(f"%{item}%"))
        else:
            clauses.append(col.ilike(f"{item}%"))
    return or_(*clauses) if clauses else None


# ── open reference (Reference(Any)) ───────────────────────────────────────────


def parse_open_reference_param(value: str, field: str) -> List[Tuple[Optional[str], int]]:
    """
    Parse "Type/id" or bare "id" for a Reference(Any) search parameter (comma = OR).
    The type is returned as a free string (None when omitted); only the shape is validated.
    """
    out: List[Tuple[Optional[str], int]] = []
    for item in split_or(value):
        parts = item.rstrip("/").split("/")
        ref_type = parts[-2] if len(parts) >= 2 and parts[-2] else None
        try:
            ref_id = int(parts[-1])
        except ValueError:
            raise _bad(f"Invalid {field} reference '{item}'. Expected 'Type/id' or numeric id.")
        out.append((ref_type, ref_id))
    return out


# ── number ────────────────────────────────────────────────────────────────────

_NUMBER_RE = re.compile(r"^(eq|ne|gt|lt|ge|le|sa|eb|ap)?(-?\d+(?:\.\d+)?)$")


def parse_number_param(value: str, field: str) -> Tuple[str, float]:
    """Parse a FHIR `number` search value with an optional comparator prefix, e.g. 'ge12.5'."""
    m = _NUMBER_RE.match(value.strip())
    if not m:
        raise _bad(f"Invalid {field} value '{value}'. Expected [prefix]<number>, e.g. 'ge12.5'.")
    return m.group(1) or "eq", float(m.group(2))
