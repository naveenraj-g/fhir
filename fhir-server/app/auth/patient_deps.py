"""
Patient ownership dependency.

get_authorized_patient — reusable FastAPI dependency that:
  1. Resolves the public patient_id from the URL path.
  2. Fetches the PatientModel from the database.
  3. Verifies that patient.user_id matches the authenticated user's sub claim.
  4. Returns the loaded PatientModel so route handlers don't need another DB hit.

Usage in a router:
    from app.auth.patient_deps import get_authorized_patient

    @router.get("/{patient_id}")
    async def get_patient(
        patient: PatientModel = Depends(get_authorized_patient),
        patient_service: PatientService = Depends(get_patient_service),
    ):
        return patient_service._to_fhir(patient)
"""

from fastapi import Depends, HTTPException, Request, Path, status
from app.models.patient import PatientModel
from app.services.patient_service import PatientService
from app.di.dependencies.patient import get_patient_service


async def get_authorized_patient(
    patient_id: int = Path(..., ge=1, description="Public patient identifier."),
    request: Request = ...,
    patient_service: PatientService = Depends(get_patient_service),
) -> PatientModel:
    """
    Dependency that resolves and ownership-validates a Patient.

    Raises:
        404 — patient not found.
        403 — authenticated user does not own this patient record.
    """
    user_id: str = request.state.user.get("sub")

    patient = await patient_service.get_raw_by_patient_id(patient_id)
    if not patient:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Patient not found")

    if patient.user_id != user_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied")

    return patient
