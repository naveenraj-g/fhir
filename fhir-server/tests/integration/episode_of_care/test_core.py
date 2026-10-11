"""Integration tests for /api/fhir/v1/episode-of-cares endpoints."""

BASE = "/api/fhir/v1/episode-of-cares"
FHIR_ACCEPT = {"Accept": "application/fhir+json"}


def _with_org(query: str) -> str:
    """Every search requires org_id (tenant scope) — add the default test org unless the query sets one."""
    if "org_id=" in query:
        return query
    return f"org_id=org-test&{query}" if query else "org_id=org-test"

MINIMAL = {
    "user_id": "u-test",
    "org_id": "org-test",
    "status": "active",
    "patient": "Patient/10001",
}

FULL = {
    "user_id": "u-test",
    "org_id": "org-test",
    "status": "active",
    "patient": "Patient/10001",
    "patient_display": "John Doe",
    "period_start": "2024-01-01T00:00:00Z",
    "period_end": "2024-12-31T23:59:59Z",
    "care_manager": "Practitioner/30001",
    "care_manager_display": "Dr. Smith",
    "identifiers": [
        {
            "system": "http://example.org/eoc",
            "value": "EOC-001",
            "use": "official",
        }
    ],
    "status_history": [
        {
            "status": "planned",
            "period_start": "2023-12-01T00:00:00Z",
            "period_end": "2024-01-01T00:00:00Z",
        }
    ],
    "types": [
        {
            "coding_system": "http://snomed.info/sct",
            "coding_code": "394602003",
            "coding_display": "Rehabilitation",
            "text": "Rehab care",
        }
    ],
    "diagnoses": [
        {
            "condition": "Condition/120001",
            "condition_display": "Diabetes",
            "role_system": "http://terminology.hl7.org/CodeSystem/diagnosis-role",
            "role_code": "CC",
            "role_display": "Chief complaint",
            "rank": 1,
        }
    ],
    "referral_requests": [
        {
            "reference": "ServiceRequest/80001",
            "reference_display": "Referral for rehab",
        }
    ],
    "team": [],
    "accounts": [],
}


# ── Helper ────────────────────────────────────────────────────────────────────


async def _create(client, payload=None) -> dict:
    resp = await client.post(BASE + "/", json=payload or MINIMAL)
    assert resp.status_code == 200, resp.text
    return resp.json()


# ── Create ────────────────────────────────────────────────────────────────────


async def test_create_minimal(client):
    data = await _create(client)
    assert isinstance(data["id"], int)
    assert data["status"] == "active"
    assert data["patient_type"] == "Patient"
    assert data["patient_id"] == 10001


async def test_create_full(client):
    r = await client.post(BASE + "/", json=FULL)
    assert r.status_code == 200, r.text
    data = r.json()

    assert data["status"] == "active"
    assert data["patient_type"] == "Patient"
    assert data["patient_id"] == 10001
    assert data["patient_display"] == "John Doe"
    assert data["care_manager_type"] == "Practitioner"
    assert data["care_manager_id"] == 30001
    assert data["care_manager_display"] == "Dr. Smith"
    assert data["period_start"] is not None
    assert data["period_end"] is not None

    assert len(data["identifiers"]) == 1
    assert data["identifiers"][0]["system"] == "http://example.org/eoc"
    assert data["identifiers"][0]["value"] == "EOC-001"

    assert len(data["status_history"]) == 1
    assert data["status_history"][0]["status"] == "planned"

    assert len(data["types"]) == 1
    assert data["types"][0]["coding_code"] == "394602003"
    assert data["types"][0]["text"] == "Rehab care"

    assert len(data["diagnoses"]) == 1
    diag = data["diagnoses"][0]
    assert diag["reference_type"] == "Condition"
    assert diag["reference_id"] == 120001
    assert diag["reference_display"] == "Diabetes"
    assert diag["role_code"] == "CC"
    assert diag["rank"] == 1

    assert len(data["referral_requests"]) == 1
    rr = data["referral_requests"][0]
    assert rr["reference_type"] == "ServiceRequest"
    assert rr["reference_id"] == 80001


