"""Eager-loading, sort fields, and the StagingObservationInput -> ORM tree builder."""

from __future__ import annotations

from sqlalchemy.orm import selectinload

from app.core.filters import parse_reference
from app.models.staging_observation import (
    StagingObservationBasedOn,
    StagingObservationCategory,
    StagingObservationComponent,
    StagingObservationComponentInterpretation,
    StagingObservationComponentReferenceRange,
    StagingObservationComponentReferenceRangeAppliesTo,
    StagingObservationDerivedFrom,
    StagingObservationDeviceReferenceType,
    StagingObservationFocus,
    StagingObservationHasMember,
    StagingObservationIdentifier,
    StagingObservationInterpretation,
    StagingObservationModel,
    StagingObservationNote,
    StagingObservationPartOf,
    StagingObservationPerformer,
    StagingObservationReferenceRange,
    StagingObservationReferenceRangeAppliesTo,
    StagingObservationSpecimenReferenceType,
    StagingObservationSubjectReferenceType,
)
from app.models.staging_medical_record import StagingMedicalRecordModel

__all__ = [
    "_SORTABLE_FIELDS",
    "_build_staging_observation",
    "_with_relationships",
]


# Fields exposed via the `sort` list-query param (see
# app.core.pagination.resolve_sort). An unrecognized value falls back to the
# default rather than erroring.
_SORTABLE_FIELDS = {
    "staging_medical_record_id": StagingMedicalRecordModel.staging_medical_record_id,
    "status": StagingMedicalRecordModel.status,
    "created_at": StagingMedicalRecordModel.created_at,
    "updated_at": StagingMedicalRecordModel.updated_at,
    "processed_at": StagingMedicalRecordModel.processed_at,
    "patient_id": StagingMedicalRecordModel.patient_id,
}


def _with_relationships(stmt):
    """Eager-load the whole staging_observation tree, four levels deep.

    Everything the serializer touches must be loaded here. Under asyncio a
    lazy load raises rather than silently issuing a query, so a missing
    selectinload is a hard failure at serialization time, not a slow response.
    """
    return stmt.options(
        selectinload(StagingMedicalRecordModel.observations).options(
            selectinload(StagingObservationModel.identifiers),
            selectinload(StagingObservationModel.based_on),
            selectinload(StagingObservationModel.part_of),
            selectinload(StagingObservationModel.categories),
            selectinload(StagingObservationModel.focus),
            selectinload(StagingObservationModel.performers),
            selectinload(StagingObservationModel.interpretations),
            selectinload(StagingObservationModel.notes),
            selectinload(StagingObservationModel.has_members),
            selectinload(StagingObservationModel.derived_from),
            selectinload(StagingObservationModel.reference_ranges).selectinload(
                StagingObservationReferenceRange.applies_to
            ),
            selectinload(StagingObservationModel.components).options(
                selectinload(StagingObservationComponent.interpretations),
                selectinload(StagingObservationComponent.reference_ranges).selectinload(
                    StagingObservationComponentReferenceRange.applies_to
                ),
            ),
        )
    )


# ── StagingObservationInput -> StagingObservationModel ──────────────────────────────────────
#
# The input schema's field names are deliberately identical to the model's
# column names, so the ~100 scalar fields are copied generically rather than
# enumerated by hand. fhir-server spells all ~90 out one per line in its
# staging_observation repository; that list silently goes stale every time a column is
# added, which is exactly the drift the OpenAPI-contract rules in its CLAUDE.md
# exist to prevent. Copying by name cannot drift — and _assert_scalar_fields_map
# below turns any genuine mismatch into an import-time crash rather than a
# runtime TypeError on the first write.

# Input fields that are NOT plain scalar columns and need their own handling.
_REFERENCE_FIELDS = {"subject", "specimen", "device"}
_CHILD_FIELDS = {
    "identifier",
    "based_on",
    "part_of",
    "category",
    "focus",
    "performer",
    "interpretation",
    "note",
    "reference_range",
    "has_member",
    "derived_from",
    "component",
}
_NON_SCALAR_FIELDS = _REFERENCE_FIELDS | _CHILD_FIELDS


def _scalar_kwargs(payload, non_scalar: set[str]) -> dict:
    """Every field on `payload` that maps straight onto a same-named column."""
    return {
        name: getattr(payload, name)
        for name in type(payload).model_fields
        if name not in non_scalar
    }


