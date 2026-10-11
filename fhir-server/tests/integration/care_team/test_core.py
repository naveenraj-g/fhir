"""Integration tests for /api/fhir/v1/care-teams endpoints."""

BASE = "/api/fhir/v1/care-teams"
FHIR_ACCEPT = {"Accept": "application/fhir+json"}


def _with_org(query: str) -> str:
    """Every search requires org_id (tenant scope) — add the default test org unless the query sets one."""
    if "org_id=" in query:
        return query
    return f"org_id=org-test&{query}" if query else "org_id=org-test"


MINIMAL = {"user_id": "u-test", "org_id": "org-test"}


def full_payload(**overrides) -> dict:
    payload = {
        **MINIMAL,
        "status": "active",
        "name": "Diabetes care team",
        "subject": "Patient/10001",
        "subject_display": "John Doe",
        "encounter": "Encounter/20001",
        "encounter_display": "Initial visit",
        "period_start": "2024-01-01T00:00:00Z",
        "period_end": "2024-12-31T00:00:00Z",
        "identifier": [{"system": "urn:teams", "value": "CT-1", "use": "official"}],
        "category": [{"coding_system": "http://loinc.org", "coding_code": "LA27976-2", "text": "Encounter-focused"}],
        "participant": [
            {
                "role": [
                    {"coding_system": "http://snomed.info/sct", "coding_code": "17561000", "text": "Cardiologist"},
                    {"coding_code": "lead"},
                ],
                "member": "Practitioner/30001",
                "member_display": "Dr. Smith",
                "on_behalf_of": "Organization/190001",
                "on_behalf_of_display": "Heart Clinic",
                "period_start": "2024-01-01T00:00:00Z",
            },
            {"role": [{"coding_code": "family"}], "member": "RelatedPerson/300001"},
        ],
        "reason_code": [{"coding_system": "http://snomed.info/sct", "coding_code": "44054006"}],
        "reason_reference": [{"reference": "Condition/120001", "reference_display": "Diabetes"}],
        "managing_organization": [{"reference": "Organization/190001"}],
        "telecom": [{"system": "phone", "value": "555-0100", "use": "work", "rank": 1}],
        "note": [
            {"text": "Weekly sync", "time": "2024-01-02T00:00:00Z", "author_string": "Nurse"},
            {"text": "Escalation path agreed", "author_reference": "Practitioner/30001"},
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


async def _patch(client, pid, body):
    return await client.patch(f"{BASE}/{pid}", json=body)


# ── CRUD ──────────────────────────────────────────────────────────────────────


async def test_create_empty_is_valid(client):
    # Every CareTeam element is 0..* / 0..1 in R4, so an empty team is accepted.
    data = await _create(client)
    assert data["id"] >= 420000
    assert data["status"] is None and data["participant"] == []


async def test_create_full_plain(client):
    data = await _create(client, full_payload())
    assert (data["status"], data["name"]) == ("active", "Diabetes care team")
    assert (data["subject_type"], data["subject_id"]) == ("Patient", 10001)
    assert (data["encounter_type"], data["encounter_id"]) == ("Encounter", 20001)
    p1, p2 = data["participant"]
    assert [r["coding_code"] for r in p1["role"]] == ["17561000", "lead"]
    assert (p1["member_type"], p1["member_id"]) == ("Practitioner", 30001)
    assert (p1["on_behalf_of_type"], p1["on_behalf_of_id"]) == ("Organization", 190001)
    assert p2["member_type"] == "RelatedPerson"
    assert data["reason_reference"][0]["reference_type"] == "Condition"
    assert data["managing_organization"][0]["reference_id"] == 190001
    assert data["telecom"][0]["system"] == "phone" and data["category"][0]["coding_code"] == "LA27976-2"
    assert data["note"][1]["author_reference_type"] == "Practitioner"


async def test_create_full_fhir(client):
    created = await _create(client, full_payload())
    body = (await client.get(f"{BASE}/{created['id']}", headers=FHIR_ACCEPT)).json()
    assert body["resourceType"] == "CareTeam" and body["id"] == str(created["id"])
    assert body["subject"]["reference"] == "Patient/10001" and body["encounter"]["reference"] == "Encounter/20001"
    assert body["participant"][0]["member"]["reference"] == "Practitioner/30001"
    assert body["participant"][0]["onBehalfOf"]["reference"] == "Organization/190001"
    assert len(body["participant"][0]["role"]) == 2
    assert body["reasonReference"][0]["reference"] == "Condition/120001"
    assert body["managingOrganization"][0]["reference"] == "Organization/190001"
    assert body["telecom"][0]["value"] == "555-0100"
    assert body["note"][0]["authorString"] == "Nurse" and body["note"][1]["authorReference"]["reference"] == "Practitioner/30001"
    assert body["period"]["start"].startswith("2024-01-01")


async def test_get_and_404(client):
    created = await _create(client)
    assert (await client.get(f"{BASE}/{created['id']}")).status_code == 200
    assert (await client.get(f"{BASE}/999999")).status_code == 404


async def test_delete_cascades(client):
    created = await _create(client, full_payload())
    assert (await client.delete(f"{BASE}/{created['id']}")).status_code == 204
    assert (await client.get(f"{BASE}/{created['id']}")).status_code == 404


# ── Validation ────────────────────────────────────────────────────────────────


async def test_invalid_status_and_extra_field(client):
    assert (await client.post(BASE + "/", json={**MINIMAL, "status": "bogus"})).status_code in (400, 422)
    assert (await client.post(BASE + "/", json={**MINIMAL, "bogus": 1})).status_code in (400, 422)


async def test_reference_validation(client):
    bad_bodies = [
        {"subject": "Practitioner/1"}, {"subject": "Patient/abc"}, {"subject": "nonsense"}, {"encounter": "Patient/1"},
        {"participant": [{"member": "Condition/1"}]},
        {"participant": [{"member": "Practitioner/x"}]},
        {"participant": [{"member": "Practitioner/1", "on_behalf_of": "Practitioner/2"}]},
        {"reason_reference": [{"reference": "Patient/1"}]},
        {"managing_organization": [{"reference": "Practitioner/1"}]},
        {"note": [{"text": "x", "author_reference": "bad"}]},
    ]
    for extra in bad_bodies:
        r = await client.post(BASE + "/", json={**MINIMAL, **extra})
        assert r.status_code in (400, 422), extra


async def test_reference_existence_not_checked(client):
    data = await _create(client, {**MINIMAL, "subject": "Patient/987654"})
    assert data["subject_id"] == 987654


async def test_ctm1_on_behalf_of_requires_practitioner(client):
    bad = {**MINIMAL, "participant": [{"member": "RelatedPerson/1", "on_behalf_of": "Organization/1"}]}
    assert (await client.post(BASE + "/", json=bad)).status_code in (400, 422)
    ok = {**MINIMAL, "participant": [{"member": "Practitioner/1", "on_behalf_of": "Organization/1"}]}
    assert (await client.post(BASE + "/", json=ok)).status_code == 200
    # no member -> ctm-1 cannot be violated (onBehalfOf.exists() implies member.resolve().iif(empty(), true, ...))
    free = {**MINIMAL, "participant": [{"on_behalf_of": "Organization/1"}]}
    assert (await client.post(BASE + "/", json=free)).status_code == 200


async def test_period_and_telecom_rules(client):
    r = await client.post(BASE + "/", json={**MINIMAL, "period_start": "2025-01-01T00:00:00Z", "period_end": "2024-01-01T00:00:00Z"})
    assert r.status_code in (400, 422)
    r = await client.post(BASE + "/", json={**MINIMAL, "participant": [
        {"member": "Patient/1", "period_start": "2025-01-01T00:00:00Z", "period_end": "2024-01-01T00:00:00Z"}]})
    assert r.status_code in (400, 422)
    assert (await client.post(BASE + "/", json={**MINIMAL, "telecom": [{"value": "555"}]})).status_code in (400, 422)  # cpt-2
    assert (await client.post(BASE + "/", json={**MINIMAL, "telecom": [{"system": "bogus", "value": "1"}]})).status_code in (400, 422)


async def test_note_author_exclusive(client):
    r = await client.post(BASE + "/", json={**MINIMAL, "note": [
        {"text": "x", "author_string": "a", "author_reference": "Practitioner/1"}]})
    assert r.status_code in (400, 422)


# ── PATCH ─────────────────────────────────────────────────────────────────────


async def test_patch_scalars_and_references(client):
    created = await _create(client, full_payload())
    r = await _patch(client, created["id"], {"status": "suspended", "name": "Renamed", "subject": "Group/5", "encounter": None, "updated_by": "u2"})
    assert r.status_code == 200, r.text
    body = r.json()
    assert (body["status"], body["name"], body["updated_by"]) == ("suspended", "Renamed", "u2")
    assert (body["subject_type"], body["subject_id"]) == ("Group", 5)
    assert body["encounter_id"] is None and body["encounter_type"] is None and body["encounter_display"] is None
    assert len(body["participant"]) == 2  # untouched
    assert (await _patch(client, created["id"], {"subject": "Practitioner/1"})).status_code in (400, 422)
    assert (await _patch(client, created["id"], {"status": "bogus"})).status_code in (400, 422)


async def test_patch_replace_participants(client):
    created = await _create(client, full_payload())
    r = await _patch(client, created["id"], {"participant": [
        {"role": [{"coding_code": "nurse"}], "member": "Practitioner/30009"}]})
    assert r.status_code == 200, r.text
    parts = r.json()["participant"]
    assert len(parts) == 1 and parts[0]["member_id"] == 30009 and parts[0]["role"][0]["coding_code"] == "nurse"
    assert parts[0]["on_behalf_of_id"] is None
    r = await _patch(client, created["id"], {"participant": []})
    assert r.json()["participant"] == []


async def test_patch_replace_other_lists(client):
    created = await _create(client, full_payload())
    r = await _patch(client, created["id"], {
        "identifier": [{"value": "X"}, {"value": "Y"}], "category": [], "reason_code": [{"coding_code": "z"}],
        "reason_reference": None, "managing_organization": [{"reference": "Organization/5"}],
        "telecom": [{"system": "email", "value": "a@b.c"}], "note": [{"text": "only"}],
    })
    assert r.status_code == 200, r.text
    body = r.json()
    assert [i["value"] for i in body["identifier"]] == ["X", "Y"]
    assert body["category"] == [] and body["reason_reference"] == []
    assert [c["coding_code"] for c in body["reason_code"]] == ["z"]
    assert body["managing_organization"][0]["reference_id"] == 5
    assert body["telecom"][0]["system"] == "email" and [n["text"] for n in body["note"]] == ["only"]
    assert len(body["participant"]) == 2  # untouched


async def test_patch_invalid_participant_rolls_back(client):
    created = await _create(client, full_payload())
    r = await _patch(client, created["id"], {"participant": [{"member": "RelatedPerson/1", "on_behalf_of": "Organization/1"}]})
    assert r.status_code in (400, 422)
    assert len((await client.get(f"{BASE}/{created['id']}")).json()["participant"]) == 2


async def test_patch_404(client):
    assert (await _patch(client, 999999, {"name": "x"})).status_code == 404


# ── Search ────────────────────────────────────────────────────────────────────


async def test_org_id_required(client):
    assert (await client.get(f"{BASE}/")).status_code in (400, 422)


async def test_org_scope_and_user_filter(client):
    a = await _create(client, {"user_id": "u1", "org_id": "org-a"})
    b = await _create(client, {"user_id": "u2", "org_id": "org-b"})
    assert a["id"] in await _ids(client, "org_id=org-a") and b["id"] not in await _ids(client, "org_id=org-a")
    assert a["id"] in await _ids(client, "org_id=org-a&user_id=u1")
    assert a["id"] not in await _ids(client, "org_id=org-a&user_id=zzz")


async def test_search_id_status_identifier_category(client):
    a = await _create(client, full_payload())
    b = await _create(client, {**MINIMAL, "status": "inactive"})
    assert await _ids(client, f"_id={a['id']}") == {a["id"]}
    assert b["id"] in await _ids(client, "status=inactive") and a["id"] not in await _ids(client, "status=inactive")
    assert a["id"] in await _ids(client, "status=inactive,active")
    assert a["id"] in await _ids(client, "identifier=urn:teams|CT-1")
    assert a["id"] not in await _ids(client, "identifier=urn:teams|NOPE")
    assert a["id"] in await _ids(client, "category=http://loinc.org|LA27976-2")
    assert a["id"] not in await _ids(client, "category=other")
    assert (await client.get(f"{BASE}/?{_with_org('status=bogus')}")).status_code in (400, 422)


async def test_search_references(client):
    a = await _create(client, full_payload())
    for q in ("subject=Patient/10001", "subject=10001", "patient=Patient/10001", "patient=10001",
              "encounter=Encounter/20001", "encounter=20001", "participant=Practitioner/30001",
              "participant=RelatedPerson/300001", "participant=300001"):
        assert a["id"] in await _ids(client, q), q
    for q in ("subject=Group/10001", "encounter=20002", "participant=Practitioner/9",
              "participant=Patient/30001"):
        assert a["id"] not in await _ids(client, q), q
    assert (await client.get(f"{BASE}/?{_with_org('subject=Practitioner/1')}")).status_code in (400, 422)
    assert (await client.get(f"{BASE}/?{_with_org('patient=Group/1')}")).status_code in (400, 422)
    assert (await client.get(f"{BASE}/?{_with_org('participant=Condition/1')}")).status_code in (400, 422)


async def test_search_dates(client):
    a = await _create(client, full_payload())
    assert a["id"] in await _ids(client, "date=ge2024-01-01&date=le2024-12-31")
    assert a["id"] in await _ids(client, "date=ap2024-06-01")
    assert a["id"] not in await _ids(client, "date=sa2025-01-01")
    assert a["id"] in await _ids(client, "_lastUpdated=ge2000-01-01")


async def test_pagination_bundle_and_order(client):
    for i in range(3):
        await _create(client, {"user_id": "u", "org_id": "org-page", "period_start": f"202{i}-01-01T00:00:00Z"})
    body = (await client.get(f"{BASE}/?org_id=org-page&limit=2&offset=0")).json()
    assert body["total"] == 3 and len(body["data"]) == 2 and body["limit"] == 2
    assert body["data"][0]["period_start"] > body["data"][1]["period_start"]  # newest first
    bundle = (await client.get(f"{BASE}/?org_id=org-page&limit=2", headers=FHIR_ACCEPT)).json()
    assert bundle["resourceType"] == "Bundle" and bundle["total"] == 3 and len(bundle["entry"]) == 2
