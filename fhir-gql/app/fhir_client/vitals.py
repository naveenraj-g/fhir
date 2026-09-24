"""
HTTP client for the Vitals service on the fhir-server.

Vitals captures health and activity metrics from wearable devices or manual entry
(steps, heart rate, blood pressure, sleep stages, weight/height, etc.). It is a
custom resource — not part of the FHIR R4 spec — so unlike ObservationClient it:
  1. Lives at its own base URL (/api/v1/vitals), outside both the FHIR namespace
     (/api/fhir/v1) and the terminology namespace, so it needs its own httpx client
     rather than reusing the shared FhirClient.
  2. Never supports `application/fhir+json` — the fhir-server always returns plain
     JSON for vitals, so there is no `accept` parameter to thread through.

It still stamps `created_by` / `updated_by` from the caller's JWT subject on writes,
mirroring FhirClient's audit-injection behaviour, because VitalsCreateSchema and
VitalsPatchSchema on the fhir-server declare those as regular body fields rather
than deriving them from a header.

This client is stateless and registered as a Singleton in CoreContainer so the
httpx connection pool is shared and reused across all vitals requests.
"""

import httpx
from fastapi import HTTPException

from app.auth.models import AuthUser


class VitalsClient:
    """
    HTTP client for the vitals endpoints on the fhir-server.

    Provides thin CRUD wrappers — no business logic here. Business rules (e.g.
    rejecting empty patches) live in VitalsService.
    """

    def __init__(self, base_url: str) -> None:
        """
        Initialise the HTTP client pointed at the vitals service base URL.

        Args:
            base_url: Root URL of the vitals service
                      (e.g. http://localhost:8001/api/v1/vitals).
                      All path arguments are appended to this by httpx.
        """
        # Timeout and follow_redirects mirror FhirClient/TerminologyClient for
        # consistency — 10s balances latency against hanging on a slow fhir-server,
        # and redirects must be followed because FastAPI 307s trailing-slash requests.
        self._http = httpx.AsyncClient(
            base_url=base_url,
            headers={"Content-Type": "application/json"},
            timeout=10.0,
            follow_redirects=True,
        )

    async def _handle(self, r: httpx.Response) -> dict | None:
        """
        Normalise an httpx response into a dict or raise HTTPException.

        Args:
            r: The raw httpx.Response from the vitals service.

        Returns:
            Parsed JSON dict for successful responses with a body, or None for 204.

        Raises:
            HTTPException: Forwarding the fhir-server's status code and error detail.
        """
        if r.status_code == 204:
            return None
        try:
            r.raise_for_status()
        except httpx.HTTPStatusError:
            try:
                detail = r.json().get("detail", r.text)
            except Exception:
                detail = r.text
            raise HTTPException(status_code=r.status_code, detail=detail)
        return r.json()

    async def create(self, data: dict, actor: AuthUser) -> dict:
        """
        POST / — create a new vitals entry.

        Stamps `created_by` from the caller's JWT `sub` claim, matching the
        fhir-server's VitalsCreateSchema.created_by body field.

        Args:
            data:  Serialised VitalsCreateSchema (exclude_none=True, mode="json").
            actor: Authenticated caller.

        Returns:
            The newly created vitals entry as a dict.
        """
        body = {**data, "created_by": actor.sub}
        r = await self._http.post("/", json=body)
        return await self._handle(r)

    async def get_by_id(self, vitals_id: int) -> dict:
        """
        GET /{vitals_id} — fetch a single vitals entry by its public integer ID.

        Args:
            vitals_id: The vitals entry's public identifier on the fhir-server.

        Returns:
            The vitals entry dict.
        """
        r = await self._http.get(f"/{vitals_id}")
        return await self._handle(r)

    async def list(self, **params) -> dict:
        """
        GET / — list vitals entries with optional filter parameters.

        Strips None values from **params before forwarding.

        Supported params: user_id, patient_id, org_id, date, recorded_at_from,
        recorded_at_to, limit, offset (matching the fhir-server's GET /vitals).

        Args:
            **params: Arbitrary keyword filters; None values are dropped.

        Returns:
            Paginated vitals dict: {total, limit, offset, data: [...]}.
        """
        clean = {k: v for k, v in params.items() if v is not None}
        r = await self._http.get("/", params=clean)
        return await self._handle(r)

    async def patch(self, vitals_id: int, data: dict, actor: AuthUser) -> dict:
        """
        PATCH /{vitals_id} — partially update a vitals entry.

        Stamps `updated_by` from the caller's JWT `sub` claim, matching the
        fhir-server's VitalsPatchSchema.updated_by body field. `user_id`,
        `patient_id`, `org_id`, and `recorded_at` are immutable after creation.

        Args:
            vitals_id: The vitals entry's public integer ID.
            data:      Serialised VitalsPatchSchema (exclude_none=True, mode="json").
            actor:     Authenticated caller.

        Returns:
            The updated vitals entry dict.
        """
        body = {**data, "updated_by": actor.sub}
        r = await self._http.patch(f"/{vitals_id}", json=body)
        return await self._handle(r)

    async def delete(self, vitals_id: int) -> None:
        """
        DELETE /{vitals_id} — permanently remove a vitals entry.

        Args:
            vitals_id: The vitals entry's public integer ID to delete.
        """
        r = await self._http.delete(f"/{vitals_id}")
        await self._handle(r)

    async def aclose(self) -> None:
        """
        Close the underlying httpx connection pool gracefully.

        Must be called during application shutdown alongside FhirClient.aclose()
        and TerminologyClient.aclose().
        """
        await self._http.aclose()
