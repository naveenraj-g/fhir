"""Integration tests for /api/fhir/v1/questionnaire-responses endpoints."""
BASE = "/api/fhir/v1/questionnaire-responses"
FHIR_ACCEPT = {"Accept": "application/fhir+json"}


def _with_org(query: str) -> str:
    """Every search requires org_id (tenant scope) — add the default test org unless the query sets one."""
    if "org_id=" in query:
        return query
    return f"org_id=org-test&{query}" if query else "org_id=org-test"

MINIMAL = {"user_id": "u-test", "org_id": "org-test", "status": "completed"}

QUESTIONNAIRE_URL = "http://example.org/fhir/Questionnaire/phq-9"


def full_payload(**overrides) -> dict:
    """Exercises every answer value type and a 4-level item tree (including items nested under answers)."""
    payload = {
        **MINIMAL,
        "questionnaire": QUESTIONNAIRE_URL,
        "identifier_system": "urn:qr", "identifier_value": "QR-1",
        "subject": "Patient/10001", "subject_display": "John",
        "authored": "2024-06-01T09:00:00Z",
        "author": "Practitioner/30001", "source": "Patient/10001",
        "based_on": [{"reference": "ServiceRequest/80001"}],
        "part_of": [{"reference": "Procedure/100001"}],
        "item": [
            {
                "link_id": "g1", "text": "Group",
                "item": [
                    {"link_id": "g1.1", "answer": [{"value_coding": {"system": "http://loinc.org", "code": "LA6568-5", "display": "Not at all"}}]},
                    {
                        "link_id": "g1.2",
                        "answer": [{
                            "value_boolean": True,
                            # item nested UNDER an answer, itself holding a deeper nested group
                            "item": [{"link_id": "g1.2.a", "answer": [{"value_string": "because"}],
                                      "item": [{"link_id": "g1.2.a.x", "answer": [{"value_integer": 3}]}]}],
                        }],
                    },
                ],
            },
            {"link_id": "dt", "answer": [{"value_date": "2024-06-01"}]},
            {"link_id": "tm", "answer": [{"value_time": "09:30:00"}]},
            {"link_id": "uri", "answer": [{"value_uri": "http://example.org/x"}]},
            {"link_id": "dtm", "answer": [{"value_datetime": "2024-06-01T09:30:00Z"}]},
            {"link_id": "dec", "answer": [{"value_decimal": 1.5}]},
            {"link_id": "qty", "answer": [{"value_quantity": {"value": 70, "unit": "kg"}}]},
            {"link_id": "ref", "answer": [{"value_reference": "Practitioner/30001", "value_reference_display": "Dr"}]},
            {"link_id": "att", "answer": [{"value_attachment": {"content_type": "application/pdf", "url": "http://x/y.pdf", "size": 10}}]},
            {"link_id": "rep", "answer": [{"value_string": "a"}, {"value_string": "b"}]},
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


def _by_link(items) -> dict:
    return {i["link_id"]: i for i in items}


# ── CRUD ──────────────────────────────────────────────────────────────────────


async def test_create_minimal_without_questionnaire(client):
    data = await _create(client)  # questionnaire is 0..1 in R4
    assert data["status"] == "completed"
    assert "questionnaire" not in data


async def test_create_full_plain_tree(client):
    data = await _create(client, full_payload())
    assert (data["subject_type"], data["subject_id"]) == ("Patient", 10001)
    assert data["author_type"] == "Practitioner" and data["source_type"] == "Patient"
    assert data["based_on"][0]["reference_type"] == "ServiceRequest"
    top = _by_link(data["item"])
    # items nested under answers must NOT leak into the top level
    assert set(top) == {"g1", "dt", "tm", "uri", "dtm", "dec", "qty", "ref", "att", "rep"}
    g1 = _by_link(top["g1"]["item"])
    assert list(g1) == ["g1.1", "g1.2"]
    ans = g1["g1.2"]["answer"][0]
    assert ans["value_boolean"] is True
    deep = ans["item"][0]
    assert deep["link_id"] == "g1.2.a" and deep["answer"][0]["value_string"] == "because"
    assert deep["item"][0]["link_id"] == "g1.2.a.x" and deep["item"][0]["answer"][0]["value_integer"] == 3
    # typed answer columns
    assert top["dt"]["answer"][0]["value_date"] == "2024-06-01"
    assert top["tm"]["answer"][0]["value_time"] == "09:30:00"
    assert top["uri"]["answer"][0]["value_uri"] == "http://example.org/x"
    assert top["rep"]["answer"][0]["value_string"] == "a" and top["rep"]["answer"][1]["value_string"] == "b"


async def test_fhir_format(client):
    r = await client.post(BASE + "/", json=full_payload(), headers=FHIR_ACCEPT)
    assert r.status_code == 200, r.text
    f = r.json()
    assert f["resourceType"] == "QuestionnaireResponse" and f["questionnaire"] == QUESTIONNAIRE_URL
    assert f["subject"] == {"reference": "Patient/10001", "display": "John"}
    assert f["identifier"]["value"] == "QR-1"
    assert f["basedOn"] == [{"reference": "ServiceRequest/80001"}] and f["partOf"] == [{"reference": "Procedure/100001"}]
    top = {i["linkId"]: i for i in f["item"]}
    assert "g1.2.a" not in top
    assert top["dt"]["answer"] == [{"valueDate": "2024-06-01"}]
    assert top["tm"]["answer"] == [{"valueTime": "09:30:00"}]
    assert top["uri"]["answer"] == [{"valueUri": "http://example.org/x"}]
    assert top["qty"]["answer"] == [{"valueQuantity": {"value": 70.0, "unit": "kg"}}]
    assert top["ref"]["answer"][0]["valueReference"] == {"reference": "Practitioner/30001", "display": "Dr"}
    nested = top["g1"]["item"][1]["answer"][0]
    assert nested["valueBoolean"] is True and nested["item"][0]["item"][0]["answer"] == [{"valueInteger": 3}]


async def test_open_subject_type(client):
    data = await _create(client, {**MINIMAL, "subject": "Practitioner/30001"})
    assert (data["subject_type"], data["subject_id"]) == ("Practitioner", 30001)


async def test_validation_errors(client):
    assert (await client.post(BASE + "/", json={**MINIMAL, "bogus": 1})).status_code == 400
    assert (await client.post(BASE + "/", json={"user_id": "u"})).status_code == 400          # status required
    assert (await client.post(BASE + "/", json={**MINIMAL, "status": "bogus"})).status_code == 400
    two = {**MINIMAL, "item": [{"link_id": "a", "answer": [{"value_string": "x", "value_boolean": True}]}]}
    assert (await client.post(BASE + "/", json=two)).status_code == 400                       # at most one value[x]


async def test_reference_format_checks(client):
    # Format is validated (never existence).
    for field, bad in (("subject", "Patient/abc"), ("subject", "Patient"), ("author", "Condition/1"),
                       ("source", "Device/1"), ("encounter", "Encounter/xyz")):
        r = await client.post(BASE + "/", json={**MINIMAL, field: bad})
        assert r.status_code == 422, (field, bad, r.status_code)
    assert (await client.post(BASE + "/", json={**MINIMAL, "based_on": [{"reference": "Patient/1"}]})).status_code == 422
    answer_ref = {**MINIMAL, "item": [{"link_id": "a", "answer": [{"value_reference": "nope"}]}]}
    assert (await client.post(BASE + "/", json=answer_ref)).status_code == 422


async def test_get_plain_fhir_not_found(client):
    data = await _create(client, full_payload())
    assert (await client.get(f"{BASE}/{data['id']}")).json()["id"] == data["id"]
    assert (await client.get(f"{BASE}/{data['id']}", headers=FHIR_ACCEPT)).json()["id"] == str(data["id"])
    assert (await client.get(f"{BASE}/9999999")).status_code == 404


async def test_patch(client):
    data = await _create(client, full_payload())
    r = await client.patch(f"{BASE}/{data['id']}", json={
        "status": "amended", "questionnaire": "http://other", "subject": "Group/5",
        "author": "Patient/10002", "source": "RelatedPerson/300001",
    })
    assert r.status_code == 200, r.text
    b = r.json()
    assert (b["status"], b["questionnaire"], b["subject_type"], b["subject_id"]) == ("amended", "http://other", "Group", 5)
    assert (b["author_type"], b["author_id"], b["source_type"]) == ("Patient", 10002, "RelatedPerson")
    # clearing optional references with null
    r = await client.patch(f"{BASE}/{data['id']}", json={"subject": None, "author": None})
    b = r.json()
    assert "subject_id" not in b and "author_id" not in b and "subject_display" not in b
    assert len(b["item"]) == 10  # items untouched


async def test_patch_rejections(client):
    data = await _create(client)
    for body in ({"status": None}, {"status": "bogus"}, {"bogus": []}):
        assert (await client.patch(f"{BASE}/{data['id']}", json=body)).status_code == 400
    assert (await client.patch(f"{BASE}/{data['id']}", json={"author": "Condition/1"})).status_code == 422
    assert (await client.patch(f"{BASE}/9999999", json={"status": "completed"})).status_code == 404


async def test_delete_cascades(client):
    data = await _create(client, full_payload())
    assert (await client.delete(f"{BASE}/{data['id']}")).status_code == 204
    assert (await client.get(f"{BASE}/{data['id']}")).status_code == 404
    assert (await client.delete(f"{BASE}/{data['id']}")).status_code == 404


async def test_deep_nesting_no_lazy_load_crash(client):
    leaf = {"link_id": "l6", "answer": [{"value_string": "end"}]}
    node = leaf
    for n in (5, 4, 3, 2, 1):
        node = {"link_id": f"g{n}", "item": [node]}
    data = await _create(client, {**MINIMAL, "item": [node]})
    cur, depth = data["item"][0], 1
    while cur.get("item"):
        cur, depth = cur["item"][0], depth + 1
    assert (cur["link_id"], depth) == ("l6", 6)
    assert (await client.get(f"{BASE}/{data['id']}", headers=FHIR_ACCEPT)).status_code == 200


# ── list / search ─────────────────────────────────────────────────────────────


async def test_list_plain_fhir_pagination(client):
    for _ in range(3):
        await _create(client)
    r = await client.get(f"{BASE}/?org_id=org-test&limit=2")
    assert len(r.json()["data"]) == 2 and r.json()["total"] == 3
    assert (await client.get(BASE + "/?org_id=org-test", headers=FHIR_ACCEPT)).json()["resourceType"] == "Bundle"


async def test_list_nulls_last(client):
    undated = await _create(client)
    dated = await _create(client, {**MINIMAL, "authored": "2024-01-01T00:00:00Z"})
    ids = [d["id"] for d in (await client.get(BASE + "/?org_id=org-test")).json()["data"]]
    assert ids.index(dated["id"]) < ids.index(undated["id"])


async def test_search_params(client):
    a = await _create(client, full_payload())
    b = await _create(client, {**MINIMAL, "status": "in-progress", "subject": "Patient/10002", "questionnaire": "Questionnaire/370001"})
    assert await _ids(client, f"_id={a['id']}") == {a["id"]}
    assert await _ids(client, "status=in-progress") == {b["id"]}
    assert await _ids(client, "status=in-progress,completed") == {a["id"], b["id"]}
    assert (await client.get(BASE + "/?" + _with_org("status=bogus"))).status_code == 422
    assert await _ids(client, "identifier=urn:qr|QR-1") == {a["id"]}
    assert await _ids(client, f"questionnaire={QUESTIONNAIRE_URL}") == {a["id"]}
    assert await _ids(client, "questionnaire=Questionnaire/370001") == {b["id"]}
    assert await _ids(client, "questionnaire=370001") == {b["id"]}
    assert await _ids(client, "patient=Patient/10001") == {a["id"]}
    assert await _ids(client, "patient=10002") == {b["id"]}
    assert await _ids(client, "patient_id=10001") == {a["id"]}
    assert await _ids(client, "subject=Patient/10001") == {a["id"]}
    assert await _ids(client, "author=Practitioner/30001") == {a["id"]}
    assert await _ids(client, "source=Patient/10001") == {a["id"]}
    assert await _ids(client, "based-on=ServiceRequest/80001") == {a["id"]}
    assert await _ids(client, "part-of=Procedure/100001") == {a["id"]}
    assert await _ids(client, "authored=2024-06-01") == {a["id"]}
    assert await _ids(client, "authored=ge2024-01-01&authored=lt2024-07-01") == {a["id"]}
    assert await _ids(client, "authored=gt2025-01-01") == set()
    assert a["id"] in await _ids(client, "_lastUpdated=ge2000-01-01")
    for bad in ("patient=Group/1", "author=Condition/1", "based-on=Patient/1", "authored=notadate", "_id=x"):
        assert (await client.get(f"{BASE}/?{_with_org(bad)}")).status_code == 422, bad


async def test_search_scoped_by_org_and_optional_user(client):
    a = await _create(client, {**MINIMAL, "user_id": "user-a", "org_id": "org-a"})
    b = await _create(client, {**MINIMAL, "user_id": "user-b", "org_id": "org-b"})
    assert await _ids(client, "user_id=user-a&org_id=org-a") == {a["id"]}
    assert await _ids(client, "org_id=org-b") == {b["id"]}                  # org scopes the result
    assert await _ids(client, "org_id=org-a&user_id=user-b") == set()       # user_id narrows further
    assert await _ids(client, "org_id=org-a") == {a["id"]}


# ── PATCH replaces child lists and the item/answer tree ───────────────────────


async def test_patch_replaces_lists_and_item_tree(client):
    data = await _create(client, full_payload())
    qid = data["id"]

    r = await client.patch(f"{BASE}/{qid}", json={
        "based_on": [{"reference": "CarePlan/290001"}, {"reference": "ServiceRequest/80002"}],
        "part_of": [],
    })
    assert r.status_code == 200, r.text
    b = r.json()
    assert [(x["reference_type"], x["reference_id"]) for x in b["based_on"]] == [("CarePlan", 290001), ("ServiceRequest", 80002)]
    assert "part_of" not in b                                    # [] cleared it
    assert len(b["item"]) == 10                                   # item tree untouched

    new_tree = [{
        "link_id": "root",
        "item": [{"link_id": "a", "answer": [{"value_integer": 42, "item": [{"link_id": "a1", "answer": [{"value_string": "why"}]}]}]}],
    }]
    r = await client.patch(f"{BASE}/{qid}", json={"status": "amended", "item": new_tree})
    assert r.status_code == 200, r.text
    b = r.json()
    assert b["status"] == "amended"
    assert [i["link_id"] for i in b["item"]] == ["root"]          # old 10 top-level items are gone
    a = b["item"][0]["item"][0]
    assert a["answer"][0]["value_integer"] == 42 and a["answer"][0]["item"][0]["link_id"] == "a1"
    assert len(b["based_on"]) == 2                                # still there

    # persisted + FHIR shape
    f = (await client.get(f"{BASE}/{qid}", headers=FHIR_ACCEPT)).json()
    assert [i["linkId"] for i in f["item"]] == ["root"]

    # validation applies to replaced lists
    bad = [{"link_id": "x", "answer": [{"value_string": "a", "value_boolean": True}]}]
    assert (await client.patch(f"{BASE}/{qid}", json={"item": bad})).status_code == 400
    assert (await client.patch(f"{BASE}/{qid}", json={"based_on": [{"reference": "Patient/1"}]})).status_code == 422

    # [] clears the whole tree
    r = await client.patch(f"{BASE}/{qid}", json={"item": []})
    assert "item" not in r.json()


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
    data = await _create(client, {**MINIMAL, "encounter": "Encounter/987654"})
    assert (data["encounter_type"], data["encounter_id"]) == ("Encounter", 987654)
    fhir = (await client.get(f"{BASE}/{data['id']}", headers=FHIR_ACCEPT)).json()
    assert fhir["encounter"]["reference"] == "Encounter/987654"
    assert await _ids(client, "encounter=Encounter/987654") == {data["id"]}
    assert await _ids(client, "encounter=987654") == {data["id"]}
    assert await _ids(client, "encounter=1") == set()
    assert (await client.get(f"{BASE}/?{_with_org('encounter=Patient/1')}")).status_code == 422   # type still checked
    cleared = (await client.patch(f"{BASE}/{data['id']}", json={"encounter": None})).json()
    assert cleared.get("encounter_id") is None   # QR plain output omits empty fields
