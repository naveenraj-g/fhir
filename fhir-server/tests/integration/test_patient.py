"""Integration tests for the /api/fhir/v1/patients endpoints."""
import pytest

from tests.helpers.assertions import (
    assert_fhir_bundle,
    assert_fhir_patient,
    assert_operation_outcome,
    assert_paginated,
    assert_plain_patient,
)

BASE = "/api/fhir/v1/patients"
FHIR_ACCEPT = {"Accept": "application/fhir+json"}

# ── Minimal payload used across tests ─────────────────────────────────────────

MINIMAL = {
    "user_id": "u-test",
    "org_id": "org-test",
    "active": True,
    "gender": "male",
}

FULL = {
    "user_id": "u-test",
    "org_id": "org-test",
    "active": True,
    "gender": "female",
    "birth_date": "1990-06-15",
    "deceased_boolean": False,
    "marital_status_system": "http://terminology.hl7.org/CodeSystem/v3-MaritalStatus",
    "marital_status_code": "M",
    "marital_status_display": "Married",
    "marital_status_text": "Married",
    "multiple_birth_boolean": False,
    "managing_organization": "Organization/190001",
    "managing_organization_display": "General Hospital",
}


# ── Create ─────────────────────────────────────────────────────────────────────


async def test_create_patient_minimal(client):
    resp = await client.post(BASE + "/", json=MINIMAL)
    assert resp.status_code == 200
    data = resp.json()
    assert_plain_patient(data, gender="male", active=True)


async def test_create_patient_full(client):
    resp = await client.post(BASE + "/", json=FULL)
    assert resp.status_code == 200
    data = resp.json()
    assert_plain_patient(
        data,
        gender="female",
        birth_date="1990-06-15",
        marital_status_code="M",
        active=True,
    )


async def test_create_patient_returns_fhir_format(client):
    resp = await client.post(BASE + "/", json=MINIMAL, headers=FHIR_ACCEPT)
    assert resp.status_code == 200
    data = resp.json()
    assert_fhir_patient(data, gender="male")
    assert data.get("active") is True


async def test_create_patient_extra_field_rejected(client):
    payload = {**MINIMAL, "nonexistent_field": "value"}
    resp = await client.post(BASE + "/", json=payload)
    # Validation errors are mapped to 400 OperationOutcome by the error handler
    assert resp.status_code == 400


# ── Get by ID ──────────────────────────────────────────────────────────────────


async def test_get_patient_by_id_plain(client):
    create_resp = await client.post(BASE + "/", json=MINIMAL)
    patient_id = create_resp.json()["id"]

    resp = await client.get(f"{BASE}/{patient_id}")
    assert resp.status_code == 200
    data = resp.json()
    assert_plain_patient(data, gender="male")
    assert data["id"] == patient_id


async def test_get_patient_by_id_fhir(client):
    create_resp = await client.post(BASE + "/", json=MINIMAL)
    patient_id = create_resp.json()["id"]

    resp = await client.get(f"{BASE}/{patient_id}", headers=FHIR_ACCEPT)
    assert resp.status_code == 200
    data = resp.json()
    assert_fhir_patient(data)
    assert data["id"] == str(patient_id)


async def test_get_patient_not_found(client):
    resp = await client.get(f"{BASE}/999999")
    assert resp.status_code == 404


# ── Patch ──────────────────────────────────────────────────────────────────────


async def test_patch_patient_gender(client):
    create_resp = await client.post(BASE + "/", json=MINIMAL)
    patient_id = create_resp.json()["id"]

    resp = await client.patch(f"{BASE}/{patient_id}", json={"gender": "female"})
    assert resp.status_code == 200
    assert resp.json()["gender"] == "female"


async def test_patch_patient_birth_date(client):
    create_resp = await client.post(BASE + "/", json=MINIMAL)
    patient_id = create_resp.json()["id"]

    resp = await client.patch(f"{BASE}/{patient_id}", json={"birth_date": "1985-03-20"})
    assert resp.status_code == 200
    assert resp.json()["birth_date"] == "1985-03-20"


async def test_patch_patient_active_false(client):
    create_resp = await client.post(BASE + "/", json=MINIMAL)
    patient_id = create_resp.json()["id"]

    resp = await client.patch(f"{BASE}/{patient_id}", json={"active": False})
    assert resp.status_code == 200
    assert resp.json()["active"] is False


async def test_patch_patient_not_found(client):
    resp = await client.patch(f"{BASE}/999999", json={"gender": "female"})
    assert resp.status_code == 404


