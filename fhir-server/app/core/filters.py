"""
Reusable, resource-agnostic filter-building helpers for list/search endpoints.

Every repository's `list()` method builds a SQLAlchemy `select()` statement by
chaining `.where()` calls for whatever filters the caller provided. Before this
module existed, PatientRepository._apply_list_filters (the first and only list
endpoint in this codebase) hand-wrote the same handful of patterns — ilike
string matching, exact token matching, a correlated EXISTS subquery against a
child table, and Reference("ResourceType/123") parsing — from scratch. As more
resources are added (see dev-docs/10-resource-rollout-plan.md on the fhir-gql
side), every one of them needs the same handful of patterns again. This module
extracts those patterns once so new repositories call a shared function
instead of re-deriving the same SQLAlchemy incantations.

See dev-docs/12-search-and-filter-standards.md (fhir-gql repo) for the full
target filter contract this module is building toward, resource by resource.

IMPORTANT — internal vs. public ID convention (see PatientModel for the
canonical example): every resource table has an internal, autoincrement `id`
(the real primary key, used ONLY for foreign-key joins between a resource and
its own child tables) and a separate public-facing `<resource>_id` sequence
column (what path parameters, filter values, and Reference strings like
"Organization/123" actually contain — the client never sees or sends an
internal `id`). `apply_child_exists_filter` below expects the CALLER to
correlate the child query to the outer query's parent table via the parent's
INTERNAL id column (matching how the child table's foreign key is actually
defined), while any filter VALUE arriving from the client — a plain scalar or
the numeric half of a parsed Reference — is always a PUBLIC id and needs no
translation before being compared against a reference column, since reference
columns (e.g. PatientModel.managing_organization_id) are themselves populated
straight from the client-supplied public id at write time (see parse_reference
below and its callers).
"""

from __future__ import annotations

from datetime import date, datetime
from enum import Enum
from typing import Optional, Type, TypeVar

from fastapi import HTTPException, status
from sqlalchemy import exists
from sqlalchemy.sql import Select

EnumT = TypeVar("EnumT", bound=Enum)


def apply_string_filter(stmt: Select, column, value: Optional[str], *, exact: bool = False) -> Select:
    """
    Apply a case-insensitive string filter to a directly-owned column.

    Defaults to substring ("contains") matching, matching the behavior every
    existing string filter (family_name, given_name) already had before this
    module existed — pass exact=True for an exact-match comparison instead.
    No-ops (returns stmt unchanged) when value is None, so callers can call
    this unconditionally for every optional filter param without an `if`.
    """
    if value is None:
        return stmt
    if exact:
        return stmt.where(column.ilike(value))
    return stmt.where(column.ilike(f"%{value}%"))


def apply_token_filter(stmt: Select, column, value) -> Select:
    """
    Apply an exact-match filter for a coded/token field (gender, status, an
    Enum column, a boolean flag, etc.). No-ops when value is None — note this
    means "no filter", not "filter for NULL"; there is deliberately no way to
    express "value IS NULL" through this helper (see the `:missing` modifier
    noted as deferred in dev-docs/12-search-and-filter-standards.md).
    """
    if value is None:
        return stmt
    return stmt.where(column == value)


def apply_date_range_filter(
    stmt: Select,
    column,
    date_from: Optional[date | datetime] = None,
    date_to: Optional[date | datetime] = None,
) -> Select:
    """
    Apply an inclusive [date_from, date_to] range filter to a date/datetime
    column. Either bound may be omitted for an open-ended range. No-ops
    entirely when both are None.

    Deliberately takes two explicit bounds rather than a single FHIR-style
    comparator-prefixed string (e.g. "ge2024-01-01") — see
    dev-docs/12-search-and-filter-standards.md's ownership/phasing section:
    full FHIR comparator/modifier syntax is intentionally deferred until a
    concrete client requires literal spec compliance; two plain query params
    per range-able field is simpler to implement, test, and document, and
    covers the same practical need ("everything in this period").
    """
    if date_from is not None:
        stmt = stmt.where(column >= date_from)
    if date_to is not None:
        stmt = stmt.where(column <= date_to)
    return stmt


def apply_child_exists_filter(stmt: Select, child_select: Select) -> Select:
    """
    Apply a correlated EXISTS filter built from a caller-constructed child
    `select()`. The caller is responsible for correlating the child query to
    the outer query's parent table via the parent's INTERNAL `id` column (see
    this module's docstring) — this helper just wraps whatever select() it's
    given in `exists()` and adds it to the outer statement's WHERE clause, so
    every repository's child-table filter looks like:

        stmt = apply_child_exists_filter(stmt, select(ChildModel.id).where(
            ChildModel.patient_id == PatientModel.id,   # internal-id join
            ChildModel.value.ilike(f"%{value}%"),
        ))

    rather than repeating `stmt.where(exists(...))` inline every time.
    """
    return stmt.where(exists(child_select))


def parse_reference(ref: str, ref_type_enum: Type[EnumT]) -> tuple[EnumT, int]:
    """
    Parse a FHIR-style reference string ("Organization/123") into its
    (type, public_id) parts, validating the type against the given Enum.

    Generalizes patient_repository.py's original `_parse_org_ref` (which
    hardcoded OrganizationReferenceType) so any resource with a typed
    reference field — Patient.generalPractitioner
    (Organization|Practitioner|PractitionerRole), Encounter.subject
    (Patient|Group), etc. — can reuse this instead of re-deriving the same
    split/validate/int-cast logic. The returned id is the referenced
    resource's PUBLIC id, exactly as the client supplied it — see this
    module's docstring on why no internal-id translation happens here.

    Raises HTTPException(422) on any malformed input, preserving the exact
    error semantics the original Patient-only implementation had.
    """
    parts = ref.split("/", 1)
    if len(parts) != 2:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Invalid reference format: '{ref}'. Expected 'ResourceType/id'.",
        )
    try:
        ref_id = int(parts[1])
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Invalid reference id in: '{ref}'. Id must be an integer.",
        )
    try:
        ref_type = ref_type_enum(parts[0])
    except ValueError:
        allowed = [e.value for e in ref_type_enum]
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Invalid reference type '{parts[0]}'. Allowed: {allowed}.",
        )
    return ref_type, ref_id
