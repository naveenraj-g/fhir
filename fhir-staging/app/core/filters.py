"""Reusable filter-building helpers for list endpoints.

A trimmed port of fhir-server's app/core/filters.py — only the four helpers
this service's single list endpoint actually needs. The rest (string filters
against child tables, EXISTS correlation, FHIR comparator-prefixed date syntax)
came with resources that had sub-resource search; staging records are filtered
entirely on their own columns.

ID convention, carried over unchanged: every table has an internal
autoincrement `id` used only for foreign keys between a parent and its own
children, and a separate public `<resource>_id` sequence column, which is what
path parameters and filter values actually contain. A filter VALUE arriving
from a client is always a public id and needs no translation.
"""

from __future__ import annotations

from datetime import date, datetime
from enum import Enum

from fastapi import HTTPException, status
from sqlalchemy.sql import Select


def apply_string_filter(
    stmt: Select, column, value: str | None, *, exact: bool = False
) -> Select:
    """Case-insensitive string filter. Substring ("contains") by default; pass
    exact=True for a full-value comparison. No-ops when value is None, so
    callers can call it unconditionally for every optional param."""
    if value is None:
        return stmt
    if exact:
        return stmt.where(column.ilike(value))
    return stmt.where(column.ilike(f"%{value}%"))


def apply_token_filter(stmt: Select, column, value) -> Select:
    """Exact-match filter for a coded/token field (an Enum column, an id, a
    boolean). No-ops when value is None — note that means "no filter", not
    "match NULL"; there is deliberately no way to express IS NULL here."""
    if value is None:
        return stmt
    return stmt.where(column == value)


def apply_date_range_filter(
    stmt: Select,
    column,
    date_from: date | datetime | None = None,
    date_to: date | datetime | None = None,
) -> Select:
    """Inclusive [date_from, date_to] range. Either bound may be omitted for an
    open-ended range; no-ops entirely when both are None.

    Two explicit bounds rather than FHIR comparator-prefixed strings
    ("ge2026-01-01") — simpler to implement, test and document, and it covers
    the same practical need."""
    if date_from is not None:
        stmt = stmt.where(column >= date_from)
    if date_to is not None:
        stmt = stmt.where(column <= date_to)
    return stmt


def parse_reference[EnumT: Enum](
    ref: str, ref_type_enum: type[EnumT]
) -> tuple[EnumT, int]:
    """Parse a FHIR-style reference string ("Patient/10001") into its
    (type, public_id) parts, validating the type against the given Enum.

    The returned id is the referenced resource's PUBLIC id, exactly as
    supplied. In this service those ids belong to fhir-server, so there is
    nothing local to resolve them against — the format and the type are all
    that get checked.
    """
    parts = ref.split("/", 1)
    if len(parts) != 2:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail=f"Invalid reference format: '{ref}'. Expected 'ResourceType/id'.",
        )
    try:
        ref_id = int(parts[1])
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail=f"Invalid reference id in: '{ref}'. Id must be an integer.",
        )
    try:
        ref_type = ref_type_enum(parts[0])
    except ValueError:
        allowed = [e.value for e in ref_type_enum]
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail=f"Invalid reference type '{parts[0]}'. Allowed: {allowed}.",
        )
    return ref_type, ref_id
