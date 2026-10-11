"""Integration tests for /api/fhir/v1/procedures endpoints."""
BASE = "/api/fhir/v1/procedures"
FHIR_ACCEPT = {"Accept": "application/fhir+json"}


def _with_org(query: str) -> str:
    """Every search requires org_id (tenant scope) — add the default test org unless the query sets one."""
    if "org_id=" in query:
        return query
    return f"org_id=org-test&{query}" if query else "org_id=org-test"

MINIMAL = {
    "user_id": "u-test",
    "org_id": "org-test",
    "status": "completed",
    "subject": "Patient/10001",
}

FULL = {
    **MINIMAL,
    "subject_display": "John Doe",
    "code_system": "http://snomed.info/sct",
    "code_code": "80146002",
    "code_display": "Appendectomy",
    "performed_datetime": "2024-01-15T10:00:00Z",
    "category_system": "http://snomed.info/sct",
    "category_code": "387713003",
    "category_display": "Surgical procedure",
    "performer": [
        {"actor": "Practitioner/30001", "actor_display": "Dr. Smith"}
    ],
    "note": [{"text": "Procedure completed without complications."}],
    "reason_code": [
        {"coding_system": "http://snomed.info/sct", "coding_code": "74400008", "coding_display": "Appendicitis"}
    ],
    "identifier": [{"system": "urn:mrn", "value": "PROC-1"}],
    "location": "Location/230001",
    "based_on": [{"reference": "ServiceRequest/80001"}],
    "part_of": [{"reference": "Procedure/100500"}],
    "reason_reference": [{"reference": "Condition/120001"}],
    "instantiates_canonical": ["http://example.org/protocol/a"],
}


async def _create(client, payload=None) -> dict:
    resp = await client.post(BASE + "/", json=payload or MINIMAL)
    assert resp.status_code == 200, resp.text
    return resp.json()


async def _ids(client, query: str) -> set[int]:
    r = await client.get(f"{BASE}/?{_with_org(query)}")
    assert r.status_code == 200, r.text
    return {d["id"] for d in r.json()["data"]}


# ── CRUD ──────────────────────────────────────────────────────────────────────


async def test_create_minimal(client):
    data = await _create(client)
    assert isinstance(data["id"], int)
    assert data["status"] == "completed"


async def test_create_full(client):
    data = await _create(client, FULL)
    assert data["code_code"] == "80146002"
    assert data["subject_type"] == "Patient"
    assert data["subject_id"] == 10001
    assert len(data["performer"]) == 1
    assert len(data["note"]) == 1
    assert len(data["reason_code"]) == 1


async def test_create_fhir_format(client):
    r = await client.post(BASE + "/", json=FULL, headers=FHIR_ACCEPT)
    assert r.status_code == 200, r.text
    data = r.json()
    assert data["resourceType"] == "Procedure"
    assert data["status"] == "completed"
    assert data["subject"]["reference"] == "Patient/10001"


async def test_create_requires_subject(client):
    payload = {k: v for k, v in MINIMAL.items() if k != "subject"}
    assert (await client.post(BASE + "/", json=payload)).status_code == 400


async def test_create_invalid_status_rejected(client):
    assert (await client.post(BASE + "/", json={**MINIMAL, "status": "bogus"})).status_code == 400


async def test_create_hyphenated_status(client):
    data = await _create(client, {**MINIMAL, "status": "in-progress"})
    assert data["status"] == "in-progress"


async def test_get_procedure(client):
    data = await _create(client)
    r = await client.get(f"{BASE}/{data['id']}")
    assert r.status_code == 200
    assert r.json()["id"] == data["id"]


async def test_get_not_found(client):
    assert (await client.get(f"{BASE}/9999999")).status_code == 404


async def test_patch_status(client):
    data = await _create(client)
    r = await client.patch(f"{BASE}/{data['id']}", json={"status": "not-done"})
    assert r.status_code == 200
    assert r.json()["status"] == "not-done"


