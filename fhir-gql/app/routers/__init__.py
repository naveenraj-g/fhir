from fastapi import APIRouter

from app.routers.appointment import router as appointments_router
from app.routers.healthcare_service import router as healthcare_services_router
from app.routers.location import router as locations_router
from app.routers.organization import router as organizations_router
from app.routers.patient import router as patients_router
from app.routers.practitioner import router as practitioners_router
from app.routers.practitioner_role import router as practitioner_roles_router
from app.routers.schedule import router as schedules_router
from app.routers.slot import router as slots_router
from app.routers.terminology import router as terminology_router

api_router = APIRouter()

api_router.include_router(organizations_router)
api_router.include_router(locations_router)
api_router.include_router(healthcare_services_router)
api_router.include_router(schedules_router)
api_router.include_router(slots_router)
api_router.include_router(practitioners_router)
api_router.include_router(practitioner_roles_router)
api_router.include_router(patients_router)
api_router.include_router(appointments_router)
api_router.include_router(terminology_router)
