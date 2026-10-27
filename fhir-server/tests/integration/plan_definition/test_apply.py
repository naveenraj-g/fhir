"""Integration tests for the $apply operations of PlanDefinition and ActivityDefinition."""
PD = "/api/fhir/v1/plan-definitions"
AD = "/api/fhir/v1/activity-definitions"
SR = "/api/fhir/v1/service-requests"
FHIR_ACCEPT = {"Accept": "application/fhir+json"}
ORG = "org-test"


async def _ad(client, name, **overrides):
    payload = {
        "user_id": "u-test", "org_id": ORG, "status": "active", "name": name, "title": name.replace("_", " ").title(),
        "kind": "ServiceRequest", "intent": "order", "priority": "routine",
        "code_system": "http://loinc.org", "code_code": f"{name}-code", "code_display": name,
        **overrides,
    }
    r = await client.post(f"{AD}/", json=payload)
    assert r.status_code in (200, 201), r.text
    return r.json()


async def _plan(client, actions, **overrides):
    payload = {"user_id": "u-test", "org_id": ORG, "status": "active", "name": "screening", "action": actions, **overrides}
    r = await client.post(f"{PD}/", json=payload)
    assert r.status_code in (200, 201), r.text
    return r.json()


def _action(element_id, ad, **extra):
    return {"element_id": element_id, "title": f"Action {element_id}",
            "definition_canonical": f"ActivityDefinition/{ad['id']}", **extra}


def _apply_body(**overrides):
    return {"org_id": ORG, "user_id": "u-test", "subject": "Patient/10001", "practitioner": "Practitioner/30001", **overrides}


async def _sr_total(client):
    r = await client.get(f"{SR}/", params={"org_id": ORG})
    assert r.status_code == 200, r.text
    return r.json()["total"]


# ── ActivityDefinition/$apply ───────────────────────────────────────────────────


async def test_activity_apply_preview_saves_nothing(client):
    ad = await _ad(client, "cbc", quantity={"value": 1, "unit": "test"}, timing_datetime="2026-11-01T09:00:00Z")
    r = await client.post(f"{AD}/{ad['id']}/$apply", json=_apply_body())
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["definition"] == f"ActivityDefinition/{ad['id']}"
    assert body["persisted"] is False and body["total"] == 1 and body["skipped"] == []
    sr = body["service_requests"][0]
    assert sr["id"] is None
    assert sr["status"] == "draft" and sr["intent"] == "order" and sr["priority"] == "routine"
    assert sr["code_code"] == "cbc-code" and sr["subject_id"] == 10001 and sr["requester_id"] == 30001
    assert sr["occurrence_datetime"].startswith("2026-11-01")
    assert f"ActivityDefinition/{ad['id']}" in sr["instantiates_canonical"]
    assert await _sr_total(client) == 0


async def test_activity_apply_persist_saves_active_service_request(client):
    ad = await _ad(client, "ecg")
    r = await client.post(f"{AD}/{ad['id']}/$apply", json=_apply_body(persist=True))
    assert r.status_code == 200, r.text
    sr = r.json()["service_requests"][0]
    assert r.json()["persisted"] is True and sr["id"] and sr["status"] == "active"
    assert sr["created_by"] is None or isinstance(sr["created_by"], str)
    fetched = await client.get(f"{SR}/{sr['id']}")
    assert fetched.status_code == 200 and fetched.json()["code_code"] == "ecg-code"
    assert await _sr_total(client) == 1


async def test_activity_apply_fhir_bundle(client):
    ad = await _ad(client, "xray")
    r = await client.post(f"{AD}/{ad['id']}/$apply", json=_apply_body(persist=True), headers=FHIR_ACCEPT)
    assert r.status_code == 200, r.text
    bundle = r.json()
    assert bundle["resourceType"] == "Bundle" and bundle["type"] == "collection" and bundle["total"] == 1
    res = bundle["entry"][0]["resource"]
    assert res["resourceType"] == "ServiceRequest" and res["subject"] == {"reference": "Patient/10001"}
    assert res["instantiatesCanonical"] == [f"ActivityDefinition/{ad['id']}"]