async def test_create_fhir_format(client):
    r = await client.post(BASE + "/", json=FULL, headers=FHIR_ACCEPT)
    assert r.status_code == 200, r.text
    data = r.json()
    assert data["resourceType"] == "EpisodeOfCare"
    assert isinstance(data["id"], str)
    assert data["status"] == "active"
    assert data["patient"]["reference"] == "Patient/10001"
    assert data["careManager"]["reference"] == "Practitioner/30001"
    assert "period" in data
    assert len(data["identifier"]) == 1
    assert len(data["statusHistory"]) == 1
    assert data["statusHistory"][0]["status"] == "planned"
    assert len(data["type"]) == 1
    assert len(data["diagnosis"]) == 1
    assert data["diagnosis"][0]["condition"]["reference"] == "Condition/120001"
    assert data["diagnosis"][0]["rank"] == 1
    assert len(data["referralRequest"]) == 1
    assert data["referralRequest"][0]["reference"] == "ServiceRequest/80001"


async def test_create_with_care_team(client):
    payload = {**MINIMAL, "team": [{"reference": "CareTeam/1", "reference_display": "Primary Team"}]}
    r = await client.post(BASE + "/", json=payload)
    assert r.status_code == 200, r.text
    data = r.json()
    assert len(data["team"]) == 1
    assert data["team"][0]["reference_type"] == "CareTeam"
    assert data["team"][0]["reference_id"] == 1


async def test_create_with_account(client):
    payload = {**MINIMAL, "accounts": [{"reference": "Account/1"}]}
    r = await client.post(BASE + "/", json=payload)
    assert r.status_code == 200, r.text
    data = r.json()
    assert len(data["accounts"]) == 1
    assert data["accounts"][0]["reference_type"] == "Account"
    assert data["accounts"][0]["reference_id"] == 1


async def test_create_invalid_patient_type(client):
    r = await client.post(BASE + "/", json={**MINIMAL, "patient": "BadType/999"})
    assert r.status_code == 422


async def test_create_invalid_care_manager_type(client):
    r = await client.post(BASE + "/", json={**MINIMAL, "care_manager": "BadType/999"})
    assert r.status_code == 422


async def test_create_invalid_diagnosis_type(client):
    payload = {**MINIMAL, "diagnoses": [{"condition": "BadType/999"}]}
    r = await client.post(BASE + "/", json=payload)
    assert r.status_code == 422


async def test_create_invalid_referral_request_type(client):
    payload = {**MINIMAL, "referral_requests": [{"reference": "BadType/999"}]}
    r = await client.post(BASE + "/", json=payload)
    assert r.status_code == 422


async def test_create_with_practitioner_role_care_manager(client):
    payload = {**MINIMAL, "care_manager": "PractitionerRole/140001"}
    r = await client.post(BASE + "/", json=payload)
    assert r.status_code == 200, r.text
    data = r.json()
    assert data["care_manager_type"] == "PractitionerRole"
    assert data["care_manager_id"] == 140001


# ── Get ───────────────────────────────────────────────────────────────────────


async def test_get_episode_of_care(client):
    data = await _create(client)
    eoc_id = data["id"]
    r = await client.get(f"{BASE}/{eoc_id}")
    assert r.status_code == 200
    assert r.json()["id"] == eoc_id


async def test_get_episode_of_care_fhir(client):
    data = await _create(client)
    eoc_id = data["id"]
    r = await client.get(f"{BASE}/{eoc_id}", headers=FHIR_ACCEPT)
    assert r.status_code == 200
    d = r.json()
    assert d["resourceType"] == "EpisodeOfCare"
    assert d["id"] == str(eoc_id)


async def test_get_not_found(client):
    r = await client.get(f"{BASE}/9999999")
    assert r.status_code == 404


# ── List ──────────────────────────────────────────────────────────────────────


