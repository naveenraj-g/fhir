"""Integration tests for /api/fhir/v1/activity-definitions endpoints."""
BASE = "/api/fhir/v1/activity-definitions"
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
        "url": "http://example.org/fhir/ActivityDefinition/zika",
        "version": "1.0.0",
        "name": "zika_assessment",
        "title": "Zika virus exposure assessment",
        "status": "active",
        "experimental": False,
        "date": "2024-03-15T00:00:00Z",
        "publisher": "Example Health",
        "description": "Assess exposure to Zika virus",
        "effective_period_start": "2024-01-01T00:00:00Z",
        "effective_period_end": "2024-12-31T00:00:00Z",
        "subject_reference": "Group/5",
        "kind": "ServiceRequest",
        "intent": "proposal",
        "priority": "routine",
        "do_not_perform": False,
        "code_system": "http://example.org/questionnaires",
        "code_code": "zika-assessment",
        "timing_timing": {"repeat": {"frequency": 1, "period": 1, "period_unit": "d"}},
        "location": "Location/230001",
        "product_reference": "Medication/250001",
        "quantity": {"value": 2, "unit": "tablet"},
        "transform": "http://example.org/fhir/StructureMap/zika",
        "identifier": [{"system": "urn:ad", "value": "AD-1"}],
        "contact": [{"name": "Dr Who", "telecom": [{"system": "email", "value": "who@example.org"}]}],
        "author": [{"name": "Author A"}],
        "use_context": [{
            "code_system": "http://terminology.hl7.org/CodeSystem/usage-context-type", "code_code": "focus",
            "value_cc_system": "http://snomed.info/sct", "value_cc_code": "44054006",
        }],
        "jurisdiction": [{"coding_system": "urn:iso:std:iso:3166", "coding_code": "US"}],
        "topic": [{"coding_code": "exposure"}],
        "related_artifact": [{"type": "depends-on", "resource": "http://example.org/fhir/Library/base"}],
        "library": ["http://example.org/fhir/Library/cql"],
        "participant": [{"type": "practitioner", "role_code": "nurse"}],
        "dosage": [{
            "sequence": 1,
            "text": "1 tablet twice daily",
            "additional_instruction": [{"coding_code": "311504000", "text": "with food"}],
            "timing": {"repeat": {"frequency": 2, "period": 1, "period_unit": "d", "bounds_duration": {"value": 7, "unit": "d"}}},
            "as_needed_boolean": False,
            "route_system": "http://snomed.info/sct", "route_code": "26643006", "route_display": "Oral",
            "dose_and_rate": [{
                "type_code": "ordered",
                "dose_range": {"low": {"value": 1, "unit": "tablet"}, "high": {"value": 2, "unit": "tablet"}},
                "rate_ratio": {"numerator": {"value": 1, "unit": "tablet"}, "denominator": {"value": 12, "unit": "h"}},
            }],
            "max_dose_per_period": {"numerator": {"value": 4, "unit": "tablet"}, "denominator": {"value": 1, "unit": "d"}},
            "max_dose_per_administration": {"value": 2, "unit": "tablet"},
        }],
        "body_site": [{"coding_code": "arm"}],
        "specimen_requirement": [{"reference": "SpecimenDefinition/9"}],
        "observation_requirement": [{"reference": "ObservationDefinition/4"}],
        "observation_result_requirement": [{"reference": "ObservationDefinition/5"}],
        "dynamic_value": [{"path": "priority", "expression": {"language": "text/fhirpath", "expression": "'stat'"}}],
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
    assert data["id"] >= 410000
    assert data["status"] == "draft"
    assert not data.get("dosage")


async def test_create_requires_status(client):
    r = await client.post(BASE + "/", json={"org_id": "org-test"})
    assert r.status_code in (400, 422)


