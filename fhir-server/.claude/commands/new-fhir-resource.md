# Add a New FHIR Resource

Complete checklist for adding a FHIR R4 resource end to end: **fhir-server** first, then the REST gateway in **fhir-gql** (never touch `fhir-gql/app/gql`).

**Before starting:** fetch the R4 spec (`https://www.hl7.org/fhir/R4/<resource>.html`, never the unversioned URL) and run `/fhir-db-model` to design the model, enums and migration.

## ARGUMENTS: $RESOURCE

Steps use `$RESOURCE` = the resource name (e.g. `Observation`, `Claim`). Adjust paths accordingly.

## Standing rules (apply to every resource — do not re-ask)

- **Spec-faithful:** every element, cardinality (1..1 → required), binding and invariant of the R4 page; add any missing field/column with a migration.
- **Search:** implement the resource's R4 search parameters (helpers in `app/core/search_params.py`). `org_id` is **mandatory** on every list/search (blank rejected), `user_id` optional. Parameters you cannot support (composite / quantity ones) are simply left out of the code AND the route descriptions — don't document them.
- **PATCH:** scalar fields AND child lists. A child list that is sent REPLACES the stored list; `[]`/null clears it; omitted = untouched. References are `Type/id` strings; null clears an optional one. When a choice type `foo[x]` variant is set, clear the other variants.
- **References to other resources:** plain `<field>_type` / `<field>_id` / `<field>_display` columns holding the PUBLIC id. No `ForeignKey`, no `relationship`, no existence lookup — only format + allowed type are validated (422). FKs exist only child → its own parent.
- **No `/me` route, no sub-resource GET/DELETE endpoints, no auth/permission dependencies on the server** (auth was removed there). Tenant fields `user_id` / `org_id` come from the request body on create.
- **Do not commit** unless asked.

---

## Server checklist (`fhir-server`)

1. **Enums** — `app/models/<resource>/enums.py`. `str, Enum`; member name = what the DB stores, value = the FHIR code (hyphenated codes use underscored member names). Re-use classes from another resource when the binding is identical, but give the PG type a resource-specific name.
2. **Model** — `app/models/<resource>/<resource>.py`
   - `Sequence("<resource>_pub_seq", start=<next block from CLAUDE.md>)`, internal `id` PK + public `<resource>_id`
   - Standard columns: `user_id`, `org_id`, `created_at`, `updated_at`, `created_by`, `updated_by`
   - 0..1 flat columns, 0..* child tables (`cascade="all, delete-orphan"` on the parent); grandchildren use their own parent FK
   - Deeply nested or recursive data (trees, big datatypes): store flat — see `app/models/plan_definition/` (`columns.py` factories + `app/fhir/mappers/plan_definition/codec.py` pack/unpack for Quantity/Range/Ratio/Period/Expression/Attachment/Timing) and `app/models/activity_definition/` (Dosage)
   - `__init__.py` exports everything; add `import app.models.<resource>.<resource>  # noqa: F401` to `migrations/env.py`; verify `configure_mappers()` succeeds
3. **Migration** — `uv run alembic revision --autogenerate -m "add <resource>"`, then clean it:
   - strip the unrelated drift autogenerate adds (`CREATE/DROP SEQUENCE` for every OTHER resource, the `questionnaire_response_item` foreign key); keep only this resource's `CREATE/DROP SEQUENCE`
   - replace every `sa.Enum(...)` with `postgresql.ENUM(..., name=..., create_type=False)`, create each distinct enum once at the start of `upgrade()` (`.create(op.get_bind(), checkfirst=True)`) and drop them at the end of `downgrade()`; shared types (`organization_reference_type`, `encounter_reference_type`, …) are never created/dropped
   - apply and prove it: `uv run alembic upgrade head && uv run alembic downgrade -1 && uv run alembic upgrade head`
   - use `python scripts/clean_migration.py <migration.py> <resource>_pub_seq [shared_enum,...]` — it does all of this mechanically (list shared PG enums such as `subject_reference_type,encounter_reference_type,organization_reference_type` as the 3rd argument)
