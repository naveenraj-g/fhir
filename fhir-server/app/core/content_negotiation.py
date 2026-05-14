from fastapi import Request
from fastapi.encoders import jsonable_encoder
from fastapi.responses import JSONResponse

FHIR_MEDIA_TYPE = "application/fhir+json"


def wants_fhir(request: Request) -> bool:
    """Return True when the client signals it wants a FHIR-formatted response."""
    return FHIR_MEDIA_TYPE in request.headers.get("accept", "")


def format_response(
    fhir_data: dict, plain_data: dict, request: Request
) -> JSONResponse:
    """
    Serialise and return either the FHIR or the plain JSON representation
    depending on the Accept header.

    Always returns a JSONResponse so that FastAPI skips response_model
    validation — the response_model decorators are kept for OpenAPI docs only.
    jsonable_encoder handles dates, Enum subclasses, Decimal, etc.
    """
    if wants_fhir(request):
        return JSONResponse(
            content=jsonable_encoder(fhir_data),
            media_type=FHIR_MEDIA_TYPE,
        )
    return JSONResponse(content=jsonable_encoder(plain_data))


def format_list_response(
    fhir_list: list, plain_list: list, request: Request
) -> JSONResponse:
    if wants_fhir(request):
        return JSONResponse(
            content=jsonable_encoder(fhir_list),
            media_type=FHIR_MEDIA_TYPE,
        )
    return JSONResponse(content=jsonable_encoder(plain_list))
