from fastapi import APIRouter

from . import core

router = APIRouter(prefix="/staging-records", tags=["Staging Medical Records"])
router.include_router(core.router)