def _assert_scalar_fields_map() -> None:
    """Fail at import if an input field has no matching model column.

    This is the guard that makes the generic copy above safe. Without it a
    renamed column or a typo'd schema field would surface as
    `TypeError: 'x' is an invalid keyword argument` on the first POST that
    happens to populate it — potentially long after the change.
    """
    from app.schemas.staging_medical_record.input.staging_observation import (
        StagingObservationComponentInput,
        StagingObservationInput,
    )

    obs_cols = {c.name for c in StagingObservationModel.__table__.columns}
    obs_fields = set(StagingObservationInput.model_fields) - _NON_SCALAR_FIELDS
    missing = obs_fields - obs_cols
    if missing:
        raise RuntimeError(
            f"StagingObservationInput fields with no StagingObservationModel column: {sorted(missing)}"
        )

    comp_cols = {c.name for c in StagingObservationComponent.__table__.columns}
    comp_fields = set(StagingObservationComponentInput.model_fields) - {
        "interpretation",
        "reference_range",
    }
    missing = comp_fields - comp_cols
    if missing:
        raise RuntimeError(
            f"StagingObservationComponentInput fields with no StagingObservationComponent "
            f"column: {sorted(missing)}"
        )


def _coding_kwargs(item) -> dict:
    return {
        "coding_system": item.coding_system,
        "coding_code": item.coding_code,
        "coding_display": item.coding_display,
        "text": item.text,
    }


def _build_note(n, audit: dict) -> StagingObservationNote:
    """Annotation.author[x] is a choice of authorString or authorReference;
    at most one is populated, and the reference half is Reference(Any)."""
    author_ref = {}
    if n.author_reference:
        parsed = _open_ref(n.author_reference)
        author_ref = {
            "author_reference_type": parsed["reference_type"],
            "author_reference_id": parsed["reference_id"],
        }
    return StagingObservationNote(
        **audit,
        text=n.text,
        time=n.time,
        author_string=n.author_string,
        **author_ref,
    )


def _reference_range_kwargs(rr) -> dict:
    return {
        "low_value": rr.low_value,
        "low_unit": rr.low_unit,
        "low_system": rr.low_system,
        "low_code": rr.low_code,
        "high_value": rr.high_value,
        "high_unit": rr.high_unit,
        "high_system": rr.high_system,
        "high_code": rr.high_code,
        "type_system": rr.type_system,
        "type_code": rr.type_code,
        "type_display": rr.type_display,
        "type_text": rr.type_text,
        "age_low_value": rr.age_low_value,
        "age_low_unit": rr.age_low_unit,
        "age_low_system": rr.age_low_system,
        "age_low_code": rr.age_low_code,
        "age_high_value": rr.age_high_value,
        "age_high_unit": rr.age_high_unit,
        "age_high_system": rr.age_high_system,
        "age_high_code": rr.age_high_code,
        "text": rr.text,
    }


