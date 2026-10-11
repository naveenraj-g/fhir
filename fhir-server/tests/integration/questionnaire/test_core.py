"""Integration tests for /api/fhir/v1/questionnaires endpoints."""
BASE = "/api/fhir/v1/questionnaires"
FHIR_ACCEPT = {"Accept": "application/fhir+json"}


def _with_org(query: str) -> str:
    """Every search requires org_id (tenant scope) — add the default test org unless the query sets one."""
    if "org_id=" in query:
        return query
    return f"org_id=org-test&{query}" if query else "org_id=org-test"

MINIMAL = {"user_id": "u-test", "org_id": "org-test", "status": "draft"}


def full_payload(**overrides) -> dict:
    """A realistic form exercising every child table and a 3-level item tree."""
    payload = {
        **MINIMAL,
        "status": "active",
        "url": "http://example.org/fhir/Questionnaire/phq-2",
        "version": "1.0.0",
        "name": "phq_2",
        "title": "PHQ-2 depression screener",
        "experimental": False,
        "date": "2024-03-01T00:00:00Z",
        "publisher": "Example Health",
        "description": "Two-question screener",
        "approval_date": "2024-02-01",
        "effective_period_start": "2024-03-01T00:00:00Z",
        "effective_period_end": "2025-03-01T00:00:00Z",
        "derived_from": ["http://example.org/fhir/Questionnaire/base"],
        "identifier": [{"system": "urn:forms", "value": "PHQ2"}],
        "subject_type": ["Patient", "RelatedPerson"],
        "contact": [{"name": "Forms team", "telecom": [{"system": "email", "value": "forms@example.org"}]}],
        "use_context": [{
            "code_system": "http://terminology.hl7.org/CodeSystem/usage-context-type",
            "code_code": "focus",
            "value_cc_system": "http://snomed.info/sct",
            "value_cc_code": "35489007",
            "value_cc_display": "Depressive disorder",
        }],
        "jurisdiction": [{"coding_system": "urn:iso:std:iso:3166", "coding_code": "US"}],
        "code": [{"system": "http://loinc.org", "code": "55757-9", "display": "PHQ-2"}],
        "item": [
            {
                "link_id": "g1",
                "type": "group",
                "text": "Over the last 2 weeks",
                "item": [
                    {
                        "link_id": "1",
                        "type": "choice",
                        "text": "Little interest or pleasure in doing things?",
                        "definition": "http://example.org/def/interest",
                        "required": True,
                        "code": [{"system": "http://loinc.org", "code": "44250-9"}],
                        "answer_option": [
                            {"value_coding_system": "http://loinc.org", "value_coding_code": "LA6568-5",
                             "value_coding_display": "Not at all", "initial_selected": True},
                            {"value_coding_system": "http://loinc.org", "value_coding_code": "LA6569-3",
                             "value_coding_display": "Several days"},
                        ],
                    },
                    {
                        "link_id": "2",
                        "type": "string",
                        "text": "Describe your symptoms",
                        "max_length": 200,
                        "enable_when": [{"question": "1", "operator": "!=", "answer_coding_code": "LA6568-5"}],
                        "initial": [{"value_string": "none"}],
                    },
                ],
            },
            {"link_id": "d1", "type": "display", "text": "Thank you."},
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
    assert isinstance(data["id"], int)
    assert data["status"] == "draft"
    assert data["item"] == []


async def test_create_full_plain_tree(client):
    data = await _create(client, full_payload())
    assert data["url"].endswith("phq-2")
    assert [s["code"] for s in data["subject_type"]] == ["Patient", "RelatedPerson"]
    assert data["contact"][0]["telecom"][0]["value"] == "forms@example.org"
    assert data["use_context"][0]["value_cc_code"] == "35489007"
    # tree: g1 -> (1, 2) and d1 at top level, in creation order
    assert [i["link_id"] for i in data["item"]] == ["g1", "d1"]
    g1 = data["item"][0]
    assert [i["link_id"] for i in g1["item"]] == ["1", "2"]
    q1, q2 = g1["item"]
    assert q1["type"] == "choice" and len(q1["answer_option"]) == 2
    assert q1["answer_option"][0]["initial_selected"] is True
    assert q1["code"][0]["code"] == "44250-9"
    assert q2["enable_when"][0]["operator"] == "!="
    assert q2["enable_when"][0]["answer_coding_code"] == "LA6568-5"
    assert q2["initial"][0]["value_string"] == "none"


async def test_create_fhir_format(client):
    r = await client.post(BASE + "/", json=full_payload(), headers=FHIR_ACCEPT)
    assert r.status_code == 200, r.text
    fhir = r.json()
    assert fhir["resourceType"] == "Questionnaire"
    assert fhir["status"] == "active"
    assert fhir["subjectType"] == ["Patient", "RelatedPerson"]
    assert fhir["useContext"][0]["valueCodeableConcept"]["coding"][0]["code"] == "35489007"
    assert fhir["effectivePeriod"]["start"].startswith("2024-03-01")
    assert fhir["derivedFrom"] == ["http://example.org/fhir/Questionnaire/base"]
    g1 = fhir["item"][0]
    assert g1["linkId"] == "g1" and g1["type"] == "group"
    q1, q2 = g1["item"]
    assert q1["answerOption"][0]["valueCoding"]["code"] == "LA6568-5"
    assert q1["answerOption"][0]["initialSelected"] is True
    assert q2["enableWhen"][0] == {"question": "1", "operator": "!=", "answerCoding": {"code": "LA6568-5"}}
    assert q2["initial"][0] == {"valueString": "none"}
    assert q2["maxLength"] == 200
    assert fhir["item"][1]["type"] == "display"


async def test_extra_field_rejected(client):
    assert (await client.post(BASE + "/", json={**MINIMAL, "bogus": 1})).status_code == 400


async def test_status_required_and_validated(client):
    assert (await client.post(BASE + "/", json={"user_id": "u"})).status_code == 400
    assert (await client.post(BASE + "/", json={**MINIMAL, "status": "bogus"})).status_code == 400


async def test_get_plain_and_fhir(client):
    data = await _create(client, full_payload())
    r = await client.get(f"{BASE}/{data['id']}")
    assert r.status_code == 200 and r.json()["id"] == data["id"]
    r = await client.get(f"{BASE}/{data['id']}", headers=FHIR_ACCEPT)
    assert r.json()["id"] == str(data["id"])


async def test_get_not_found(client):
    assert (await client.get(f"{BASE}/9999999")).status_code == 404


async def test_patch(client):
    data = await _create(client)
    r = await client.patch(f"{BASE}/{data['id']}", json={"status": "retired", "title": "Old", "derived_from": ["http://a", "http://b"]})
    assert r.status_code == 200
    body = r.json()
    assert (body["status"], body["title"], body["derived_from"]) == ("retired", "Old", ["http://a", "http://b"])


async def test_patch_rejects_null_and_invalid_status(client):
    data = await _create(client)
    assert (await client.patch(f"{BASE}/{data['id']}", json={"status": None})).status_code == 400
    assert (await client.patch(f"{BASE}/{data['id']}", json={"status": "bogus"})).status_code == 400
    assert (await client.patch(f"{BASE}/{data['id']}", json={"bogus": []})).status_code == 400  # unknown field


async def test_patch_not_found(client):
    assert (await client.patch(f"{BASE}/9999999", json={"status": "active"})).status_code == 404


async def test_delete_cascades(client):
    data = await _create(client, full_payload())
    assert (await client.delete(f"{BASE}/{data['id']}")).status_code == 204
    assert (await client.get(f"{BASE}/{data['id']}")).status_code == 404


async def test_delete_not_found(client):
    assert (await client.delete(f"{BASE}/9999999")).status_code == 404


# ── R4 item invariants ────────────────────────────────────────────────────────


async def _bad_item(client, item) -> int:
    return (await client.post(BASE + "/", json={**MINIMAL, "item": [item]})).status_code


async def test_item_invariants(client):
    assert await _bad_item(client, {"link_id": "a", "type": "group"}) == 400  # que-1 group needs items
    assert await _bad_item(client, {"link_id": "a", "type": "display", "item": [{"link_id": "b", "type": "string"}]}) == 400  # que-2
    assert await _bad_item(client, {"link_id": "a", "type": "display", "code": [{"code": "x"}]}) == 400  # que-3
    assert await _bad_item(client, {"link_id": "a", "type": "choice", "answer_value_set": "http://vs",
                                    "answer_option": [{"value_string": "x"}]}) == 400  # que-4
    assert await _bad_item(client, {"link_id": "a", "type": "string", "answer_value_set": "http://vs"}) == 400  # que-5
    assert await _bad_item(client, {"link_id": "a", "type": "display", "required": True}) == 400  # que-6
    assert await _bad_item(client, {"link_id": "a", "type": "choice", "max_length": 5}) == 400  # que-10
    assert await _bad_item(client, {"link_id": "a", "type": "choice", "initial": [{"value_string": "x"}],
                                    "answer_option": [{"value_string": "y"}]}) == 400  # que-11
    assert await _bad_item(client, {"link_id": "a", "type": "string", "initial": [{"value_string": "x"}, {"value_string": "y"}]}) == 400  # que-13
    assert await _bad_item(client, {"link_id": "a", "type": "string", "enable_when": [
        {"question": "q", "operator": "=", "answer_string": "x"}, {"question": "r", "operator": "=", "answer_string": "y"}]}) == 400  # que-12


async def test_choice_type_exactly_one_variant(client):
    two = {"link_id": "a", "type": "string", "initial": [{"value_string": "x", "value_boolean": True}]}
    none = {"link_id": "a", "type": "string", "initial": [{}]}
    assert await _bad_item(client, two) == 400
    assert await _bad_item(client, none) == 400
    bad_exists = {"link_id": "a", "type": "string", "enable_when": [{"question": "q", "operator": "exists", "answer_string": "x"}]}
    assert await _bad_item(client, bad_exists) == 400  # que-7


async def test_duplicate_link_id_rejected(client):
    payload = {**MINIMAL, "item": [
        {"link_id": "x", "type": "string"},
        {"link_id": "g", "type": "group", "item": [{"link_id": "x", "type": "string"}]},
    ]}
    assert (await client.post(BASE + "/", json=payload)).status_code == 400


async def test_use_context_requires_one_value(client):
    payload = {**MINIMAL, "use_context": [{"code_code": "focus"}]}
    assert (await client.post(BASE + "/", json=payload)).status_code == 400


async def test_deep_nesting_roundtrip(client):
    leaf = {"link_id": "l4", "type": "string"}
    node = leaf
    for n in (3, 2, 1):
        node = {"link_id": f"g{n}", "type": "group", "item": [node]}
    data = await _create(client, {**MINIMAL, "item": [node]})
    cur, depth = data["item"][0], 1
    while cur["item"]:
        cur, depth = cur["item"][0], depth + 1
    assert (cur["link_id"], depth) == ("l4", 4)


# ── list / pagination ─────────────────────────────────────────────────────────


async def test_list_plain_and_fhir(client):
    await _create(client)
    r = await client.get(BASE + "/?org_id=org-test")
    assert r.status_code == 200 and r.json()["total"] >= 1
    r = await client.get(BASE + "/?org_id=org-test", headers=FHIR_ACCEPT)
    assert r.json()["resourceType"] == "Bundle"


async def test_list_pagination(client):
    for _ in range(3):
        await _create(client)
    r = await client.get(f"{BASE}/?org_id=org-test&limit=2&offset=0")
    assert len(r.json()["data"]) == 2 and r.json()["total"] == 3


# ── FHIR R4 search parameters ─────────────────────────────────────────────────


async def test_search_basic_tokens(client):
    a = await _create(client, full_payload())
    b = await _create(client, {**MINIMAL, "status": "retired", "name": "other", "title": "Other form", "version": "9"})
    assert await _ids(client, f"_id={a['id']}") == {a["id"]}
    assert await _ids(client, "status=retired") == {b["id"]}
    assert await _ids(client, "status=retired,active") == {a["id"], b["id"]}
    assert (await client.get(BASE + "/?" + _with_org("status=bogus"))).status_code == 422
    assert await _ids(client, "url=http://example.org/fhir/Questionnaire/phq-2") == {a["id"]}
    assert await _ids(client, "version=9") == {b["id"]}
    assert await _ids(client, "identifier=urn:forms|PHQ2") == {a["id"]}
    assert await _ids(client, "identifier=PHQ2") == {a["id"]}
    assert await _ids(client, "jurisdiction=urn:iso:std:iso:3166|US") == {a["id"]}
    assert await _ids(client, "subject-type=RelatedPerson") == {a["id"]}
    assert await _ids(client, "context=http://snomed.info/sct|35489007") == {a["id"]}
    assert await _ids(client, "context-type=focus") == {a["id"]}


async def test_search_strings_with_modifiers(client):
    a = await _create(client, full_payload())
    assert await _ids(client, "name=PHQ") == {a["id"]}               # prefix, case-insensitive
    assert await _ids(client, "name=2") == set()                     # not a prefix
    assert await _ids(client, "name:contains=hq_") == {a["id"]}
    assert await _ids(client, "name:exact=phq_2") == {a["id"]}
    assert await _ids(client, "name:exact=PHQ_2") == set()           # exact is case-sensitive
    assert await _ids(client, "title:contains=depression") == {a["id"]}
    assert await _ids(client, "publisher=example") == {a["id"]}
    assert await _ids(client, "description:contains=screener") == {a["id"]}


async def test_search_item_code_and_definition(client):
    a = await _create(client, full_payload())
    other = await _create(client)
    assert await _ids(client, "code=http://loinc.org|44250-9") == {a["id"]}   # item.code
    assert await _ids(client, "code=55757-9") == {a["id"]}                    # questionnaire-level code
    assert await _ids(client, "code=nope") == set()
    assert await _ids(client, "definition=http://example.org/def/interest") == {a["id"]}
    assert other["id"] not in await _ids(client, "code=44250-9")


async def test_search_dates(client):
    a = await _create(client, full_payload())
    assert await _ids(client, "date=2024-03-01") == {a["id"]}
    assert await _ids(client, "date=ge2024-01-01&date=lt2024-06-01") == {a["id"]}
    assert await _ids(client, "date=gt2025-01-01") == set()
    assert await _ids(client, "effective=ap2024-09-01") == {a["id"]}          # inside effectivePeriod
    assert await _ids(client, "effective=lt2023-01-01") == set()
    assert a["id"] in await _ids(client, "_lastUpdated=ge2000-01-01")
    assert (await client.get(BASE + "/?" + _with_org("date=notadate"))).status_code == 422


async def test_search_scoped_by_org_and_optional_user(client):
    a = await _create(client, {**MINIMAL, "user_id": "user-a", "org_id": "org-a"})
    b = await _create(client, {**MINIMAL, "user_id": "user-b", "org_id": "org-b"})
    assert await _ids(client, "user_id=user-a&org_id=org-a") == {a["id"]}
    assert await _ids(client, "org_id=org-b") == {b["id"]}                  # org scopes the result
    assert await _ids(client, "org_id=org-a&user_id=user-b") == set()       # user_id narrows further
    assert await _ids(client, "org_id=org-a") == {a["id"]}


# ── PATCH replaces child lists and the item tree ──────────────────────────────


async def test_patch_replaces_child_lists(client):
    data = await _create(client, full_payload())
    qid = data["id"]
    r = await client.patch(f"{BASE}/{qid}", json={
        "subject_type": ["Group"],
        "code": [{"system": "http://loinc.org", "code": "NEW-1"}],
        "jurisdiction": [],
        "identifier": [{"system": "urn:forms", "value": "PHQ2-v2"}],
    })
    assert r.status_code == 200, r.text
    b = r.json()
    assert [s["code"] for s in b["subject_type"]] == ["Group"]
    assert [c["code"] for c in b["code"]] == ["NEW-1"]
    assert b["jurisdiction"] == []
    assert [i["value"] for i in b["identifier"]] == ["PHQ2-v2"]
    assert len(b["contact"]) == 1 and len(b["use_context"]) == 1       # omitted lists untouched
    assert [i["link_id"] for i in b["item"]] == ["g1", "d1"]            # item tree untouched


async def test_patch_replaces_item_tree(client):
    data = await _create(client, full_payload())
    qid = data["id"]
    new_tree = [{
        "link_id": "root", "type": "group", "item": [
            {"link_id": "q1", "type": "choice", "answer_option": [{"value_string": "yes"}, {"value_string": "no"}]},
            {"link_id": "q2", "type": "integer", "enable_when": [{"question": "q1", "operator": "=", "answer_string": "yes"}]},
        ],
    }]
    r = await client.patch(f"{BASE}/{qid}", json={"item": new_tree})
    assert r.status_code == 200, r.text
    items = r.json()["item"]
    assert [i["link_id"] for i in items] == ["root"]
    assert [i["link_id"] for i in items[0]["item"]] == ["q1", "q2"]
    assert len(items[0]["item"][0]["answer_option"]) == 2
    # search reflects the new tree (old item codes are gone)
    assert await _ids(client, "code=44250-9") == set()
    assert (await client.get(f"{BASE}/{qid}", headers=FHIR_ACCEPT)).json()["item"][0]["linkId"] == "root"

    # the tree is validated exactly like on create
    assert (await client.patch(f"{BASE}/{qid}", json={"item": [{"link_id": "g", "type": "group"}]})).status_code == 400
    dup = [{"link_id": "x", "type": "string"}, {"link_id": "x", "type": "string"}]
    assert (await client.patch(f"{BASE}/{qid}", json={"item": dup})).status_code == 400

    # [] clears the tree
    r = await client.patch(f"{BASE}/{qid}", json={"item": []})
    assert r.json()["item"] == []


async def test_search_requires_org_id(client):
    """org_id is mandatory on every search; user_id is optional."""
    await client.post(BASE + "/", json=MINIMAL)
    for url in (BASE + "/", f"{BASE}/?limit=5", BASE + "/?user_id=u-test"):
        assert (await client.get(url)).status_code == 400, url
    assert (await client.get(f"{BASE}/?org_id=")).status_code == 400                 # blank is not a tenant
    assert (await client.get(f"{BASE}/?org_id=org-test")).status_code == 200
    assert (await client.get(f"{BASE}/?org_id=org-test&user_id=nobody")).json()["total"] == 0
    assert (await client.get(f"{BASE}/?org_id=other-org")).json()["total"] == 0
