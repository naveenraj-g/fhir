"""
Practitioner ownership dependency.

get_authorized_practitioner — reusable FastAPI dependency that:
  1. Resolves the public practitioner_id from the URL path.
  2. Fetches the PractitionerModel from the database.
  3. Verifies that practitioner.user_id matches the authenticated user's sub claim.
  4. Returns the loaded PractitionerModel so route handlers skip an extra DB hit.

Usage in a router:
    from app.auth.practitioner_deps import get_authorized_practitioner

    @router.get("/{practitioner_id}")
    async def get_practitioner(
        practitioner: PractitionerModel = Depends(get_authorized_practitioner),
        practitioner_service: PractitionerService = Depends(get_practitioner_service),
    ):
        return practitioner_service._to_fhir(practitioner)
"""

from fastapi import Depends, HTTPException, Request, Path, status
from app.models.practitioner import PractitionerModel
from app.services.practitioner_service import PractitionerService
from app.di.dependencies.practitioner import get_practitioner_service


async def get_authorized_practitioner(
    practitioner_id: int = Path(..., ge=1, description="Public practitioner identifier."),
    request: Request = ...,
    practitioner_service: PractitionerService = Depends(get_practitioner_service),
) -> PractitionerModel:
    """
    Dependency that resolves and ownership-validates a Practitioner.

    Raises:
        404 — practitioner not found.
        403 — authenticated user does not own this practitioner record.
    """
    user_id: str = request.state.user.get("sub")

    practitioner = await practitioner_service.get_raw_by_practitioner_id(practitioner_id)
    if not practitioner:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Practitioner not found")

    if practitioner.user_id != user_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied")

    return practitioner
