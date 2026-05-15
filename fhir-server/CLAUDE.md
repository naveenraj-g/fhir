# FHIR Server — Architecture & Agent Guide

## FHIR References

**This project targets FHIR R4. Always use R4 spec URLs. Never model from the default `https://www.hl7.org/fhir/` URL — that serves R5.**

- FHIR R4 base spec: https://www.hl7.org/fhir/R4/
- QuestionnaireResponse R4: https://www.hl7.org/fhir/R4/questionnaireresponse.html
- Datatypes R4: https://www.hl7.org/fhir/R4/datatypes.html
- Resource index R4: https://www.hl7.org/fhir/R4/resourcelist.html

---

## Project Overview

A **FHIR R4-compliant REST API server** built with FastAPI and PostgreSQL. It manages six healthcare resources: `Patient`, `Practitioner`, `Encounter`, `Appointment`, `QuestionnaireResponse`, and `Vitals` (non-FHIR, wearable data). Every endpoint supports dual-format responses: full FHIR R4 JSON (`application/fhir+json`) and a simplified snake_case JSON (`application/json`), selected via the `Accept` header.

---

## Tech Stack

| Concern | Library |
|---|---|
| Web framework | FastAPI + Uvicorn |
| Database | PostgreSQL 15 (async via asyncpg) |
| ORM | SQLAlchemy 2.0+ (async) |
| Auth | PyJWT + PyJWKClient (JWKS endpoint) |
| Sessions | Redis 7 (server-side) |
| DI container | dependency-injector |
| FHIR validation | fhir-resources 8.x |
| Config | pydantic-settings (.env) |
| Package manager | uv |
| Python | 3.12+ |

---

## Directory Structure

```
app/
├── main.py                          # FastAPI app, lifespan, middleware, router mount
├── core/
│   ├── config.py                    # Pydantic Settings — reads .env
│   ├── database.py                  # SQLAlchemy async engine + session_maker
│   ├── logging.py                   # JSON structured logging
│   ├── redis.py                     # Redis async client singleton
│   ├── session.py                   # Redis-backed server-side session manager
│   ├── request_context.py           # ContextVar for request_id + middleware
│   ├── content_negotiation.py       # format_response() / format_paginated_response()
│   ├── references.py                # parse_reference(), resolve_subject()
│   ├── schema_utils.py              # inline_schema() — inlines $ref/$defs for OpenAPI
│   └── keycloak.py                  # Optional Keycloak OIDC integration
├── auth/
│   ├── dependencies.py              # get_current_user(), require_permission(), decode_token()
│   ├── patient_deps.py              # get_authorized_patient() — ownership check
│   ├── appointment_deps.py          # get_authorized_appointment()
│   ├── encounter_deps.py            # get_authorized_encounter()
│   ├── practitioner_deps.py         # get_authorized_practitioner()
│   ├── vitals_deps.py               # get_authorized_vitals()
│   └── questionnaire_response_deps.py
├── di/
│   ├── container.py                 # Main DI container wiring all modules
│   ├── core.py                      # CoreContainer — Database singleton
│   ├── modules/                     # Per-resource DI modules (repository + service)
│   │   ├── patient.py
│   │   ├── appointment.py
│   │   ├── encounter.py
│   │   ├── practitioner.py
│   │   ├── questionnaire_response.py
│   │   └── vitals.py
│   └── dependencies/                # FastAPI @Depends wrappers that call DI container
│       ├── patient.py               # get_patient_service()
│       ├── appointment.py
│       ├── encounter.py
│       ├── practitioner.py
│       ├── questionnaire_response.py
│       └── vitals.py
├── models/
│   ├── enums.py                     # SubjectReferenceType, GenderType, IdentifierUse, etc.
│   ├── datatypes.py                 # CodeableConceptModel, CodingModel (shared)
│   ├── patient.py                   # PatientModel, PatientIdentifier, PatientTelecom, PatientAddress
│   ├── practitioner.py              # PractitionerModel + sub-resources
│   ├── appointment/
│   │   ├── appointment.py           # AppointmentModel, AppointmentParticipant,
│   │   │                            # AppointmentReasonCode, AppointmentRecurrenceTemplate
│   │   └── enums.py                 # AppointmentStatus, ParticipantStatus, ActorType
│   ├── encounter/
│   │   ├── encounter.py             # EncounterModel + sub-resources
│   │   └── enums.py
│   ├── questionnaire_response/
│   │   ├── questionnaire_response.py  # QRModel, QRItemModel, QRAnswerModel
│   │   ├── enums.py
│   │   └── __init__.py
│   └── vitals/
│       └── vitals.py                # VitalsModel (non-FHIR wearable data)
├── fhir/
│   └── mappers/                     # ORM model → FHIR dict and plain dict
│       ├── patient.py               # to_fhir_patient(), to_plain_patient()
│       ├── appointment.py           # to_fhir_appointment(), to_plain_appointment()
│       ├── encounter.py
│       ├── practitioner.py
│       └── questionnaire_response.py
├── repository/
│   ├── patient_repository.py        # PatientRepository — CRUD + filters + sub-resources
│   ├── appointment_repository.py
│   ├── encounter_repository.py
│   ├── practitioner_repository.py
│   ├── questionnaire_response_repository.py
│   └── vitals_repository.py
├── services/
│   ├── patient_service.py           # PatientService — thin orchestration layer
│   ├── appointment_service.py
│   ├── encounter_service.py
│   ├── practitioner_service.py
│   ├── questionnaire_response_service.py
│   └── vitals_service.py
├── routers/
│   ├── __init__.py                  # Assembles api_router from all sub-routers
│   ├── patient.py                   # POST/GET/PATCH/DELETE + sub-resource POSTs
│   ├── appointment.py
│   ├── encounter.py
│   ├── practitioner.py
│   ├── questionnaire_response.py
│   └── vitals.py                    # Non-FHIR; uses JSONResponse directly
├── schemas/
│   ├── patient.py                   # PatientCreateSchema, PatientPatchSchema
│   ├── appointment.py
│   ├── encounter.py
│   ├── practitioner.py
│   ├── questionnaire_response/      # Package — complex recursive schemas
│   │   ├── __init__.py              # Re-exports all QR input + response types
│   │   ├── input.py                 # CreateSchema, PatchSchema, AnswerInput, ItemInput (recursive)
│   │   └── response.py              # FHIR + plain response schemas
│   ├── vitals.py                    # VitalsCreateSchema, VitalsPatchSchema, PaginatedVitalsResponse
│   └── fhir/
│       ├── __init__.py              # Re-exports all FHIR + plain response schemas
│       ├── common.py                # FHIRBundle, FHIRReference, FHIRCoding
│       ├── patient.py               # FHIRPatientSchema, PlainPatientResponse, PaginatedPatientResponse
│       ├── appointment.py
│       ├── encounter.py
│       ├── practitioner.py
│       └── questionnaire_response.py
└── errors/
    ├── base.py                      # ApplicationError base class
    ├── handlers.py                  # Global exception handlers → FHIR OperationOutcome
    ├── auth.py / authorization.py / validation.py / infrastructure.py / domain.py
    └── validator/validate_model.py
```

