# CodeableConcept Terminology Service — Implementation Plan

## Problem

FHIR resources use `CodeableConcept` in dozens of fields (Condition.clinicalStatus, Condition.category, Observation.code, Appointment.serviceType, etc.). Each field has its own set of valid codes drawn from one or more standard terminologies (SNOMED-CT, LOINC, ICD-10, HL7 value sets) or custom org-specific codes.

The challenges:

- **Frontend can't hard-code them** — too many, change over time, some are org-specific.
- **Backend needs to know field → value set mapping** — so it can tell callers "here are the valid codes for Condition.clinicalStatus."
- **Multiple sources** — some codes come from FHIR standard bindings, some from external terminologies, some from the organization itself.
- **Dynamic discovery** — a form building a Condition record needs to ask "what are the valid clinical status codes?" without the frontend developer hard-coding them.

---

## Architecture Overview

Three layers:

```
┌─────────────────────────────────────────────────────────────┐
│  1. ValueSet Registry                                        │
│     Maps  resource + field  →  ValueSet(s)                  │
│     e.g.  Condition.clinicalStatus → condition-clinical      │
├─────────────────────────────────────────────────────────────┤
│  2. Concept Store                                            │
│     Stores all codes per ValueSet                            │
│     system + code + display + active + org_id (nullable)    │
├─────────────────────────────────────────────────────────────┤
│  3. Terminology API                                          │
│     GET /terminology/fields?resource=Condition               │
│     GET /terminology/concepts?resource=Condition&field=clinicalStatus │
│     POST /terminology/concepts  (add org-specific codes)     │
└─────────────────────────────────────────────────────────────┘
```

---

## Data Model

### Table: `terminology_value_set`

Describes a named set of valid codes for a specific resource field.

```sql
CREATE TABLE terminology_value_set (
    id          SERIAL PRIMARY KEY,
    name        VARCHAR NOT NULL,          -- e.g. "condition-clinical"
    title       VARCHAR,                   -- human label
    description TEXT,
    resource    VARCHAR NOT NULL,          -- "Condition"
    field       VARCHAR NOT NULL,          -- "clinicalStatus"
    system      VARCHAR,                   -- canonical system URI (nullable if multi-system)
    binding     VARCHAR NOT NULL           -- "required" | "preferred" | "extensible" | "example"
                DEFAULT 'preferred',
    org_id      VARCHAR,                   -- NULL = global (all orgs); set = org-specific override
    active      BOOLEAN NOT NULL DEFAULT TRUE,
    UNIQUE (resource, field, org_id)
);
```

### Table: `terminology_concept`

One row per code within a value set.

```sql
CREATE TABLE terminology_concept (
    id            SERIAL PRIMARY KEY,
    value_set_id  INTEGER REFERENCES terminology_value_set(id) ON DELETE CASCADE,
    system        VARCHAR NOT NULL,       -- e.g. "http://terminology.hl7.org/CodeSystem/condition-clinical"
    code          VARCHAR NOT NULL,       -- e.g. "active"
    display       VARCHAR NOT NULL,       -- e.g. "Active"
    definition    TEXT,                   -- optional human description
    active        BOOLEAN NOT NULL DEFAULT TRUE,
    sort_order    INTEGER DEFAULT 0,
    org_id        VARCHAR,               -- NULL = standard; set = org-specific addition
    UNIQUE (value_set_id, system, code, org_id)
);
```

SQLAlchemy models go in `app/models/terminology/`.

---

## ValueSet ↔ Resource Field Registry

A **static Python dict** (not database) maps every resource+field to its value set name and system URI. This is the authoritative source for "what codes are valid here?" — frontend and backend both derive from it.

Location: `app/fhir/terminology/registry.py`

