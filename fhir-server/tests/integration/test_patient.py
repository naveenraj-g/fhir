"""Integration tests for the /api/fhir/v1/patients endpoints.

These tests are intentionally written as integration tests instead of unit tests:
- they exercise the FastAPI router layer
- they use the real service/repository stack
- they validate the actual JSON contract returned to API clients

The goal is not to brute-force every nullable FHIR field permutation.
The goal is to cover every endpoint plus every high-risk behavior:
- content negotiation
- CRUD
- list filtering/pagination
- permission failures
- OperationOutcome error payloads
- payload-to-storage-to-response mapping for custom fields
- sub-resource CRUD for all patient child endpoints
"""

from tests.helpers.assertions import (
    assert_fhir_bundle,
    assert_fhir_patient,
    assert_operation_outcome,
    assert_paginated,
    assert_plain_patient,
)


# Base route used by every test in this module.
BASE = "/api/fhir/v1/patients"

# Reusable Accept header for FHIR output.
FHIR_ACCEPT = {"Accept": "application/fhir+json"}


# Minimal valid create payload.
# Keep this small so failures point to the endpoint itself instead of an unrelated field.
MINIMAL = {
    "user_id": "u-test",
    "org_id": "org-test",
    "active": True,
    "gender": "male",
}


# Rich payload used to validate optional-field mapping.
# This is our "representative full object" check. We do not need every nullable field
# in isolated tests, but we do need one payload that proves the richer mappings work.
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


# Small helper to reduce repetition in tests that need a patient id first.
async def _create_patient(client, payload=None) -> int:
    payload = payload or MINIMAL
    resp = await client.post(BASE + "/", json=payload)
    assert resp.status_code == 200
    return resp.json()["id"]


# Small helper for readable child-delete tests.
async def _get_first_child_id(client, path: str) -> int:
    resp = await client.get(path)
    assert resp.status_code == 200
    data = resp.json()
    assert data["total"] >= 1
    return data["data"][0]["id"]


# -----------------------------------------------------------------------------
# Create
# -----------------------------------------------------------------------------


async def test_create_patient_minimal(client):
    # Minimal create proves the endpoint accepts the smallest supported payload.
    resp = await client.post(BASE + "/", json=MINIMAL)
    assert resp.status_code == 200
    data = resp.json()
    assert_plain_patient(data, gender="male", active=True)


async def test_create_patient_full(client):
    # Rich create validates that optional scalar fields survive end-to-end.
    resp = await client.post(BASE + "/", json=FULL)
    assert resp.status_code == 200
    data = resp.json()
    assert_plain_patient(
        data,
        gender="female",
        birth_date="1990-06-15",
        marital_status_code="M",
        marital_status_display="Married",
        multiple_birth_boolean=False,
    )
    # The API stores the managingOrganization FHIR reference as split columns and
    # returns the plain-json form as snake_case pieces.
    assert data["managing_organization_type"] == "Organization"
    assert data["managing_organization_id"] == 190001
    assert data["managing_organization_display"] == "General Hospital"


async def test_create_patient_returns_fhir_format(client):
    # FHIR create must return a Patient resource, not the plain snake_case shape.
    resp = await client.post(BASE + "/", json=MINIMAL, headers=FHIR_ACCEPT)
    assert resp.status_code == 200
    assert "application/fhir+json" in resp.headers["content-type"]
    data = resp.json()
    assert_fhir_patient(data, gender="male")
    assert data.get("active") is True


async def test_create_patient_full_returns_fhir_reference_mapping(client):
    # This checks the mapper-sensitive part of the full payload in FHIR form.
    resp = await client.post(BASE + "/", json=FULL, headers=FHIR_ACCEPT)
    assert resp.status_code == 200
    data = resp.json()
    assert_fhir_patient(data, gender="female")
    assert data["birthDate"] == "1990-06-15"
    assert data["maritalStatus"]["coding"][0]["code"] == "M"
    assert data["managingOrganization"]["reference"] == "Organization/190001"
    assert data["managingOrganization"]["display"] == "General Hospital"


