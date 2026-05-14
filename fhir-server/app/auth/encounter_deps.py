"""
Encounter ownership dependency.

get_authorized_encounter — reusable FastAPI dependency that:
  1. Resolves the public encounter_id from the URL path.
  2. Fetches the EncounterModel from the database.
  3. Verifies that encounter.user_id matches the authenticated user's sub claim.
  4. Returns the loaded EncounterModel so route handlers don't need another DB hit.
"""

from fastapi import Depends, HTTPException, Request, Path, status

from app.models.encounter.encounter import EncounterModel
from app.services.encounter_service import EncounterService
from app.di.dependencies.encounter import get_encounter_service


async def get_authorized_encounter(
    encounter_id: int = Path(..., ge=1, description="Public encounter identifier."),
    request: Request = ...,
    encounter_service: EncounterService = Depends(get_encounter_service),
) -> EncounterModel:
    """
    Dependency that resolves and ownership-validates an Encounter.

    Raises:
        404 — encounter not found.
        403 — authenticated user does not own this encounter record.
    """
    user_id: str = request.state.user.get("sub")

    encounter = await encounter_service.get_raw_by_encounter_id(encounter_id)
    if not encounter:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Encounter not found"
        )

    if encounter.user_id != user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Access denied"
        )

    return encounter
