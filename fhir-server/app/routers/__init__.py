from fastapi import APIRouter

from .patient import router as patient_router
from .practitioner import router as practitioner_router
from .encounter import router as encounter_router
from .appointment import router as appointment_router
from .questionnaire_response import router as questionnaire_response_router
from .condition import router as condition_router
from .service_request import router as service_request_router
from .device_request import router as device_request_router
from .diagnostic_report import router as diagnostic_report_router
from .medication_request import router as medication_request_router

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

api_router.include_router(condition_router, prefix="/conditions", tags=["Conditions"])

api_router.include_router(
    service_request_router, prefix="/service-requests", tags=["ServiceRequests"]
)

api_router.include_router(
    device_request_router, prefix="/device-requests", tags=["DeviceRequests"]
)

api_router.include_router(
    diagnostic_report_router, prefix="/diagnostic-reports", tags=["DiagnosticReports"]
)

api_router.include_router(
    medication_request_router, prefix="/medication-requests", tags=["MedicationRequests"]
)
