from fastapi import Depends, HTTPException, status

from app.di.dependencies.specimen import get_specimen_service
from app.models.specimen.specimen import SpecimenModel
from app.services.specimen_service import SpecimenService


async def get_authorized_specimen(
    specimen_id: int,
    service: SpecimenService = Depends(get_specimen_service),
) -> SpecimenModel:
    sp = await service.get_specimen(specimen_id)
    if sp is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Specimen not found")
    return sp
