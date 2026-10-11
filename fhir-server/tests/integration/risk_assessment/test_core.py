"""Integration tests for /api/fhir/v1/risk-assessments endpoints."""
BASE = "/api/fhir/v1/risk-assessments"
FHIR_ACCEPT = {"Accept": "application/fhir+json"}


def _with_org(query: str) -> str:
    """Every search requires org_id (tenant scope) — add the default test org unless the query sets one."""
    if "org_id=" in query:
        return query
    return f"org_id=org-test&{query}" if query else "org_id=org-test"

MINIMAL = {"user_id": "u-test", "org_id": "org-test", "status": "final", "subject": "Patient/10001"}


def full_payload(**overrides) -> dict:
    payload = {
        **MINIMAL,
        "subject_display": "John Doe",
        "identifier": [{"system": "urn:ra", "value": "RA-1"}],
        "method_system": "http://example.org/methods", "method_code": "framingham", "method_text": "Framingham",
        "code_system": "http://snomed.info/sct", "code_code": "225338004",
        "based_on": "ServiceRequest/80001", "parent": "Procedure/100001",
        "occurrence_datetime": "2024-03-15T10:30:00Z",
        "condition": "Condition/120001",
        "performer": "Practitioner/30001",
        "mitigation": "Statins",
        "reason_code": [{"coding_system": "http://snomed.info/sct", "coding_code": "38341003"}],
        "reason_reference": [{"reference": "Observation/160001"}],
        "basis": [{"reference": "DiagnosticReport/110001"}, {"reference": "Observation/160002"}],
        "prediction": [
            {
                "outcome_system": "http://snomed.info/sct", "outcome_code": "53741008",
                "probability_decimal": 12.5,
                "qualitative_risk_system": "http://terminology.hl7.org/CodeSystem/risk-probability",
                "qualitative_risk_code": "moderate",
                "relative_risk": 1.4,
                "when_range_low_value": 0, "when_range_high_value": 10, "when_range_high_unit": "years",
                "rationale": "Age and BP",
            },
            {
                "outcome_text": "Stroke",
                "probability_range_low_value": 40, "probability_range_low_code": "%",
                "probability_range_high_value": 60, "probability_range_high_code": "%",
                "qualitative_risk_code": "high",
                "when_period_start": "2024-03-15T00:00:00Z", "when_period_end": "2034-03-15T00:00:00Z",
            },
        ],
        "note": [{"text": "Reassess yearly", "author_reference": "Practitioner/30001"}],
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
    assert data["id"] >= 380000
    assert (data["status"], data["subject_type"], data["subject_id"]) == ("final", "Patient", 10001)
    assert data["prediction"] == []


async def test_create_full_plain(client):
    data = await _create(client, full_payload())
    assert (data["based_on_type"], data["based_on_id"]) == ("ServiceRequest", 80001)
    assert (data["condition_type"], data["performer_type"]) == ("Condition", "Practitioner")
    assert len(data["basis"]) == 2 and data["basis"][0]["reference_type"] == "DiagnosticReport"
    assert data["reason_reference"][0]["reference_type"] == "Observation"
    p1, p2 = data["prediction"]
    assert p1["probability_decimal"] == 12.5 and p1["qualitative_risk_code"] == "moderate"
    assert p2["probability_range_high_value"] == 60 and p2["when_period_start"].startswith("2034") is False
    assert data["note"][0]["author_reference_type"] == "Practitioner"


async def test_create_fhir_format(client):
    r = await client.post(BASE + "/", json=full_payload(), headers=FHIR_ACCEPT)
    assert r.status_code == 200, r.text
    f = r.json()
    assert f["resourceType"] == "RiskAssessment" and f["status"] == "final"
    assert f["subject"] == {"reference": "Patient/10001", "display": "John Doe"}
    assert f["basedOn"] == {"reference": "ServiceRequest/80001"}
    assert f["condition"] == {"reference": "Condition/120001"}
    assert f["method"]["coding"][0]["code"] == "framingham"
    assert f["occurrenceDateTime"].startswith("2024-03-15")
    assert [b["reference"] for b in f["basis"]] == ["DiagnosticReport/110001", "Observation/160002"]
    p1, p2 = f["prediction"]
    assert p1["probabilityDecimal"] == 12.5 and p1["relativeRisk"] == 1.4
    assert p1["whenRange"]["high"] == {"value": 10.0, "unit": "years"}
    assert p1["qualitativeRisk"]["coding"][0]["code"] == "moderate"
    assert p2["probabilityRange"]["low"] == {"value": 40.0, "code": "%"}
    assert p2["whenPeriod"]["start"].startswith("2024-03-15")
    assert f["note"][0]["authorReference"] == {"reference": "Practitioner/30001"}
    assert f["mitigation"] == "Statins"


async def test_validation_errors(client):
    assert (await client.post(BASE + "/", json={**MINIMAL, "bogus": 1})).status_code == 400
    assert (await client.post(BASE + "/", json={"user_id": "u", "status": "final"})).status_code == 400   # subject required
    assert (await client.post(BASE + "/", json={"user_id": "u", "subject": "Patient/1"})).status_code == 400  # status required
    assert (await client.post(BASE + "/", json={**MINIMAL, "status": "bogus"})).status_code == 400


async def test_prediction_rules(client):
    def pred(**kw):
        return {**MINIMAL, "prediction": [kw]}

    assert (await client.post(BASE + "/", json=pred(probability_decimal=150))).status_code == 400            # ras-2
    assert (await client.post(BASE + "/", json=pred(probability_range_low_value=1, probability_range_low_code="mg"))).status_code == 400  # ras-1
    assert (await client.post(BASE + "/", json=pred(probability_range_high_value=250))).status_code == 400   # ras-1 bounds
    assert (await client.post(BASE + "/", json=pred(probability_decimal=5, probability_range_low_value=1))).status_code == 400
    assert (await client.post(BASE + "/", json=pred(when_period_start="2024-01-01T00:00:00Z", when_range_low_value=1))).status_code == 400
    assert (await client.post(BASE + "/", json={**MINIMAL, "occurrence_datetime": "2024-01-01T00:00:00Z",
                                                 "occurrence_period_start": "2024-01-01T00:00:00Z"})).status_code == 400


async def test_reference_format_checks(client):
    for field, bad in (("subject", "Practitioner/1"), ("subject", "Patient/abc"), ("subject", "Patient"),
                       ("condition", "Observation/1"), ("performer", "Patient/1"), ("based_on", "nope")):
        r = await client.post(BASE + "/", json={**MINIMAL, field: bad})
        assert r.status_code == 422, (field, bad, r.status_code)
    assert (await client.post(BASE + "/", json={**MINIMAL, "basis": [{"reference": "x"}]})).status_code == 422
    assert (await client.post(BASE + "/", json={**MINIMAL, "reason_reference": [{"reference": "Patient/1"}]})).status_code == 422
    # any resource type is fine for the open Reference(Any) fields
    assert (await client.post(BASE + "/", json={**MINIMAL, "based_on": "Anything/5", "basis": [{"reference": "Foo/1"}]})).status_code == 200


async def test_get_not_found_patch_delete(client):
    data = await _create(client, full_payload())
    assert (await client.get(f"{BASE}/{data['id']}")).json()["id"] == data["id"]
    assert (await client.get(f"{BASE}/{data['id']}", headers=FHIR_ACCEPT)).json()["id"] == str(data["id"])
    assert (await client.get(f"{BASE}/9999999")).status_code == 404

    r = await client.patch(f"{BASE}/{data['id']}", json={
        "status": "amended", "mitigation": "More", "subject": "Group/3", "condition": "Condition/120002",
        "performer": "Device/9", "based_on": "CarePlan/7",
    })
    assert r.status_code == 200, r.text
    b = r.json()
    assert (b["status"], b["mitigation"], b["subject_type"], b["condition_id"], b["performer_type"]) == ("amended", "More", "Group", 120002, "Device")
    assert (b["based_on_type"], b["based_on_id"]) == ("CarePlan", 7)
    r = await client.patch(f"{BASE}/{data['id']}", json={"condition": None, "performer": None})
    b = r.json()
    assert b["condition_id"] is None and b["performer_id"] is None and len(b["prediction"]) == 2

    for body in ({"status": None}, {"subject": None}, {"status": "bogus"}, {"bogus": []}):
        assert (await client.patch(f"{BASE}/{data['id']}", json=body)).status_code == 400
    assert (await client.patch(f"{BASE}/{data['id']}", json={"performer": "Patient/1"})).status_code == 422
    assert (await client.patch(f"{BASE}/9999999", json={"status": "final"})).status_code == 404

    assert (await client.delete(f"{BASE}/{data['id']}")).status_code == 204
    assert (await client.get(f"{BASE}/{data['id']}")).status_code == 404
    assert (await client.delete(f"{BASE}/{data['id']}")).status_code == 404


# ── list / search ─────────────────────────────────────────────────────────────


async def test_list_pagination_and_ordering(client):
    undated = await _create(client)
    dated = await _create(client, {**MINIMAL, "occurrence_datetime": "2024-01-01T00:00:00Z"})
    for _ in range(2):
        await _create(client)
    r = await client.get(f"{BASE}/?org_id=org-test&limit=2")
    assert len(r.json()["data"]) == 2 and r.json()["total"] == 4
    ids = [d["id"] for d in (await client.get(BASE + "/?org_id=org-test")).json()["data"]]
    assert ids.index(dated["id"]) < ids.index(undated["id"])
    assert (await client.get(BASE + "/?org_id=org-test", headers=FHIR_ACCEPT)).json()["resourceType"] == "Bundle"


async def test_search_params(client):
    a = await _create(client, full_payload())
    b = await _create(client, {**MINIMAL, "status": "preliminary", "subject": "Patient/10002"})
    assert await _ids(client, f"_id={a['id']}") == {a["id"]}
    assert await _ids(client, "status=preliminary") == {b["id"]}
    assert await _ids(client, "status=preliminary,final") == {a["id"], b["id"]}
    assert (await client.get(BASE + "/?" + _with_org("status=bogus"))).status_code == 422
    assert await _ids(client, "identifier=urn:ra|RA-1") == {a["id"]}
    assert await _ids(client, "method=http://example.org/methods|framingham") == {a["id"]}
    assert await _ids(client, "method=framingham") == {a["id"]}
    assert await _ids(client, "patient=Patient/10001") == {a["id"]}
    assert await _ids(client, "patient=10002") == {b["id"]}
    assert await _ids(client, "subject=Patient/10001") == {a["id"]}
    assert await _ids(client, "condition=Condition/120001") == {a["id"]}
    assert await _ids(client, "performer=Practitioner/30001") == {a["id"]}
    assert await _ids(client, "performer=Practitioner/39999") == set()
    assert await _ids(client, "risk=moderate") == {a["id"]}
    assert await _ids(client, "risk=http://terminology.hl7.org/CodeSystem/risk-probability|moderate") == {a["id"]}
    assert await _ids(client, "risk=low") == set()
    assert await _ids(client, "date=2024-03-15") == {a["id"]}
    assert await _ids(client, "date=ge2024-01-01&date=lt2024-06-01") == {a["id"]}
    assert await _ids(client, "date=gt2025-01-01") == set()
    assert a["id"] in await _ids(client, "_lastUpdated=ge2000-01-01")
    for bad in ("patient=Group/1", "subject=Practitioner/1", "condition=Patient/1", "performer=Patient/1",
                "date=notadate", "probability=abc", "_id=x"):
        assert (await client.get(f"{BASE}/?{_with_org(bad)}")).status_code == 422, bad


async def test_search_probability(client):
    a = await _create(client, full_payload())  # predictions: decimal 12.5 and range 40-60
    other = await _create(client, {**MINIMAL, "prediction": [{"probability_decimal": 90}]})
    assert await _ids(client, "probability=12.5") == {a["id"]}
    assert await _ids(client, "probability=50") == {a["id"]}               # inside the 40-60 range
    assert await _ids(client, "probability=gt80") == {other["id"]}
    assert await _ids(client, "probability=ge90") == {other["id"]}
    assert await _ids(client, "probability=lt10") == set()
    assert await _ids(client, "probability=le12.5") == {a["id"]}
    assert await _ids(client, "probability=ne12.5") >= {other["id"]}
    assert await _ids(client, "probability=ge10&probability=le20") == {a["id"]}   # AND across values


async def test_search_scoped_by_org_and_optional_user(client):
    a = await _create(client, {**MINIMAL, "user_id": "user-a", "org_id": "org-a"})
    b = await _create(client, {**MINIMAL, "user_id": "user-b", "org_id": "org-b"})
    assert await _ids(client, "user_id=user-a&org_id=org-a") == {a["id"]}
    assert await _ids(client, "org_id=org-b") == {b["id"]}                  # org scopes the result
    assert await _ids(client, "org_id=org-a&user_id=user-b") == set()       # user_id narrows further
    assert await _ids(client, "org_id=org-a") == {a["id"]}


# ── PATCH replaces child lists ────────────────────────────────────────────────


async def test_patch_replaces_child_lists(client):
    data = await _create(client, full_payload())
    rid = data["id"]
    assert len(data["prediction"]) == 2 and len(data["basis"]) == 2 and len(data["note"]) == 1

    r = await client.patch(f"{BASE}/{rid}", json={
        "status": "amended",
        "prediction": [{"outcome_text": "Heart failure", "probability_decimal": 70, "qualitative_risk_code": "high"}],
        "basis": [{"reference": "Observation/160009"}],
        "reason_reference": [],
    })
    assert r.status_code == 200, r.text
    b = r.json()
    assert b["status"] == "amended"
    assert [p["outcome_text"] for p in b["prediction"]] == ["Heart failure"]      # replaced
    assert b["prediction"][0]["probability_decimal"] == 70
    assert [(x["reference_type"], x["reference_id"]) for x in b["basis"]] == [("Observation", 160009)]
    assert b["reason_reference"] == []                                              # [] cleared
    assert len(b["note"]) == 1 and len(b["reason_code"]) == 1                       # omitted untouched

    # replaced predictions are searchable, old ones are gone
    assert rid in await _ids(client, "probability=70")
    assert await _ids(client, "probability=12.5") == set()
    assert await _ids(client, "risk=moderate") == set()

    # validation applies to replaced lists
    assert (await client.patch(f"{BASE}/{rid}", json={"prediction": [{"probability_decimal": 150}]})).status_code == 400
    assert (await client.patch(f"{BASE}/{rid}", json={"reason_reference": [{"reference": "Patient/1"}]})).status_code == 422


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