async def test_list_episode_of_cares(client):
    await _create(client)
    r = await client.get(BASE + "/?org_id=org-test")
    assert r.status_code == 200
    data = r.json()
    assert "total" in data
    assert "data" in data
    assert data["total"] >= 1


async def test_list_fhir_format(client):
    await _create(client)
    r = await client.get(BASE + "/?org_id=org-test", headers=FHIR_ACCEPT)
    assert r.status_code == 200
    data = r.json()
    assert data["resourceType"] == "Bundle"
    assert data["type"] == "searchset"


async def test_list_pagination(client):
    for _ in range(3):
        await _create(client)
    r = await client.get(f"{BASE}/?org_id=org-test&limit=2&offset=0")
    assert r.status_code == 200
    data = r.json()
    assert len(data["data"]) <= 2
    assert data["limit"] == 2
    assert data["offset"] == 0


async def test_list_filter_by_status(client):
    await _create(client, {**MINIMAL, "status": "active"})
    await _create(client, {**MINIMAL, "status": "finished"})
    r = await client.get(f"{BASE}/?org_id=org-test&status=active")
    assert r.status_code == 200
    data = r.json()
    for item in data["data"]:
        assert item["status"] == "active"


async def test_list_filter_by_patient_id(client):
    await _create(client, {**MINIMAL, "patient": "Patient/10001"})
    await _create(client, {**MINIMAL, "patient": "Patient/10002"})
    r = await client.get(f"{BASE}/?org_id=org-test&patient_id=10001")
    assert r.status_code == 200
    data = r.json()
    for item in data["data"]:
        assert item["patient_id"] == 10001


# ── Patch ─────────────────────────────────────────────────────────────────────


async def test_patch_status(client):
    data = await _create(client)
    eoc_id = data["id"]
    r = await client.patch(f"{BASE}/{eoc_id}", json={"status": "finished"})
    assert r.status_code == 200
    assert r.json()["status"] == "finished"


async def test_patch_care_manager(client):
    data = await _create(client)
    eoc_id = data["id"]
    r = await client.patch(f"{BASE}/{eoc_id}", json={"care_manager": "Practitioner/30002"})
    assert r.status_code == 200
    d = r.json()
    assert d["care_manager_type"] == "Practitioner"
    assert d["care_manager_id"] == 30002


async def test_patch_diagnoses(client):
    data = await _create(client)
    eoc_id = data["id"]
    r = await client.patch(f"{BASE}/{eoc_id}", json={
        "diagnoses": [
            {"condition": "Condition/120002", "rank": 2}
        ]
    })
    assert r.status_code == 200
    d = r.json()
    assert len(d["diagnoses"]) == 1
    assert d["diagnoses"][0]["reference_id"] == 120002
    assert d["diagnoses"][0]["rank"] == 2


async def test_patch_identifiers(client):
    data = await _create(client)
    eoc_id = data["id"]
    r = await client.patch(f"{BASE}/{eoc_id}", json={
        "identifiers": [{"system": "http://example.org", "value": "NEW-001"}]
    })
    assert r.status_code == 200
    d = r.json()
    assert len(d["identifiers"]) == 1
    assert d["identifiers"][0]["value"] == "NEW-001"


async def test_patch_status_history(client):
    data = await _create(client)
    eoc_id = data["id"]
    r = await client.patch(f"{BASE}/{eoc_id}", json={
        "status_history": [
            {"status": "active", "period_start": "2024-01-01T00:00:00Z"}
        ]
    })
    assert r.status_code == 200
    d = r.json()
    assert len(d["status_history"]) == 1
    assert d["status_history"][0]["status"] == "active"


async def test_patch_not_found(client):
    r = await client.patch(f"{BASE}/9999999", json={"status": "finished"})
    assert r.status_code == 404


# ── Delete ────────────────────────────────────────────────────────────────────


async def test_delete_episode_of_care(client):
    data = await _create(client)
    eoc_id = data["id"]
    r = await client.delete(f"{BASE}/{eoc_id}")
    assert r.status_code == 204
    r2 = await client.get(f"{BASE}/{eoc_id}")
    assert r2.status_code == 404