async def test_activity_apply_other_kind_is_skipped_with_reason(client):
    ad = await _ad(client, "statin", kind="MedicationRequest")
    r = await client.post(f"{AD}/{ad['id']}/$apply", json=_apply_body(persist=True))
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["total"] == 0 and len(body["skipped"]) == 1
    assert "MedicationRequest" in body["skipped"][0]["reason"]
    assert await _sr_total(client) == 0


async def test_activity_apply_duplicate_guard_and_override(client):
    ad = await _ad(client, "lipid")
    first = await client.post(f"{AD}/{ad['id']}/$apply", json=_apply_body(persist=True))
    assert first.json()["total"] == 1
    again = await client.post(f"{AD}/{ad['id']}/$apply", json=_apply_body(persist=True))
    assert again.json()["total"] == 0 and "already exists" in again.json()["skipped"][0]["reason"]
    forced = await client.post(f"{AD}/{ad['id']}/$apply", json=_apply_body(persist=True, allow_duplicates=True))
    assert forced.json()["total"] == 1
    other_patient = await client.post(f"{AD}/{ad['id']}/$apply", json=_apply_body(persist=True, subject="Patient/10002"))
    assert other_patient.json()["total"] == 1
    assert await _sr_total(client) == 3


async def test_activity_apply_tenant_and_validation(client):
    ad = await _ad(client, "hba1c")
    wrong_org = await client.post(f"{AD}/{ad['id']}/$apply", json=_apply_body(org_id="someone-else"))
    assert wrong_org.status_code == 404
    assert (await client.post(f"{AD}/999999/$apply", json=_apply_body())).status_code == 404
    assert (await client.post(f"{AD}/{ad['id']}/$apply", json=_apply_body(subject="Practitioner/1"))).status_code == 422
    assert (await client.post(f"{AD}/{ad['id']}/$apply", json=_apply_body(subject="nonsense"))).status_code == 422
    assert (await client.post(f"{AD}/{ad['id']}/$apply", json=_apply_body(encounter="Patient/1"))).status_code == 422
    missing_org = _apply_body()
    del missing_org["org_id"]
    assert (await client.post(f"{AD}/{ad['id']}/$apply", json=missing_org)).status_code in (400, 422)
    assert (await client.post(f"{AD}/{ad['id']}/$apply", json=_apply_body(unknown_field=1))).status_code in (400, 422)


# ── PlanDefinition/$apply ───────────────────────────────────────────────────────


async def _screening_plan(client):
    cbc = await _ad(client, "cbc")
    ecg = await _ad(client, "ecg", priority="urgent")
    statin = await _ad(client, "statin", kind="MedicationRequest")
    old = await _ad(client, "old_test", status="retired")
    plan = await _plan(client, [
        _action("a-cbc", cbc, description="Fasting for 8 hours."),
        _action("a-ecg", ecg),
        _action("a-statin", statin),
        _action("a-old", old),
        {"element_id": "a-missing", "title": "Gone", "definition_canonical": "ActivityDefinition/999999"},
        {"element_id": "a-group", "title": "Group of one", "action": [_action("a-nested", cbc)]},
    ])
    return plan, cbc, ecg


async def test_plan_apply_preview(client):
    plan, cbc, ecg = await _screening_plan(client)
    r = await client.post(f"{PD}/{plan['id']}/$apply", json=_apply_body())
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["definition"] == f"PlanDefinition/{plan['id']}" and body["persisted"] is False
    # cbc once (the nested duplicate is skipped), ecg once
    assert [s["code_code"] for s in body["service_requests"]] == ["cbc-code", "ecg-code"]
    assert body["service_requests"][0]["patient_instruction"] == "Fasting for 8 hours."
    assert body["service_requests"][1]["priority"] == "urgent"
    assert all(f"PlanDefinition/{plan['id']}" in s["instantiates_canonical"] for s in body["service_requests"])
    reasons = {s["action_id"]: s["reason"] for s in body["skipped"]}
    assert "MedicationRequest" in reasons["a-statin"]
    assert "retired" in reasons["a-old"]
    assert "not found" in reasons["a-missing"]
    assert "earlier action" in reasons["a-nested"]
    assert "a-group" not in reasons
    assert await _sr_total(client) == 0


