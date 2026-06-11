"""
Business logic layer for the Appointment resource.

AppointmentService sits between the router and AppointmentClient. It owns:
  - Empty-patch rejection (422 if the caller sends an empty PATCH body)
  - /me lookup: returns a paginated list of the caller's appointments (Variant B)

The service does NOT inject created_by or updated_by — FhirClient does that.
The service does NOT inject user_id or org_id — the caller supplies them in the
request body (optional, matching the fhir-server schema).
"""

from fastapi import HTTPException, status

from app.auth.models import AuthUser
from app.fhir_client.appointment import AppointmentClient
from app.schemas.appointment.input import (
    AppointmentCreateSchema,
    AppointmentPatchSchema,
    ListAppointmentsSchema,
    MeAppointmentsSchema,
)


class AppointmentService:
    """
    Service layer for Appointment CRUD operations.

    Mediates between the FastAPI router and AppointmentClient. All methods
    accept an optional `accept` string threaded through to the fhir-server for
    content negotiation.
    """

    def __init__(self, client: AppointmentClient) -> None:
        """
        Initialise with an AppointmentClient injected by the DI container.

        Args:
            client: The domain-specific HTTP client for Appointment operations.
        """
        self._client = client

    async def create(
        self,
        dto: AppointmentCreateSchema,
        actor: AuthUser,
        accept: str | None = None,
    ) -> dict:
        """
        Create a new Appointment resource on the fhir-server.

        Uses `by_alias=True` so the `class_` field is serialised as `"class"` in the
        JSON body (matching the fhir-server schema). `exclude_none=True` drops
        Optional fields that were not provided. FhirClient.post() stamps
        `created_by` from actor.sub automatically.

        All child arrays (participant, slot, reason, etc.) are embedded in this single
        call — the fhir-server has no separate sub-resource routes for Appointment.

        Args:
            dto:    Validated create input from the router.
            actor:  Authenticated caller — used by FhirClient for created_by.
            accept: Content-type preference forwarded to the fhir-server.

        Returns:
            The newly created Appointment dict (plain JSON or FHIR R4).
        """
        # by_alias=True: serialises `class_` → `"class"` for the fhir-server
        payload = dto.model_dump(by_alias=True, exclude_none=True)
        return await self._client.create(payload, actor, accept=accept)

    async def get_by_id(
        self,
        appointment_id: int,
        actor: AuthUser,
        accept: str | None = None,
    ) -> dict:
        """
        Fetch a single Appointment by integer primary key.

        The fhir-server populates all child arrays in the response automatically.

        Args:
            appointment_id: The appointment's integer ID on the fhir-server.
            actor:          Authenticated caller (kept for RBAC consistency).
            accept:         Content-type preference forwarded to the fhir-server.

        Returns:
            The Appointment resource dict with all child arrays populated.
        """
        return await self._client.get_by_id(appointment_id, accept=accept)

    async def list(
        self,
        filters: ListAppointmentsSchema,
        actor: AuthUser,
        accept: str | None = None,
    ) -> dict:
        """
        List Appointments with optional filters.

        Forwards all non-None filter values. `start_from`/`start_to` datetimes
        are serialised to ISO 8601 strings for the fhir-server query string.

        Args:
            filters: Validated query parameters from the router.
            actor:   Authenticated caller (kept for RBAC consistency).
            accept:  Content-type preference forwarded to the fhir-server.

        Returns:
            Paginated plain JSON or FHIR Bundle depending on accept.
        """
        return await self._client.list(
            accept=accept,
            status=filters.status.value if filters.status else None,
            patient_id=filters.patient_id,
            start_from=filters.start_from.isoformat() if filters.start_from else None,
            start_to=filters.start_to.isoformat() if filters.start_to else None,
            user_id=filters.user_id,
            org_id=filters.org_id,
            limit=filters.limit,
            offset=filters.offset,
        )

    async def update(
        self,
        appointment_id: int,
        dto: AppointmentPatchSchema,
        actor: AuthUser,
        accept: str | None = None,
    ) -> dict:
        """
        Partially update scalar fields on an Appointment.

        Only scalar fields are patchable (status, start, end, minutes_duration,
        description, cancellation_date, priority_*, recurrence_id, occurrence_changed).
        Rejects the request with 422 if all fields are None (empty body).
        FhirClient.patch() stamps updated_by from actor.sub automatically.

        Args:
            appointment_id: The appointment's integer primary key.
            dto:            Validated patch input; at least one field must be non-None.
            actor:          Authenticated caller — used by FhirClient for updated_by.
            accept:         Content-type preference forwarded to the fhir-server.

        Returns:
            The updated Appointment resource dict.

        Raises:
            HTTPException(422): If the patch body is empty.
        """
        payload = dto.model_dump(exclude_none=True)
        if not payload:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="At least one field must be provided for update.",
            )
        # Serialise enum values to their string representation for the fhir-server.
        if "status" in payload and hasattr(payload["status"], "value"):
            payload["status"] = payload["status"].value
        return await self._client.patch(appointment_id, payload, actor, accept=accept)

    async def delete(self, appointment_id: int, actor: AuthUser) -> None:
        """
        Permanently delete an Appointment and all its child records.

        The fhir-server cascades the delete to all child tables (participant, slot,
        reason, etc.). This operation is irreversible.

        Args:
            appointment_id: The appointment's integer primary key to delete.
            actor:          Authenticated caller (kept for RBAC consistency).
        """
        await self._client.delete(appointment_id)

    async def get_me(
        self,
        filters: MeAppointmentsSchema,
        actor: AuthUser,
        accept: str | None = None,
    ) -> dict:
        """
        Return a paginated list of Appointments belonging to the authenticated user (Variant B).

        Filters by `user_id=actor.sub` — the JWT subject is used as the user_id
        to scope results to the caller's own appointments. Additional optional filters
        (status, start_from, start_to, limit, offset) are forwarded from MeAppointmentsSchema.

        This is Variant B (1-to-many) — a user can have many appointments, so
        the response is a full paginated envelope, not a single resource.

        Args:
            filters: Validated query parameters from the router (no user_id/org_id).
            actor:   Authenticated caller — JWT subject used as user_id filter.
            accept:  Content-type preference forwarded to the fhir-server.

        Returns:
            Paginated plain JSON or FHIR Bundle of the caller's Appointments.
        """
        return await self._client.list(
            accept=accept,
            user_id=actor.sub,
            status=filters.status.value if filters.status else None,
            start_from=filters.start_from.isoformat() if filters.start_from else None,
            start_to=filters.start_to.isoformat() if filters.start_to else None,
            limit=filters.limit,
            offset=filters.offset,
        )