async def test_patch_null_status_rejected(client):
    data = await _create(client)
    assert (await client.patch(f"{BASE}/{data['id']}", json={"status": None})).status_code == 400


async def test_patch_invalid_status_rejected(client):
    data = await _create(client)
    assert (await client.patch(f"{BASE}/{data['id']}", json={"status": "bogus"})).status_code == 400


async def test_patch_references(client):
    data = await _create(client)
    r = await client.patch(
        f"{BASE}/{data['id']}",
        json={"subject": "Patient/10002", "recorder": "Practitioner/30001", "location": "Location/230001"},
    )
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["subject_id"] == 10002
    assert (body["recorder_type"], body["recorder_id"]) == ("Practitioner", 30001)
    assert (body["location_type"], body["location_id"]) == ("Location", 230001)

    r = await client.patch(f"{BASE}/{data['id']}", json={"recorder": None})
    assert r.json()["recorder_id"] is None


async def test_patch_bad_reference_type(client):
    data = await _create(client)
    r = await client.patch(f"{BASE}/{data['id']}", json={"recorder": "Device/1"})
    assert r.status_code == 422


async def test_patch_not_found(client):
    assert (await client.patch(f"{BASE}/9999999", json={"status": "stopped"})).status_code == 404


async def test_delete_procedure(client):
    data = await _create(client)
    assert (await client.delete(f"{BASE}/{data['id']}")).status_code == 204
    assert (await client.get(f"{BASE}/{data['id']}")).status_code == 404


async def test_delete_not_found(client):
    assert (await client.delete(f"{BASE}/9999999")).status_code == 404


# ── list / pagination ─────────────────────────────────────────────────────────


async def test_list_procedures(client):
    await _create(client)
    r = await client.get(BASE + "/?org_id=org-test")
    assert r.status_code == 200
    assert r.json()["total"] >= 1


async def test_list_fhir(client):
    await _create(client)
    r = await client.get(BASE + "/?org_id=org-test", headers=FHIR_ACCEPT)
    assert r.status_code == 200
    assert r.json()["resourceType"] == "Bundle"


async def test_list_pagination(client):
    for _ in range(3):
        await _create(client)
    r = await client.get(f"{BASE}/?org_id=org-test&limit=2&offset=0")
    assert len(r.json()["data"]) <= 2


async def test_list_nulls_last(client):
    undated = await _create(client)
    dated = await _create(client, {**MINIMAL, "performed_datetime": "2024-01-01T00:00:00Z"})
    ids = [d["id"] for d in (await client.get(BASE + "/?org_id=org-test")).json()["data"]]
    assert ids.index(dated["id"]) < ids.index(undated["id"])


# ── FHIR R4 search parameters ─────────────────────────────────────────────────


async def test_search_id_and_status(client):
    a = await _create(client)
    b = await _create(client, {**MINIMAL, "status": "stopped"})
    assert await _ids(client, f"_id={a['id']}") == {a["id"]}
    assert await _ids(client, "status=stopped") == {b["id"]}
    assert await _ids(client, "status=stopped,completed") == {a["id"], b["id"]}
    assert (await client.get(BASE + "/?" + _with_org("status=bogus"))).status_code == 422


async def test_search_tokens(client):
    p = await _create(client, FULL)
    other = await _create(client)
    assert await _ids(client, "code=80146002") == {p["id"]}
    assert await _ids(client, "code=http://snomed.info/sct|80146002") == {p["id"]}
    assert await _ids(client, "code=http://other|80146002") == set()
    assert await _ids(client, "category=387713003") == {p["id"]}
    assert await _ids(client, "identifier=urn:mrn|PROC-1") == {p["id"]}
    assert await _ids(client, "identifier=PROC-1") == {p["id"]}
    assert await _ids(client, "reason-code=74400008") == {p["id"]}
    assert other["id"] not in await _ids(client, "code=80146002")