async def test_create_patient_extra_field_rejected(client):
    # Extra fields should fail schema validation and be returned as OperationOutcome.
    payload = {**MINIMAL, "nonexistent_field": "value"}
    resp = await client.post(BASE + "/", json=payload)
    assert_operation_outcome(resp.json(), expected_status=400, response_status=resp.status_code)


async def test_create_patient_invalid_managing_organization_reference_rejected(client):
    # This is a high-value validation case because the repository parses FHIR references.
    payload = {**MINIMAL, "managing_organization": "BadReference"}
    resp = await client.post(BASE + "/", json=payload)
    assert_operation_outcome(resp.json(), expected_status=422, response_status=resp.status_code)


# -----------------------------------------------------------------------------
# Get by ID
# -----------------------------------------------------------------------------


async def test_get_patient_by_id_plain(client):
    patient_id = await _create_patient(client)
    resp = await client.get(f"{BASE}/{patient_id}")
    assert resp.status_code == 200
    data = resp.json()
    assert_plain_patient(data, gender="male")
    assert data["id"] == patient_id


async def test_get_patient_by_id_fhir(client):
    patient_id = await _create_patient(client)
    resp = await client.get(f"{BASE}/{patient_id}", headers=FHIR_ACCEPT)
    assert resp.status_code == 200
    assert "application/fhir+json" in resp.headers["content-type"]
    data = resp.json()
    assert_fhir_patient(data)
    assert data["id"] == str(patient_id)


async def test_get_patient_not_found(client):
    resp = await client.get(f"{BASE}/999999")
    assert_operation_outcome(resp.json(), expected_status=404, response_status=resp.status_code)


# -----------------------------------------------------------------------------
# Patch
# -----------------------------------------------------------------------------


async def test_patch_patient_gender(client):
    patient_id = await _create_patient(client)
    resp = await client.patch(f"{BASE}/{patient_id}", json={"gender": "female"})
    assert resp.status_code == 200
    assert resp.json()["gender"] == "female"


async def test_patch_patient_birth_date(client):
    patient_id = await _create_patient(client)
    resp = await client.patch(f"{BASE}/{patient_id}", json={"birth_date": "1985-03-20"})
    assert resp.status_code == 200
    assert resp.json()["birth_date"] == "1985-03-20"


async def test_patch_patient_active_false(client):
    patient_id = await _create_patient(client)
    resp = await client.patch(f"{BASE}/{patient_id}", json={"active": False})
    assert resp.status_code == 200
    assert resp.json()["active"] is False


async def test_patch_patient_can_clear_nullable_fields(client):
    # Explicit nulls should clear stored nullable fields when the patch schema allows them.
    patient_id = await _create_patient(client, FULL)
    resp = await client.patch(
        f"{BASE}/{patient_id}",
        json={
            "birth_date": None,
            "managing_organization": None,
            "managing_organization_display": None,
        },
    )
    assert resp.status_code == 200
    data = resp.json()
    # Plain mapper drops None fields entirely, so absence is the expected contract.
    assert "birth_date" not in data
    assert "managing_organization_type" not in data
    assert "managing_organization_id" not in data
    assert "managing_organization_display" not in data


async def test_patch_patient_invalid_managing_organization_reference_rejected(client):
    patient_id = await _create_patient(client)
    resp = await client.patch(
        f"{BASE}/{patient_id}",
        json={"managing_organization": "Not/A/Valid/Ref"},
    )
    assert_operation_outcome(resp.json(), expected_status=422, response_status=resp.status_code)


async def test_patch_patient_not_found(client):
    resp = await client.patch(f"{BASE}/999999", json={"gender": "female"})
    assert_operation_outcome(resp.json(), expected_status=404, response_status=resp.status_code)


# -----------------------------------------------------------------------------
# Delete
# -----------------------------------------------------------------------------