# ── Delete ─────────────────────────────────────────────────────────────────────


async def test_delete_patient(client):
    create_resp = await client.post(BASE + "/", json=MINIMAL)
    patient_id = create_resp.json()["id"]

    resp = await client.delete(f"{BASE}/{patient_id}")
    assert resp.status_code == 204

    get_resp = await client.get(f"{BASE}/{patient_id}")
    assert get_resp.status_code == 404


async def test_delete_patient_not_found(client):
    resp = await client.delete(f"{BASE}/999999")
    assert resp.status_code == 404


# ── List ───────────────────────────────────────────────────────────────────────


async def test_list_patients_plain(client):
    await client.post(BASE + "/", json=MINIMAL)
    await client.post(BASE + "/", json={**FULL})

    resp = await client.get(BASE + "/")
    assert resp.status_code == 200
    data = resp.json()
    assert_paginated(data, min_total=2)


async def test_list_patients_fhir_bundle(client):
    await client.post(BASE + "/", json=MINIMAL)

    resp = await client.get(BASE + "/", headers=FHIR_ACCEPT)
    assert resp.status_code == 200
    data = resp.json()
    assert_fhir_bundle(data, min_total=1)
    assert data["entry"][0]["resource"]["resourceType"] == "Patient"


async def test_list_patients_pagination(client):
    for _ in range(5):
        await client.post(BASE + "/", json=MINIMAL)

    resp = await client.get(BASE + "/?limit=2&offset=0")
    assert resp.status_code == 200
    data = resp.json()
    assert data["limit"] == 2
    assert data["offset"] == 0
    assert len(data["data"]) == 2
    assert data["total"] >= 5


async def test_list_patients_filter_gender(client):
    await client.post(BASE + "/", json={**MINIMAL, "gender": "male"})
    await client.post(BASE + "/", json={**MINIMAL, "gender": "female"})

    resp = await client.get(BASE + "/?gender=female")
    assert resp.status_code == 200
    data = resp.json()
    assert_paginated(data, min_total=1)
    for p in data["data"]:
        assert p["gender"] == "female"


async def test_list_patients_filter_active(client):
    await client.post(BASE + "/", json={**MINIMAL, "active": True})
    await client.post(BASE + "/", json={**MINIMAL, "active": False})

    resp = await client.get(BASE + "/?active=true")
    assert resp.status_code == 200
    data = resp.json()
    for p in data["data"]:
        assert p["active"] is True


async def test_list_patients_empty(client):
    resp = await client.get(BASE + "/")
    assert resp.status_code == 200
    data = resp.json()
    assert data["total"] == 0
    assert data["data"] == []


# ── /me ────────────────────────────────────────────────────────────────────────


async def test_get_my_patient_profile_found(client):
    await client.post(BASE + "/", json=MINIMAL)

    resp = await client.get(BASE + "/me")
    assert resp.status_code == 200
    data = resp.json()
    assert_plain_patient(data, gender="male")


async def test_get_my_patient_profile_not_found(client):
    resp = await client.get(BASE + "/me")
    assert resp.status_code == 404


async def test_get_my_patient_profile_org_isolation(client, other_client):
    # Create patient belonging to u-test / org-test
    await client.post(BASE + "/", json=MINIMAL)

    # u-other / org-other should not see it via /me
    resp = await other_client.get(BASE + "/me")
    assert resp.status_code == 404


# ── Permissions ────────────────────────────────────────────────────────────────


async def test_create_patient_no_permission(client):
    """POST without patient:create permission → 403."""
    from app.auth.dependencies import get_current_user as _gcu
    from tests.conftest import make_test_user

    app = client._transport.app  # the ASGI app bound to this client
    app.dependency_overrides[_gcu] = make_test_user(permissions=["patient:read"])
    try:
        resp = await client.post(BASE + "/", json=MINIMAL)
        assert resp.status_code == 403
    finally:
        app.dependency_overrides[_gcu] = make_test_user()


# ── Sub-resource: Names ────────────────────────────────────────────────────────


async def test_add_and_list_patient_name(client):
    create_resp = await client.post(BASE + "/", json=MINIMAL)
    patient_id = create_resp.json()["id"]

    name_payload = {
        "use": "official",
        "family": "Smith",
        "given": ["John", "Paul"],
        "prefix": ["Mr."],
    }
    resp = await client.post(f"{BASE}/{patient_id}/names", json=name_payload)
    assert resp.status_code == 200
    data = resp.json()
    # Plain patient response embeds names under the key "name"
    names = data.get("name", [])
    assert len(names) >= 1
    found = next((n for n in names if n.get("family") == "Smith"), None)
    assert found is not None
    assert "John" in (found.get("given") or [])