async def test_search_references(client):
    p = await _create(client, FULL)
    other = await _create(client, {**MINIMAL, "subject": "Patient/10002"})
    assert await _ids(client, "patient=Patient/10001") == {p["id"]}
    assert await _ids(client, "patient=10002") == {other["id"]}
    assert await _ids(client, "patient_id=10001") == {p["id"]}
    assert await _ids(client, "subject=Patient/10001") == {p["id"]}
    assert await _ids(client, "performer=Practitioner/30001") == {p["id"]}
    assert await _ids(client, "performer=Practitioner/39999") == set()
    assert await _ids(client, "location=Location/230001") == {p["id"]}
    assert await _ids(client, "based-on=ServiceRequest/80001") == {p["id"]}
    assert await _ids(client, "part-of=Procedure/100500") == {p["id"]}
    assert await _ids(client, "reason-reference=Condition/120001") == {p["id"]}
    assert (await client.get(BASE + "/?" + _with_org("patient=Group/1"))).status_code == 422
    assert (await client.get(BASE + "/?" + _with_org("performer=Condition/1"))).status_code == 422


async def test_search_instantiates(client):
    p = await _create(client, FULL)
    assert await _ids(client, "instantiates-canonical=http://example.org/protocol/a") == {p["id"]}
    assert await _ids(client, "instantiates-canonical=http://example.org/protocol") == set()


async def test_search_date(client):
    dt = await _create(client, {**MINIMAL, "performed_datetime": "2024-01-15T10:00:00Z"})
    period = await _create(client, {
        **MINIMAL,
        "performed_period_start": "2024-02-01T00:00:00Z",
        "performed_period_end": "2024-02-10T00:00:00Z",
    })
    assert await _ids(client, "date=2024-01-15") == {dt["id"]}
    assert await _ids(client, "date=2024-01") == {dt["id"]}
    assert await _ids(client, "date=ge2024-01-01&date=lt2024-02-01") == {dt["id"]}
    assert await _ids(client, "date=gt2024-01-31") == {period["id"]}
    assert await _ids(client, "date=lt2024-02-01") == {dt["id"]}
    assert await _ids(client, "date=ap2024-02-05") == {period["id"]}
    assert (await client.get(BASE + "/?" + _with_org("date=notadate"))).status_code == 422


async def test_search_last_updated(client):
    p = await _create(client)
    assert p["id"] in await _ids(client, "_lastUpdated=ge2000-01-01")
    assert await _ids(client, "_lastUpdated=lt2000-01-01") == set()


async def test_search_scoped_by_org_and_optional_user(client):
    a = await _create(client, {**MINIMAL, "user_id": "user-a", "org_id": "org-a"})
    b = await _create(client, {**MINIMAL, "user_id": "user-b", "org_id": "org-b"})
    assert await _ids(client, "user_id=user-a&org_id=org-a") == {a["id"]}
    assert await _ids(client, "org_id=org-b") == {b["id"]}                  # org scopes the result
    assert await _ids(client, "org_id=org-a&user_id=user-b") == set()       # user_id narrows further
    assert await _ids(client, "org_id=org-a") == {a["id"]}


# ── performed[x] Age / Range full datatype fidelity ───────────────────────────


async def test_performed_age_roundtrip(client):
    data = await _create(client, {
        **MINIMAL,
        "performed_age_value": 12,
        "performed_age_comparator": ">=",
        "performed_age_unit": "years",
        "performed_age_system": "http://unitsofmeasure.org",
        "performed_age_code": "a",
    })
    assert data["performed_age_comparator"] == ">="
    r = await client.get(f"{BASE}/{data['id']}", headers=FHIR_ACCEPT)
    assert r.json()["performedAge"] == {
        "value": 12.0, "comparator": ">=", "unit": "years",
        "system": "http://unitsofmeasure.org", "code": "a",
    }