---

## Layered Architecture

Every FHIR resource follows the same strict 4-layer flow:

```
HTTP Request
    │
    ▼
Router (app/routers/<resource>.py)
  - Validates request body via Pydantic schema
  - Extracts JWT claims from request.state.user
  - Calls service methods
  - Calls format_response() / format_paginated_response()
    │
    ▼
Service (app/services/<resource>_service.py)
  - Thin orchestration: delegates to repository
  - Hosts _to_fhir() and _to_plain() mapper wrappers
  - May contain cross-entity logic (e.g., patient_id resolution in VitalsService)
    │
    ▼
Repository (app/repository/<resource>_repository.py)
  - All database I/O via async SQLAlchemy
  - Session-per-operation pattern (async with self.session_factory() as session)
  - _with_relationships() helper for eager-loading sub-resources
  - _apply_list_filters() for reusable WHERE clauses
    │
    ▼
SQLAlchemy ORM Models (app/models/)
  - Declarative, async-compatible
  - Internal PK (id) + public sequence-based ID (patient_id, etc.)
```

---

## Public vs. Internal IDs

Every resource has **two IDs**:

| Column | Description | Exposed? |
|---|---|---|
| `id` | Auto-increment internal PK | Never — DB-internal only |
| `<resource>_id` | Sequence-based public ID starting at 10000+ | Yes — used in all APIs, FHIR references |

Sequences start at: Patient=10000, Practitioner=30000, Encounter=20000, Appointment=40000, QR=60000, Vitals=70000.

**Why:** Prevents enumeration, allows ID spaces to not collide, allows remapping.

```python
# Example from models/patient.py
patient_id_seq = Sequence("patient_id_seq", start=10000, increment=1)

class PatientModel(Base):
    __tablename__ = "patient"
    id = Column(Integer, primary_key=True)  # never exposed
    patient_id = Column(Integer, unique=True, server_default=patient_id_seq.next_value())
```

---

## Multi-Tenancy & Ownership

Every resource row stores:
- `user_id` — the JWT `sub` claim of the creating user
- `org_id` — the JWT `activeOrganizationId` claim

**Ownership enforcement** happens in `app/auth/<resource>_deps.py` via FastAPI path dependencies:

```python
# Pattern: get_authorized_<resource>()
async def get_authorized_vitals(
    vitals_id: int = Path(...),
    request: Request,
    vitals_service: VitalsService = Depends(get_vitals_service),
) -> VitalsModel:
    user_id = request.state.user.get("sub")
    vitals = await vitals_service.get_raw_by_vitals_id(vitals_id)
    if not vitals or vitals.user_id != user_id:
        raise HTTPException(status_code=403, detail="Access denied")
    return vitals
```

Used as `Depends(get_authorized_vitals)` in route function signatures — the loaded model is passed directly to the handler.

---

## JWT Authentication

All routes are protected by `get_current_user` from `app/auth/dependencies.py`, mounted globally on the API router in `main.py`.

```python
# main.py
app.include_router(api_router, prefix="/api/fhir/v1", dependencies=[Depends(get_current_user)])
app.include_router(vitals_router, prefix="/api/v1/vitals", dependencies=[Depends(get_current_user)])
```

`get_current_user` decodes the JWT using JWKS endpoint, validates expiry + audience, and stores claims in `request.state.user`. Routes read:

```python
user_id: str = request.state.user.get("sub")           # Used as created_by / user identity
org_id: str = request.state.user.get("activeOrganizationId")
```

**Permission checks** (for FHIR resources except vitals) use `require_permission`:

```python
dependencies=[Depends(require_permission("appointment", "create"))]
```

**Vitals** does NOT use `require_permission` — it uses `get_authorized_vitals` in function params instead.

---

## Content Negotiation

All FHIR resource routes return either FHIR JSON or plain JSON based on the `Accept` header. The decision is made by `format_response()` in `app/core/content_negotiation.py`:

```python
# Single resource
return format_response(
    service._to_fhir(model),   # dict with FHIR camelCase keys
    service._to_plain(model),  # dict with snake_case keys
    request,
)

# Paginated list
return format_paginated_response(
    [service._to_fhir(m) for m in models],
    [service._to_plain(m) for m in models],
    total, limit, offset, request,
)
```