```python
FIELD_VALUE_SETS: dict[tuple[str, str], dict] = {
    # (Resource, field) → value set info
    ("Condition", "clinicalStatus"): {
        "value_set": "condition-clinical",
        "system": "http://terminology.hl7.org/CodeSystem/condition-clinical",
        "binding": "required",
        "standard_codes": [
            {"code": "active",      "display": "Active"},
            {"code": "recurrence",  "display": "Recurrence"},
            {"code": "relapse",     "display": "Relapse"},
            {"code": "inactive",    "display": "Inactive"},
            {"code": "remission",   "display": "Remission"},
            {"code": "resolved",    "display": "Resolved"},
        ],
    },
    ("Condition", "verificationStatus"): {
        "value_set": "condition-ver-status",
        "system": "http://terminology.hl7.org/CodeSystem/condition-ver-status",
        "binding": "required",
        "standard_codes": [
            {"code": "unconfirmed",       "display": "Unconfirmed"},
            {"code": "provisional",       "display": "Provisional"},
            {"code": "differential",      "display": "Differential"},
            {"code": "confirmed",         "display": "Confirmed"},
            {"code": "refuted",           "display": "Refuted"},
            {"code": "entered-in-error",  "display": "Entered in Error"},
        ],
    },
    ("Condition", "category"): {
        "value_set": "condition-category",
        "system": "http://terminology.hl7.org/CodeSystem/condition-category",
        "binding": "preferred",
        "standard_codes": [
            {"code": "problem-list-item",    "display": "Problem List Item"},
            {"code": "encounter-diagnosis",  "display": "Encounter Diagnosis"},
        ],
    },
    ("Condition", "severity"): {
        "value_set": "condition-severity",
        "system": "http://snomed.info/sct",
        "binding": "preferred",
        "standard_codes": [
            {"code": "255604002", "display": "Mild"},
            {"code": "6736007",   "display": "Moderate"},
            {"code": "24484000",  "display": "Severe"},
        ],
    },
    ("Appointment", "status"): {
        "value_set": "appointmentstatus",
        "system": "http://hl7.org/fhir/appointmentstatus",
        "binding": "required",
        "standard_codes": [
            {"code": "proposed",    "display": "Proposed"},
            {"code": "pending",     "display": "Pending"},
            {"code": "booked",      "display": "Booked"},
            {"code": "arrived",     "display": "Arrived"},
            {"code": "fulfilled",   "display": "Fulfilled"},
            {"code": "cancelled",   "display": "Cancelled"},
            {"code": "noshow",      "display": "No Show"},
            {"code": "entered-in-error", "display": "Entered in Error"},
            {"code": "checked-in",  "display": "Checked In"},
            {"code": "waitlist",    "display": "Waitlist"},
        ],
    },
    # ... add every resource/field combination
}
```

**Why a static dict, not a DB table for this mapping?**
The mapping of field → value set is part of the FHIR spec — it doesn't change without a spec update. Only the *concepts* within a value set can be extended (org-specific codes). The registry dict is version-controlled alongside the code.

---

## Seeding Strategy

On startup (or via a seed CLI command), read `FIELD_VALUE_SETS` and populate `terminology_value_set` and `terminology_concept` tables if they don't exist.

```python
# app/fhir/terminology/seeder.py

async def seed_standard_concepts(session: AsyncSession) -> None:
    for (resource, field), info in FIELD_VALUE_SETS.items():
        vs = await get_or_create_value_set(session, resource, field, info)
        for c in info["standard_codes"]:
            await get_or_create_concept(session, vs.id, info["system"], c["code"], c["display"])
```

Call this from `app/main.py` startup event (idempotent — uses `INSERT ... ON CONFLICT DO NOTHING`).

This means:
- Standard codes are always present after first boot.
- Re-seeding never overwrites customized display names or org-specific codes.
- Adding a new resource just means adding entries to `FIELD_VALUE_SETS`.

---

## API Endpoints

Mount at `/terminology`. All routes are read-accessible without special permissions; write routes require `require_permission("terminology", "create")`.

### List fields for a resource

```
GET /terminology/fields?resource=Condition
```

Response:
```json
[
  {
    "resource": "Condition",
    "field": "clinicalStatus",
    "value_set": "condition-clinical",
    "system": "http://terminology.hl7.org/CodeSystem/condition-clinical",
    "binding": "required"
  },
  {
    "resource": "Condition",
    "field": "verificationStatus",
    ...
  }
]
```

Frontend uses this to discover which fields have controlled vocabularies before building a form.

---

### Get concepts for a specific field

```
GET /terminology/concepts?resource=Condition&field=clinicalStatus
GET /terminology/concepts?resource=Condition&field=clinicalStatus&org_id=org-abc
```

Response:
```json
{
  "resource": "Condition",
  "field": "clinicalStatus",
  "binding": "required",
  "system": "http://terminology.hl7.org/CodeSystem/condition-clinical",
  "concepts": [
    { "system": "...", "code": "active",     "display": "Active",     "active": true },
    { "system": "...", "code": "recurrence", "display": "Recurrence", "active": true },
    ...
  ]
}
```

When `org_id` is supplied, the response merges standard codes + org-specific additions. This is the primary endpoint the frontend calls to populate dropdowns.

---

### Look up a single concept

```
GET /terminology/concepts/lookup?system=http://snomed.info/sct&code=44054006
```

Response:
```json
{ "system": "http://snomed.info/sct", "code": "44054006", "display": "Diabetes mellitus type 2" }
```

Useful for resolving a code stored in a resource back to a human-readable display.