async def test_create_full_plain(client):
    data = await _create(client, full_payload())
    assert data["title"] == "Zika virus exposure assessment"
    assert (data["kind"], data["intent"], data["priority"]) == ("ServiceRequest", "proposal", "routine")
    assert (data["subject_reference_type"], data["subject_reference_id"]) == ("Group", 5)
    assert (data["location_type"], data["location_id"]) == ("Location", 230001)
    assert (data["product_reference_type"], data["product_reference_id"]) == ("Medication", 250001)
    assert data["quantity"] == {"value": 2.0, "unit": "tablet"}
    assert data["timing_timing"]["repeat"]["frequency"] == 1
    assert data["participant"][0]["type"] == "practitioner"
    d = data["dosage"][0]
    assert d["text"] == "1 tablet twice daily" and d["route_code"] == "26643006"
    assert d["timing"]["repeat"]["bounds_duration"]["value"] == 7
    assert d["additional_instruction"][0]["text"] == "with food"
    dr = d["dose_and_rate"][0]
    assert dr["type_code"] == "ordered" and dr["dose_range"]["high"]["value"] == 2
    assert dr["rate_ratio"]["denominator"]["unit"] == "h"
    assert d["max_dose_per_period"]["numerator"]["value"] == 4
    assert d["max_dose_per_administration"]["value"] == 2
    assert data["specimen_requirement"][0]["reference_id"] == 9
    assert data["observation_requirement"][0]["reference_type"] == "ObservationDefinition"
    assert data["observation_result_requirement"][0]["reference_id"] == 5
    assert data["body_site"][0]["coding_code"] == "arm"
    assert data["dynamic_value"][0]["path"] == "priority"
    assert len(data["identifier"]) == 1 and len(data["author"]) == 1 and len(data["contact"]) == 1
    assert data["library"] and data["related_artifact"]


async def test_create_full_fhir(client):
    created = await _create(client, full_payload())
    r = await client.get(f"{BASE}/{created['id']}", headers=FHIR_ACCEPT)
    assert r.status_code == 200
    body = r.json()
    assert body["resourceType"] == "ActivityDefinition"
    assert body["id"] == str(created["id"])
    assert body["kind"] == "ServiceRequest" and body["intent"] == "proposal"
    assert body["subjectReference"]["reference"] == "Group/5"
    assert body["location"]["reference"] == "Location/230001"
    assert body["productReference"]["reference"] == "Medication/250001"
    assert body["timingTiming"]["repeat"]["frequency"] == 1
    assert body["dosage"][0]["doseAndRate"][0]["rateRatio"]["numerator"]["value"] == 1
    assert body["dosage"][0]["maxDosePerPeriod"]["denominator"]["unit"] == "d"
    assert body["dosage"][0]["route"]["coding"][0]["code"] == "26643006"
    assert body["specimenRequirement"][0]["reference"] == "SpecimenDefinition/9"
    assert body["observationResultRequirement"][0]["reference"] == "ObservationDefinition/5"
    assert body["library"] == ["http://example.org/fhir/Library/cql"]
    assert body["dynamicValue"][0]["expression"]["language"] == "text/fhirpath"


async def test_get_and_404(client):
    created = await _create(client)
    assert (await client.get(f"{BASE}/{created['id']}")).status_code == 200
    assert (await client.get(f"{BASE}/999999")).status_code == 404


async def test_delete_cascades(client):
    created = await _create(client, full_payload())
    assert (await client.delete(f"{BASE}/{created['id']}")).status_code == 204
    assert (await client.get(f"{BASE}/{created['id']}")).status_code == 404


# ── Validation ────────────────────────────────────────────────────────────────


async def test_bad_reference_type_rejected(client):
    for field, value in (("subject_reference", "Patient/1"), ("location", "Patient/1"),
                         ("product_reference", "Patient/1"), ("subject_reference", "Group/abc")):
        r = await client.post(BASE + "/", json=full_payload(**{field: value}))
        assert r.status_code in (400, 422), (field, value)


async def test_bad_reference_list_type_rejected(client):
    r = await client.post(BASE + "/", json=full_payload(specimen_requirement=[{"reference": "ObservationDefinition/1"}]))
    assert r.status_code in (400, 422)


async def test_reference_existence_not_checked(client):
    data = await _create(client, full_payload(location="Location/987654"))
    assert data["location_id"] == 987654


async def test_enum_validation(client):
    for field, value in (("kind", "Patient"), ("intent", "bogus"), ("priority", "bogus")):
        r = await client.post(BASE + "/", json=full_payload(**{field: value}))
        assert r.status_code in (400, 422), field


