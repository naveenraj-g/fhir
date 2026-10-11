"""Integration tests for /api/fhir/v1/flags endpoints."""
BASE = "/api/fhir/v1/flags"
FHIR_ACCEPT = {"Accept": "application/fhir+json"}


def _with_org(query: str) -> str:
    """Every search requires org_id (tenant scope) — add the default test org unless the query sets one."""
    if "org_id=" in query:
        return query
    return f"org_id=org-test&{query}" if query else "org_id=org-test"

MINIMAL = {
    "user_id": "u-test", "org_id": "org-test", "status": "active",
    "code_text": "Penicillin allergy", "subject": "Patient/10001",
}


def full_payload(**overrides) -> dict:
    payload = {
        **MINIMAL,
        "code_system": "http://snomed.info/sct", "code_code": "91936005", "code_display": "Allergy to penicillin",
        "subject_display": "John Doe",
        "period_start": "2024-03-15T00:00:00Z", "period_end": "2024-09-15T00:00:00Z",
        "author": "Practitioner/30001",
        "identifier": [{"system": "urn:flags", "value": "FLAG-1"}],
        "category": [
            {"coding_system": "http://terminology.hl7.org/CodeSystem/flag-category", "coding_code": "safety"},
            {"coding_code": "clinical", "text": "Clinical"},
        ],
    }
    payload.update(overrides)
    return payload


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
    assert data["id"] >= 390000
    assert (data["status"], data["subject_type"], data["subject_id"], data["code_text"]) == ("active", "Patient", 10001, "Penicillin allergy")
    assert data["identifier"] == [] and data["category"] == []


async def test_create_full_plain_and_fhir(client):
    data = await _create(client, full_payload())
    assert (data["author_type"], data["author_id"]) == ("Practitioner", 30001)
    assert [c["coding_code"] for c in data["category"]] == ["safety", "clinical"]
    assert data["identifier"][0]["value"] == "FLAG-1"

    r = await client.get(f"{BASE}/{data['id']}", headers=FHIR_ACCEPT)
    f = r.json()
    assert f["resourceType"] == "Flag" and f["id"] == str(data["id"]) and f["status"] == "active"
    assert f["subject"] == {"reference": "Patient/10001", "display": "John Doe"}
    assert f["code"]["coding"][0]["code"] == "91936005" and f["code"]["text"] == "Penicillin allergy"
    assert f["period"]["start"].startswith("2024-03-15") and f["period"]["end"].startswith("2024-09-15")
    assert f["author"] == {"reference": "Practitioner/30001"}
    assert [c["coding"][0]["code"] for c in f["category"]][0] == "safety"
    assert f["identifier"][0]["value"] == "FLAG-1"


async def test_validation_errors(client):
    assert (await client.post(BASE + "/", json={**MINIMAL, "bogus": 1})).status_code == 400
    assert (await client.post(BASE + "/", json={k: v for k, v in MINIMAL.items() if k != "subject"})).status_code == 400
    assert (await client.post(BASE + "/", json={k: v for k, v in MINIMAL.items() if k != "status"})).status_code == 400
    assert (await client.post(BASE + "/", json={k: v for k, v in MINIMAL.items() if k != "code_text"})).status_code == 400  # code 1..1
    assert (await client.post(BASE + "/", json={**MINIMAL, "status": "bogus"})).status_code == 400
    backwards = {**MINIMAL, "period_start": "2024-02-01T00:00:00Z", "period_end": "2024-01-01T00:00:00Z"}
    assert (await client.post(BASE + "/", json=backwards)).status_code == 400


async def test_reference_format_checks(client):
    for field, bad in (("subject", "Condition/1"), ("subject", "Patient/abc"), ("subject", "Patient"),
                       ("author", "Condition/1"), ("author", "RelatedPerson/1")):
        r = await client.post(BASE + "/", json={**MINIMAL, field: bad})
        assert r.status_code == 422, (field, bad, r.status_code)
    # every allowed subject type is accepted
    for t in ("Patient", "Location", "Group", "Organization", "Practitioner", "PlanDefinition", "Medication", "Procedure"):
        assert (await client.post(BASE + "/", json={**MINIMAL, "subject": f"{t}/5"})).status_code == 200, t


async def test_get_patch_delete(client):
    data = await _create(client, full_payload())
    fid = data["id"]
    assert (await client.get(f"{BASE}/{fid}")).json()["id"] == fid
    assert (await client.get(f"{BASE}/9999999")).status_code == 404

    # retire the flag
    r = await client.patch(f"{BASE}/{fid}", json={"status": "inactive", "period_end": "2024-12-01T00:00:00Z",
                                                    "subject": "Location/7", "author": "Device/3", "code_text": "Updated"})
    assert r.status_code == 200, r.text
    b = r.json()
    assert (b["status"], b["subject_type"], b["subject_id"], b["author_type"], b["code_text"]) == ("inactive", "Location", 7, "Device", "Updated")
    assert b["period_end"].startswith("2024-12-01") and len(b["category"]) == 2   # child lists untouched

    r = await client.patch(f"{BASE}/{fid}", json={"author": None})
    assert r.json()["author_id"] is None and r.json()["author_display"] is None

    for body in ({"status": None}, {"subject": None}, {"status": "bogus"}, {"bogus": 1}):
        assert (await client.patch(f"{BASE}/{fid}", json=body)).status_code == 400
    assert (await client.patch(f"{BASE}/{fid}", json={"subject": "Condition/1"})).status_code == 422
    assert (await client.patch(f"{BASE}/{fid}", json={"period_end": "2020-01-01T00:00:00Z"})).status_code == 422   # before start
    assert (await client.patch(f"{BASE}/9999999", json={"status": "active"})).status_code == 404

    assert (await client.delete(f"{BASE}/{fid}")).status_code == 204
    assert (await client.get(f"{BASE}/{fid}")).status_code == 404
    assert (await client.delete(f"{BASE}/{fid}")).status_code == 404