async def test_delete_patient(client):
    patient_id = await _create_patient(client)
    resp = await client.delete(f"{BASE}/{patient_id}")
    assert resp.status_code == 204

    # A deleted patient must no longer be retrievable.
    get_resp = await client.get(f"{BASE}/{patient_id}")
    assert get_resp.status_code == 404


async def test_delete_patient_not_found(client):
    resp = await client.delete(f"{BASE}/999999")
    assert_operation_outcome(resp.json(), expected_status=404, response_status=resp.status_code)


# -----------------------------------------------------------------------------
# List
# -----------------------------------------------------------------------------


async def test_list_patients_plain(client):
    await client.post(BASE + "/", json=MINIMAL)
    await client.post(BASE + "/", json={**FULL})

    resp = await client.get(BASE + "/")
    assert resp.status_code == 200
    assert_paginated(resp.json(), min_total=2)


async def test_list_patients_fhir_bundle(client):
    await client.post(BASE + "/", json=MINIMAL)
    resp = await client.get(BASE + "/", headers=FHIR_ACCEPT)
    assert resp.status_code == 200
    assert "application/fhir+json" in resp.headers["content-type"]
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
    for patient in data["data"]:
        assert patient["gender"] == "female"


async def test_list_patients_filter_active(client):
    await client.post(BASE + "/", json={**MINIMAL, "active": True})
    await client.post(BASE + "/", json={**MINIMAL, "active": False})

    resp = await client.get(BASE + "/?active=true")
    assert resp.status_code == 200
    data = resp.json()
    for patient in data["data"]:
        assert patient["active"] is True


async def test_list_patients_filter_family_name(client):
    patient_id = await _create_patient(client)
    await client.post(f"{BASE}/{patient_id}/names", json={"use": "official", "family": "TargetFamily"})

    await client.post(BASE + "/", json={**MINIMAL, "user_id": "u-test-2"})
    other_id = await _create_patient(client, {**MINIMAL, "user_id": "u-test-3"})
    await client.post(f"{BASE}/{other_id}/names", json={"use": "official", "family": "DifferentFamily"})

    resp = await client.get(BASE + "/?family_name=TargetFamily")
    assert resp.status_code == 200
    data = resp.json()
    assert data["total"] >= 1
    assert all(p["id"] == patient_id for p in data["data"])


async def test_list_patients_filter_given_name(client):
    patient_id = await _create_patient(client)
    await client.post(
        f"{BASE}/{patient_id}/names",
        json={"use": "official", "family": "Person", "given": ["UniqueGiven"]},
    )

    other_id = await _create_patient(client, {**MINIMAL, "user_id": "u-test-4"})
    await client.post(
        f"{BASE}/{other_id}/names",
        json={"use": "official", "family": "Person", "given": ["CommonGiven"]},
    )

    resp = await client.get(BASE + "/?given_name=UniqueGiven")
    assert resp.status_code == 200
    data = resp.json()
    assert data["total"] >= 1
    assert all(p["id"] == patient_id for p in data["data"])


async def test_list_patients_empty(client):
    resp = await client.get(BASE + "/")
    assert resp.status_code == 200
    data = resp.json()
    assert data["total"] == 0
    assert data["data"] == []


# -----------------------------------------------------------------------------
# /me
# -----------------------------------------------------------------------------


async def test_get_my_patient_profile_found(client):
    # The payload user_id/org_id must match the mocked JWT in conftest.py.
    await client.post(BASE + "/", json=MINIMAL)
    resp = await client.get(BASE + "/me")
    assert resp.status_code == 200
    assert_plain_patient(resp.json(), gender="male")


async def test_get_my_patient_profile_not_found(client):
    resp = await client.get(BASE + "/me")
    assert_operation_outcome(resp.json(), expected_status=404, response_status=resp.status_code)


async def test_get_my_patient_profile_org_isolation(client, other_client):
    # /me is the one place where current code does scope by user/org.
    await client.post(BASE + "/", json=MINIMAL)
    resp = await other_client.get(BASE + "/me")
    assert_operation_outcome(resp.json(), expected_status=404, response_status=resp.status_code)