- `Accept: application/fhir+json` → FHIR R4 format (resourceType, camelCase, FHIR Bundle for lists)
- `Accept: application/json` or absent → plain snake_case JSON, `{total, limit, offset, data[]}` for lists

**Vitals** does NOT use content negotiation — it returns only plain JSON via `JSONResponse` + `jsonable_encoder`.

---

## OpenAPI Spec is the Source of Truth

**The OpenAPI spec generated by this server is consumed by an MCP server (FastMCP) that exposes every endpoint as an AI tool. Any drift between the code and the emitted spec breaks the MCP layer silently.**

Rules that follow from this:

- **Every field that exists in the DB must appear in the response schema** — if it is in the model but missing from the response Pydantic schema, it will be invisible to MCP callers.
- **Every field that callers can send must appear in the request/create schema** — if it is accepted by the service but absent from the schema, MCP callers cannot pass it.
- **Content-negotiation variants must both be complete** — `application/json` (plain snake_case) and `application/fhir+json` both appear in the OpenAPI `responses` block. Keep both schemas up-to-date.
- **`inline_schema()` constants must be recomputed when schemas change** — they are module-level constants derived from `model_json_schema()`; if you add a field to a Pydantic schema the constant auto-updates on next import, but verify the emitted `/openapi.json` actually includes the field.
- **Summary / description strings on routes and fields matter** — MCP uses them to explain tools and parameters to the AI. Keep them accurate and specific.

---

## Full-Flow Checklist for Any Field Change

When you add, rename, or remove a field on any resource — even a single column — you must walk the entire stack. Missing any layer causes silent bugs or MCP contract drift.

### Adding / changing a field (e.g. adding `foo` to Patient)

1. **ORM Model** (`app/models/<resource>/<resource>.py`)
   - Add the `Column(...)` definition with correct type and `nullable=True/False`
   - Generate an Alembic migration: `just migrate-generate "add_foo_to_patient"` then `just migrate`

2. **CreateSchema** (`app/schemas/resources/<resource>.py` — `PatientCreateSchema`)
   - Add `foo: Optional[...] = Field(None, description="...")`
   - Add `foo` to the `json_schema_extra` example (with a realistic value)
   - Include `user_id` and `org_id` at the top of the example if not already present

3. **PatchSchema** (`PatientPatchSchema`)
   - Add the same field as optional (omit immutable fields like `recorded_at`)

4. **Repository** (`app/repository/<resource>_repository.py`)
   - Add `foo=payload.foo` in the `create()` method when constructing the ORM model
   - Add `if data.get("foo") is not None: model.foo = data["foo"]` in the `patch()` method

5. **FHIR Mapper** (`app/fhir/mappers/<resource>.py`)
   - `to_fhir_<resource>()`: map `model.foo` to the correct FHIR camelCase key
   - `to_plain_<resource>()`: add `"foo": model.foo` to the plain dict

6. **FHIR Response Schema** (`app/schemas/fhir/<resource>.py`)
   - `FHIRXxxSchema`: add the FHIR camelCase field
   - `PlainXxxResponse`: add the snake_case field
   - Both schemas feed the OpenAPI spec — both must be complete

7. **OpenAPI constants** (`app/routers/<resource>.py`)
   - `_SINGLE_200`, `_SINGLE_201`, `_LIST_200` are derived from the Pydantic schemas via `inline_schema(model_json_schema())`
   - They auto-update as long as the Pydantic schema is correct — verify by checking `/openapi.json` after the server starts
   - If you add a new route, add the corresponding `_SINGLE_*` or `_LIST_*` constant and wire it into `responses=`

8. **Service** (`app/services/<resource>_service.py`)
   - If `_to_fhir()` or `_to_plain()` call the mapper directly, no change needed
   - If the service does any field-level logic (e.g. cross-entity resolution), update it here

9. **Verify the emitted spec**
   - Start the server (`uv run fastapi dev app/main.py`) and open `http://localhost:8000/openapi.json`
   - Confirm `foo` appears in both the request body schema and the response schema for the affected routes
   - Confirm both `application/json` and `application/fhir+json` content types include the field where applicable

### Removing a field

Follow the same order in reverse. Remove from mapper first, then response schema, then create/patch schema, then repository, then model + migration.

---

## OpenAPI Response Schema Pattern

All routes define response schemas inline to avoid `$ref` resolution issues with Pydantic v2 complex models.

```python
# Module-level pre-computed constants (evaluated once at import)
_SINGLE_200 = {
    200: {
        "content": {
            "application/json": {"schema": inline_schema(PlainEncounterResponse.model_json_schema())},
            "application/fhir+json": {"schema": inline_schema(FHIREncounterSchema.model_json_schema())},
        }
    }
}
_SINGLE_201 = {201: _SINGLE_200[200]}   # Same content, correct status code for POST
_LIST_200 = {
    200: {
        "description": "Paginated list of encounters",
        "content": {
            "application/json": {"schema": inline_schema(PaginatedEncounterResponse.model_json_schema())},
            "application/fhir+json": {"schema": inline_schema(FHIREncounterBundle.model_json_schema())},
        },
    }
}

# Usage in routes
@router.post("/", status_code=201, responses={**_SINGLE_201, **_ERR_AUTH, **_ERR_VALIDATION})
@router.get("/{id}", responses={**_SINGLE_200, **_ERR_AUTH, **_ERR_NOT_FOUND})
@router.get("/", responses={**_LIST_200, **_ERR_AUTH})
```

**Vitals** only uses `application/json` (no FHIR dual-format) in its schema constants.

`inline_schema()` in `app/core/schema_utils.py` resolves `$defs` and `$ref` pointers so the emitted OpenAPI has no external references.

---

## Repository Pattern Details

