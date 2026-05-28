"""FHIR R4 built-in CodeSystem + ValueSet loader.

Accepts three input forms:
  1. A Bundle JSON file (valuesets.json or v3-codesystems.json from hl7.org/fhir/R4/definitions.json.zip)
  2. A single CodeSystem or ValueSet JSON file
  3. A directory containing CodeSystem-*.json / ValueSet-*.json files (FHIR NPM package)

Download:
  curl -L https://hl7.org/fhir/R4/definitions.json.zip -o fhir-r4.zip
  unzip fhir-r4.zip valuesets.json v3-codesystems.json

Run:
  uv run python -m app.terminology.import_.cli --source fhir-r4 --file valuesets.json
  uv run python -m app.terminology.import_.cli --source fhir-r4 --file v3-codesystems.json
"""
import glob
import json
import os
import time
from typing import Any

from app.terminology.import_.base import BaseLoader


class FhirR4Loader(BaseLoader):
    source_name = "fhir-r4"

    async def load(self, path: str) -> None:
        t0 = time.monotonic()
        resources = self._read_input(path)

        code_systems = [r for r in resources if r.get("resourceType") == "CodeSystem"]
        value_sets = [r for r in resources if r.get("resourceType") == "ValueSet"]
        self._log(
            f"Found {len(code_systems)} CodeSystems + {len(value_sets)} ValueSets"
        )

        # ── Phase 1: load all CodeSystems + their concepts ─────────────────────
        total_concepts = 0
        for cs in code_systems:
            count = await self._load_code_system(cs)
            total_concepts += count
        self._log(f"CodeSystems done — {total_concepts:,} total concepts")

        # ── Phase 2: load ValueSets + concept memberships ─────────────────────
        if value_sets:
            self._log("Loading ValueSets...")
            loaded_vs = 0
            skipped_vs = 0
            for vs in value_sets:
                ok = await self._load_value_set(vs)
                if ok:
                    loaded_vs += 1
                else:
                    skipped_vs += 1
            self._log(
                f"ValueSets done — {loaded_vs} loaded, {skipped_vs} skipped "
                "(filter/compose-only sets are skipped)"
            )

        self._log(f"Total time: {time.monotonic() - t0:.1f}s")

    # ── Input parsing ──────────────────────────────────────────────────────────

    def _read_input(self, path: str) -> list[dict]:
        if os.path.isdir(path):
            return self._read_directory(path)
        with open(path, encoding="utf-8") as f:
            data = json.load(f)
        if data.get("resourceType") == "Bundle":
            return [e["resource"] for e in data.get("entry", []) if "resource" in e]
        if data.get("resourceType") in ("CodeSystem", "ValueSet"):
            return [data]
        raise ValueError(f"Unrecognised FHIR input at {path!r}")

    def _read_directory(self, directory: str) -> list[dict]:
        result = []
        for pattern in ("CodeSystem-*.json", "ValueSet-*.json"):
            for filepath in glob.glob(os.path.join(directory, pattern)):
                with open(filepath, encoding="utf-8") as f:
                    try:
                        data = json.load(f)
                        if data.get("resourceType") in ("CodeSystem", "ValueSet"):
                            result.append(data)
                    except json.JSONDecodeError:
                        pass
        return result

    # ── CodeSystem ─────────────────────────────────────────────────────────────

    async def _load_code_system(self, cs: dict[str, Any]) -> int:
        url = cs.get("url") or cs.get("id")
        if not url:
            return 0
        name = cs.get("name") or url.split("/")[-1]

        cs_id = await self.upsert_code_system(
            canonical_url=url,
            name=name,
            title=cs.get("title"),
            version=cs.get("version"),
            publisher=cs.get("publisher"),
            content_mode=cs.get("content"),
        )

        concepts: list[dict] = cs.get("concept", [])
        if not concepts:
            return 0

        records: list[tuple] = []
        self._flatten_concepts(concepts, cs_id, records)
        await self.bulk_insert_concepts(records)
        return len(records)

    def _flatten_concepts(self, concepts: list[dict], cs_id: int, out: list) -> None:
        for c in concepts:
            code = (c.get("code") or "").strip()
            display = (c.get("display") or code).strip()
            definition = (c.get("definition") or "").strip() or None
            if code:
                out.append((cs_id, code, display, definition))
            for child in c.get("concept", []):
                self._flatten_concepts([child], cs_id, out)

    # ── ValueSet ───────────────────────────────────────────────────────────────

    async def _load_value_set(self, vs: dict[str, Any]) -> bool:
        url = vs.get("url") or vs.get("id")
        if not url:
            return False

        name = vs.get("name") or url.split("/")[-1]
        binding_strength = "required" if vs.get("immutable") else "extensible"

        # Insert / upsert the ValueSet row
        vs_id: int = await self.conn.fetchval(
            """
            INSERT INTO terminology_value_set
                (canonical_url, name, title, description, version, fhir_version, binding_strength)
            VALUES ($1, $2, $3, $4, $5, $6, $7)
            ON CONFLICT (canonical_url) DO UPDATE SET
                name           = EXCLUDED.name,
                title          = COALESCE(EXCLUDED.title, terminology_value_set.title),
                updated_at     = NOW()
            RETURNING id
            """,
            url,
            name,
            vs.get("title"),
            vs.get("description"),
            vs.get("version"),
            "4.0.1",
            binding_strength,
        )

        # Collect explicit concept codes from compose.include
        # Skip ValueSets that only have filters (can't resolve without expansion)
        compose = vs.get("compose") or {}
        includes = compose.get("include", [])

        concept_db_ids: list[int] = []
        for inc in includes:
            system_url = inc.get("system")
            codes = inc.get("concept", [])
            filters = inc.get("filter", [])

            if not system_url:
                continue
            if filters:
                continue  # filter-based expansion — can't resolve without runtime expansion

            if codes:
                # Explicit code list
                rows = await self.conn.fetch(
                    """
                    SELECT tc.id FROM terminology_concept tc
                    JOIN terminology_code_system cs ON cs.id = tc.code_system_id
                    WHERE cs.canonical_url = $1 AND tc.code = ANY($2::text[])
                      AND tc.org_id IS NULL
                    """,
                    system_url,
                    [c["code"] for c in codes],
                )
            else:
                # Whole-system include — link all concepts from this CodeSystem
                rows = await self.conn.fetch(
                    """
                    SELECT tc.id FROM terminology_concept tc
                    JOIN terminology_code_system cs ON cs.id = tc.code_system_id
                    WHERE cs.canonical_url = $1 AND tc.org_id IS NULL
                    """,
                    system_url,
                )
            concept_db_ids.extend(r["id"] for r in rows)

        if not concept_db_ids:
            return False  # nothing to link

        await self.conn.executemany(
            """
            INSERT INTO terminology_value_set_concept (value_set_id, concept_id)
            VALUES ($1, $2)
            ON CONFLICT DO NOTHING
            """,
            [(vs_id, cid) for cid in concept_db_ids],
        )
        return True
