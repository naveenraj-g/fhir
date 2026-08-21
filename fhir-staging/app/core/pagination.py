"""
Reusable list-endpoint query parameters and sort-string resolution.

Every list/search endpoint needs the same handful of universal parameters —
page size, offset, sort, and how hard to try computing the total count.
`ListParams` below is a class-based FastAPI dependency: using it via
`Depends()` makes every one of its `__init__` parameters behave exactly like an
inline `Query(...)` parameter would, so a route gets all four by adding one
argument to its signature.

Ported verbatim from fhir-server's app/core/pagination.py so both services
present the same query-string contract.
"""

from __future__ import annotations

from typing import Literal, Optional

from fastapi import Query


class ListParams:
    """FastAPI class-based dependency for the universal list-endpoint params."""

    def __init__(
        self,
        limit: int = Query(50, ge=1, le=200, description="Page size."),
        offset: int = Query(0, ge=0, description="Number of rows to skip."),
        sort: Optional[str] = Query(
            None,
            description="Field to sort by. Prefix with '-' for descending (e.g. '-created_at').",
        ),
        total_mode: Literal["accurate", "none"] = Query(
            "accurate",
            description=(
                "'accurate' runs a COUNT(*) and returns the real total. "
                "'none' skips it entirely (total is returned as null) — use this "
                "on large tables when the caller only needs the current page."
            ),
        ),
    ):
        self.limit = limit
        self.offset = offset
        self.sort = sort
        self.total_mode = total_mode


def resolve_sort(
    sort: Optional[str],
    sortable_fields: dict[str, object],
    default_column,
    *,
    default_desc: bool = True,
):
    """
    Resolve a `sort` query string (e.g. "-created_at") against a resource's
    map of {public field name: SQLAlchemy column}, returning (column, desc).

    Falls back to (default_column, default_desc) when `sort` is None or
    doesn't name a recognized field — an unrecognized sort field is silently
    ignored rather than raising, since a harmless typo in `sort` shouldn't
    fail an otherwise-valid list request.
    """
    if not sort:
        return default_column, default_desc
    desc = sort.startswith("-")
    field_name = sort[1:] if desc else sort
    column = sortable_fields.get(field_name)
    if column is None:
        return default_column, default_desc
    return column, desc