### Session-per-operation
```python
async def get_by_encounter_id(self, encounter_id: int) -> Optional[EncounterModel]:
    async with self.session_factory() as session:   # opens + auto-closes
        stmt = _with_relationships(
            select(EncounterModel).where(EncounterModel.encounter_id == encounter_id)
        )
        result = await session.execute(stmt)
        return result.scalars().first()
```

### Eager-loading sub-resources (avoids N+1)
```python
def _with_relationships(stmt):
    return stmt.options(
        selectinload(EncounterModel.participants),
        selectinload(EncounterModel.diagnoses),
        selectinload(EncounterModel.locations),
        # ...
    )
```
Always use `_with_relationships()` when loading a model that will be serialized.

### Reusable filter helper
```python
def _apply_list_filters(self, stmt, user_id, org_id, status, patient_id, ...):
    if user_id:
        stmt = stmt.where(AppointmentModel.user_id == user_id)
    if status:
        stmt = stmt.where(AppointmentModel.status == status)
    # ... each filter is conditional
    return stmt

async def list(self, ...) -> Tuple[List[AppointmentModel], int]:
    async with self.session_factory() as session:
        base = self._apply_list_filters(_with_relationships(select(AppointmentModel)), ...)
        count_base = self._apply_list_filters(select(func.count()).select_from(AppointmentModel), ...)
        total = (await session.execute(count_base)).scalar_one()
        rows = list((await session.execute(base.order_by(...).offset(offset).limit(limit))).scalars().all())
    return rows, total
```

`get_me()` reuses `_apply_list_filters()` with `user_id`/`org_id` always non-None, plus the same optional resource filters as `list()`.

---

## Pydantic Schema Conventions

### Input schemas (request bodies)
Located in `app/schemas/<resource>.py` (flat file) or `app/schemas/<resource>/` (package for complex resources like QuestionnaireResponse that have recursive sub-schemas). Three schema types per resource:

1. **CreateSchema** — all optional fields except required ones; includes `user_id`, `org_id`, `pseudo_id`/`pseudo_id2` (identity); has `json_schema_extra` with a complete example including `user_id` and `org_id`
2. **PatchSchema** — same fields but all optional; excludes identity fields that cannot change (`user_id`, `org_id`, `recorded_at` for vitals)
3. **ResponseSchema** — all fields the API returns; includes `id` (public), `created_at`, `updated_at`

All schemas use `model_config = ConfigDict(extra="forbid")` to reject unknown fields.

### FHIR response schemas
Located in `app/schemas/fhir/`. Two variants per resource:
- `FHIRXxxSchema` — FHIR R4 camelCase structure, `resourceType` field
- `PlainXxxResponse` — snake_case flat structure
- `PaginatedXxxResponse` — wraps `List[PlainXxxResponse]` with `total`, `limit`, `offset`
- `FHIRXxxBundle` — FHIR Bundle with `entry[]`

### Recursive schemas (QuestionnaireResponse)
`AnswerInput` and `ItemInput` self-reference (items can contain items). Must call `model_rebuild()` after class definition:
```python
AnswerInput.model_rebuild()
ItemInput.model_rebuild()
```

---

## FHIR Mapper Pattern

Located in `app/fhir/mappers/<resource>.py`. Each file has two public functions:

```python
def to_fhir_<resource>(model: XxxModel) -> dict:
    """Returns FHIR R4 dict with camelCase keys and resourceType."""
    result = {
        "resourceType": "Appointment",
        "id": str(model.appointment_id),   # always string in FHIR
        "status": model.status,
    }
    # References reconstructed from stored enum + id
    if model.subject_type and model.subject_id:
        result["subject"] = {
            "reference": f"{model.subject_type.value}/{model.subject_id}",
            "display": model.subject_display,
        }
    # Strip None values at end
    return {k: v for k, v in result.items() if v is not None}

def to_plain_<resource>(model: XxxModel) -> dict:
    """Returns flat snake_case dict."""
    return {
        "id": model.appointment_id,        # int in plain JSON
        "status": model.status,
        "subject": f"{model.subject_type.value}/{model.subject_id}" if model.subject_type else None,
        # ...
    }
```

References stored in DB as `(subject_type: Enum, subject_id: int)` → reconstructed as `"Patient/10001"` strings in output.

---

## Audit Fields

All resources track:
- `created_at` — DB server default (`func.now()`)
- `updated_at` — DB `onupdate=func.now()`
- `created_by` — set from `request.state.user.get("sub")` in POST routes
- `updated_by` — set from `request.state.user.get("sub")` in PATCH routes

```python
# Route handler pattern
async def create_encounter(payload, request, encounter_service):
    created_by: str = request.state.user.get("sub")
    encounter = await encounter_service.create_encounter(payload, payload.user_id, payload.org_id, created_by)

async def patch_encounter(payload, request, encounter, encounter_service):
    updated_by: str = request.state.user.get("sub")
    updated = await encounter_service.patch_encounter(encounter.encounter_id, payload, updated_by=updated_by)
```

---

## Paginated Response Structure

All list endpoints return:
```json
{
    "total": 150,
    "limit": 50,
    "offset": 0,
    "data": [...]
}
```

FHIR Bundle format (when `Accept: application/fhir+json`):
```json
{
    "resourceType": "Bundle",
    "type": "searchset",
    "total": 150,
    "entry": [{"resource": {...}}]
}
```

Pagination query params on all list + `/me` routes:
- `limit: int = Query(50, ge=1, le=200)`
- `offset: int = Query(0, ge=0)`

---

## `/me` Route Pattern

Each resource has a `GET /me` route that scopes results to the authenticated user's `sub` and `activeOrganizationId`. These routes support the same filters as `GET /` (minus `user_id`/`org_id` which come from the JWT).