# -----------------------------------------------------------------------------
# Permissions
# -----------------------------------------------------------------------------


async def test_create_patient_no_permission(client):
    # This overrides the auth dependency just for this test.
    from app.auth.dependencies import get_current_user as _gcu
    from tests.conftest import make_test_user

    app = client._transport.app
    app.dependency_overrides[_gcu] = make_test_user(permissions=["patient:read"])
    try:
        resp = await client.post(BASE + "/", json=MINIMAL)
        assert_operation_outcome(resp.json(), expected_status=403, response_status=resp.status_code)
    finally:
        app.dependency_overrides[_gcu] = make_test_user()


# -----------------------------------------------------------------------------
# Sub-resource: Names
# -----------------------------------------------------------------------------


async def test_add_and_list_patient_name(client):
    patient_id = await _create_patient(client)
    name_payload = {
        "use": "official",
        "family": "Smith",
        "given": ["John", "Paul"],
        "prefix": ["Mr."],
    }

    # POST returns the updated patient resource, not the child row directly.
    resp = await client.post(f"{BASE}/{patient_id}/names", json=name_payload)
    assert resp.status_code == 200
    names = resp.json().get("name", [])
    found = next((name for name in names if name.get("family") == "Smith"), None)
    assert found is not None
    assert "John" in (found.get("given") or [])

    list_resp = await client.get(f"{BASE}/{patient_id}/names")
    assert list_resp.status_code == 200
    data = list_resp.json()
    assert data["total"] >= 1
    assert data["data"][0]["family"] == "Smith"


async def test_list_patient_names_fhir(client):
    patient_id = await _create_patient(client)
    await client.post(
        f"{BASE}/{patient_id}/names",
        json={"use": "official", "family": "Doe", "given": ["Jane"]},
    )

    resp = await client.get(f"{BASE}/{patient_id}/names", headers=FHIR_ACCEPT)
    assert resp.status_code == 200
    assert "application/fhir+json" in resp.headers["content-type"]
    data = resp.json()
    assert data["total"] == 1
    assert data["data"][0]["family"] == "Doe"
    assert data["data"][0]["given"] == ["Jane"]


async def test_delete_patient_name(client):
    patient_id = await _create_patient(client)
    await client.post(f"{BASE}/{patient_id}/names", json={"use": "official", "family": "Temp"})
    name_id = await _get_first_child_id(client, f"{BASE}/{patient_id}/names")

    del_resp = await client.delete(f"{BASE}/{patient_id}/names/{name_id}")
    assert del_resp.status_code == 204

    names_resp = await client.get(f"{BASE}/{patient_id}/names")
    assert names_resp.json()["total"] == 0


# -----------------------------------------------------------------------------
# Sub-resource: Identifiers
# -----------------------------------------------------------------------------


async def test_add_and_list_identifier(client):
    patient_id = await _create_patient(client)
    id_payload = {
        "use": "official",
        "type_system": "http://terminology.hl7.org/CodeSystem/v2-0203",
        "type_code": "MR",
        "type_display": "Medical record number",
        "type_text": "MRN",
        "system": "http://hospital.example.org/mrn",
        "value": "MRN-001",
        "assigner": "Hospital A",
    }

    resp = await client.post(f"{BASE}/{patient_id}/identifiers", json=id_payload)
    assert resp.status_code == 200

    list_resp = await client.get(f"{BASE}/{patient_id}/identifiers")
    assert list_resp.status_code == 200
    data = list_resp.json()
    assert data["total"] == 1
    assert data["data"][0]["value"] == "MRN-001"
    assert data["data"][0]["type_code"] == "MR"