def _build_staging_observation(payload, *, org_id, user_id, actor) -> StagingObservationModel:
    """Build a fully-populated StagingObservationModel (children included) from one
    StagingObservationInput.

    Tenancy and audit come from the parent staging record, not the payload —
    a document and everything extracted from it belong to one tenant by
    construction, which is why StagingObservationInput has no org_id/user_id/
    created_by fields to disagree with.
    """
    # status is already an StagingObservationStatus — the input schema types it as the
    # enum so an invalid code is rejected by Pydantic as a 422 with the allowed
    # values listed, rather than reaching here and raising a bare ValueError
    # (a 500) from inside the transaction.
    scalars = _scalar_kwargs(payload, _NON_SCALAR_FIELDS)

    subject_type, subject_id = (None, None)
    if payload.subject:
        subject_type, subject_id = parse_reference(
            payload.subject, StagingObservationSubjectReferenceType
        )
    specimen_type, specimen_id = (None, None)
    if payload.specimen:
        specimen_type, specimen_id = parse_reference(
            payload.specimen, StagingObservationSpecimenReferenceType
        )
    device_type, device_id = (None, None)
    if payload.device:
        device_type, device_id = parse_reference(
            payload.device, StagingObservationDeviceReferenceType
        )

    obs = StagingObservationModel(
        **scalars,
        org_id=org_id,
        user_id=user_id,
        created_by=actor,
        subject_type=subject_type,
        subject_id=subject_id,
        specimen_type=specimen_type,
        specimen_id=specimen_id,
        device_type=device_type,
        device_id=device_id,
    )

    audit = {"org_id": org_id}

    obs.identifiers = [
        StagingObservationIdentifier(
            **audit,
            use=i.use,
            type_system=i.type_system,
            type_code=i.type_code,
            type_display=i.type_display,
            type_text=i.type_text,
            system=i.system,
            value=i.value,
            period_start=i.period_start,
            period_end=i.period_end,
            assigner=i.assigner,
        )
        for i in (payload.identifier or [])
    ]

    obs.categories = [
        StagingObservationCategory(**audit, **_coding_kwargs(c))
        for c in (payload.category or [])
    ]
    obs.interpretations = [
        StagingObservationInterpretation(**audit, **_coding_kwargs(i))
        for i in (payload.interpretation or [])
    ]

    # Typed references — each list has its own allowed-target enum, so the
    # reference string is validated against the right one.
    obs.based_on = [
        StagingObservationBasedOn(
            **audit,
            **_typed_ref(b.reference, StagingObservationBasedOn),
            reference_display=b.reference_display,
        )
        for b in (payload.based_on or [])
    ]
    obs.part_of = [
        StagingObservationPartOf(
            **audit,
            **_typed_ref(p.reference, StagingObservationPartOf),
            reference_display=p.reference_display,
        )
        for p in (payload.part_of or [])
    ]
    obs.performers = [
        StagingObservationPerformer(
            **audit,
            **_typed_ref(p.reference, StagingObservationPerformer),
            reference_display=p.reference_display,
        )
        for p in (payload.performer or [])
    ]
    obs.has_members = [
        StagingObservationHasMember(
            **audit,
            **_typed_ref(h.reference, StagingObservationHasMember),
            reference_display=h.reference_display,
        )
        for h in (payload.has_member or [])
    ]
    obs.derived_from = [
        StagingObservationDerivedFrom(
            **audit,
            **_typed_ref(d.reference, StagingObservationDerivedFrom),
            reference_display=d.reference_display,
        )
        for d in (payload.derived_from or [])
    ]

    # focus is Reference(Any) in R4 — an open reference, so its column is a
    # plain String and there is no enum to validate the type against.
    obs.focus = [
        StagingObservationFocus(
            **audit,
            **_open_ref(f.reference),
            reference_display=f.reference_display,
        )
        for f in (payload.focus or [])
    ]

    obs.notes = [_build_note(n, audit) for n in (payload.note or [])]

    obs.reference_ranges = [
        StagingObservationReferenceRange(
            **audit,
            **_reference_range_kwargs(rr),
            applies_to=[
                StagingObservationReferenceRangeAppliesTo(**audit, **_coding_kwargs(at))
                for at in (rr.applies_to or [])
            ],
        )
        for rr in (payload.reference_range or [])
    ]

    obs.components = [
        StagingObservationComponent(
            **audit,
            **_scalar_kwargs(comp, {"interpretation", "reference_range"}),
            interpretations=[
                StagingObservationComponentInterpretation(**audit, **_coding_kwargs(ci))
                for ci in (comp.interpretation or [])
            ],
            reference_ranges=[
                StagingObservationComponentReferenceRange(
                    **audit,
                    **_reference_range_kwargs(rr),
                    applies_to=[
                        StagingObservationComponentReferenceRangeAppliesTo(
                            **audit, **_coding_kwargs(at)
                        )
                        for at in (rr.applies_to or [])
                    ],
                )
                for rr in (comp.reference_range or [])
            ],
        )
        for comp in (payload.component or [])
    ]

    return obs


# Each typed-reference child table declares its own allowed-target enum on the
# reference_type column; read it off the column rather than maintaining a
# second mapping that could disagree with the model.
def _typed_ref(ref: str, model_cls) -> dict:
    enum_cls = model_cls.__table__.c.reference_type.type.enum_class
    ref_type, ref_id = parse_reference(ref, enum_cls)
    return {"reference_type": ref_type, "reference_id": ref_id}


def _open_ref(ref: str) -> dict:
    """Reference(Any): keep the type as a free string, still splitting on '/'
    so the id half lands in an integer column."""
    parts = ref.split("/", 1)
    if len(parts) != 2 or not parts[1].isdigit():
        from fastapi import HTTPException, status

        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail=f"Invalid reference '{ref}'. Expected 'ResourceType/<integer id>'.",
        )
    return {"reference_type": parts[0], "reference_id": int(parts[1])}


_assert_scalar_fields_map()