```
GET /api/fhir/v1/appointments/me?status=booked&start_from=2026-01-01
GET /api/fhir/v1/encounters/me?status=finished&class_code=AMB
GET /api/fhir/v1/questionnaire-responses/me?questionnaire=http://loinc.org/phq-9
GET /api/v1/vitals/me?date=2026-05-01
```

Route ordering: `/me` must be declared **before** `/{id}` in the router file to avoid FastAPI treating `me` as a path parameter.

---

## Error Handling

All errors return FHIR OperationOutcome format:

```json
{
    "resourceType": "OperationOutcome",
    "issue": [
        {
            "severity": "error",
            "code": "invalid",
            "diagnostics": "Field body.status — field required",
            "expression": ["status"]
        }
    ]
}
```

Registered handlers in `app/errors/handlers.py`:
- `ApplicationError` (400/401/403/404/500 depending on subclass)
- `RequestValidationError` (422 — Pydantic body validation)
- `HTTPException` (FastAPI standard)
- `Exception` (catch-all 500)

---

## Dependency Injection Setup

The DI container uses `dependency-injector`. Pattern for every resource:

```python
# di/modules/appointment.py
class AppointmentContainer(containers.DeclarativeContainer):
    core = providers.DependenciesContainer()

    appointment_repository = providers.Factory(
        AppointmentRepository,
        session_factory=core.database.provided.session,
    )
    appointment_service = providers.Factory(
        AppointmentService,
        repository=appointment_repository,
    )

# di/dependencies/appointment.py
@inject
def get_appointment_service(
    service: AppointmentService = Depends(Provide[Container.appointment.appointment_service]),
) -> AppointmentService:
    return service

# In route handler
async def create_appointment(
    ...,
    appointment_service: AppointmentService = Depends(get_appointment_service),
):
    ...
```

---

## Environment Configuration

Required `.env` variables (see `.env.example`):

```
ENVIRONMENT=development
FHIR_DATABASE_URL=postgresql+asyncpg://user:password@localhost/fhir-server
REDIS_URL=redis://localhost:6379
IAM_ISSUER=https://your-iam-provider/issuer
IAM_JWKS_URL=https://your-iam-provider/.well-known/jwks.json
# Optional Keycloak integration:
KEYCLOAK_URL=http://localhost:8080
KEYCLOAK_REALM_NAME=your-realm
KEYCLOAK_CLIENT_ID=your-client-id
KEYCLOAK_CLIENT_SECRET=your-secret
```

---

## Running the Project

```bash
# Install dependencies
uv sync

# Start dev server (auto-reload)
uv run fastapi dev app/main.py

# OpenAPI docs
http://localhost:8000/docs

# Docker (includes postgres + redis)
docker compose up --build
```

---

## FHIR Model Design Rules

### Always read the full spec before modeling

When given a FHIR resource URL (e.g. `https://www.hl7.org/fhir/procedure.html`), **do not model from memory or assumption**. Fetch and read:

1. **The resource page itself** — full element definition table, every field, cardinality, type, and allowed codes.
2. **Every named datatype used in that resource** — follow each type link and read its own spec page. Common ones that have non-obvious internal structure:

| Datatype | Spec URL | Key structure to read |
|---|---|---|
| `Annotation` | `.../datatypes.html#Annotation` | `text` is **1..1 required**; `author[x]` is string OR Reference; `time` is dateTime |
| `Timing` | `.../datatypes.html#Timing` | Has nested `repeat` BackboneElement with 15+ fields |
| `Dosage` | `.../datatypes.html#Dosage` | Has `doseAndRate[]` (0..*) and `additionalInstruction[]` (0..*) — both need child tables |
| `Identifier` | `.../datatypes.html#Identifier` | Has `type` (CodeableConcept), `period` (Period), `assigner` (Reference) |
| `CodeableConcept` | `.../datatypes.html#CodeableConcept` | Has `coding[]` (0..*) and `text` (0..1) |
| `Quantity / SimpleQuantity / Duration / Age` | `.../datatypes.html#Quantity` | Quantity has `comparator`; SimpleQuantity does not |
| `Range` | `.../datatypes.html#Range` | `low` and `high` are SimpleQuantity |
| `Ratio` | `.../datatypes.html#Ratio` | `numerator` is Quantity; `denominator` is SimpleQuantity |
| `Period` | `.../datatypes.html#Period` | `start` and `end` are dateTime |
| `ExtendedContactDetail` | `.../metadatatypes-definitions.html` | Has `purpose` (CodeableConcept), `name[]` (HumanName, 0..*), `telecom[]` (ContactPoint, 0..*), `address` (0..1 Address), `organization` (Reference), `period` — **name[] and telecom[] are 0..* so they become grandchild tables** |
| `Availability` | `.../metadatatypes-definitions.html` | Has `availableTime[]` (0..*, BackboneElement) and `notAvailableTime[]` (0..*, BackboneElement) — the Availability row itself is a grouping parent; its two arrays are child tables |
| `HumanName` | `.../datatypes.html#HumanName` | `given[]`, `prefix[]`, `suffix[]` are 0..* — store comma-separated since they are ordered display strings, never individually filtered |
| `ContactPoint` | `.../datatypes.html#ContactPoint` | `system`, `value`, `use`, `rank`, `period` — all scalar; one row per contact point |
| `Address` | `.../datatypes.html#Address` | `line[]` is 0..* — store comma-separated; all other fields are scalar and flatten to columns |

3. **Every BackboneElement** in the resource — these have their own sub-fields that must be read, not assumed. Backbone elements with `0..*` cardinality become child tables; their internal `0..*` sub-fields become grandchild tables.