async def test_choice_types_exclusive(client):
    r = await client.post(BASE + "/", json=full_payload(timing_datetime="2024-01-01T00:00:00Z"))
    assert r.status_code in (400, 422)  # timing_timing already set
    r = await client.post(BASE + "/", json=full_payload(subject_cc_code="x"))
    assert r.status_code in (400, 422)
    r = await client.post(BASE + "/", json=full_payload(product_cc_code="x"))
    assert r.status_code in (400, 422)


async def test_dosage_choice_types(client):
    p = full_payload()
    p["dosage"][0]["as_needed_code"] = "x"
    assert (await client.post(BASE + "/", json=p)).status_code in (400, 422)
    p = full_payload()
    p["dosage"][0]["dose_and_rate"][0]["dose_quantity"] = {"value": 1}
    assert (await client.post(BASE + "/", json=p)).status_code in (400, 422)


async def test_expression_requires_expression_or_reference(client):
    r = await client.post(BASE + "/", json=full_payload(dynamic_value=[{"path": "x", "expression": {"language": "text/cql"}}]))
    assert r.status_code in (400, 422)


async def test_effective_period_order(client):
    r = await client.post(BASE + "/", json=full_payload(
        effective_period_start="2025-01-01T00:00:00Z", effective_period_end="2024-01-01T00:00:00Z"))
    assert r.status_code in (400, 422)


async def test_extra_field_forbidden(client):
    r = await client.post(BASE + "/", json={**MINIMAL, "bogus": 1})
    assert r.status_code in (400, 422)


# ── PATCH ─────────────────────────────────────────────────────────────────────


async def test_patch_scalars(client):
    created = await _create(client, full_payload())
    r = await _patch(client, created["id"], {"title": "New", "status": "retired", "intent": "order", "updated_by": "u2"})
    assert r.status_code == 200, r.text
    body = r.json()
    assert (body["title"], body["status"], body["intent"], body["updated_by"]) == ("New", "retired", "order", "u2")
    assert len(body["dosage"]) == 1  # untouched


async def test_patch_status_not_null(client):
    created = await _create(client)
    assert (await _patch(client, created["id"], {"status": None})).status_code in (400, 422)


async def test_patch_references(client):
    created = await _create(client, full_payload())
    r = await _patch(client, created["id"], {"location": "Location/1", "product_reference": None})
    body = r.json()
    assert body["location_id"] == 1 and body["product_reference_id"] is None
    r = await _patch(client, created["id"], {"location": "Patient/1"})
    assert r.status_code in (400, 422)


async def test_patch_nested_datatype_and_choice_swap(client):
    created = await _create(client, full_payload())
    r = await _patch(client, created["id"], {"timing_age": {"value": 5, "unit": "a"}})
    body = r.json()
    assert body["timing_age"]["value"] == 5
    assert body["timing_timing"] is None  # other timing[x] variants cleared
    r = await _patch(client, created["id"], {"quantity": {"value": 9, "unit": "mg"}})
    assert r.json()["quantity"]["value"] == 9
    r = await _patch(client, created["id"], {"quantity": None, "timing_age": None})
    assert r.json()["quantity"] is None and r.json()["timing_age"] is None


async def test_patch_product_choice_swap(client):
    created = await _create(client, full_payload())
    r = await _patch(client, created["id"], {"product_cc_code": "123", "product_cc_text": "Aspirin"})
    body = r.json()
    assert body["product_cc_code"] == "123" and body["product_reference_id"] is None


async def test_patch_replace_dosage(client):
    created = await _create(client, full_payload())
    r = await _patch(client, created["id"], {"dosage": [{"text": "A"}, {"text": "B", "dose_and_rate": [{"dose_quantity": {"value": 3}}]}]})
    assert r.status_code == 200, r.text
    body = r.json()
    assert [d["text"] for d in body["dosage"]] == ["A", "B"]
    assert body["dosage"][1]["dose_and_rate"][0]["dose_quantity"]["value"] == 3
    r = await _patch(client, created["id"], {"dosage": []})
    assert r.json()["dosage"] == []


