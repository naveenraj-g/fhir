"""Shared base class for repositories backed by a SQLAlchemy async session.

Ported from fhir-server's app/repository/base.py. A repository's own `list()`
builds only the WHERE-clause filtering; the generic half — apply sort, run the
count query (or skip it), run the paginated row query — lives here.
"""

from __future__ import annotations

from collections.abc import Sequence

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.sql import Select


class BaseRepository:
    """Mixin providing generic paginated-list execution."""

    def __init__(self, session_factory):
        self.session_factory = session_factory

    async def _execute_paginated(
        self,
        session: AsyncSession,
        base_stmt: Select,
        count_stmt: Select | None,
        *,
        sort_column,
        sort_desc: bool,
        limit: int,
        offset: int,
        total_mode: str = "accurate",
    ) -> tuple[Sequence, int | None]:
        """Run a filtered-but-unsorted-and-unpaginated `base_stmt` (rows) and
        its matching `count_stmt` (COUNT(*), same filters, no sort/limit/offset
        — the caller builds both from identical filter calls so they cannot
        drift apart), applying sort and pagination generically here.

        `total_mode="none"` skips the count entirely and returns None for the
        total, so a caller doesn't pay for a COUNT(*) when it only needs the
        current page (see app.core.pagination.ListParams).
        """
        ordered = base_stmt.order_by(
            sort_column.desc() if sort_desc else sort_column.asc()
        )
        rows = list(
            (await session.execute(ordered.offset(offset).limit(limit))).scalars().all()
        )

        total: int | None = None
        if total_mode != "none" and count_stmt is not None:
            total = (await session.execute(count_stmt)).scalar_one()

        return rows, total
