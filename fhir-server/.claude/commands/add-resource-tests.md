# Add Integration Tests for a FHIR Resource

Complete checklist for adding pytest integration tests for any FHIR R4 resource in this server.

The test stack uses **pytest-asyncio** with `asyncio_mode = "auto"`, **httpx AsyncClient**, and **SQLite in-memory** (StaticPool). The shared `tests/conftest.py` handles all infrastructure — you only write the test module.

---

## ARGUMENTS: $RESOURCE

Steps use `$RESOURCE` = the resource name (e.g. `Patient`, `Claim`). Adjust snake_case paths accordingly (e.g. `claim_response` → `ClaimResponse`).

---

## Before Starting

Read these files first — they determine what your tests assert:

- `app/routers/<resource>.py` — route paths, HTTP methods, status codes, query param names
- `app/fhir/mappers/<resource>/plain.py` — exact field names in the plain JSON response (FHIR singular names like `"name"`, `"identifier"`, not `"names"`)
- `app/schemas/<resource>/input.py` — required vs optional fields in create/patch payloads
- `app/auth/<resource>_deps.py` — whether `get_authorized_<resource>` checks `user_id` ownership

---

## Step 1 — Add permissions to `make_test_user` call

In `tests/integration/test_<resource>.py`, use:

```python
from tests.conftest import make_test_user
from app.auth.dependencies import get_current_user
```

The `client` fixture in `conftest.py` already provides a user with `patient:*` permissions. For other resources, override `get_current_user` inside your test module's fixture **or** pass `permissions=` to `make_test_user()`.

---

## Step 2 — Create `tests/integration/test_<resource>.py`

```
tests/integration/test_<resource>.py
```

### Required sections

```python
"""Integration tests for /api/fhir/v1/<resources> endpoints."""
import pytest

from tests.helpers.assertions import (
    assert_fhir_bundle,
    assert_plain_<resource>,   # add to assertions.py if not already present
    assert_operation_outcome,
    assert_paginated,
)

BASE = "/api/fhir/v1/<resources>"
FHIR_ACCEPT = {"Accept": "application/fhir+json"}
```

### Fixture — permissions

If the resource is not `patient`, add a module-level fixture that overrides auth permissions for this test module:

```python
from tests.conftest import make_test_user
from app.auth.dependencies import get_current_user
from app.main import app

@pytest.fixture(autouse=True)
def _set_permissions(client):
    app.dependency_overrides[get_current_user] = make_test_user(
        permissions=[
            "<resource>:create",
            "<resource>:read",
            "<resource>:update",
            "<resource>:delete",
        ]
    )
    yield
    app.dependency_overrides[get_current_user] = make_test_user()
```

### Payloads

```python
MINIMAL = {
    "user_id": "u-test",
    "org_id": "org-test",
    # ... minimum required fields ...
}

FULL = {
    "user_id": "u-test",
    "org_id": "org-test",
    # ... all optional fields ...
}
```

---

## Step 3 — Test cases to cover

Write one `async def test_*` function per behaviour. Name tests descriptively.

### Create

```python
async def test_create_<resource>_minimal(client):
    resp = await client.post(BASE + "/", json=MINIMAL)
    assert resp.status_code == 200  # format_response() always returns 200
    data = resp.json()
    assert_plain_<resource>(data, ...)  # key scalar fields

async def test_create_<resource>_full(client):
    resp = await client.post(BASE + "/", json=FULL)
    assert resp.status_code == 200
    ...

async def test_create_<resource>_fhir_format(client):
    resp = await client.post(BASE + "/", json=MINIMAL, headers=FHIR_ACCEPT)
    assert resp.status_code == 200
    assert resp.json()["resourceType"] == "<Resource>"

async def test_create_<resource>_extra_field_rejected(client):
    resp = await client.post(BASE + "/", json={**MINIMAL, "bad": "field"})
    assert resp.status_code == 400  # RequestValidationError → 400 OperationOutcome
```

### Get by ID

```python
async def test_get_<resource>_by_id_plain(client):
    r_id = (await client.post(BASE + "/", json=MINIMAL)).json()["id"]
    resp = await client.get(f"{BASE}/{r_id}")
    assert resp.status_code == 200
    data = resp.json()
    assert data["id"] == r_id

async def test_get_<resource>_by_id_fhir(client):
    r_id = (await client.post(BASE + "/", json=MINIMAL)).json()["id"]
    resp = await client.get(f"{BASE}/{r_id}", headers=FHIR_ACCEPT)
    assert resp.status_code == 200
    assert resp.json()["resourceType"] == "<Resource>"
    assert resp.json()["id"] == str(r_id)

async def test_get_<resource>_not_found(client):
    resp = await client.get(f"{BASE}/999999")
    assert resp.status_code == 404
```

### Patch

```python
async def test_patch_<resource>(client):
    r_id = (await client.post(BASE + "/", json=MINIMAL)).json()["id"]
    resp = await client.patch(f"{BASE}/{r_id}", json={"<field>": "<new_value>"})
    assert resp.status_code == 200
    assert resp.json()["<field>"] == "<new_value>"

async def test_patch_<resource>_not_found(client):
    resp = await client.patch(f"{BASE}/999999", json={"<field>": "x"})
    assert resp.status_code == 404
```

### Delete

```python
async def test_delete_<resource>(client):
    r_id = (await client.post(BASE + "/", json=MINIMAL)).json()["id"]
    assert (await client.delete(f"{BASE}/{r_id}")).status_code == 204
    assert (await client.get(f"{BASE}/{r_id}")).status_code == 404

async def test_delete_<resource>_not_found(client):
    assert (await client.delete(f"{BASE}/999999")).status_code == 404
```

