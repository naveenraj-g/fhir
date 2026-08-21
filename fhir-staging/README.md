# fhir-staging

A staging area for medical-record documents and the FHIR R4 Observations an AI
agent extracts from them.

## The flow

1. A document is registered here with its **filenest** file handle (an opaque
   `file_id` plus name/mimetype/size, which land in the flattened FHIR R4
   `Attachment` fields) and the clinical context it belongs to — patient,
   encounter, and the ServiceRequest it was produced against.
2. The record lands with `status: pending`. `GET /staging-records?status=pending`
   is the agent's work queue.
3. The agent fetches the file from filenest, reads it, and extracts
   Observations.
4. It writes them back with a single `PATCH` — `status`, `processed_at`, and the
   `observations` list. On failure: `status: failed` plus an `error_message`.
5. A doctor/practitioner reviews the extracted data and records a decision via
   `PATCH /{id}/review` — `accepted`, `rejected`, or `needs_revision`.

Nothing is promoted into the FHIR server from here automatically; this is a
holding pen so extraction output can be inspected, reviewed, and corrected
first. `status` and `review_status` are deliberately separate columns: the
former tracks whether the agent finished extracting data, the latter tracks
whether a clinician has since signed off on it.

## Two tables

| Table | What it holds |
|---|---|
| `staging_record` | The flattened FHIR R4 `Attachment`, the filenest handle, the clinical-context ids, the extraction pipeline state, and the clinician review state |
| `staging_observation` (+16 child tables) | The extracted results — a full flattened FHIR R4 Observation, ported column-for-column from `fhir-server`, so a staged row promotes without translation |

Every column is nullable for now. The agent's real output shape is not settled;
tightening later is cheaper than undoing a constraint added too early.

## What this service deliberately is not

- **No FHIR wire format.** There is no `application/fhir+json`, no content
  negotiation, no Bundle, no `resourceType`. Every response is plain snake_case
  JSON. The FHIR R4 standard governs the *table shape* here — this is an
  internal service.
- **No auth.** `org_id` / `user_id` / `created_by` / `updated_by` are plain
  forwarded input fields, trusted as given.
- **No Redis.**
- **No reference validation.** `patient_id`, `encounter_id`,
  `service_request_id` and friends are public ids belonging to *fhir-server*, so
  there is nothing in this database to check them against.

## Endpoints

All under `/api/v1/staging-records`.

| Method | Path | |
|---|---|---|
| POST | `/` | Register a document |
| GET | `/` | List — filtered, sorted, paginated |
| GET | `/{id}` | Fetch one, with its observation tree nested |
| PATCH | `/{id}` | Update; write back extracted observations (the agent's write path) |
| PATCH | `/{id}/review` | Record a clinician's accept/reject/needs-revision decision (the reviewer's write path) |
| DELETE | `/{id}` | Delete; observations cascade |

⚠️ **`observations` on PATCH is REPLACE, not append.** Sending the key deletes
every existing observation and inserts what you sent; sending `[]` clears them.
Omit the key to leave them alone — an omitted key and an explicit `[]` are
different requests.

`/review` is a separate endpoint from the generic PATCH on purpose: the agent
pipeline and a clinician are different callers writing different kinds of
fact, and `reviewed_at` is always set server-side to when the review request
is processed.

## Running it

```bash
just setup                    # uv sync + create .env from the example
                              # then set STAGING_DATABASE_URL in .env
just migrate                  # apply migrations
just dev                      # dev server with autoreload
```

OpenAPI at http://localhost:8002/docs. Port 8002 so this runs alongside
fhir-server (8001).

```bash
just test                     # or: just test-q / just test-k <keyword>
just check                    # import the app without starting a server
just openapi                  # dump the spec to openapi.json for diffing
```

`just --list` for the rest — mostly migration recipes. Two worth knowing:
`just migrate-sql` renders pending migrations as SQL without touching a
database, and `just migrate-verify` proves the migration still matches the
models (apply, then autogenerate — an empty revision is the proof).

## Configuration

Three layers, highest precedence first — see
`app/core/config.py`'s `settings_customise_sources()`:

1. A real environment variable
2. `.env` — the database URL, and nothing else
3. `configs/config.yaml` — checked-in application behavior (logging, which
   routers are mounted)

Nested fields are env-overridable with `__` as the delimiter, e.g.
`LOGGING__LEVEL=DEBUG`.

⚠️ `logging.debug_payloads` writes full request payloads to the log stream. The
documents staged here are medical records. Local development only.
