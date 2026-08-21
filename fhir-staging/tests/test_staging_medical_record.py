"""Integration tests for the five staging-medical-record endpoints.

Everything goes through the real ASGI app — router, service, repository, ORM —
against an in-memory SQLite database. What is NOT covered here is anything
PostgreSQL-specific: the enum types, the sequences (simulated in conftest), and
BIGSERIAL. Those are exercised by applying the migration to a real database.
"""

import pytest

from .conftest import BASE


def _record(**overrides) -> dict:
    body = {
        "file_id": "f_01HQ8X2K9Z",
        "attachment_title": "cbc-panel.pdf",
        "attachment_content_type": "application/pdf",
        "attachment_size": 248193,
        "org_id": "org-1",
        "user_id": "user-1",
        "patient_id": 10001,
        "encounter_id": 20001,
        "service_request_id": 80001,
        "created_by": "agent-intake",
    }
    body.update(overrides)
    return body


def _staging_observation(**overrides) -> dict:
    obs = {
        "status": "final",
        "code_system": "http://loinc.org",
        "code_code": "718-7",
        "code_display": "Hemoglobin [Mass/volume] in Blood",
        "subject": "Patient/10001",
        "value_quantity_value": 13.5,
        "value_quantity_unit": "g/dL",
    }
    obs.update(overrides)
    return obs


# ── Create ────────────────────────────────────────────────────────────────────


async def test_create_defaults_to_pending_and_allocates_public_id(client):
    r = await client.post(BASE, json=_record())
    assert r.status_code == 201, r.text
    body = r.json()

    # status defaults to pending — this is what puts the record on the agent's
    # queue, so a NULL here would make it invisible to ?status=pending.
    assert body["status"] == "pending"
    # Public sequence starts at 10000; the internal PK is never exposed.
    assert body["id"] == 10000
    assert body["file_id"] == "f_01HQ8X2K9Z"
    assert body["attachment_size"] == 248193
    assert body["patient_id"] == 10001
    # "not extracted yet" is [], not null.
    assert body["observations"] == []


async def test_create_rejects_unknown_field(client):
    """extra='forbid' — a typo'd field is a 422, not a silently ignored key."""
    r = await client.post(BASE, json=_record(patinet_id=10001))
    assert r.status_code == 422
    assert r.json()["error"]["code"] == "SCHEMA_VALIDATION_ERROR"


async def test_create_rejects_staging_observation_tenancy_fields(client):
    """Observations inherit org_id from the parent; accepting it per
    staging_observation would let the two disagree."""
    r = await client.post(
        BASE, json=_record(observations=[_staging_observation(org_id="org-other")])
    )
    assert r.status_code == 422


async def test_create_with_nested_staging_observations(client):
    r = await client.post(
        BASE,
        json=_record(
            status="completed",
            observations=[_staging_observation(), _staging_observation(code_code="789-8")],
        ),
    )
    assert r.status_code == 201, r.text
    body = r.json()
    assert len(body["observations"]) == 2
    # Observation public ids come from their own sequence, starting at 20000.
    assert sorted(o["id"] for o in body["observations"]) == [20000, 20001]
    # Tenancy is stamped from the parent record, not the staging_observation payload.
    assert all(o["org_id"] == "org-1" for o in body["observations"])
    assert all(o["user_id"] == "user-1" for o in body["observations"])
    assert all(o["created_by"] == "agent-intake" for o in body["observations"])


async def test_staging_observation_reference_is_split_into_type_and_id(client):
    r = await client.post(BASE, json=_record(observations=[_staging_observation()]))
    obs = r.json()["observations"][0]
    assert obs["subject_type"] == "Patient"
    assert obs["subject_id"] == 10001


async def test_staging_observation_rejects_bad_reference_type(client):
    r = await client.post(
        BASE, json=_record(observations=[_staging_observation(subject="Banana/1")])
    )
    assert r.status_code == 422