async def test_list_patient_identifiers_fhir(client):
    patient_id = await _create_patient(client)
    await client.post(
        f"{BASE}/{patient_id}/identifiers",
        json={"system": "http://hospital.example.org/mrn", "value": "MRN-XYZ"},
    )

    resp = await client.get(f"{BASE}/{patient_id}/identifiers", headers=FHIR_ACCEPT)
    assert resp.status_code == 200
    data = resp.json()
    assert data["total"] == 1
    assert data["data"][0]["system"] == "http://hospital.example.org/mrn"
    assert data["data"][0]["value"] == "MRN-XYZ"


async def test_delete_patient_identifier(client):
    patient_id = await _create_patient(client)
    await client.post(
        f"{BASE}/{patient_id}/identifiers",
        json={"system": "http://hospital.example.org/mrn", "value": "MRN-DELETE"},
    )
    identifier_id = await _get_first_child_id(client, f"{BASE}/{patient_id}/identifiers")

    del_resp = await client.delete(f"{BASE}/{patient_id}/identifiers/{identifier_id}")
    assert del_resp.status_code == 204
    assert (await client.get(f"{BASE}/{patient_id}/identifiers")).json()["total"] == 0


# -----------------------------------------------------------------------------
# Sub-resource: Telecom
# -----------------------------------------------------------------------------


async def test_add_and_list_telecom(client):
    patient_id = await _create_patient(client)

    resp = await client.post(
        f"{BASE}/{patient_id}/telecom",
        json={"system": "email", "value": "test@example.com", "use": "home", "rank": 1},
    )
    assert resp.status_code == 200

    list_resp = await client.get(f"{BASE}/{patient_id}/telecom")
    assert list_resp.status_code == 200
    data = list_resp.json()
    assert data["total"] == 1
    assert data["data"][0]["value"] == "test@example.com"
    assert data["data"][0]["rank"] == 1


async def test_list_patient_telecom_fhir(client):
    patient_id = await _create_patient(client)
    await client.post(
        f"{BASE}/{patient_id}/telecom",
        json={"system": "phone", "value": "+1-555-0000", "use": "mobile", "rank": 1},
    )

    resp = await client.get(f"{BASE}/{patient_id}/telecom", headers=FHIR_ACCEPT)
    assert resp.status_code == 200
    data = resp.json()
    assert data["total"] == 1
    assert data["data"][0]["system"] == "phone"
    assert data["data"][0]["use"] == "mobile"


async def test_delete_patient_telecom(client):
    patient_id = await _create_patient(client)
    await client.post(
        f"{BASE}/{patient_id}/telecom",
        json={"system": "email", "value": "delete@example.com"},
    )
    telecom_id = await _get_first_child_id(client, f"{BASE}/{patient_id}/telecom")

    del_resp = await client.delete(f"{BASE}/{patient_id}/telecom/{telecom_id}")
    assert del_resp.status_code == 204
    assert (await client.get(f"{BASE}/{patient_id}/telecom")).json()["total"] == 0


async def test_add_patient_telecom_invalid_rank_rejected(client):
    patient_id = await _create_patient(client)
    resp = await client.post(
        f"{BASE}/{patient_id}/telecom",
        json={"system": "email", "value": "bad@example.com", "rank": 0},
    )
    assert_operation_outcome(resp.json(), expected_status=400, response_status=resp.status_code)


# -----------------------------------------------------------------------------
# Sub-resource: Addresses
# -----------------------------------------------------------------------------


async def test_add_and_list_address(client):
    patient_id = await _create_patient(client)

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
    assert data["data"][0]["line"] == ["123 Main St", "Apt 4B"]


async def test_list_patient_addresses_fhir(client):
    patient_id = await _create_patient(client)
    await client.post(
        f"{BASE}/{patient_id}/addresses",
        json={"use": "home", "type": "both", "line": ["456 River Rd"], "city": "Austin"},
    )

    resp = await client.get(f"{BASE}/{patient_id}/addresses", headers=FHIR_ACCEPT)
    assert resp.status_code == 200
    data = resp.json()
    assert data["total"] == 1
    assert data["data"][0]["use"] == "home"
    assert data["data"][0]["city"] == "Austin"


