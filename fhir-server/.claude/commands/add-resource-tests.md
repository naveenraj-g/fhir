# Add Integration Tests for a FHIR Resource

Checklist for the pytest integration suite of one FHIR R4 resource.

Stack: **pytest-asyncio** (`asyncio_mode = "auto"`), **httpx AsyncClient**, **SQLite in-memory** (`StaticPool`). `tests/conftest.py` provides the `client` fixture (and `other_client`), builds every table except `terminology*`, and simulates Postgres sequences. **Auth was removed** from the server: there are no permission overrides, no `/me` routes, no `make_test_user` usage — don't add any.

## ARGUMENTS: $RESOURCE

---

## Before starting — read these (assert runtime behaviour, not route descriptions)

- `app/routers/<resource>.py` — paths, query params and aliases
- `app/fhir/mappers/<resource>/plain.py` and `fhir.py` — exact output field names
- `app/schemas/<resource>/input.py` — required fields, enums (FHIR hyphenated values), validators
- `app/repository/<resource>_repository.py` — search params, ordering, replace-semantics patch

## Layout

`tests/integration/<resource>/__init__.py` (empty) + `test_core.py`. No `conftest.py` is needed (only add one for genuinely resource-specific fixtures). Large resources may split extra files (`test_nested_fields.py`) — keep each file scannable.

## Helpers at the top of `test_core.py`

```python
BASE = "/api/fhir/v1/<resources>"
FHIR_ACCEPT = {"Accept": "application/fhir+json"}

def _with_org(query: str) -> str:
    """Every search requires org_id — add the default test org unless the query sets one."""
    if "org_id=" in query:
        return query
    return f"org_id=org-test&{query}" if query else "org_id=org-test"

MINIMAL = {"user_id": "u-test", "org_id": "org-test", "status": "..."}   # smallest valid body
def full_payload(**overrides) -> dict: ...                                # exercises every branch

async def _create(client, payload=None): ...   # asserts 200, returns json
async def _ids(client, query): ...             # GET list with org, returns the set of ids
```

## What to cover

1. **CRUD** — minimal create, full create (plain), full create read back as FHIR (`resourceType`, camelCase keys, `id` is a string), get + 404, delete (204) + get 404 (cascade).
2. **Validation** — required fields (400/422), extra field forbidden, enum values, every R4 invariant / choice-type exclusivity, bad reference type, bad reference format, **reference existence is NOT checked** (a non-existent id is accepted), ordering rules (period end before start).
3. **PATCH** — scalars; `status` not-null; clearing a reference with null; nested-datatype replace/clear; choice-type swap clears the other variants; **every child list** replaced / cleared with `[]` / left untouched when omitted; kinds that share a table (contact/author/...) independent; cross-part integrity (e.g. PlanDefinition goal vs action ids) → 422; 404 on unknown id.
4. **Search** — `org_id` required (422/400 without it), org isolation, `user_id` filter, `_id`, `_lastUpdated`, every implemented R4 param (token `system|code` forms, string default/`:contains`/`:exact`, reference `Type/id` and bare id, date prefixes incl. period matching — note `eq` on a period means *contained in*, use `ap`/`ge`/`le` for overlap), invalid enum token → 4xx, pagination (`total/limit/offset/data`), FHIR Bundle (`resourceType`, `total`, `entry`), default order (newest date first, nulls last).
5. **Content negotiation** — default is plain JSON; `application/fhir+json` gives the FHIR form for single and list.

## Runtime facts to assert (current behaviour)

- Create returns **200** (not 201); schema-level request validation errors return **400** with an `OperationOutcome` (repository/service-raised reference errors return **422**) — use `in (400, 422)` unless you verified which path fires.
- The plain `id` is the public `<resource>_id` (int); the FHIR `id` is its string form.
- Enum inputs use the FHIR code (`depends-on`, `original-order`); DB labels are member names — don't assert on DB labels.
- Create a fresh tenant for isolation/pagination tests (`org_id=org-page` etc.) so other tests' rows don't interfere.

## Run

```bash
uv run pytest tests/integration/<resource> -q -p no:cacheprovider
```

Run the neighbouring suites too when you touched shared code (`app/core/search_params.py`, `app/models/plan_definition/columns.py`, the codec). The whole suite (~1000 tests) takes ~20 minutes — run it in the background.

| Symptom | Fix |
|---|---|
| `ModuleNotFoundError: app.auth` | leftover permission override from an old test — delete it (auth no longer exists) |
| `assert 200 == 201` on POST | create returns 200 |
| `assert 422 == 400` | schema-level validation is 400 |
| `NotImplementedError ... sequence` on SQLite | importing the model before `tests/conftest.py` patches sequences; use the `client` fixture |
| search returns nothing for a period | wrong prefix — `eq` requires the whole period inside the search range |
| `Unknown ... column` after model change | the test DB is rebuilt from `Base.metadata` each run; check the model import is registered |

## Principles

- Endpoint-complete coverage plus focused tests for all custom logic; not every nullable permutation.
- Assert `OperationOutcome` shape for error cases where it matters, not just the status code.
- Comment the intent of non-obvious tests.