async def test_staging_observation_rejects_malformed_reference(client):
    r = await client.post(
        BASE, json=_record(observations=[_staging_observation(subject="Patient")])
    )
    assert r.status_code == 422


async def test_staging_observation_status_defaults_to_preliminary(client):
    """The column is NOT NULL (FHIR 1..1) but an extracting agent cannot always
    assert a status, and 'preliminary' is FHIR's own term for interim data."""
    obs = _staging_observation()
    del obs["status"]
    r = await client.post(BASE, json=_record(observations=[obs]))
    assert r.status_code == 201, r.text
    assert r.json()["observations"][0]["status"] == "preliminary"


async def test_staging_observation_rejects_bad_status_code(client):
    r = await client.post(
        BASE, json=_record(observations=[_staging_observation(status="bogus")])
    )
    assert r.status_code == 422


# ── Deep staging_observation structure ────────────────────────────────────────────────


async def test_component_and_reference_range_round_trip(client):
    """A blood panel is Observation.component[] — the deepest nesting the
    schema has, four levels down to component.referenceRange.appliesTo."""
    r = await client.post(
        BASE,
        json=_record(
            observations=[
                _staging_observation(
                    category=[{"coding_code": "laboratory"}],
                    interpretation=[{"coding_code": "N", "text": "Normal"}],
                    note=[{"text": "Sample slightly haemolysed"}],
                    reference_range=[
                        {
                            "low_value": 13.0,
                            "high_value": 17.0,
                            "text": "13.0-17.0 g/dL",
                            "applies_to": [{"coding_code": "male"}],
                        }
                    ],
                    component=[
                        {
                            "code_code": "789-8",
                            "code_display": "RBC",
                            "value_quantity_value": 4.7,
                            "interpretation": [{"coding_code": "N"}],
                            "reference_range": [
                                {
                                    "low_value": 4.2,
                                    "high_value": 5.8,
                                    "applies_to": [{"coding_code": "male"}],
                                }
                            ],
                        }
                    ],
                )
            ]
        ),
    )
    assert r.status_code == 201, r.text
    obs = r.json()["observations"][0]

    assert obs["category"][0]["coding_code"] == "laboratory"
    assert obs["interpretation"][0]["text"] == "Normal"
    assert obs["note"][0]["text"] == "Sample slightly haemolysed"

    rr = obs["reference_range"][0]
    assert rr["low_value"] == 13.0 and rr["high_value"] == 17.0
    assert rr["applies_to"][0]["coding_code"] == "male"

    comp = obs["component"][0]
    assert comp["code_display"] == "RBC"
    assert comp["value_quantity_value"] == 4.7
    assert comp["interpretation"][0]["coding_code"] == "N"
    assert comp["reference_range"][0]["applies_to"][0]["coding_code"] == "male"


async def test_timing_repeat_fields_round_trip(client):
    """These are accepted, stored, and returned. fhir-server's plain mapper
    drops them on read, making them write-only there; this asserts the round
    trip actually closes here."""
    r = await client.post(
        BASE,
        json=_record(
            observations=[
                _staging_observation(
                    effective_timing_repeat_count=3,
                    effective_timing_repeat_frequency=2,
                    effective_timing_repeat_period=1.5,
                    effective_timing_repeat_period_unit="d",
                    effective_timing_repeat_day_of_week="mon,wed,fri",
                )
            ]
        ),
    )
    assert r.status_code == 201, r.text
    obs = r.json()["observations"][0]
    assert obs["effective_timing_repeat_count"] == 3
    assert obs["effective_timing_repeat_frequency"] == 2
    assert obs["effective_timing_repeat_period"] == 1.5
    assert obs["effective_timing_repeat_period_unit"] == "d"
    assert obs["effective_timing_repeat_day_of_week"] == "mon,wed,fri"


# ── Read ──────────────────────────────────────────────────────────────────────


async def test_get_by_id(client):
    created = (await client.post(BASE, json=_record())).json()
    r = await client.get(f"{BASE}{created['id']}")
    assert r.status_code == 200
    assert r.json()["id"] == created["id"]