4. **Input schemas** — `app/schemas/<resource>/input.py`: `CreateSchema` (`extra="forbid"`, example with `user_id`/`org_id`, R4 invariants as validators, choice types "at most one"), `PatchSchema` (all optional, `status` not-null, child lists replace-semantics, same validators). Nested datatypes may reuse `app/schemas/plan_definition/input.py` (`Pd*` inputs).
5. **Response schemas** — `app/schemas/<resource>/response.py`: `FHIR<Resource>Schema` (+ `BundleEntry`, `Bundle(FHIRBundle)`), `Plain<Resource>Response`, `Paginated<Resource>Response`; every DB field must appear. `__init__.py` re-exports.
6. **Mappers** — `app/fhir/mappers/<resource>/` package: `fhir.py`, `plain.py`, `__init__.py`. Shared helpers from `app/fhir/datatypes.py`. Plain output includes child-row `id`s; FHIR strips None/empty containers.
7. **Repository** — `app/repository/<resource>_repository.py`
   - `<Resource>Search` dataclass; `_with_relationships()` eager-loads every collection (selectinload chains for grandchildren)
   - `_apply_list_filters()` implements the R4 search params; default order `date/created desc nulls last, id desc`
   - `create()` via a shared `_add_children()`; `patch()` = scalars (`exclude_unset`) + `CHILD_FIELDS` replace (`collection.clear()` or selective remove, `flush`, re-add); parse references format-only; integrity checks that span replaced/non-replaced parts → 422
   - session-per-operation, count + rows in one session
8. **Service** — `app/services/<resource>_service.py` (`_to_fhir`/`_to_plain`, `get_raw_by_…`, `list_…`, `create_…`, `patch_…`, `delete_…`)
9. **Deps** — `app/deps/<resource>_deps.py`: `resolve_<resource>()` loads by public id, 404 if missing
10. **DI** — `app/di/modules/<resource>.py`, `app/di/dependencies/<resource>.py`, register in `app/di/modules/__init__.py` and `app/di/container.py`
11. **Router** — `app/routers/<resource>.py`: `POST /`, `GET /{id}`, `PATCH /{id}`, `GET /`, `DELETE /{id}`. `operation_id`/`summary`/`description`/`responses=` on every route (MCP reads them); inline `responses=` with `inline_schema()` for BOTH content types, never `response_model=`; `org_id: str = Query(..., min_length=1)`; `status` query param renamed with `alias="status"`; `:contains`/`:exact` and hyphenated params via `alias=`. DELETE returns `None` with `status_code=204` (never `JSONResponse(content=None)`).
12. **Register** — `app/routers/__init__.py` (prefix `/<resources>`, tag), `app/core/openapi_tags.py`, and the sequence table in `CLAUDE.md` (+ bump "Next available block").
13. **Tests** — see `/add-resource-tests`; run them and the neighbouring suites.
14. **Verify** — `from app.main import app; app.openapi()` shows the paths; check request/response schemas contain every field.

## Gateway checklist (`fhir-gql`, REST only)

Mirror an existing resource (e.g. `plan_definition` / `activity_definition` / `flag`) and keep the detailed docstrings/comments:

1. `app/schemas/enums.py` — add the enums the input schemas import.
2. `app/schemas/<resource>/{input,response,__init__}.py` — input = server input with the enum import swapped to `app.schemas.enums`, plus `List<Resource>sSchema` (`org_id` required `min_length=1`, `user_id` optional, status-token validator); response = server response with a local Bundle model.
3. `app/fhir_client/<resource>.py` — path `/<resources>`, `list(**params)` strips None/empty lists.
4. `app/services/<resource>_service.py` — `model_dump(exclude_none=True, mode="json")`, empty-patch 422, maps python names to FHIR param names (`_id`, `_lastUpdated`, `name:contains`, `context-type`, …).
5. `app/di/modules/<resource>.py`, `app/di/dependencies/<resource>.py`, register in `app/di/modules/__init__.py` and `app/di/container.py`.
6. `app/routers/<resource>.py` — explicit `Query(alias=…)` params → `List…Schema` (`ValidationError` → 422), `require_permission("<resource_snake>", …)`, both content types in `responses=`; register in `app/routers/__init__.py`.
7. **Live e2e:** start the server (`uv run uvicorn app.main:app --port 8001` from fhir-server), drive the gateway app through `httpx.ASGITransport` with `get_current_user` overridden to set `request.state.user = {"sub", "activeOrganizationId", "permissions": [...]}` — create, get (both formats), search (+422 cases), patch, delete, 404. Stop the server afterwards.

## Tooling notes

- Bash heredocs containing quotes can fail to parse in this environment — write files with the Write tool and keep Bash for simple commands.
- Run only the suites you touched while iterating (`uv run pytest tests/integration/<resource> -q -p no:cacheprovider`); the full suite takes ~20 minutes.