async def test_delete_patient_address(client):
    patient_id = await _create_patient(client)
    await client.post(
        f"{BASE}/{patient_id}/addresses",
        json={"line": ["Delete Address"]},
    )
    address_id = await _get_first_child_id(client, f"{BASE}/{patient_id}/addresses")

    del_resp = await client.delete(f"{BASE}/{patient_id}/addresses/{address_id}")
    assert del_resp.status_code == 204
    assert (await client.get(f"{BASE}/{patient_id}/addresses")).json()["total"] == 0


# -----------------------------------------------------------------------------
# Sub-resource: Photos
# -----------------------------------------------------------------------------


async def test_add_and_list_photo(client):
    patient_id = await _create_patient(client)
    photo_payload = {
        "content_type": "image/png",
        "language": "en",
        "data": "ZmFrZS1pbWFnZS1kYXRh",
        "url": "https://example.com/photo.png",
        "size": 15,
        "hash": "ZmFrZS1oYXNo",
        "title": "Profile photo",
        "creation": "2025-01-02T03:04:05",
    }

    resp = await client.post(f"{BASE}/{patient_id}/photos", json=photo_payload)
    assert resp.status_code == 200

    list_resp = await client.get(f"{BASE}/{patient_id}/photos")
    assert list_resp.status_code == 200
    data = list_resp.json()
    assert data["total"] == 1
    assert data["data"][0]["content_type"] == "image/png"
    assert data["data"][0]["title"] == "Profile photo"


async def test_list_patient_photos_fhir(client):
    patient_id = await _create_patient(client)
    await client.post(
        f"{BASE}/{patient_id}/photos",
        json={"content_type": "image/jpeg", "title": "FHIR photo"},
    )

    resp = await client.get(f"{BASE}/{patient_id}/photos", headers=FHIR_ACCEPT)
    assert resp.status_code == 200
    data = resp.json()
    assert data["total"] == 1
    assert data["data"][0]["contentType"] == "image/jpeg"
    assert data["data"][0]["title"] == "FHIR photo"


async def test_delete_patient_photo(client):
    patient_id = await _create_patient(client)
    await client.post(f"{BASE}/{patient_id}/photos", json={"title": "Delete Me"})
    photo_id = await _get_first_child_id(client, f"{BASE}/{patient_id}/photos")

    del_resp = await client.delete(f"{BASE}/{patient_id}/photos/{photo_id}")
    assert del_resp.status_code == 204
    assert (await client.get(f"{BASE}/{patient_id}/photos")).json()["total"] == 0


# -----------------------------------------------------------------------------
# Sub-resource: Contacts
# -----------------------------------------------------------------------------


async def test_add_and_list_contact(client):
    patient_id = await _create_patient(client)
    contact_payload = {
        "relationship": [
            {
                "coding_system": "http://terminology.hl7.org/CodeSystem/v2-0131",
                "coding_code": "N",
                "coding_display": "Next-of-kin",
                "text": "Next-of-kin",
            }
        ],
        "role": [
            {
                "coding_system": "http://example.org/contact-role",
                "coding_code": "guardian",
                "coding_display": "Guardian",
                "text": "Guardian",
            }
        ],
        "name_use": "official",
        "name_family": "Caregiver",
        "name_given": ["Casey"],
        "telecom": [{"system": "phone", "value": "+1-555-1111", "use": "mobile"}],
        "additional_name": [{"family": "Alias", "given": ["C"]}],
        "address_use": "home",
        "address_line": ["1 Contact St"],
        "address_city": "Seattle",
        "additional_address": [{"line": ["2 Backup Ave"], "city": "Tacoma"}],
        "gender": "female",
        "organization": "Organization/190001",
        "organization_display": "General Hospital",
    }

    resp = await client.post(f"{BASE}/{patient_id}/contacts", json=contact_payload)
    assert resp.status_code == 200

    list_resp = await client.get(f"{BASE}/{patient_id}/contacts")
    assert list_resp.status_code == 200
    data = list_resp.json()
    assert data["total"] == 1
    contact = data["data"][0]
    assert contact["name_family"] == "Caregiver"
    assert contact["relationship"][0]["coding_code"] == "N"
    assert contact["role"][0]["coding_code"] == "guardian"
    assert contact["telecom"][0]["value"] == "+1-555-1111"
    assert contact["additional_name"][0]["family"] == "Alias"
    assert contact["additional_address"][0]["city"] == "Tacoma"
    assert contact["organization_type"] == "Organization"
    assert contact["organization_id"] == 190001