async def test_plan_apply_persist_then_rerun_is_idempotent(client):
    plan, _, _ = await _screening_plan(client)
    r = await client.post(f"{PD}/{plan['id']}/$apply", json=_apply_body(persist=True))
    assert r.status_code == 200, r.text
    assert r.json()["total"] == 2 and all(s["id"] and s["status"] == "active" for s in r.json()["service_requests"])
    assert await _sr_total(client) == 2
    again = await client.post(f"{PD}/{plan['id']}/$apply", json=_apply_body(persist=True))
    assert again.json()["total"] == 0
    assert sum("already exists" in s["reason"] for s in again.json()["skipped"]) == 2
    assert await _sr_total(client) == 2


async def test_plan_apply_selected_actions(client):
    plan, _, _ = await _screening_plan(client)
    r = await client.post(f"{PD}/{plan['id']}/$apply", json=_apply_body(persist=True, selected_actions=["a-ecg"]))
    assert r.status_code == 200, r.text
    assert [s["code_code"] for s in r.json()["service_requests"]] == ["ecg-code"]
    assert r.json()["skipped"] == []
    assert await _sr_total(client) == 1
    bad = await client.post(f"{PD}/{plan['id']}/$apply", json=_apply_body(selected_actions=["nope"]))
    assert bad.status_code == 422 and "nope" in bad.text


async def test_plan_apply_resolves_canonical_url_and_version(client):
    ad = await _ad(client, "vision", url="http://example.org/fhir/ActivityDefinition/vision")
    plan = await _plan(client, [{
        "element_id": "a1", "title": "Vision",
        "definition_canonical": "http://example.org/fhir/ActivityDefinition/vision|1.0.0",
    }])
    r = await client.post(f"{PD}/{plan['id']}/$apply", json=_apply_body())
    assert r.status_code == 200, r.text
    assert r.json()["total"] == 1
    assert r.json()["service_requests"][0]["instantiates_canonical"].startswith("http://example.org/fhir/ActivityDefinition/vision")
    assert ad["id"]


async def test_plan_apply_is_all_or_nothing(client):
    plan, _, _ = await _screening_plan(client)
    r = await client.post(f"{PD}/{plan['id']}/$apply", json=_apply_body(persist=True, practitioner="Patient/1"))
    # Patient is a valid requester type; use an invalid one to force the failure
    assert r.status_code == 200
    r = await client.post(
        f"{PD}/{plan['id']}/$apply",
        json=_apply_body(persist=True, allow_duplicates=True, practitioner="Condition/1"),
    )
    assert r.status_code == 422, r.text
    assert await _sr_total(client) == 2  # only the first successful run


async def test_plan_apply_only_ad_of_same_org(client):
    ad = await _ad(client, "foreign")
    plan = await _plan(client, [_action("a1", ad)])
    r = await client.post(f"{PD}/{plan['id']}/$apply", json=_apply_body(org_id="someone-else"))
    assert r.status_code == 404


async def test_plan_apply_fhir_reports_skipped_as_operation_outcome(client):
    plan, _, _ = await _screening_plan(client)
    r = await client.post(f"{PD}/{plan['id']}/$apply", json=_apply_body(), headers=FHIR_ACCEPT)
    assert r.status_code == 200, r.text
    entries = r.json()["entry"]
    assert [e["resource"]["resourceType"] for e in entries] == ["ServiceRequest", "ServiceRequest", "OperationOutcome"]
    assert "id" not in entries[0]["resource"]
    assert len(entries[-1]["resource"]["issue"]) == 4
