from fastapi import APIRouter

from .patient import router as patient_router
from .practitioner import router as practitioner_router
from .encounter import router as encounter_router
from .appointment import router as appointment_router
from .questionnaire_response import router as questionnaire_response_router

api_router = APIRouter()

api_router.include_router(patient_router, prefix="/patients", tags=["Patients"])

api_router.include_router(
    practitioner_router, prefix="/practitioners", tags=["Practitioners"]
)

api_router.include_router(encounter_router, prefix="/encounters", tags=["Encounters"])

api_router.include_router(
    appointment_router, prefix="/appointments", tags=["Appointments"]
)

api_router.include_router(
    questionnaire_response_router,
    prefix="/questionnaire-responses",
    tags=["QuestionnaireResponses"],
)