async def test_delete_not_found(client):
    r = await client.delete(f"{BASE}/9999999")
    assert r.status_code == 404


# ── R4 required elements / validation ─────────────────────────────────────────


async def test_required_and_validated_fields(client):
    assert (await client.post(BASE + "/", json={k: v for k, v in MINIMAL.items() if k != "patient"})).status_code == 400
    assert (await client.post(BASE + "/", json={k: v for k, v in MINIMAL.items() if k != "status"})).status_code == 400
    assert (await client.post(BASE + "/", json={**MINIMAL, "status": "bogus"})).status_code == 400
    assert (await client.post(BASE + "/", json={**MINIMAL, "bogus": 1})).status_code == 400
    backwards = {**MINIMAL, "period_start": "2024-02-01T00:00:00Z", "period_end": "2024-01-01T00:00:00Z"}
    assert (await client.post(BASE + "/", json=backwards)).status_code == 400
    bad_history = [{"status": "bogus", "period_start": "2024-01-01T00:00:00Z"}]
    assert (await client.post(BASE + "/", json={**MINIMAL, "status_history": bad_history})).status_code == 400
    no_period = [{"status": "planned"}]
    assert (await client.post(BASE + "/", json={**MINIMAL, "status_history": no_period})).status_code == 400
    assert (await client.post(BASE + "/", json={**MINIMAL, "diagnoses": [{"rank": 1}]})).status_code == 400   # condition 1..1


# ── PATCH: null clears, lists replace ─────────────────────────────────────────


async def test_patch_clears_and_validates(client):
    created = await _create(client, {**FULL})
    eid = created["id"]
    r = await client.patch(f"{BASE}/{eid}", json={"care_manager": None})
    assert r.status_code == 200, r.text
    assert r.json().get("care_manager_id") is None and r.json().get("care_manager_display") is None
    for body in ({"status": None}, {"patient": None}, {"status": "bogus"}, {"bogus": 1}):
        assert (await client.patch(f"{BASE}/{eid}", json=body)).status_code == 400
    assert (await client.patch(f"{BASE}/{eid}", json={"patient": "Practitioner/1"})).status_code == 422
    assert (await client.patch(f"{BASE}/{eid}", json={"care_manager": "Patient/1"})).status_code == 422
    assert (await client.patch(f"{BASE}/{eid}", json={"diagnoses": [{"condition": "Patient/1"}]})).status_code == 422


async def test_patch_replaces_and_clears_child_lists(client):
    created = await _create(client, {**FULL})
    eid = created["id"]
    r = await client.patch(f"{BASE}/{eid}", json={
        "types": [{"coding_code": "new-type"}],
        "identifiers": [{"system": "urn:e", "value": "E-2"}, {"value": "E-3"}],
        "diagnoses": None,
        "status_history": [],
    })
    assert r.status_code == 200, r.text
    b = r.json()
    assert [t["coding_code"] for t in b["types"]] == ["new-type"]
    assert [i["value"] for i in b["identifiers"]] == ["E-2", "E-3"]
    assert not b.get("diagnoses") and not b.get("status_history")                # null / [] cleared them
    assert len(b["referral_requests"]) == 1                                      # omitted list untouched


# ── FHIR R4 search parameters ─────────────────────────────────────────────────


async def _ids(client, query: str) -> set:
    r = await client.get(f"{BASE}/?{_with_org(query)}")
    assert r.status_code == 200, r.text
    return {d["id"] for d in r.json()["data"]}