4. **Always use R4 spec** — fetch from `https://www.hl7.org/fhir/R4/<resource>.html`. Never use `https://www.hl7.org/fhir/<resource>.html` (that is R5). Key R4 patterns to remember:
   - `reasonCode[]` + `reasonReference[]` are **separate** arrays in R4 (R5 merges them into `reason[]` CodeableReference)
   - `complication[]` + `complicationDetail[]` are separate in R4
   - `usedReference[]` + `usedCode[]` are separate in R4
   - `category` is **0..1** in R4 for most resources (R5 changes to 0..*)
   - `CodeableReference` does **not exist** in R4 — it is an R5 datatype
   - `QuestionnaireResponse.identifier` is **0..1** in R4 (flat columns), **0..\*** in R5 (child table)
   - `QuestionnaireResponse.questionnaire` is **0..1** in R4 (optional), **1..1** in R5
   - `QuestionnaireResponse.source` in R4: Reference(Patient | Practitioner | PractitionerRole | RelatedPerson) — Device and Organization are R5-only
   - `QuestionnaireResponse.author` in R4: Reference(Device | Practitioner | PractitionerRole | Patient | RelatedPerson | Organization) — Group is R5-only
   - **PractitionerRole**: this project intentionally models PractitionerRole using the R5 structure (contact + availability) as an exception — do not revert it

**The rule:** if a field's type is a named FHIR datatype (not a primitive like `string`, `boolean`, `dateTime`, `integer`), fetch its spec page before deciding how to store it. Never assume structure from the type name alone.

---

### Cardinality → storage mapping

The cardinality in the FHIR spec directly determines where a field lives in the DB:

| FHIR cardinality | Storage |
|---|---|
| `1..1` or `0..1` | Flat column(s) on the main model table |
| `0..*` | Separate child table + one-to-many relationship |

**Never put a repeating (0..*) field in a single column** (e.g. comma-separated text). Each array element needs its own row so it can be queried, filtered, and individually deleted. Allowed exceptions (stored as comma-separated `Text` because they are never individually filtered):
- `instantiatesCanonical[]` / `instantiatesUri[]` — simple URI lists
- `availableTime.daysOfWeek[]` — ordered code list (`mon,tue,wed`); always read/written as a unit
- `HumanName.given[]` / `HumanName.prefix[]` / `HumanName.suffix[]` — display-only ordered strings
- `Address.line[]` — ordered street address lines

```python
# ✓ 0..1  →  flat columns on main table
code_system  = Column(String, nullable=True)
code_code    = Column(String, nullable=True)
code_display = Column(String, nullable=True)

# ✓ 0..*  →  child table
class ServiceRequestCategory(Base):
    __tablename__ = "service_request_category"
    id                 = Column(Integer, primary_key=True, autoincrement=True)
    service_request_id = Column(Integer, ForeignKey("service_request.id"), nullable=False, index=True)
    coding_system      = Column(String, nullable=True)
    coding_code        = Column(String, nullable=True)
    coding_display     = Column(String, nullable=True)
    text               = Column(String, nullable=True)
    service_request    = relationship("ServiceRequestModel", back_populates="categories")
```

### CodeableConcept flattening

A single `CodeableConcept` (0..1) is flattened to `<field>_system`, `<field>_code`, `<field>_display`, `<field>_text` on the main table.
A repeated `CodeableConcept[]` (0..*) gets a child table with columns `coding_system`, `coding_code`, `coding_display`, `text`.

### Reference flattening

A reference (0..1) is stored as two or three columns on the main table:
```python
subject_type    = Column(Enum(SubjectReferenceType), nullable=True)  # "Patient" | "Group"
subject_id      = Column(Integer, nullable=True)                      # public resource id
subject_display = Column(String, nullable=True)                       # optional human label
```
A repeated reference (0..*) gets a child table with `reference_type`, `reference_id`, `reference_display`.

Use an **Enum** for `reference_type` when the allowed resource types are a closed, known set (e.g. subject can only be Patient or Group). Use a plain **String** when the type is open (e.g. `supportingInfo[]` allows any resource type).

### Shared PostgreSQL enum types

Some FHIR reference types appear across many resources and reuse a **single shared PostgreSQL enum type** to avoid duplicate type creation. Always import from `app.models.enums` and use `create_type=False`:

| Python class | DB type name | Allowed value | Used by |
|---|---|---|---|
| `OrganizationReferenceType` | `organization_reference_type` | `"Organization"` | Patient, Encounter, Practitioner, PractitionerRole, HealthcareService, … |
| `SubjectReferenceType` | `subject_reference_type` | `"Patient"`, `"Group"` | Encounter, Appointment, QuestionnaireResponse |

```python
from app.models.enums import OrganizationReferenceType

# Correct — always create_type=False because the PG type already exists
organization_type = Column(
    Enum(OrganizationReferenceType, name="organization_reference_type", create_type=False),
    nullable=True,
)
organization_id      = Column(Integer, nullable=True)
organization_display = Column(String, nullable=True)
```

**Never** store an Organization reference as a plain `String` column. The `organization_reference_type` PG enum was created by the first migration that used it (Patient); every subsequent table reuses it with `create_type=False`. The `ContactPointSystem` and `ContactPointUse` enums in `app/schemas/enums.py` follow the same shared-type pattern.

### CodeableReference flattening (R5)

`CodeableReference` is an R5 datatype that combines a `CodeableConcept` (concept) and a `Reference` (reference) in a single field. Both halves are optional — callers may provide either or both.

**Rule:** Every `CodeableReference` column in a child table gets **both** the concept columns AND the reference columns:

```python
class AppointmentReason(Base):
    __tablename__ = "appointment_reason"
    id             = Column(Integer, primary_key=True, autoincrement=True)
    appointment_id = Column(Integer, ForeignKey("appointment.id"), nullable=False, index=True)
    org_id         = Column(String, nullable=True)

    # concept (CodeableConcept)
    coding_system  = Column(String, nullable=True)
    coding_code    = Column(String, nullable=True)
    coding_display = Column(String, nullable=True)
    text           = Column(String, nullable=True)

    # reference (Reference — closed set → Enum; open set → String)
    reference_type = Column(
        Enum(AppointmentReasonReferenceType, name="appointment_reason_reference_type"),
        nullable=True,
    )
    reference_id      = Column(Integer, nullable=True)
    reference_display = Column(String, nullable=True)
```

