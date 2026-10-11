"""Integration tests for /api/fhir/v1/plan-definitions endpoints."""
BASE = "/api/fhir/v1/plan-definitions"
FHIR_ACCEPT = {"Accept": "application/fhir+json"}


def _with_org(query: str) -> str:
    """Every search requires org_id (tenant scope) — add the default test org unless the query sets one."""
    if "org_id=" in query:
        return query
    return f"org_id=org-test&{query}" if query else "org_id=org-test"


MINIMAL = {"user_id": "u-test", "org_id": "org-test", "status": "draft"}


def full_payload(**overrides) -> dict:
    payload = {
        **MINIMAL,
        "url": "http://example.org/fhir/PlanDefinition/diabetes",
        "version": "1.0.0",
        "name": "diabetes_care",
        "title": "Diabetes care protocol",
        "status": "active",
        "experimental": False,
        "date": "2024-03-15T00:00:00Z",
        "publisher": "Example Health",
        "description": "Protocol for managing type 2 diabetes",
        "type_system": "http://terminology.hl7.org/CodeSystem/plan-definition-type",
        "type_code": "clinical-protocol",
        "effective_period_start": "2024-01-01T00:00:00Z",
        "effective_period_end": "2024-12-31T00:00:00Z",
        "subject_reference": "Group/5",
        "identifier": [{"system": "urn:pd", "value": "PD-1"}],
        "contact": [{"name": "Dr Who", "telecom": [{"system": "email", "value": "who@example.org"}]}],
        "author": [{"name": "Author A"}],
        "use_context": [{
            "code_system": "http://terminology.hl7.org/CodeSystem/usage-context-type", "code_code": "focus",
            "value_cc_system": "http://snomed.info/sct", "value_cc_code": "44054006",
        }],
        "jurisdiction": [{"coding_system": "urn:iso:std:iso:3166", "coding_code": "US"}],
        "topic": [{"coding_code": "diabetes"}],
        "related_artifact": [{"type": "depends-on", "resource": "http://example.org/fhir/Library/base"}],
        "library": ["http://example.org/fhir/Library/cql"],
        "goal": [
            {
                "element_id": "g1",
                "description_text": "HbA1c below 7%",
                "addresses": [{"coding_code": "44054006"}],
                "target": [{"measure_code": "4548-4", "detail_range": {"high": {"value": 7, "unit": "%"}}}],
            },
            {"element_id": "g2", "description_text": "Weight loss"},
        ],
        "action": [
            {
                "element_id": "a1",
                "title": "Order HbA1c",
                "goal_id": ["g1"],
                "code": [{"coding_code": "hba1c"}],
                "definition_canonical": "http://example.org/fhir/ActivityDefinition/hba1c",
                "timing_timing": {"repeat": {"frequency": 1, "period": 3, "period_unit": "mo"}},
                "participant": [{"type": "practitioner"}],
                "condition": [{"kind": "applicability", "expression": {"language": "text/cql", "expression": "true"}}],
                "action": [{"element_id": "a1a", "title": "Collect blood"}],
            },
            {
                "element_id": "a2",
                "title": "Review results",
                "related_action": [{"action_id": "a1", "relationship": "after", "offset_duration": {"value": 1, "unit": "d"}}],
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
    assert data["id"] >= 400000
    assert data["status"] == "draft"
    assert data["goal"] == [] or data["goal"] is None
    assert not data.get("action")


async def test_create_requires_status(client):
    r = await client.post(BASE + "/", json={"org_id": "org-test"})
    assert r.status_code in (400, 422)


async def test_create_full_plain(client):
    data = await _create(client, full_payload())
    assert data["title"] == "Diabetes care protocol"
    assert (data["subject_reference_type"], data["subject_reference_id"]) == ("Group", 5)
    assert [g["element_id"] for g in data["goal"]] == ["g1", "g2"]
    assert len(data["goal"][0]["target"]) == 1
    assert [a["element_id"] for a in data["action"]] == ["a1", "a2"]
    a1 = data["action"][0]
    assert a1["goal_id"] == ["g1"]
    assert [s["element_id"] for s in a1["action"]] == ["a1a"]
    assert data["action"][1]["related_action"][0]["action_id"] == "a1"
    assert len(data["identifier"]) == 1 and len(data["author"]) == 1 and len(data["contact"]) == 1
    assert data["library"] and data["related_artifact"]


async def test_create_full_fhir(client):
    created = await _create(client, full_payload())
    r = await client.get(f"{BASE}/{created['id']}", headers=FHIR_ACCEPT)
    assert r.status_code == 200
    body = r.json()
    assert body["resourceType"] == "PlanDefinition"
    assert body["id"] == str(created["id"])
    assert body["subjectReference"]["reference"] == "Group/5"
    assert body["goal"][0]["id"] == "g1"
    assert body["action"][0]["goalId"] == ["g1"]
    assert body["action"][0]["action"][0]["id"] == "a1a"
    assert body["action"][1]["relatedAction"][0]["actionId"] == "a1"
    assert body["library"] == ["http://example.org/fhir/Library/cql"]
    assert body["author"][0]["name"] == "Author A"
    assert body["action"][0]["timingTiming"]["repeat"]["frequency"] == 1


async def test_get_and_404(client):
    created = await _create(client)
    assert (await client.get(f"{BASE}/{created['id']}")).status_code == 200
    assert (await client.get(f"{BASE}/999999")).status_code == 404


async def test_delete_cascades(client):
    created = await _create(client, full_payload())
    r = await client.delete(f"{BASE}/{created['id']}")
    assert r.status_code == 204
    assert (await client.get(f"{BASE}/{created['id']}")).status_code == 404


# ── Validation (R4 invariants, references) ────────────────────────────────────


async def test_bad_reference_type_rejected(client):
    r = await client.post(BASE + "/", json=full_payload(subject_reference="Patient/1"))
    assert r.status_code in (400, 422)


async def test_bad_reference_format_rejected(client):
    r = await client.post(BASE + "/", json=full_payload(subject_reference="Group/abc"))
    assert r.status_code in (400, 422)


async def test_reference_existence_not_checked(client):
    data = await _create(client, full_payload(subject_reference="Group/987654"))
    assert data["subject_reference_id"] == 987654


async def test_unknown_goal_id_rejected(client):
    p = full_payload()
    p["action"][0]["goal_id"] = ["nope"]
    r = await client.post(BASE + "/", json=p)
    assert r.status_code in (400, 422)


async def test_unknown_related_action_rejected(client):
    p = full_payload()
    p["action"][1]["related_action"][0]["action_id"] = "ghost"
    r = await client.post(BASE + "/", json=p)
    assert r.status_code in (400, 422)


async def test_duplicate_action_id_rejected(client):
    p = full_payload()
    p["action"][1]["element_id"] = "a1"
    r = await client.post(BASE + "/", json=p)
    assert r.status_code in (400, 422)


async def test_effective_period_order(client):
    r = await client.post(BASE + "/", json=full_payload(
        effective_period_start="2025-01-01T00:00:00Z", effective_period_end="2024-01-01T00:00:00Z"))
    assert r.status_code in (400, 422)


async def test_subject_choice_exclusive(client):
    r = await client.post(BASE + "/", json=full_payload(subject_cc_code="x"))
    assert r.status_code in (400, 422)


async def test_extra_field_forbidden(client):
    r = await client.post(BASE + "/", json={**MINIMAL, "bogus": 1})
    assert r.status_code in (400, 422)


# ── PATCH (scalars + replace semantics for child lists) ───────────────────────


async def test_patch_scalars(client):
    created = await _create(client, full_payload())
    r = await _patch(client, created["id"], {"title": "New title", "status": "retired", "updated_by": "u2"})
    assert r.status_code == 200, r.text
    body = r.json()
    assert (body["title"], body["status"], body["updated_by"]) == ("New title", "retired", "u2")
    assert len(body["action"]) == 2  # untouched


async def test_patch_status_not_null(client):
    created = await _create(client)
    r = await _patch(client, created["id"], {"status": None})
    assert r.status_code in (400, 422)


async def test_patch_clear_reference(client):
    created = await _create(client, full_payload())
    r = await _patch(client, created["id"], {"subject_reference": None})
    assert r.status_code == 200
    assert r.json()["subject_reference_id"] is None


async def test_patch_replace_identifier(client):
    created = await _create(client, full_payload())
    r = await _patch(client, created["id"], {"identifier": [{"system": "urn:x", "value": "X"}, {"value": "Y"}]})
    assert [i["value"] for i in r.json()["identifier"]] == ["X", "Y"]
    r = await _patch(client, created["id"], {"identifier": []})
    assert r.json()["identifier"] == []


async def test_patch_contact_kinds_independent(client):
    created = await _create(client, full_payload())
    r = await _patch(client, created["id"], {"author": [{"name": "B"}, {"name": "C"}]})
    body = r.json()
    assert [a["name"] for a in body["author"]] == ["B", "C"]
    assert [c["name"] for c in body["contact"]] == ["Dr Who"]  # untouched
    r = await _patch(client, created["id"], {"contact": []})
    assert r.json()["contact"] == [] and len(r.json()["author"]) == 2


async def test_patch_replace_simple_lists(client):
    created = await _create(client, full_payload())
    r = await _patch(client, created["id"], {
        "jurisdiction": [{"coding_code": "GB"}], "topic": [], "library": ["http://x/Library/1"],
        "use_context": [], "related_artifact": [{"type": "citation", "citation": "J Med"}],
    })
    body = r.json()
    assert [j["coding_code"] for j in body["jurisdiction"]] == ["GB"]
    assert body["topic"] == [] and body["use_context"] == []
    assert body["library"] == [{"canonical": "http://x/Library/1"}] or "http://x/Library/1" in str(body["library"])
    assert [a["type"] for a in body["related_artifact"]] == ["citation"]


async def test_patch_replace_actions_tree(client):
    created = await _create(client, full_payload())
    r = await _patch(client, created["id"], {"action": [{"title": "Only", "goal_id": ["g2"], "action": [{"title": "child"}]}]})
    assert r.status_code == 200, r.text
    body = r.json()
    assert [a["title"] for a in body["action"]] == ["Only"]
    assert body["action"][0]["goal_id"] == ["g2"]
    assert body["action"][0]["action"][0]["title"] == "child"
    assert len(body["goal"]) == 2  # goals untouched
    r = await _patch(client, created["id"], {"action": []})
    assert r.json()["action"] == []


async def test_patch_action_with_unknown_stored_goal_rejected(client):
    created = await _create(client, full_payload())
    r = await _patch(client, created["id"], {"action": [{"title": "x", "goal_id": ["zzz"]}]})
    assert r.status_code in (400, 422)


async def test_patch_goal_replace_keeps_actions_valid(client):
    created = await _create(client, full_payload())
    # action a1 points at g1; replacing goals without g1 must be rejected
    r = await _patch(client, created["id"], {"goal": [{"element_id": "g9", "description_text": "x"}]})
    assert r.status_code in (400, 422)
    # replacing both consistently works
    r = await _patch(client, created["id"], {
        "goal": [{"element_id": "g9", "description_text": "x"}],
        "action": [{"title": "t", "goal_id": ["g9"]}],
    })
    assert r.status_code == 200, r.text
    assert [g["element_id"] for g in r.json()["goal"]] == ["g9"]


async def test_patch_404(client):
    assert (await _patch(client, 999999, {"title": "x"})).status_code == 404


# ── Search ────────────────────────────────────────────────────────────────────


async def test_org_id_required(client):
    r = await client.get(f"{BASE}/")
    assert r.status_code in (400, 422)


async def test_org_scope_isolates(client):
    a = await _create(client, {**MINIMAL, "org_id": "org-a"})
    b = await _create(client, {**MINIMAL, "org_id": "org-b"})
    assert a["id"] in await _ids(client, "org_id=org-a")
    assert b["id"] not in await _ids(client, "org_id=org-a")


async def test_user_id_filter(client):
    a = await _create(client, {**MINIMAL, "user_id": "u1"})
    b = await _create(client, {**MINIMAL, "user_id": "u2"})
    ids = await _ids(client, "user_id=u1")
    assert a["id"] in ids and b["id"] not in ids


async def test_search_id_status_url_version(client):
    a = await _create(client, full_payload())
    b = await _create(client, {**MINIMAL, "status": "retired", "url": "http://other", "version": "2"})
    assert await _ids(client, f"_id={a['id']}") == {a["id"]}
    assert b["id"] in await _ids(client, "status=retired")
    assert a["id"] not in await _ids(client, "status=retired")
    assert await _ids(client, "url=http://other") == {b["id"]}
    assert b["id"] in await _ids(client, "version=2")
    r = await client.get(f"{BASE}/?{_with_org('status=bogus')}")
    assert r.status_code in (400, 422)


async def test_search_string_modes(client):
    a = await _create(client, full_payload())
    assert a["id"] in await _ids(client, "name=diab")
    assert a["id"] not in await _ids(client, "name=care")
    assert a["id"] in await _ids(client, "name:contains=BETES")
    assert a["id"] not in await _ids(client, "name:exact=Diabetes_care")
    assert a["id"] in await _ids(client, "name:exact=diabetes_care")
    assert a["id"] in await _ids(client, "title:contains=care")
    assert a["id"] in await _ids(client, "publisher=example")
    assert a["id"] in await _ids(client, "description:contains=type 2")


async def test_search_tokens(client):
    a = await _create(client, full_payload())
    assert a["id"] in await _ids(client, "identifier=urn:pd|PD-1")
    assert a["id"] not in await _ids(client, "identifier=urn:pd|NOPE")
    assert a["id"] in await _ids(client, "type=clinical-protocol")
    assert a["id"] in await _ids(client, "type=http://terminology.hl7.org/CodeSystem/plan-definition-type|clinical-protocol")
    assert a["id"] in await _ids(client, "topic=diabetes")
    assert a["id"] in await _ids(client, "jurisdiction=urn:iso:std:iso:3166|US")
    assert a["id"] in await _ids(client, "context=http://snomed.info/sct|44054006")
    assert a["id"] in await _ids(client, "context-type=focus")


async def test_search_definition_and_relations(client):
    a = await _create(client, full_payload())
    assert a["id"] in await _ids(client, "definition=http://example.org/fhir/ActivityDefinition/hba1c")
    assert a["id"] in await _ids(client, "definition=ActivityDefinition/hba1c")
    assert a["id"] not in await _ids(client, "definition=ActivityDefinition/other")
    assert a["id"] in await _ids(client, "depends-on=http://example.org/fhir/Library/base")
    assert a["id"] in await _ids(client, "depends-on=Library/cql")  # via library[]
    assert a["id"] not in await _ids(client, "derived-from=Library/base")


async def test_search_dates(client):
    a = await _create(client, full_payload())
    assert a["id"] in await _ids(client, "date=ge2024-01-01&date=le2024-12-31")
    assert a["id"] not in await _ids(client, "date=gt2025-01-01")
    assert a["id"] in await _ids(client, "effective=ap2024-06-01")
    assert a["id"] not in await _ids(client, "effective=sa2025-01-01&effective=ge2026-01-01")
    assert a["id"] in await _ids(client, "_lastUpdated=ge2000-01-01")


async def test_pagination_and_bundle(client):
    for _ in range(3):
        await _create(client, {**MINIMAL, "org_id": "org-page"})
    r = await client.get(f"{BASE}/?org_id=org-page&limit=2&offset=0")
    body = r.json()
    assert body["total"] == 3 and len(body["data"]) == 2 and body["limit"] == 2
    r = await client.get(f"{BASE}/?org_id=org-page&limit=2", headers=FHIR_ACCEPT)
    bundle = r.json()
    assert bundle["resourceType"] == "Bundle" and bundle["total"] == 3 and len(bundle["entry"]) == 2


async def test_default_order_newest_date_first_nulls_last(client):
    old = await _create(client, {**MINIMAL, "org_id": "org-ord", "date": "2020-01-01T00:00:00Z"})
    new = await _create(client, {**MINIMAL, "org_id": "org-ord", "date": "2024-01-01T00:00:00Z"})
    r = await client.get(f"{BASE}/?org_id=org-ord")
    ids = [d["id"] for d in r.json()["data"]]
    assert ids.index(new["id"]) < ids.index(old["id"])