async def test_patch_replaces_child_lists(client):
    data = await _create(client, full_payload())
    fid = data["id"]
    r = await client.patch(f"{BASE}/{fid}", json={
        "category": [{"coding_code": "admin", "text": "Administrative"}],
        "identifier": [{"system": "urn:flags", "value": "FLAG-2"}, {"value": "FLAG-3"}],
    })
    assert r.status_code == 200, r.text
    b = r.json()
    assert [c["coding_code"] for c in b["category"]] == ["admin"]                    # replaced
    assert [i["value"] for i in b["identifier"]] == ["FLAG-2", "FLAG-3"]
    assert await _ids(client, "category=safety") == set()                            # old category gone
    assert await _ids(client, "category=admin") == {fid}

    r = await client.patch(f"{BASE}/{fid}", json={"category": []})                    # [] clears one list
    b = r.json()
    assert b["category"] == [] and len(b["identifier"]) == 2                         # other list untouched
    r = await client.patch(f"{BASE}/{fid}", json={"status": "inactive"})              # omitted lists untouched
    assert len(r.json()["identifier"]) == 2

    assert (await client.patch(f"{BASE}/{fid}", json={"identifier": [{"bogus": 1}]})).status_code == 400
    assert (await client.patch(f"{BASE}/{fid}", json={"identifier": [{"system": "x"}]})).status_code == 400  # value required


# ── list / search ─────────────────────────────────────────────────────────────


async def test_list_pagination_ordering_bundle(client):
    undated = await _create(client)
    dated = await _create(client, full_payload())
    for _ in range(2):
        await _create(client)
    assert len((await client.get(f"{BASE}/?org_id=org-test&limit=2")).json()["data"]) == 2
    ids = [d["id"] for d in (await client.get(BASE + "/?org_id=org-test")).json()["data"]]
    assert ids.index(dated["id"]) < ids.index(undated["id"])        # nulls last
    assert (await client.get(BASE + "/?org_id=org-test", headers=FHIR_ACCEPT)).json()["resourceType"] == "Bundle"


async def test_search_params(client):
    a = await _create(client, full_payload())
    b = await _create(client, {**MINIMAL, "status": "inactive", "subject": "Patient/10002", "code_code": "X1"})
    assert await _ids(client, f"_id={a['id']}") == {a["id"]}
    assert await _ids(client, "status=inactive") == {b["id"]}
    assert await _ids(client, "status=inactive,active") == {a["id"], b["id"]}
    assert (await client.get(BASE + "/?" + _with_org("status=bogus"))).status_code == 422
    assert await _ids(client, "identifier=urn:flags|FLAG-1") == {a["id"]}
    assert await _ids(client, "identifier=FLAG-1") == {a["id"]}
    assert await _ids(client, "category=http://terminology.hl7.org/CodeSystem/flag-category|safety") == {a["id"]}
    assert await _ids(client, "category=clinical") == {a["id"]}
    assert await _ids(client, "code=http://snomed.info/sct|91936005") == {a["id"]}
    assert await _ids(client, "code=X1") == {b["id"]}
    assert await _ids(client, "patient=Patient/10001") == {a["id"]}
    assert await _ids(client, "patient=10002") == {b["id"]}
    assert await _ids(client, "subject=Patient/10001") == {a["id"]}
    assert await _ids(client, "author=Practitioner/30001") == {a["id"]}
    assert await _ids(client, "author=Practitioner/39999") == set()
    assert a["id"] in await _ids(client, "_lastUpdated=ge2000-01-01")
    for bad in ("patient=Group/1", "subject=Condition/1", "author=Patient2/1", "date=notadate", "_id=x"):
        assert (await client.get(f"{BASE}/?{_with_org(bad)}")).status_code == 422, bad


async def test_search_date_period(client):
    closed = await _create(client, full_payload())                                             # 2024-03-15 .. 2024-09-15
    open_ended = await _create(client, {**MINIMAL, "period_start": "2025-01-01T00:00:00Z"})    # still active
    assert await _ids(client, "date=ap2024-06-01") == {closed["id"]}                          # inside the period
    assert await _ids(client, "date=ge2025-06-01") == {open_ended["id"]}                      # open end counts as ongoing
    assert await _ids(client, "date=lt2024-01-01") == set()
    assert await _ids(client, "date=gt2024-10-01") == {open_ended["id"]}
    assert await _ids(client, "date=ge2024-01-01&date=lt2024-04-01") == {closed["id"]}


async def test_search_scoped_by_org_and_optional_user(client):
    a = await _create(client, {**MINIMAL, "user_id": "user-a", "org_id": "org-a"})
    b = await _create(client, {**MINIMAL, "user_id": "user-b", "org_id": "org-b"})
    assert await _ids(client, "user_id=user-a&org_id=org-a") == {a["id"]}
    assert await _ids(client, "org_id=org-b") == {b["id"]}                  # org scopes the result
    assert await _ids(client, "org_id=org-a&user_id=user-b") == set()       # user_id narrows further
    assert await _ids(client, "org_id=org-a") == {a["id"]}


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
