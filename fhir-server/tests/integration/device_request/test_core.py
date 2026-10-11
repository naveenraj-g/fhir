"""Integration tests for /api/fhir/v1/device-requests endpoints."""
from app.main import app

BASE = "/api/fhir/v1/device-requests"
FHIR_ACCEPT = {"Accept": "application/fhir+json"}

MINIMAL = {
    "user_id": "u-test",
    "org_id": "org-test",
    "intent": "order",
}

FULL = {
    **MINIMAL,
    "status": "active",
    "priority": "routine",
    "subject": "Patient/10001",
    "reason_code": [
        {"coding_system": "http://snomed.info/sct", "coding_code": "74400008", "coding_display": "Appendicitis"}
    ],
    "note": [{"text": "Please expedite."}],
}


async def _create(client, payload=None) -> dict:
    resp = await client.post(BASE + "/", json=payload or MINIMAL)
    assert resp.status_code == 200, resp.text
    return resp.json()


async def test_create_minimal(client):
    data = await _create(client)
    assert isinstance(data["id"], int)
    assert data["intent"] == "order"


async def test_create_full(client):
    r = await client.post(BASE + "/", json=FULL)
    assert r.status_code == 200, r.text
    data = r.json()
    assert data["intent"] == "order"
    assert data["status"] == "active"
    assert data["subject_type"] == "Patient"
    assert data["subject_id"] == 10001
    assert len(data["reason_code"]) == 1
    assert data["reason_code"][0]["coding_code"] == "74400008"
    assert len(data["note"]) == 1


async def test_create_fhir_format(client):
    r = await client.post(BASE + "/", json=FULL, headers=FHIR_ACCEPT)
    assert r.status_code == 200, r.text
    data = r.json()
    assert data["resourceType"] == "DeviceRequest"
    assert data["intent"] == "order"
    assert data["subject"]["reference"] == "Patient/10001"


async def test_get_device_request(client):
    data = await _create(client)
    r = await client.get(f"{BASE}/{data['id']}")
    assert r.status_code == 200
    assert r.json()["id"] == data["id"]


async def test_get_fhir(client):
    data = await _create(client)
    r = await client.get(f"{BASE}/{data['id']}", headers=FHIR_ACCEPT)
    assert r.status_code == 200
    assert r.json()["resourceType"] == "DeviceRequest"


async def test_get_not_found(client):
    assert (await client.get(f"{BASE}/9999999")).status_code == 404


async def test_list_device_requests(client):
    await _create(client)
    r = await client.get(BASE + "/")
    assert r.status_code == 200
    assert r.json()["total"] >= 1


async def test_list_fhir(client):
    await _create(client)
    r = await client.get(BASE + "/", headers=FHIR_ACCEPT)
    assert r.status_code == 200
    assert r.json()["resourceType"] == "Bundle"


async def test_list_pagination(client):
    for _ in range(3):
        await _create(client)
    r = await client.get(f"{BASE}/?limit=2&offset=0")
    assert r.status_code == 200
    assert len(r.json()["data"]) <= 2


async def test_patch_status(client):
    data = await _create(client)
    r = await client.patch(f"{BASE}/{data['id']}", json={"status": "completed"})
    assert r.status_code == 200
    assert r.json()["status"] == "completed"


async def test_patch_not_found(client):
    assert (await client.patch(f"{BASE}/9999999", json={"status": "revoked"})).status_code == 404


async def test_delete_device_request(client):
    data = await _create(client)
    assert (await client.delete(f"{BASE}/{data['id']}")).status_code == 204
    assert (await client.get(f"{BASE}/{data['id']}")).status_code == 404


async def test_delete_not_found(client):
    assert (await client.delete(f"{BASE}/9999999")).status_code == 404