async def test_patch_replace_lists(client):
    created = await _create(client, full_payload())
    r = await _patch(client, created["id"], {
        "identifier": [{"value": "X"}, {"value": "Y"}], "jurisdiction": [{"coding_code": "GB"}], "topic": [],
        "library": ["http://x/Library/1"], "use_context": [], "body_site": [{"coding_code": "leg"}],
        "participant": [{"type": "patient"}], "specimen_requirement": [], "dynamic_value": [],
        "observation_requirement": [{"reference": "ObservationDefinition/77"}],
        "related_artifact": [{"type": "citation", "citation": "J Med"}],
    })
    assert r.status_code == 200, r.text
    body = r.json()
    assert [i["value"] for i in body["identifier"]] == ["X", "Y"]
    assert [j["coding_code"] for j in body["jurisdiction"]] == ["GB"]
    assert body["topic"] == [] and body["use_context"] == [] and body["specimen_requirement"] == []
    assert body["dynamic_value"] == []
    assert [l["canonical"] for l in body["library"]] == ["http://x/Library/1"]
    assert [b["coding_code"] for b in body["body_site"]] == ["leg"]
    assert [p["type"] for p in body["participant"]] == ["patient"]
    assert body["observation_requirement"][0]["reference_id"] == 77
    assert body["observation_result_requirement"][0]["reference_id"] == 5  # untouched
    assert [a["type"] for a in body["related_artifact"]] == ["citation"]


async def test_patch_contact_kinds_independent(client):
    created = await _create(client, full_payload())
    r = await _patch(client, created["id"], {"author": [{"name": "B"}, {"name": "C"}]})
    body = r.json()
    assert [a["name"] for a in body["author"]] == ["B", "C"]
    assert [c["name"] for c in body["contact"]] == ["Dr Who"]
    r = await _patch(client, created["id"], {"contact": []})
    assert r.json()["contact"] == [] and len(r.json()["author"]) == 2


async def test_patch_404(client):
    assert (await _patch(client, 999999, {"title": "x"})).status_code == 404


# ── Search ────────────────────────────────────────────────────────────────────


async def test_org_id_required(client):
    assert (await client.get(f"{BASE}/")).status_code in (400, 422)


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
    assert (await client.get(f"{BASE}/?{_with_org('status=bogus')}")).status_code in (400, 422)


async def test_search_string_modes(client):
    a = await _create(client, full_payload())
    assert a["id"] in await _ids(client, "name=zika")
    assert a["id"] not in await _ids(client, "name=assess")
    assert a["id"] in await _ids(client, "name:contains=ASSESS")
    assert a["id"] not in await _ids(client, "name:exact=Zika_assessment")
    assert a["id"] in await _ids(client, "name:exact=zika_assessment")
    assert a["id"] in await _ids(client, "title:contains=exposure")
    assert a["id"] in await _ids(client, "publisher=example")
    assert a["id"] in await _ids(client, "description:contains=zika")


async def test_search_tokens(client):
    a = await _create(client, full_payload())
    assert a["id"] in await _ids(client, "identifier=urn:ad|AD-1")
    assert a["id"] not in await _ids(client, "identifier=urn:ad|NOPE")
    assert a["id"] in await _ids(client, "topic=exposure")
    assert a["id"] in await _ids(client, "jurisdiction=urn:iso:std:iso:3166|US")
    assert a["id"] in await _ids(client, "context=http://snomed.info/sct|44054006")
    assert a["id"] in await _ids(client, "context-type=focus")


async def test_search_relations(client):
    a = await _create(client, full_payload())
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
    body = (await client.get(f"{BASE}/?org_id=org-page&limit=2&offset=0")).json()
    assert body["total"] == 3 and len(body["data"]) == 2 and body["limit"] == 2
    bundle = (await client.get(f"{BASE}/?org_id=org-page&limit=2", headers=FHIR_ACCEPT)).json()
    assert bundle["resourceType"] == "Bundle" and bundle["total"] == 3 and len(bundle["entry"]) == 2


async def test_default_order_newest_date_first(client):
    old = await _create(client, {**MINIMAL, "org_id": "org-ord", "date": "2020-01-01T00:00:00Z"})
    new = await _create(client, {**MINIMAL, "org_id": "org-ord", "date": "2024-01-01T00:00:00Z"})
    ids = [d["id"] for d in (await client.get(f"{BASE}/?org_id=org-ord")).json()["data"]]
    assert ids.index(new["id"]) < ids.index(old["id"])