async def test_get_missing_returns_404(client):
    r = await client.get(f"{BASE}99999")
    assert r.status_code == 404
    assert r.json()["error"]["code"] == "NOT_FOUND"


# ── List ──────────────────────────────────────────────────────────────────────


async def test_list_envelope_and_pagination(client):
    for i in range(3):
        await client.post(BASE, json=_record(file_id=f"f_{i}"))

    r = await client.get(BASE, params={"limit": 2})
    assert r.status_code == 200
    body = r.json()
    assert body["total"] == 3
    assert body["limit"] == 2 and body["offset"] == 0
    assert len(body["data"]) == 2


async def test_list_total_mode_none_skips_count(client):
    await client.post(BASE, json=_record())
    r = await client.get(BASE, params={"total_mode": "none"})
    assert r.json()["total"] is None


async def test_list_status_filter_is_the_agent_queue(client):
    await client.post(BASE, json=_record(file_id="a"))  # pending
    await client.post(BASE, json=_record(file_id="b", status="completed"))

    r = await client.get(BASE, params={"status": "pending"})
    body = r.json()
    assert body["total"] == 1
    assert body["data"][0]["file_id"] == "a"


async def test_list_rejects_bad_status_value(client):
    r = await client.get(BASE, params={"status": "nonsense"})
    assert r.status_code == 422


@pytest.mark.parametrize(
    "param,value,expected_hits",
    [
        ("patient_id", 10001, 1),
        ("patient_id", 99999, 0),
        ("org_id", "org-1", 1),
        ("org_id", "org-nope", 0),
        ("service_request_id", 80001, 1),
        ("file_id", "f_01HQ8X2K9Z", 1),
        ("attachment_title", "cbc", 1),  # case-insensitive substring
        ("attachment_title", "CBC-PANEL", 1),
        ("attachment_title", "mri", 0),
    ],
)
async def test_list_filters(client, param, value, expected_hits):
    await client.post(BASE, json=_record())
    r = await client.get(BASE, params={param: value})
    assert r.json()["total"] == expected_hits


async def test_list_sort(client):
    for i in range(3):
        await client.post(BASE, json=_record(file_id=f"f_{i}"))

    desc = await client.get(BASE, params={"sort": "-staging_medical_record_id"})
    asc = await client.get(BASE, params={"sort": "staging_medical_record_id"})
    desc_ids = [d["id"] for d in desc.json()["data"]]
    asc_ids = [d["id"] for d in asc.json()["data"]]
    assert desc_ids == sorted(desc_ids, reverse=True)
    assert asc_ids == sorted(asc_ids)
    assert desc_ids == list(reversed(asc_ids))


async def test_list_unknown_sort_field_falls_back(client):
    """A typo in `sort` shouldn't fail an otherwise-valid request."""
    await client.post(BASE, json=_record())
    r = await client.get(BASE, params={"sort": "not_a_column"})
    assert r.status_code == 200
    assert r.json()["total"] == 1


# ── Patch ─────────────────────────────────────────────────────────────────────


async def test_patch_writes_back_extraction_result(client):
    created = (await client.post(BASE, json=_record())).json()
    r = await client.patch(
        f"{BASE}{created['id']}",
        json={
            "status": "completed",
            "processed_at": "2026-08-13T10:15:00Z",
            "updated_by": "agent-extractor",
            "observations": [_staging_observation()],
        },
    )
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["status"] == "completed"
    assert body["updated_by"] == "agent-extractor"
    assert len(body["observations"]) == 1
    # Observations inherit tenancy from the record as it now stands.
    assert body["observations"][0]["org_id"] == "org-1"


async def test_patch_records_failure(client):
    created = (await client.post(BASE, json=_record())).json()
    r = await client.patch(
        f"{BASE}{created['id']}",
        json={"status": "failed", "error_message": "PDF had no extractable text"},
    )
    assert r.status_code == 200
    assert r.json()["status"] == "failed"
    assert r.json()["error_message"] == "PDF had no extractable text"