async def test_search_params(client):
    a = await _create(client, {**FULL, "identifiers": [{"system": "urn:e", "value": "EOC-1"}]})
    b = await _create(client, {**MINIMAL, "status": "finished", "patient": "Patient/10002",
                               "period_start": "2022-01-01T00:00:00Z", "period_end": "2022-06-01T00:00:00Z"})
    assert await _ids(client, f"_id={a['id']}") == {a["id"]}
    assert await _ids(client, "status=finished") == {b["id"]}
    assert await _ids(client, "status=finished,active") == {a["id"], b["id"]}
    assert (await client.get(f"{BASE}/?org_id=org-test&status=bogus")).status_code == 422
    assert await _ids(client, "identifier=urn:e|EOC-1") == {a["id"]}
    assert await _ids(client, "type=http://snomed.info/sct|394602003") == {a["id"]}
    assert await _ids(client, "type=394602003") == {a["id"]}
    assert await _ids(client, "patient=Patient/10001") == {a["id"]}
    assert await _ids(client, "patient=10002") == {b["id"]}
    assert await _ids(client, "patient_id=10001") == {a["id"]}
    assert await _ids(client, "care-manager=Practitioner/30001") == {a["id"]}
    assert await _ids(client, "condition=Condition/120001") == {a["id"]}
    assert await _ids(client, "incoming-referral=ServiceRequest/80001") == {a["id"]}
    assert await _ids(client, "date=ap2024-06-01") == {a["id"]}      # overlap; plain eq needs the period inside the day
    assert await _ids(client, "date=lt2023-01-01") == {b["id"]}
    assert await _ids(client, "date=ge2024-01-01&date=lt2025-01-01") == {a["id"]}
    assert a["id"] in await _ids(client, "_lastUpdated=ge2000-01-01")
    for bad in ("patient=Group/1", "care-manager=Patient/1", "condition=Patient/1", "date=notadate", "_id=x"):
        assert (await client.get(f"{BASE}/?{_with_org(bad)}")).status_code == 422, bad


async def test_managing_organization_is_stored_not_looked_up(client):
    """managingOrganization is type/id/display only — the Organization does not have to exist."""
    with_org = await _create(client, {**MINIMAL, "managing_organization": "Organization/190777",
                                      "managing_organization_display": "Gen Hospital"})
    without = await _create(client)
    fhir = (await client.get(f"{BASE}/{with_org['id']}", headers=FHIR_ACCEPT)).json()
    assert fhir["managingOrganization"] == {"reference": "Organization/190777", "display": "Gen Hospital"}
    assert with_org["managing_organization_id"] == 190777
    assert await _ids(client, "organization=Organization/190777") == {with_org["id"]}
    assert await _ids(client, "organization=190777") == {with_org["id"]}
    assert without["id"] not in await _ids(client, "organization=190777")
    assert (await client.get(f"{BASE}/?org_id=org-test&organization=Patient/1")).status_code == 422
    assert (await client.post(BASE + "/", json={**MINIMAL, "managing_organization": "Patient/1"})).status_code == 422
    cleared = (await client.patch(f"{BASE}/{with_org['id']}", json={"managing_organization": None})).json()
    assert cleared.get("managing_organization_id") is None


async def test_search_scoped_by_org_and_optional_user(client):
    a = await _create(client, {**MINIMAL, "user_id": "user-a", "org_id": "org-a"})
    b = await _create(client, {**MINIMAL, "user_id": "user-b", "org_id": "org-b"})
    assert await _ids(client, "org_id=org-a") == {a["id"]}
    assert await _ids(client, "org_id=org-b") == {b["id"]}
    assert await _ids(client, "org_id=org-a&user_id=user-a") == {a["id"]}
    assert await _ids(client, "org_id=org-a&user_id=user-b") == set()


async def test_search_requires_org_id(client):
    await _create(client)
    for url in (BASE + "/", f"{BASE}/?limit=5", BASE + "/?user_id=u-test", BASE + "/?status=active"):
        assert (await client.get(url)).status_code == 400, url
    assert (await client.get(f"{BASE}/?org_id=")).status_code == 400
    assert (await client.get(f"{BASE}/?org_id=org-test")).status_code == 200


async def test_list_ordering_nulls_last(client):
    undated = await _create(client)
    dated = await _create(client, {**MINIMAL, "period_start": "2024-01-01T00:00:00Z"})
    ids = [d["id"] for d in (await client.get(f"{BASE}/?org_id=org-test")).json()["data"]]
    assert ids.index(dated["id"]) < ids.index(undated["id"])