### List

```python
async def test_list_<resource>s_plain(client):
    await client.post(BASE + "/", json=MINIMAL)
    resp = await client.get(BASE + "/")
    assert resp.status_code == 200
    assert_paginated(resp.json(), min_total=1)

async def test_list_<resource>s_fhir_bundle(client):
    await client.post(BASE + "/", json=MINIMAL)
    resp = await client.get(BASE + "/", headers=FHIR_ACCEPT)
    assert resp.status_code == 200
    assert_fhir_bundle(resp.json(), min_total=1)

async def test_list_<resource>s_pagination(client):
    for _ in range(3):
        await client.post(BASE + "/", json=MINIMAL)
    resp = await client.get(BASE + "/?limit=2&offset=0")
    data = resp.json()
    assert data["limit"] == 2
    assert len(data["data"]) == 2
    assert data["total"] >= 3

async def test_list_<resource>s_empty(client):
    resp = await client.get(BASE + "/")
    data = resp.json()
    assert data["total"] == 0
    assert data["data"] == []
```

### /me (if the resource has a /me endpoint)

```python
async def test_get_my_<resource>s_found(client):
    await client.post(BASE + "/", json=MINIMAL)  # MINIMAL must have user_id/org_id matching fixture
    resp = await client.get(BASE + "/me")
    assert resp.status_code == 200
    assert_paginated(resp.json(), min_total=1)

async def test_get_my_<resource>s_org_isolation(client, other_client):
    await client.post(BASE + "/", json=MINIMAL)  # created as u-test / org-test
    resp = await other_client.get(BASE + "/me")  # u-other / org-other
    assert resp.json()["total"] == 0
```

### Permissions

```python
async def test_create_<resource>_no_permission(client):
    from app.main import app as _app
    _app.dependency_overrides[get_current_user] = make_test_user(permissions=["<resource>:read"])
    try:
        resp = await client.post(BASE + "/", json=MINIMAL)
        assert resp.status_code == 403
    finally:
        _app.dependency_overrides[get_current_user] = make_test_user(
            permissions=["<resource>:create", "<resource>:read", "<resource>:update", "<resource>:delete"]
        )
```

### Sub-resource endpoints (for each `POST /{id}/<sub>` route)

```python
async def test_add_and_list_<sub>(client):
    r_id = (await client.post(BASE + "/", json=MINIMAL)).json()["id"]
    payload = { ... }
    assert (await client.post(f"{BASE}/{r_id}/<subs>", json=payload)).status_code == 200

    list_resp = await client.get(f"{BASE}/{r_id}/<subs>")
    assert list_resp.status_code == 200
    data = list_resp.json()
    assert data["total"] == 1
    assert "id" in data["data"][0]

async def test_delete_<sub>(client):
    r_id = (await client.post(BASE + "/", json=MINIMAL)).json()["id"]
    await client.post(f"{BASE}/{r_id}/<subs>", json={ ... })
    sub_id = (await client.get(f"{BASE}/{r_id}/<subs>")).json()["data"][0]["id"]
    assert (await client.delete(f"{BASE}/{r_id}/<subs>/{sub_id}")).status_code == 204
    assert (await client.get(f"{BASE}/{r_id}/<subs>")).json()["total"] == 0
```

---

## Step 4 — Update `tests/helpers/assertions.py`

Add resource-specific helpers if the generic ones are insufficient:

```python
def assert_plain_<resource>(data: dict, **expected) -> None:
    assert data.get("id") is not None
    for field, value in expected.items():
        assert data.get(field) == value, f"expected {field}={value!r}, got {data.get(field)!r}"

def assert_fhir_<resource>(data: dict, **expected) -> None:
    assert data.get("resourceType") == "<Resource>"
    assert data.get("id") is not None
    for field, value in expected.items():
        assert data.get(field) == value
```

---

## Step 5 — Run and verify

```bash
uv run pytest tests/integration/test_<resource>.py -v
```

All tests should pass. Common issues and fixes:

| Symptom | Fix |
|---|---|
| `NotImplementedError: Dialect 'sqlite' does not support sequence increments` | `_strip_server_defaults()` not stripping — check `type(sd.arg).__name__ == "next_value"` |
| `429 Too Many Requests` in later tests | `RateLimitMiddleware.dispatch` not patched — check conftest.py |
| `assert 200 == 201` on POST create | `format_response()` always returns 200; change assertion to 200 |
| `assert 422 == 400` on validation error | Error handler maps validation to 400 OperationOutcome; use 400 |
| `assert 0 >= 1` on sub-resource list | Wrong field name — use FHIR singular (`"name"` not `"names"`) |
| `404` on `/me` even after create | `user_id` in payload doesn't match JWT `sub` in fixture (`"u-test"`) |

---

## Key invariants (do not forget)

- `format_response()` always returns HTTP **200** — even for POST create (`status_code=201` on the decorator is only for OpenAPI docs)
- Validation errors return HTTP **400** (OperationOutcome), not 422
- Plain response field names are **FHIR R4 singular**: `"name"`, `"identifier"`, `"telecom"`, `"address"` — never `"names"` etc.
- Sub-resource responses are `{"data": [...], "total": N}` — each item includes `"id"` for DELETE
- `MINIMAL` payload must include `"user_id": "u-test"` and `"org_id": "org-test"` for `/me` tests to work
- `other_client` fixture shares the **same database** as `client` (same `_engine`) — use it for org isolation