async def test_get_names_sub_resource(client):
    create_resp = await client.post(BASE + "/", json=MINIMAL)
    patient_id = create_resp.json()["id"]

    await client.post(
        f"{BASE}/{patient_id}/names",
        json={"use": "official", "family": "Doe", "given": ["Jane"]},
    )

    resp = await client.get(f"{BASE}/{patient_id}/names")
    assert resp.status_code == 200
    data = resp.json()
    assert "data" in data
    assert data["total"] >= 1
    name_entry = data["data"][0]
    assert "id" in name_entry
    assert name_entry["family"] == "Doe"


async def test_delete_patient_name(client):
    create_resp = await client.post(BASE + "/", json=MINIMAL)
    patient_id = create_resp.json()["id"]

    await client.post(
        f"{BASE}/{patient_id}/names",
        json={"use": "official", "family": "Temp"},
    )
    names_resp = await client.get(f"{BASE}/{patient_id}/names")
    name_id = names_resp.json()["data"][0]["id"]

    del_resp = await client.delete(f"{BASE}/{patient_id}/names/{name_id}")
    assert del_resp.status_code == 204

    names_resp2 = await client.get(f"{BASE}/{patient_id}/names")
    assert names_resp2.json()["total"] == 0


# ── Sub-resource: Identifiers ──────────────────────────────────────────────────


async def test_add_and_list_identifier(client):
    create_resp = await client.post(BASE + "/", json=MINIMAL)
    patient_id = create_resp.json()["id"]

    id_payload = {
        "use": "official",
        "system": "http://hospital.example.org/mrn",
        "value": "MRN-001",
    }
    resp = await client.post(f"{BASE}/{patient_id}/identifiers", json=id_payload)
    assert resp.status_code == 200

    list_resp = await client.get(f"{BASE}/{patient_id}/identifiers")
    assert list_resp.status_code == 200
    data = list_resp.json()
    assert data["total"] == 1
    assert data["data"][0]["value"] == "MRN-001"


# ── Sub-resource: Telecom ──────────────────────────────────────────────────────


async def test_add_and_list_telecom(client):
    create_resp = await client.post(BASE + "/", json=MINIMAL)
    patient_id = create_resp.json()["id"]

    resp = await client.post(
        f"{BASE}/{patient_id}/telecom",
        json={"system": "email", "value": "test@example.com", "use": "home"},
    )
    assert resp.status_code == 200

    list_resp = await client.get(f"{BASE}/{patient_id}/telecom")
    assert list_resp.status_code == 200
    data = list_resp.json()
    assert data["total"] == 1
    assert data["data"][0]["value"] == "test@example.com"


# ── Sub-resource: Addresses ────────────────────────────────────────────────────


async def test_add_and_list_address(client):
    create_resp = await client.post(BASE + "/", json=MINIMAL)
    patient_id = create_resp.json()["id"]

    resp = await client.post(
        f"{BASE}/{patient_id}/addresses",
        json={
            "use": "home",
            "type": "physical",
            "line": ["123 Main St", "Apt 4B"],
            "city": "Springfield",
            "state": "IL",
            "postal_code": "62701",
            "country": "US",
        },
    )
    assert resp.status_code == 200

    list_resp = await client.get(f"{BASE}/{patient_id}/addresses")
    assert list_resp.status_code == 200
    data = list_resp.json()
    assert data["total"] == 1
    assert data["data"][0]["city"] == "Springfield"


# ── Content negotiation ────────────────────────────────────────────────────────


async def test_content_negotiation_defaults_to_plain(client):
    resp = await client.post(BASE + "/", json=MINIMAL)
    assert resp.status_code == 200
    data = resp.json()
    # Plain format: no resourceType, has snake_case id as int
    assert "resourceType" not in data
    assert isinstance(data["id"], int)


async def test_content_negotiation_fhir_accept(client):
    resp = await client.post(BASE + "/", json=MINIMAL, headers=FHIR_ACCEPT)
    assert resp.status_code == 200
    data = resp.json()
    assert data["resourceType"] == "Patient"
    assert isinstance(data["id"], str)


async def test_list_content_negotiation_fhir(client):
    await client.post(BASE + "/", json=MINIMAL)

    resp = await client.get(BASE + "/", headers=FHIR_ACCEPT)
    assert resp.status_code == 200
    data = resp.json()
    assert data["resourceType"] == "Bundle"
    assert data["type"] == "searchset"