**Enum naming convention:** `<Resource><Field>ReferenceType` in Python, `<table_name>_reference_type` as the PostgreSQL type name.

**FHIR R5 output:**
```python
entry = {}
concept = _cc(r.coding_system, r.coding_code, r.coding_display, r.text)
if concept:
    entry["concept"] = concept
if r.reference_type and r.reference_id:
    ref = {"reference": f"{r.reference_type.value}/{r.reference_id}"}
    if r.reference_display:
        ref["display"] = r.reference_display
    entry["reference"] = ref
```

### PostgreSQL Enum migration rules

Alembic autogenerate is unreliable for enum columns. **Always manually fix generated migrations** before applying:

1. **Use `postgresql.ENUM` not `sa.Enum`** — autogenerate emits `sa.Enum('MEMBER_NAME', ...)` using Python uppercase member names; replace with `postgresql.ENUM('TitleCaseValue', ...)` matching actual FHIR values.

2. **Create the type explicitly** — call `.create(op.get_bind(), checkfirst=True)` before the first `alter_column` or `add_column` that uses it; use `create_type=False` on the column definition to avoid double-creation:
```python
from sqlalchemy.dialects import postgresql

_my_enum = postgresql.ENUM('Condition', 'Procedure', name='my_enum_type')

def upgrade() -> None:
    _my_enum.create(op.get_bind(), checkfirst=True)
    op.add_column('my_table', sa.Column(
        'reference_type',
        postgresql.ENUM('Condition', 'Procedure', name='my_enum_type', create_type=False),
        nullable=True,
    ))
```

3. **VARCHAR → Enum requires USING clause** — when converting an existing VARCHAR column:
```python
op.alter_column('my_table', 'reference_type',
    existing_type=sa.VARCHAR(),
    type_=postgresql.ENUM('Condition', 'Procedure', name='my_enum_type', create_type=False),
    existing_nullable=True,
    postgresql_using='reference_type::my_enum_type',
)
```

4. **Downgrade must drop the type** — call `.drop(op.get_bind(), checkfirst=True)` after reverting the column.

### `_cast_ref_type` helper in repository

When a CodeableReference input arrives as a plain string reference (e.g. `"Condition/12345"`), validate the resource type against the closed enum at the repository layer:

```python
def _cast_ref_type(value: str, enum_cls, field: str):
    try:
        return enum_cls(value)
    except ValueError:
        allowed = [e.value for e in enum_cls]
        raise HTTPException(
            status_code=422,
            detail=f"Invalid reference type '{value}' for {field}. Allowed: {allowed}.",
        )

# Usage in create():
ref_type_str, ref_id = _parse_open_ref(r.reference)   # splits "Condition/123" → ("Condition", 123)
ref_type_enum = _cast_ref_type(ref_type_str, AppointmentReasonReferenceType, "reason.reference")
```

### Child table conventions

Every child table must have:
- `id` — auto-increment PK
- `<parent>_id` — FK to `<parent>.id` (internal PK), indexed, `nullable=False`
- `org_id` — nullable String (for future tenant-scoped sub-resource queries)
- A `relationship()` back to the parent with no `cascade` on the child side

The parent model declares the relationship with `cascade="all, delete-orphan"`.

### Multi-level nesting (grandchild tables)

When a `0..*` field's type is itself a complex datatype that contains `0..*` sub-fields, you need **three levels of tables**: main → child → grandchild. Never flatten grandchild arrays into the child row.

**Example — PractitionerRole `contact[]` (ExtendedContactDetail):**

```
practitioner_role                        ← main table
  └── practitioner_role_contact          ← child: one row per ExtendedContactDetail entry
        ├── practitioner_role_contact_name[]    ← grandchild: HumanName (0..*)
        └── practitioner_role_contact_telecom[] ← grandchild: ContactPoint (0..*)
```

```python
# Child table: one row per contact entry
class PractitionerRoleContact(Base):
    __tablename__ = "practitioner_role_contact"
    id = Column(Integer, primary_key=True, autoincrement=True)
    practitioner_role_id = Column(Integer, ForeignKey("practitioner_role.id"), nullable=False, index=True)
    # flat fields: purpose (CodeableConcept), address, organization ref, period
    names   = relationship("PractitionerRoleContactName",   back_populates="contact", cascade="all, delete-orphan")
    telecoms = relationship("PractitionerRoleContactTelecom", back_populates="contact", cascade="all, delete-orphan")

# Grandchild table: one row per HumanName within a contact
class PractitionerRoleContactName(Base):
    __tablename__ = "practitioner_role_contact_name"
    id         = Column(Integer, primary_key=True, autoincrement=True)
    contact_id = Column(Integer, ForeignKey("practitioner_role_contact.id"), nullable=False, index=True)
    ...
```

**Example — PractitionerRole `availability[]` (Availability datatype):**

```
practitioner_role
  └── practitioner_role_availability          ← grouping row (one per Availability entry)
        ├── practitioner_role_availability_time[]      ← availableTime BackboneElement
        └── practitioner_role_not_available_time[]     ← notAvailableTime BackboneElement
```

The Availability grouping row carries no scalar fields of its own — it exists only to anchor the two `0..*` child arrays. Do not collapse available_times and not_available_times into a single flat table.

### No redundant columns on parent tables

Do not add flat columns to a parent resource's table for data that belongs to a dedicated child resource. If a field is properly modeled as a child/related resource, access it via join — never duplicate it as a shortcut column.