---

### Batch lookup (for hydrating a response)

```
POST /terminology/concepts/lookup-batch
Body: [
  { "system": "http://snomed.info/sct", "code": "44054006" },
  { "system": "http://terminology.hl7.org/CodeSystem/condition-clinical", "code": "active" }
]
```

Response: same items with `display` filled in.

---

### Add org-specific concept

```
POST /terminology/concepts
Authorization: Bearer <token>  (requires terminology:create)
{
  "resource": "Condition",
  "field": "clinicalStatus",
  "system": "http://terminology.hl7.org/CodeSystem/condition-clinical",
  "code": "managed",
  "display": "Managed",
  "definition": "Condition is actively managed but not fully resolved."
}
```

This inserts a row with `org_id` from the JWT, allowing organizations to extend standard value sets with domain-specific codes. The concept appears in the GET response when that org's `org_id` is in scope.

---

### List all value sets (admin discovery)

```
GET /terminology/value-sets
```

Returns every registered resource+field combination with code counts. Used by admin UIs or API consumers to discover the full vocabulary surface.

---

## Frontend Consumption Pattern

```
App boot
  └─ GET /terminology/fields?resource=Condition    → cache in store
  └─ GET /terminology/fields?resource=Appointment  → cache in store

Form: "New Condition"
  └─ Read from cache: fields for Condition
  └─ For each field with a value_set:
       GET /terminology/concepts?resource=Condition&field=clinicalStatus&org_id=<activeOrgId>
       → populate dropdown
  └─ Cache responses in localStorage (TTL: 1 hour) to avoid re-fetching
  └─ On submit: send code + system + display in the request body
```

The frontend should:
1. Always send `system`, `code`, and `display` — never just the code.
2. Cache aggressively (terminology changes slowly).
3. Fall back to free-text entry when binding is `"example"` or `"extensible"`.

---

## FHIR R4 Binding Strengths

| Binding | Frontend behavior |
|---|---|
| `required` | Only show standard codes; no free text allowed |
| `preferred` | Show standard codes; allow free text with a warning |
| `extensible` | Show standard codes; allow any code from any system |
| `example` | Standard codes are suggestions only; always allow free text |

The `binding` field is included in every GET response so the frontend can enforce the right behavior without hard-coding it.

---

## Codebase Layout

```
app/
├── models/terminology/
│   ├── __init__.py
│   ├── terminology.py          # TerminologyValueSet, TerminologyConcept ORM models
│   └── enums.py                # BindingStrength enum
├── fhir/terminology/
│   ├── registry.py             # FIELD_VALUE_SETS static dict
│   └── seeder.py               # seed_standard_concepts()
├── schemas/terminology/
│   ├── __init__.py
│   ├── input.py                # ConceptCreateSchema
│   └── response.py             # ConceptResponse, FieldResponse, etc.
├── repository/
│   └── terminology_repository.py
├── services/
│   └── terminology_service.py
├── routers/
│   └── terminology.py          # all endpoints above
└── di/modules/
    └── terminology.py          # TerminologyContainer
```

---

## Migration Plan

1. Add `terminology_value_set` and `terminology_concept` tables (new migration).
2. Add `seeder.py` with all current FHIR field bindings from this project's resources.
3. Call seeder in `app/main.py` on `startup` event.
4. Build repository + service + router.
5. Wire into DI container.
6. Register `/terminology` prefix in `app/routers/__init__.py`.
7. Add FHIR standard codes for every resource already in this project.

---

## External Terminologies (Future)

For large code systems (SNOMED-CT = 350k+ codes, LOINC = 95k+ codes), don't seed everything into Postgres. Instead:

- Seed only the **subset actually used** by this organization's workflows.
- Provide a `POST /terminology/concepts/import` endpoint to bulk-import from a FHIR ValueSet JSON file (R4 ValueSet resource format).
- Optionally integrate a dedicated terminology server (e.g., Ontoserver, HAPI FHIR Terminology Server) as a remote backend — the `/terminology/concepts` endpoint proxies to it and caches results in Redis.

For this project's current scale, seeding curated subsets into Postgres (as shown above) is the right approach.

---

## Summary

| Decision | Choice |
|---|---|
| Field → ValueSet mapping | Static Python dict (version-controlled) |
| Concept storage | Postgres `terminology_concept` table |
| Org-specific codes | Same table, `org_id` column discriminates |
| Standard code seeding | Startup seeder (idempotent) |
| Caching | Redis (server), localStorage (frontend) |
| API surface | `/terminology/fields`, `/terminology/concepts`, `/terminology/value-sets` |
| External systems (future) | Bulk import from FHIR ValueSet JSON |