async def test_list_patient_contacts_fhir(client):
    patient_id = await _create_patient(client)
    await client.post(
        f"{BASE}/{patient_id}/contacts",
        json={
            "name_family": "FHIRContact",
            "name_given": ["Taylor"],
            "organization": "Organization/190001",
        },
    )

    resp = await client.get(f"{BASE}/{patient_id}/contacts", headers=FHIR_ACCEPT)
    assert resp.status_code == 200
    data = resp.json()
    assert data["total"] == 1
    assert data["data"][0]["name"]["family"] == "FHIRContact"
    assert data["data"][0]["organization"]["reference"] == "Organization/190001"


async def test_delete_patient_contact(client):
    patient_id = await _create_patient(client)
    await client.post(f"{BASE}/{patient_id}/contacts", json={"name_family": "Delete Contact"})
    contact_id = await _get_first_child_id(client, f"{BASE}/{patient_id}/contacts")

    del_resp = await client.delete(f"{BASE}/{patient_id}/contacts/{contact_id}")
    assert del_resp.status_code == 204
    assert (await client.get(f"{BASE}/{patient_id}/contacts")).json()["total"] == 0


# -----------------------------------------------------------------------------
# Sub-resource: Communications
# -----------------------------------------------------------------------------


async def test_add_and_list_communication(client):
    patient_id = await _create_patient(client)
    resp = await client.post(
        f"{BASE}/{patient_id}/communications",
        json={
            "language_system": "urn:ietf:bcp:47",
            "language_code": "en",
            "language_display": "English",
            "language_text": "English",
            "preferred": True,
        },
    )
    assert resp.status_code == 200

    list_resp = await client.get(f"{BASE}/{patient_id}/communications")
    assert list_resp.status_code == 200
    data = list_resp.json()
    assert data["total"] == 1
    assert data["data"][0]["language_code"] == "en"
    assert data["data"][0]["preferred"] is True


async def test_list_patient_communications_fhir(client):
    patient_id = await _create_patient(client)
    await client.post(
        f"{BASE}/{patient_id}/communications",
        json={"language_code": "fr", "language_display": "French"},
    )

    resp = await client.get(f"{BASE}/{patient_id}/communications", headers=FHIR_ACCEPT)
    assert resp.status_code == 200
    data = resp.json()
    assert data["total"] == 1
    assert data["data"][0]["language"]["coding"][0]["code"] == "fr"


async def test_delete_patient_communication(client):
    patient_id = await _create_patient(client)
    await client.post(f"{BASE}/{patient_id}/communications", json={"language_code": "de"})
    comm_id = await _get_first_child_id(client, f"{BASE}/{patient_id}/communications")

    del_resp = await client.delete(f"{BASE}/{patient_id}/communications/{comm_id}")
    assert del_resp.status_code == 204
    assert (await client.get(f"{BASE}/{patient_id}/communications")).json()["total"] == 0


# -----------------------------------------------------------------------------
# Sub-resource: General Practitioners
# -----------------------------------------------------------------------------


async def test_add_and_list_general_practitioner(client):
    patient_id = await _create_patient(client)
    resp = await client.post(
        f"{BASE}/{patient_id}/general-practitioners",
        json={
            "reference_type": "Practitioner",
            "reference_id": 30001,
            "reference_display": "Dr. Green",
        },
    )
    assert resp.status_code == 200

    list_resp = await client.get(f"{BASE}/{patient_id}/general-practitioners")
    assert list_resp.status_code == 200
    data = list_resp.json()
    assert data["total"] == 1
    assert data["data"][0]["reference_type"] == "Practitioner"
    assert data["data"][0]["reference_id"] == 30001