**Wrong:** adding `role` and `specialty` columns to `PractitionerModel` because "it's convenient" when `PractitionerRoleModel` already owns that data via `codes[]` and `specialties[]`.

**Right:** query role/specialty through `practitioner.roles` → `PractitionerRoleCode` / `PractitionerRoleSpecialty`.

This also applies to filtering: remove `role` as a filter param from `PractitionerRepository.list()` and instead filter via a join to `practitioner_role_code` when needed.

### Sequence allocation

Each new resource picks a start value that does not collide with existing sequences:

| Resource | sequence start |
|---|---|
| Patient | 10000 |
| Encounter | 20000 |
| Practitioner | 30000 |
| Appointment | 40000 |
| QuestionnaireResponse | 60000 |
| Vitals | 70000 |
| ServiceRequest | 80000 |
| MedicationRequest | 90000 |
| Procedure | 100000 |
| DiagnosticReport | 110000 |
| Condition | 120000 |
| DeviceRequest | 130000 |
| PractitionerRole | 140000 |

Pick the next available block of 10000 for any new resource.

---

## Adding a New FHIR Resource — Checklist

When adding a new resource (e.g. `Observation`), follow this order:

1. **Model** — `app/models/observation/observation.py`
   - Internal `id` PK + public `observation_id` via Sequence (pick a new start number)
   - `user_id`, `org_id`, `created_by`, `updated_by`, `created_at`, `updated_at`
   - Sub-resource tables as needed with `cascade="all, delete-orphan"`

2. **Enums** — `app/models/observation/enums.py` (if needed)

3. **Input Schemas** — `app/schemas/observation.py`
   - `ObservationCreateSchema(BaseModel)` — `extra="forbid"`, includes `user_id`, `org_id`, `json_schema_extra` with full example
   - `ObservationPatchSchema(BaseModel)` — patchable fields only
   - `ObservationResponseSchema(BaseModel)` — for non-FHIR resources (like vitals); or use FHIR schemas

4. **FHIR Response Schemas** — `app/schemas/fhir/observation.py`
   - `FHIRObservationSchema`, `PlainObservationResponse`, `PaginatedObservationResponse`, `FHIRObservationBundle`
   - Export from `app/schemas/fhir/__init__.py`

5. **Mappers** — `app/fhir/mappers/observation.py`
   - `to_fhir_observation(model) -> dict`
   - `to_plain_observation(model) -> dict`

6. **Repository** — `app/repository/observation_repository.py`
   - `_with_relationships()`, `_apply_list_filters()`
   - `get_by_observation_id()`, `get_me()`, `list()`, `create()`, `patch()`, `delete()`
   - `get_me()` must reuse `_apply_list_filters()` with `user_id`/`org_id` always set

7. **Service** — `app/services/observation_service.py`
   - `_to_fhir()`, `_to_plain()` wrappers
   - `get_raw_by_observation_id()` — for auth dep
   - `get_me()`, `list_observations()`, `create_observation()`, `patch_observation()`, `delete_observation()`

8. **DI Module** — `app/di/modules/observation.py`
   - `ObservationContainer` with `observation_repository` + `observation_service`

9. **DI Dependency** — `app/di/dependencies/observation.py`
   - `get_observation_service()` with `@inject` + `Provide[Container.observation.observation_service]`

10. **Wire container** — `app/di/container.py`
    - Add `observation = providers.Container(ObservationContainer, core=core)`

11. **Auth dep** — `app/auth/observation_deps.py`
    - `get_authorized_observation()` — loads + checks `user_id` ownership

12. **Router** — `app/routers/observation.py`
    - Module-level `_SINGLE_200`, `_SINGLE_201`, `_LIST_200` constants using `inline_schema()`
    - Routes in order: POST /, GET /me, GET /{id}, PATCH /{id}, GET /, DELETE /{id}
    - All POST → `_SINGLE_201`, all GET single/patch → `_SINGLE_200`, all list → `_LIST_200`
    - Use `require_permission("observation", "create|read|update|delete")` as dependency
    - `status` query param → rename to `obs_status` with `alias="status"` to avoid shadowing `fastapi.status`

13. **Register router** — `app/routers/__init__.py`
    - `api_router.include_router(observation_router, prefix="/observations", tags=["Observations"])`

---

## Common Pitfalls & Rules

- **Never use `response_model=`** on routes — use inline `responses=` with `inline_schema()` instead; avoids double-serialization and `$ref` problems
- **`/me` before `/{id}`** — route declaration order matters in FastAPI; `/me` must come first
- **`status` parameter shadowing** — if a route has a `status` query param, name it `enc_status`/`appt_status`/`qr_status` with `alias="status"` to avoid shadowing `from fastapi import status`
- **Always eager-load relationships** — use `_with_relationships()` on every query that returns a model for serialization; otherwise lazy-load will fail in async context
- **Session-per-operation** — do not hold sessions across multiple operations; each repository method opens its own `async with self.session_factory() as session`
- **`model_dump(exclude_unset=True)`** — use this in PATCH handlers to only apply fields the caller explicitly provided
- **`created_by` / `updated_by`** — always pass from `request.state.user.get("sub")`; never hardcode or skip
- **`user_id` / `org_id` in example** — `json_schema_extra` examples on CreateSchemas must include `user_id` and `org_id` fields at the top
- **`inline_schema()` at module level** — call once at import time, not inside route handlers; prevents repeated computation
- **OpenAPI spec = MCP contract** — every field change must propagate through the full stack (model → repo → mapper → FHIR schema → plain schema → router constants); see "Full-Flow Checklist for Any Field Change" above
- **Verify `/openapi.json` after any schema change** — start the server and confirm the field appears in both request body and response schemas for every affected route before marking the task done
