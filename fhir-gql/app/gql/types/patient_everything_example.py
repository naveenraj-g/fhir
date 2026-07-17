"""
EXAMPLE / reference file — fans out from one known Patient ID to every OTHER
FHIR resource type clinically related to that patient (Appointments,
Encounters, ServiceRequests, alongside the Patient itself), mirroring what
FHIR's own `Patient/$everything` operation returns in a single call.

This is a separate pattern from app/gql/types/patient_lazy_example.py, even
though it reuses that module's `PatientLazyType` for its own `patient`
field: that file demonstrates independent/dependent resolvers WITHIN one
resource (a Patient's own sub-resource arrays); this file demonstrates the
same "independent siblings, known ID up front" shape ACROSS resource TYPES —
Patient, Appointment, Encounter, ServiceRequest are different FHIR resources
entirely, each with its own service, its own response schema, and its own
RBAC permission.

`patient`, `appointments`, `encounters`, and `serviceRequests` below are each
an independent `@strawberry.field` resolver that needs only the same
`patient_id` (stored once, privately, as `strawberry.Private[int]` so it's
usable internally without being exposed as its own GraphQL field) — never
another field's result. So unlike `patientsLazy` in
app/gql/resolvers/patient_lazy_example.py (where each patient's sub-resource
fetches are gated behind that same patient's own row resolving out of a
list first), there is no dependency chain here at all: the ID is already
known as a query argument, exactly like `patientLazy`'s own sub-resources,
just fanned out across resource types instead of across one resource's
fields. Request more than one of the four together and graphql-core awaits
them fully in parallel — the same free concurrency, one level up.

Each of the four fields also enforces its OWN resource's RBAC permission
independently (`patient:read` / `appointment:read` / `encounter:read` /
`service_request:read`) rather than one blanket check at the top-level
resolver. That is a genuine GraphQL-over-REST advantage worth naming
explicitly: a caller missing only `encounter:read` still gets `patient`,
`appointments`, and `serviceRequests` back correctly, with a GraphQLError
scoped to just the `encounters` field (`extensions.code == 403`) instead of
the whole request failing — REST's one-endpoint-one-permission-gate model
can't express that granularity for a request spanning several resource
types in a single round trip.
"""

from typing import List

import strawberry

from app.gql.context import get_container
from app.gql.errors import translate_errors
from app.gql.permissions import require_gql_permission
from app.gql.types.patient_lazy_example import PatientLazyType
from app.schemas.appointment.input import ListAppointmentsSchema
from app.schemas.appointment.response import AppointmentResponse
from app.schemas.encounter.input import ListEncountersSchema
from app.schemas.encounter.response import EncounterResponse
from app.schemas.service_request.input import ListServiceRequestsSchema
from app.schemas.service_request.response import ServiceRequestResponse

# ── Leaf response types ───────────────────────────────────────────────────
# Deliberately named `Everything...` rather than `AppointmentType`/
# `EncounterType`/`ServiceRequestType` — those names are reserved for the
# real GraphQL types the rollout plan adds when Appointment/Encounter/
# ServiceRequest get their own app/gql/types/<resource>.py, per
# ARCHITECTURE.md's plan. This file is read-only and example-scoped, so it
# gets its own names to avoid colliding with that future work.
#
# Each type below lists its fields explicitly via `strawberry.auto` instead
# of `all_fields=True`. Unlike Patient/Organization (whose nested sub-models
# were deliberately wrapped one by one for the real pilot), Appointment/
# Encounter/ServiceRequest's response schemas each nest 10-20+ child-array
# sub-models (PlainAppointmentParticipant, PlainEncounterDiagnosis, etc.).
# `all_fields=True` would try to wrap every one of those too and fail with
# `UnregisteredTypeException` until each is individually registered — real
# work belonging to those resources' own future rollout, not this "does the
# fan-out concurrency pattern work across resource types" example. Naming
# the summary-relevant scalar fields explicitly here keeps this example
# self-contained and correctly scoped.


@strawberry.experimental.pydantic.type(
    model=AppointmentResponse,
    description="An Appointment that includes this patient — read-only summary used by patientEverything.",
)
class EverythingAppointmentType:
    """An Appointment that includes this patient (patientEverything example only)."""

    id: strawberry.auto
    status: strawberry.auto
    start: strawberry.auto
    end: strawberry.auto
    minutes_duration: strawberry.auto
    description: strawberry.auto
    subject_id: strawberry.auto
    subject_display: strawberry.auto
    encounter_id: strawberry.auto