async def test_list_patient_general_practitioners_fhir(client):
    patient_id = await _create_patient(client)
    await client.post(
        f"{BASE}/{patient_id}/general-practitioners",
        json={"reference_type": "Organization", "reference_id": 190001},
    )

    resp = await client.get(f"{BASE}/{patient_id}/general-practitioners", headers=FHIR_ACCEPT)
    assert resp.status_code == 200
    data = resp.json()
    assert data["total"] == 1
    assert data["data"][0]["reference"] == "Organization/190001"


async def test_delete_patient_general_practitioner(client):
    patient_id = await _create_patient(client)
    await client.post(
        f"{BASE}/{patient_id}/general-practitioners",
        json={"reference_type": "PractitionerRole", "reference_id": 140001},
    )
    gp_id = await _get_first_child_id(client, f"{BASE}/{patient_id}/general-practitioners")

    del_resp = await client.delete(f"{BASE}/{patient_id}/general-practitioners/{gp_id}")
    assert del_resp.status_code == 204
    assert (await client.get(f"{BASE}/{patient_id}/general-practitioners")).json()["total"] == 0


# -----------------------------------------------------------------------------
# Sub-resource: Links
# -----------------------------------------------------------------------------


async def test_add_and_list_link(client):
    patient_id = await _create_patient(client)
    resp = await client.post(
        f"{BASE}/{patient_id}/links",
        json={
            "other_type": "Patient",
            "other_id": 10099,
            "other_display": "Linked patient",
            "type": "seealso",
        },
    )
    assert resp.status_code == 200

    list_resp = await client.get(f"{BASE}/{patient_id}/links")
    assert list_resp.status_code == 200
    data = list_resp.json()
    assert data["total"] == 1
    assert data["data"][0]["other_type"] == "Patient"
    assert data["data"][0]["other_id"] == 10099
    assert data["data"][0]["type"] == "seealso"


async def test_list_patient_links_fhir(client):
    patient_id = await _create_patient(client)
    await client.post(
        f"{BASE}/{patient_id}/links",
        json={"other_type": "RelatedPerson", "other_id": 50001, "type": "refer"},
    )

    resp = await client.get(f"{BASE}/{patient_id}/links", headers=FHIR_ACCEPT)
    assert resp.status_code == 200
    data = resp.json()
    assert data["total"] == 1
    assert data["data"][0]["other"]["reference"] == "RelatedPerson/50001"
    assert data["data"][0]["type"] == "refer"


async def test_delete_patient_link(client):
    patient_id = await _create_patient(client)
    await client.post(
        f"{BASE}/{patient_id}/links",
        json={"other_type": "Patient", "other_id": 10101, "type": "replaces"},
    )
    link_id = await _get_first_child_id(client, f"{BASE}/{patient_id}/links")

    del_resp = await client.delete(f"{BASE}/{patient_id}/links/{link_id}")
    assert del_resp.status_code == 204
    assert (await client.get(f"{BASE}/{patient_id}/links")).json()["total"] == 0


# -----------------------------------------------------------------------------
# Content negotiation defaults
# -----------------------------------------------------------------------------


async def test_content_negotiation_defaults_to_plain(client):
    # No Accept header means plain json by default.
    resp = await client.post(BASE + "/", json=MINIMAL)
    assert resp.status_code == 200
    assert "application/json" in resp.headers["content-type"]
    data = resp.json()
    assert "resourceType" not in data
    assert isinstance(data["id"], int)


async def test_content_negotiation_fhir_accept(client):
    resp = await client.post(BASE + "/", json=MINIMAL, headers=FHIR_ACCEPT)
    assert resp.status_code == 200
    assert "application/fhir+json" in resp.headers["content-type"]
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
