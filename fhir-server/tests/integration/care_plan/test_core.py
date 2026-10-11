"""Integration tests for /api/fhir/v1/care-plans endpoints."""

BASE = "/api/fhir/v1/care-plans"
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
    "intent": "plan",
    "subject": "Patient/10001",
}


def full_payload(**overrides) -> dict:
    payload = {
        **MINIMAL,
        "title": "Diabetes Management Plan",
        "description": "Comprehensive diabetes care plan",
        "subject_display": "John Doe",
        "encounter": "Encounter/20001",
        "encounter_display": "Initial Visit",
        "period_start": "2024-01-01T00:00:00Z",
        "period_end": "2024-12-31T23:59:59Z",
        "created": "2024-01-01T08:00:00Z",
        "author": "Practitioner/30001",
        "author_display": "Dr. Smith",
        "instantiates_canonical": "http://example.org/fhir/PlanDefinition/diabetes,http://example.org/fhir/Questionnaire/intake",
        "instantiates_uri": "http://example.org/protocols/diabetes",
        "identifiers": [{"system": "http://hospital.org/care-plans", "value": "CP-001", "use": "official"}],
        "based_on": [{"reference": "CarePlan/290001", "reference_display": "Parent Plan"}],
        "replaces": [{"reference": "CarePlan/290002"}],
        "part_of": [{"reference": "CarePlan/290003"}],
        "categories": [{"coding_system": "http://snomed.info/sct", "coding_code": "736055001", "text": "Diabetes Plan"}],
        "contributors": [{"reference": "Practitioner/30002", "reference_display": "Dr. Jones"}],
        "care_teams": [{"reference": "CareTeam/1"}],
        "addresses": [{"reference": "Condition/120001", "reference_display": "Type 2 Diabetes"}],
        "supporting_info": [{"reference": "Observation/160001"}],
        "goals": [{"reference": "Goal/1"}],
        "notes": [{"text": "Patient is motivated.", "time": "2024-01-01T09:00:00Z", "author_string": "Dr. Smith"}],
        "activities": [
            {  # activity.reference variant (no detail — cpl-3)
                "reference": "ServiceRequest/80001",
                "reference_display": "Lab order",
                "outcome_codeable_concepts": [{"coding_system": "http://snomed.info/sct", "coding_code": "415068001"}],
                "outcome_references": [{"reference": "Observation/160002"}],
                "progress": [{"text": "Initial assessment completed.", "author_string": "Nurse"}],
            },
            {  # activity.detail variant
                "detail_kind": "ServiceRequest",
                "detail_code_system": "http://snomed.info/sct",
                "detail_code_code": "43396009",
                "detail_status": "scheduled",
                "detail_do_not_perform": False,
                "detail_description": "Check HbA1c every 3 months",
                "detail_scheduled_period_start": "2024-01-15T08:00:00Z",
                "detail_scheduled_period_end": "2024-01-15T12:00:00Z",
                "detail_location": "Location/230001",
                "detail_product_reference": "Medication/250001",
                "detail_daily_amount_value": 2,
                "detail_daily_amount_unit": "tablet",
                "detail_quantity_value": 30,
                "detail_reason_codes": [{"coding_code": "44054006"}],
                "detail_reason_references": [{"reference": "Condition/120001"}],
                "detail_goals": [{"reference": "Goal/1"}],
                "detail_performers": [{"reference": "Practitioner/30001", "reference_display": "Dr. Smith"}],
            },
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


async def test_create_minimal(client):
    data = await _create(client)
    assert data["id"] >= 290000
    assert (data["status"], data["intent"], data["subject_type"], data["subject_id"]) == ("active", "plan", "Patient", 10001)


async def test_create_full_plain(client):
    data = await _create(client, full_payload())
    assert (data["encounter_type"], data["encounter_id"]) == ("Encounter", 20001)
    assert (data["author_type"], data["author_id"]) == ("Practitioner", 30001)
    assert len(data["identifiers"]) == 1 and len(data["notes"]) == 1 and len(data["goals"]) == 1
    assert data["based_on"][0]["reference_id"] == 290001
    ref_act, detail_act = data["activities"]
    assert ref_act["reference_type"] == "ServiceRequest" and ref_act["reference_id"] == 80001
    assert ref_act["outcome_references"][0]["reference_id"] == 160002
    assert ref_act["progress"][0]["text"] == "Initial assessment completed."
    assert detail_act["detail_status"] == "scheduled" and detail_act["detail_kind"] == "ServiceRequest"
    assert detail_act["detail_location_id"] == 230001 and detail_act["detail_product_reference_type"] == "Medication"
    assert detail_act["detail_performers"][0]["reference_type"] == "Practitioner"


async def test_create_full_fhir(client):
    created = await _create(client, full_payload())
    r = await client.get(f"{BASE}/{created['id']}", headers=FHIR_ACCEPT)
    body = r.json()
    assert body["resourceType"] == "CarePlan" and body["id"] == str(created["id"])
    assert body["subject"]["reference"] == "Patient/10001"
    assert body["instantiatesCanonical"] == [
        "http://example.org/fhir/PlanDefinition/diabetes", "http://example.org/fhir/Questionnaire/intake"]
    assert body["activity"][0]["reference"]["reference"] == "ServiceRequest/80001"
    detail = body["activity"][1]["detail"]
    assert detail["status"] == "scheduled" and detail["location"]["reference"] == "Location/230001"
    assert detail["productReference"]["reference"] == "Medication/250001"
    assert detail["performer"][0]["reference"] == "Practitioner/30001"
    assert detail["scheduledPeriod"]["start"].startswith("2024-01-15")


async def test_create_timing_with_bounds(client):
    payload = full_payload(activities=[{
        "detail_status": "in-progress",
        "detail_scheduled_timing_event": "2024-01-01T08:00:00Z,2024-02-01T08:00:00Z",
        "detail_scheduled_timing_repeat_frequency": 1,
        "detail_scheduled_timing_repeat_period": 7.0,
        "detail_scheduled_timing_repeat_period_unit": "d",
        "detail_scheduled_timing_repeat_bounds_duration_value": 3,
        "detail_scheduled_timing_repeat_bounds_duration_unit": "mo",
    }])
    created = await _create(client, payload)
    act = created["activities"][0]
    assert act["detail_scheduled_timing_repeat_bounds_duration_value"] == 3
    body = (await client.get(f"{BASE}/{created['id']}", headers=FHIR_ACCEPT)).json()
    timing = body["activity"][0]["detail"]["scheduledTiming"]
    assert timing["repeat"]["boundsDuration"] == {"value": 3.0, "unit": "mo"}
    assert len(timing["event"]) == 2

    payload = full_payload(activities=[{
        "detail_status": "scheduled",
        "detail_scheduled_timing_repeat_bounds_range_low_value": 1,
        "detail_scheduled_timing_repeat_bounds_range_high_value": 4,
        "detail_scheduled_timing_repeat_bounds_range_high_unit": "wk",
    }])
    created = await _create(client, payload)
    body = (await client.get(f"{BASE}/{created['id']}", headers=FHIR_ACCEPT)).json()
    assert body["activity"][0]["detail"]["scheduledTiming"]["repeat"]["boundsRange"]["high"] == {"value": 4.0, "unit": "wk"}


async def test_get_and_404(client):
    created = await _create(client)
    assert (await client.get(f"{BASE}/{created['id']}")).status_code == 200
    assert (await client.get(f"{BASE}/999999")).status_code == 404


async def test_delete_cascades(client):
    created = await _create(client, full_payload())
    assert (await client.delete(f"{BASE}/{created['id']}")).status_code == 204
    assert (await client.get(f"{BASE}/{created['id']}")).status_code == 404
    assert (await client.delete(f"{BASE}/{created['id']}")).status_code == 404


# ── Validation (R4 cardinality, cpl-3, choice types, references) ──────────────


async def test_required_fields(client):
    for missing in ("status", "intent", "subject"):
        body = {k: v for k, v in MINIMAL.items() if k != missing}
        assert (await client.post(BASE + "/", json=body)).status_code in (400, 422), missing


async def test_invalid_enums(client):
    assert (await client.post(BASE + "/", json={**MINIMAL, "status": "bad"})).status_code in (400, 422)
    assert (await client.post(BASE + "/", json={**MINIMAL, "intent": "bad"})).status_code in (400, 422)
    bad = full_payload(activities=[{"detail_status": "bad"}])
    assert (await client.post(BASE + "/", json=bad)).status_code in (400, 422)
    bad = full_payload(activities=[{"detail_status": "scheduled", "detail_kind": "Patient"}])
    assert (await client.post(BASE + "/", json=bad)).status_code in (400, 422)


async def test_reference_validation(client):
    for field, value in (("subject", "Practitioner/1"), ("subject", "Patient/abc"), ("subject", "nonsense"),
                         ("author", "Condition/1"), ("encounter", "Patient/1")):
        r = await client.post(BASE + "/", json={**MINIMAL, field: value})
        assert r.status_code in (400, 422), (field, value)
    r = await client.post(BASE + "/", json=full_payload(activities=[{"reference": "Patient/1"}]))
    assert r.status_code in (400, 422)
    r = await client.post(BASE + "/", json=full_payload(care_teams=[{"reference": "Patient/1"}]))
    assert r.status_code in (400, 422)


async def test_reference_existence_not_checked(client):
    data = await _create(client, {**MINIMAL, "subject": "Patient/987654"})
    assert data["subject_id"] == 987654


async def test_cpl3_reference_xor_detail(client):
    bad = full_payload(activities=[{"reference": "Task/1", "detail_status": "scheduled"}])
    assert (await client.post(BASE + "/", json=bad)).status_code in (400, 422)


async def test_detail_status_required_with_detail(client):
    bad = full_payload(activities=[{"detail_description": "no status"}])
    assert (await client.post(BASE + "/", json=bad)).status_code in (400, 422)


async def test_choice_types_exclusive(client):
    both = full_payload(activities=[{
        "detail_status": "scheduled", "detail_scheduled_string": "weekly",
        "detail_scheduled_period_start": "2024-01-01T00:00:00Z"}])
    assert (await client.post(BASE + "/", json=both)).status_code in (400, 422)
    product = full_payload(activities=[{
        "detail_status": "scheduled", "detail_product_reference": "Medication/1", "detail_product_codeable_concept_code": "x"}])
    assert (await client.post(BASE + "/", json=product)).status_code in (400, 422)
    bounds = full_payload(activities=[{
        "detail_status": "scheduled",
        "detail_scheduled_timing_repeat_bounds_duration_value": 1,
        "detail_scheduled_timing_repeat_bounds_start": "2024-01-01T00:00:00Z"}])
    assert (await client.post(BASE + "/", json=bounds)).status_code in (400, 422)


async def test_period_order_and_extra_field(client):
    r = await client.post(BASE + "/", json={**MINIMAL, "period_start": "2025-01-01T00:00:00Z", "period_end": "2024-01-01T00:00:00Z"})
    assert r.status_code in (400, 422)
    assert (await client.post(BASE + "/", json={**MINIMAL, "bogus": 1})).status_code in (400, 422)


# ── PATCH ─────────────────────────────────────────────────────────────────────


async def test_patch_scalars(client):
    created = await _create(client, full_payload())
    r = await _patch(client, created["id"], {"status": "completed", "intent": "order", "title": "New", "updated_by": "u2"})
    assert r.status_code == 200, r.text
    body = r.json()
    assert (body["status"], body["intent"], body["title"], body["updated_by"]) == ("completed", "order", "New", "u2")
    assert len(body["activities"]) == 2 and len(body["goals"]) == 1  # untouched


async def test_patch_required_not_null(client):
    created = await _create(client)
    for field in ("status", "intent", "subject"):
        assert (await _patch(client, created["id"], {field: None})).status_code in (400, 422), field
    assert (await _patch(client, created["id"], {"status": "bogus"})).status_code in (400, 422)


async def test_patch_references(client):
    created = await _create(client, full_payload())
    body = (await _patch(client, created["id"], {"subject": "Group/5", "encounter": None, "author": "Organization/190001"})).json()
    assert (body["subject_type"], body["subject_id"]) == ("Group", 5)
    assert body.get("encounter_id") is None and body.get("encounter_type") is None
    assert (body["author_type"], body["author_id"]) == ("Organization", 190001)
    assert (await _patch(client, created["id"], {"subject": "Condition/1"})).status_code in (400, 422)


async def test_patch_replace_lists(client):
    created = await _create(client, full_payload())
    r = await _patch(client, created["id"], {
        "identifiers": [{"value": "X"}, {"value": "Y"}],
        "categories": [], "goals": [{"reference": "Goal/9"}], "based_on": [{"reference": "CarePlan/1"}],
        "replaces": None, "notes": [{"text": "new"}],
        "contributors": [{"reference": "Patient/10001"}], "supporting_info": [{"reference": "Task/3"}],
    })
    assert r.status_code == 200, r.text
    body = r.json()
    assert [i["value"] for i in body["identifiers"]] == ["X", "Y"]
    assert not body.get("categories") and not body.get("replaces")
    assert [g["reference_id"] for g in body["goals"]] == [9]
    assert [n["text"] for n in body["notes"]] == ["new"]
    assert body["part_of"][0]["reference_id"] == 290003  # untouched
    assert body["care_teams"][0]["reference_id"] == 1  # untouched
    assert body["contributors"][0]["reference_type"] == "Patient"


async def test_patch_replace_activities(client):
    created = await _create(client, full_payload())
    r = await _patch(client, created["id"], {"activities": [
        {"detail_status": "in-progress", "detail_description": "only one", "detail_performers": [{"reference": "CareTeam/2"}]}]})
    assert r.status_code == 200, r.text
    acts = r.json()["activities"]
    assert len(acts) == 1 and acts[0]["detail_status"] == "in-progress"
    assert acts[0]["detail_performers"][0]["reference_type"] == "CareTeam"
    r = await _patch(client, created["id"], {"activities": []})
    assert not r.json().get("activities")


async def test_patch_invalid_activity_rejected(client):
    created = await _create(client, full_payload())
    r = await _patch(client, created["id"], {"activities": [{"reference": "Task/1", "detail_status": "scheduled"}]})
    assert r.status_code in (400, 422)
    assert len((await client.get(f"{BASE}/{created['id']}")).json()["activities"]) == 2  # unchanged


async def test_patch_404(client):
    assert (await _patch(client, 999999, {"title": "x"})).status_code == 404


# ── Search ────────────────────────────────────────────────────────────────────


async def test_org_id_required(client):
    assert (await client.get(f"{BASE}/")).status_code in (400, 422)


async def test_org_scope_and_user_filter(client):
    a = await _create(client, {**MINIMAL, "org_id": "org-a", "user_id": "u1"})
    b = await _create(client, {**MINIMAL, "org_id": "org-b", "user_id": "u2"})
    assert a["id"] in await _ids(client, "org_id=org-a") and b["id"] not in await _ids(client, "org_id=org-a")
    assert a["id"] in await _ids(client, "org_id=org-a&user_id=u1")
    assert a["id"] not in await _ids(client, "org_id=org-a&user_id=zzz")


async def test_search_id_status_intent_identifier_category(client):
    a = await _create(client, full_payload())
    b = await _create(client, {**MINIMAL, "status": "draft", "intent": "order"})
    assert await _ids(client, f"_id={a['id']}") == {a["id"]}
    assert b["id"] in await _ids(client, "status=draft") and a["id"] not in await _ids(client, "status=draft")
    assert b["id"] in await _ids(client, "intent=order") and a["id"] not in await _ids(client, "intent=order")
    assert a["id"] in await _ids(client, "status=draft,active")
    assert a["id"] in await _ids(client, "identifier=http://hospital.org/care-plans|CP-001")
    assert a["id"] not in await _ids(client, "identifier=http://hospital.org/care-plans|NOPE")
    assert a["id"] in await _ids(client, "category=http://snomed.info/sct|736055001")
    assert a["id"] not in await _ids(client, "category=other")
    for bad in ("status=bogus", "intent=bogus"):
        assert (await client.get(f"{BASE}/?{_with_org(bad)}")).status_code in (400, 422)


async def test_search_references(client):
    a = await _create(client, full_payload())
    for q in ("subject=Patient/10001", "subject=10001", "patient=Patient/10001", "patient=10001",
              "encounter=Encounter/20001", "based-on=CarePlan/290001", "replaces=290002", "part-of=CarePlan/290003",
              "care-team=CareTeam/1", "condition=Condition/120001", "goal=Goal/1",
              "activity-reference=ServiceRequest/80001", "performer=Practitioner/30001"):
        assert a["id"] in await _ids(client, q), q
    for q in ("subject=Group/10001", "patient=Group/10001", "based-on=CarePlan/9", "activity-reference=Task/80001",
              "performer=Practitioner/9", "care-team=CareTeam/9"):
        assert a["id"] not in await _ids(client, q), q
    assert (await client.get(f"{BASE}/?{_with_org('subject=Practitioner/1')}")).status_code in (400, 422)


async def test_search_activity_code_and_instantiates(client):
    a = await _create(client, full_payload())
    assert a["id"] in await _ids(client, "activity-code=http://snomed.info/sct|43396009")
    assert a["id"] in await _ids(client, "activity-code=43396009")
    assert a["id"] not in await _ids(client, "activity-code=999")
    assert a["id"] in await _ids(client, "instantiates-canonical=http://example.org/fhir/Questionnaire/intake")
    assert a["id"] in await _ids(client, "instantiates-canonical=PlanDefinition/diabetes")
    assert a["id"] not in await _ids(client, "instantiates-canonical=PlanDefinition/other")
    assert a["id"] in await _ids(client, "instantiates-uri=http://example.org/protocols/diabetes")
    assert a["id"] not in await _ids(client, "instantiates-uri=http://nope")


async def test_search_dates(client):
    a = await _create(client, full_payload())
    assert a["id"] in await _ids(client, "date=ge2024-01-01&date=le2024-12-31")
    assert a["id"] in await _ids(client, "date=ap2024-06-01")
    assert a["id"] not in await _ids(client, "date=sa2025-01-01")
    assert a["id"] in await _ids(client, "activity-date=ap2024-01-15")
    assert a["id"] not in await _ids(client, "activity-date=sa2025-01-01")
    assert a["id"] in await _ids(client, "_lastUpdated=ge2000-01-01")


async def test_pagination_bundle_and_order(client):
    for i in range(3):
        await _create(client, {**MINIMAL, "org_id": "org-page", "created": f"202{i}-01-01T00:00:00Z"})
    body = (await client.get(f"{BASE}/?org_id=org-page&limit=2&offset=0")).json()
    assert body["total"] == 3 and len(body["data"]) == 2 and body["limit"] == 2
    assert body["data"][0]["created"] > body["data"][1]["created"]  # newest first
    bundle = (await client.get(f"{BASE}/?org_id=org-page&limit=2", headers=FHIR_ACCEPT)).json()
    assert bundle["resourceType"] == "Bundle" and bundle["total"] == 3 and len(bundle["entry"]) == 2