async def test_patch_only_touches_supplied_fields(client):
    created = (await client.post(BASE, json=_record())).json()
    r = await client.patch(f"{BASE}{created['id']}", json={"status": "processing"})
    body = r.json()
    assert body["status"] == "processing"
    # Untouched fields survive.
    assert body["file_id"] == "f_01HQ8X2K9Z"
    assert body["patient_id"] == 10001


async def test_patch_staging_observations_replaces_the_whole_list(client):
    created = (
        await client.post(
            BASE,
            json=_record(
                observations=[_staging_observation(code_code="a"), _staging_observation(code_code="b")]
            ),
        )
    ).json()
    assert len(created["observations"]) == 2

    r = await client.patch(
        f"{BASE}{created['id']}",
        json={"observations": [_staging_observation(code_code="c")]},
    )
    body = r.json()
    assert len(body["observations"]) == 1
    assert body["observations"][0]["code_code"] == "c"


async def test_patch_empty_staging_observations_clears_them(client):
    created = (
        await client.post(BASE, json=_record(observations=[_staging_observation()]))
    ).json()
    r = await client.patch(f"{BASE}{created['id']}", json={"observations": []})
    assert r.json()["observations"] == []


async def test_patch_omitting_staging_observations_leaves_them_alone(client):
    """The distinction exclude_unset buys: an omitted key and an explicit []
    are different requests."""
    created = (
        await client.post(BASE, json=_record(observations=[_staging_observation()]))
    ).json()
    r = await client.patch(f"{BASE}{created['id']}", json={"status": "processing"})
    assert len(r.json()["observations"]) == 1


async def test_patch_missing_returns_404(client):
    r = await client.patch(f"{BASE}99999", json={"status": "completed"})
    assert r.status_code == 404


async def test_patch_rejects_unknown_field(client):
    created = (await client.post(BASE, json=_record())).json()
    r = await client.patch(f"{BASE}{created['id']}", json={"stauts": "completed"})
    assert r.status_code == 422


# ── Delete ────────────────────────────────────────────────────────────────────


async def test_delete_cascades_to_staging_observations(client):
    created = (
        await client.post(
            BASE,
            json=_record(
                observations=[
                    _staging_observation(
                        component=[{"code_code": "x", "interpretation": [{"coding_code": "N"}]}]
                    )
                ]
            ),
        )
    ).json()

    r = await client.delete(f"{BASE}{created['id']}")
    assert r.status_code == 204
    assert (await client.get(f"{BASE}{created['id']}")).status_code == 404

    # The child rows must be gone too, not orphaned.
    from sqlalchemy import func, select

    from app.models.staging_observation import StagingObservationComponent, StagingObservationModel

    db = __import__("app.main", fromlist=["container"]).container.core.database()
    async with db.session() as session:
        for model in (StagingObservationModel, StagingObservationComponent):
            count = (
                await session.execute(select(func.count()).select_from(model))
            ).scalar_one()
            assert count == 0, f"{model.__tablename__} rows survived the delete"


async def test_delete_missing_returns_404(client):
    r = await client.delete(f"{BASE}99999")
    assert r.status_code == 404


# ── Cross-cutting ─────────────────────────────────────────────────────────────


async def test_no_fhir_representation_is_served(client):
    """Asking for FHIR gets plain JSON — this service has FHIR-shaped tables,
    not a FHIR wire format."""
    created = (await client.post(BASE, json=_record())).json()
    r = await client.get(
        f"{BASE}{created['id']}", headers={"Accept": "application/fhir+json"}
    )
    assert r.status_code == 200
    assert r.headers["content-type"].startswith("application/json")
    assert "resourceType" not in r.json()


async def test_request_id_is_echoed(client):
    r = await client.get(BASE, headers={"X-Request-ID": "trace-me-123"})
    assert r.headers["X-Request-ID"] == "trace-me-123"


async def test_health(client):
    r = await client.get("/health")
    assert r.status_code == 200
    assert r.json() == {"status": "ok"}
