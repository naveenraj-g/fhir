"""
Appointment ownership dependency.

get_authorized_appointment — reusable FastAPI dependency that:
  1. Resolves the public appointment_id from the URL path.
  2. Fetches the AppointmentModel from the database.
  3. Verifies that appointment.user_id matches the authenticated user's sub claim.
  4. Returns the loaded AppointmentModel so route handlers don't need another DB hit.
"""

from fastapi import Depends, HTTPException, Request, Path, status

from app.models.appointment.appointment import AppointmentModel
from app.services.appointment_service import AppointmentService
from app.di.dependencies.appointment import get_appointment_service


async def get_authorized_appointment(
    appointment_id: int = Path(..., ge=1, description="Public appointment identifier."),
    request: Request = ...,
    appointment_service: AppointmentService = Depends(get_appointment_service),
) -> AppointmentModel:
    """
    Dependency that resolves and ownership-validates an Appointment.

    Raises:
        404 — appointment not found.
        403 — authenticated user does not own this appointment record.
    """
    user_id: str = request.state.user.get("sub")

    appointment = await appointment_service.get_raw_by_appointment_id(appointment_id)
    if not appointment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Appointment not found"
        )

    if appointment.user_id != user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Access denied"
        )

    return appointment