@strawberry.experimental.pydantic.type(
    model=EncounterResponse,
    description="An Encounter for this patient — read-only summary used by patientEverything.",
)
class EverythingEncounterType:
    """An Encounter for this patient (patientEverything example only)."""

    id: strawberry.auto
    status: strawberry.auto
    subject_id: strawberry.auto
    subject_display: strawberry.auto
    actual_period_start: strawberry.auto
    actual_period_end: strawberry.auto
    planned_start_date: strawberry.auto
    planned_end_date: strawberry.auto
    service_provider_display: strawberry.auto


@strawberry.experimental.pydantic.type(
    model=ServiceRequestResponse,
    description="A ServiceRequest for this patient — read-only summary used by patientEverything.",
)
class EverythingServiceRequestType:
    """A ServiceRequest for this patient (patientEverything example only)."""

    id: strawberry.auto
    status: strawberry.auto
    intent: strawberry.auto
    priority: strawberry.auto
    code_display: strawberry.auto
    code_text: strawberry.auto
    subject_id: strawberry.auto
    subject_display: strawberry.auto
    encounter_id: strawberry.auto
    occurrence_datetime: strawberry.auto
    authored_on: strawberry.auto
    requester_display: strawberry.auto


@strawberry.type(
    description=(
        "EXAMPLE root type mirroring FHIR's Patient/$everything operation: fans out "
        "from one patientId to every resource type clinically related to that "
        "patient. `patient`, `appointments`, `encounters`, and `serviceRequests` are "
        "all independent of each other — each needs only patientId, never another "
        "field's result — so requesting more than one resolves them fully in "
        "parallel. Each field enforces its own resource's permission independently; "
        "see this module's docstring for why that matters."
    )
)
class PatientEverythingType:
    """Fans out from one patientId to every FHIR resource type related to that patient — all siblings, all independent, all parallel."""

    # Not exposed as a GraphQL field itself (strawberry.Private excludes it
    # from the schema) — it exists purely so the four resolvers below have
    # something to key their own independent fetches off of.
    patient_id: strawberry.Private[int]

    @strawberry.field(description="The Patient itself, with its own lazily-resolved sub-resources — see PatientLazyType. Requires `patient:read`.")
    @translate_errors
    async def patient(self, info: strawberry.types.Info) -> PatientLazyType:
        actor = require_gql_permission(info, "patient", "read")
        service = get_container(info).patient.patient_service()
        core = await service.get_by_id(self.patient_id, actor)
        return PatientLazyType.from_core_dict(core)

    @strawberry.field(
        description=(
            "Appointments that include this patient. Independent of the other "
            "Everything fields — needs only patientId. Requires `appointment:read`."
        )
    )
    @translate_errors
    async def appointments(self, info: strawberry.types.Info) -> List[EverythingAppointmentType]:
        actor = require_gql_permission(info, "appointment", "read")
        service = get_container(info).appointment.appointment_service()
        filters = ListAppointmentsSchema(patient_id=self.patient_id)
        data = await service.list(filters, actor)
        return [EverythingAppointmentType.from_pydantic(AppointmentResponse.model_validate(item)) for item in data["data"]]

    @strawberry.field(
        description=(
            "Encounters for this patient. Independent of the other Everything "
            "fields — needs only patientId. Requires `encounter:read`."
        )
    )
    @translate_errors
    async def encounters(self, info: strawberry.types.Info) -> List[EverythingEncounterType]:
        actor = require_gql_permission(info, "encounter", "read")
        service = get_container(info).encounter.encounter_service()
        filters = ListEncountersSchema(patient_id=self.patient_id)
        data = await service.list(filters, actor)
        return [EverythingEncounterType.from_pydantic(EncounterResponse.model_validate(item)) for item in data["data"]]

    @strawberry.field(
        description=(
            "ServiceRequests for this patient. Independent of the other Everything "
            "fields — needs only patientId. Requires `service_request:read`."
        )
    )
    @translate_errors
    async def service_requests(self, info: strawberry.types.Info) -> List[EverythingServiceRequestType]:
        actor = require_gql_permission(info, "service_request", "read")
        service = get_container(info).service_request.service_request_service()
        filters = ListServiceRequestsSchema(patient_id=self.patient_id)
        data = await service.list(filters, actor)
        return [
            EverythingServiceRequestType.from_pydantic(ServiceRequestResponse.model_validate(item)) for item in data["data"]
        ]