async def test_performed_range_roundtrip(client):
    data = await _create(client, {
        **MINIMAL,
        "performed_range_low_value": 1, "performed_range_low_unit": "h",
        "performed_range_low_system": "http://unitsofmeasure.org", "performed_range_low_code": "h",
        "performed_range_high_value": 2,
    })
    assert data["performed_range_low_code"] == "h"
    r = await client.get(f"{BASE}/{data['id']}", headers=FHIR_ACCEPT)
    rng = r.json()["performedRange"]
    assert rng["low"] == {"value": 1.0, "unit": "h", "system": "http://unitsofmeasure.org", "code": "h"}
    assert rng["high"] == {"value": 2.0}


# ── PATCH replaces child lists ────────────────────────────────────────────────


async def test_patch_replaces_child_lists(client):
    data = await _create(client, FULL)
    pid = data["id"]
    assert len(data["performer"]) == 1 and len(data["reason_code"]) == 1 and len(data["note"]) == 1

    r = await client.patch(f"{BASE}/{pid}", json={
        "performer": [{"actor": "Practitioner/30002"}, {"actor": "Device/9"}],
        "note": [{"text": "replaced"}],
        "reason_reference": [{"reference": "Condition/120009"}],
    })
    assert r.status_code == 200, r.text
    body = r.json()
    assert [p["actor_id"] for p in body["performer"]] == [30002, 9]          # replaced, not appended
    assert [n["text"] for n in body["note"]] == ["replaced"]
    assert body["reason_reference"][0]["reference_id"] == 120009
    assert len(body["reason_code"]) == 1                                       # omitted list untouched
    assert body["identifier"][0]["value"] == "PROC-1"

    # [] clears one list, others stay
    r = await client.patch(f"{BASE}/{pid}", json={"reason_code": [], "note": None})
    body = r.json()
    assert body["reason_code"] == [] and body["note"] == [] and len(body["performer"]) == 2

    # persisted
    again = (await client.get(f"{BASE}/{pid}")).json()
    assert again["reason_code"] == [] and len(again["performer"]) == 2

    # validation on replaced lists
    assert (await client.patch(f"{BASE}/{pid}", json={"performer": [{"actor": "Condition/1"}]})).status_code == 422
    assert (await client.patch(f"{BASE}/{pid}", json={"note": [{"bogus": 1}]})).status_code == 400


async def test_search_requires_org_id(client):
    """org_id is mandatory on every search; user_id is optional."""
    await client.post(BASE + "/", json=MINIMAL)
    for url in (BASE + "/", f"{BASE}/?limit=5", BASE + "/?user_id=u-test"):
        assert (await client.get(url)).status_code == 400, url
    assert (await client.get(f"{BASE}/?org_id=")).status_code == 400                 # blank is not a tenant
    assert (await client.get(f"{BASE}/?org_id=org-test")).status_code == 200
    assert (await client.get(f"{BASE}/?org_id=org-test&user_id=nobody")).json()["total"] == 0
    assert (await client.get(f"{BASE}/?org_id=other-org")).json()["total"] == 0


async def test_encounter_reference_is_stored_not_looked_up(client):
    """References to other resources are type/id/display only — the Encounter does not have to exist."""
    data = await _create(client, {**MINIMAL, "encounter_id": 987654})
    assert (data["encounter_type"], data["encounter_id"]) == ("Encounter", 987654)
    fhir = (await client.get(f"{BASE}/{data['id']}", headers=FHIR_ACCEPT)).json()
    assert fhir["encounter"]["reference"] == "Encounter/987654"
    assert await _ids(client, "encounter=Encounter/987654") == {data["id"]}
    assert await _ids(client, "encounter=987654") == {data["id"]}
    assert await _ids(client, "encounter=1") == set()
    assert (await client.get(f"{BASE}/?{_with_org('encounter=Patient/1')}")).status_code == 422   # type still checked
    cleared = (await client.patch(f"{BASE}/{data['id']}", json={"encounter_id": None})).json()
    assert cleared["encounter_id"] is None
