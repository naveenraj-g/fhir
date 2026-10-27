"""
Seed script to import SIMS Preventive Health Screening mock data bundles into PostgreSQL.

Reads FHIR R4 Bundle JSON files from `mock-data/sims-preventive-health-screening/`
and creates PlanDefinition and ActivityDefinition resources in the database.

Conventions & Architecture Rules:
  * Sequence bases generate public integer IDs:
      - PlanDefinition:     plan_definition_pub_seq     (starts at 400000)
      - ActivityDefinition: activity_definition_pub_seq (starts at 410000)
  * Canonical URLs use the pattern:
      - PlanDefinition:     PlanDefinition/{plan_definition_id}
      - ActivityDefinition: ActivityDefinition/{activity_definition_id}
  * PlanDefinition action `definitionCanonical` references are rewritten to:
      ActivityDefinition/{target_activity_definition_id}
  * Tenant scoped: `--org-id` is REQUIRED. Existing-record lookups (idempotency) and `--clean`
    only ever touch rows of that org_id — other tenants' data is never reused or deleted.
  * Idempotent by default: reuses the org's existing ActivityDefinitions by name and skips
    existing PlanDefinitions. Use `--clean` to remove and re-seed fresh.
  * Only the fields listed in HANDLED_* below are imported; any other field found in the bundles
    is reported as a warning so it is never dropped silently.

Usage:
    uv run python scripts/seed_preventive_health_screening.py --org-id <org-id>
    uv run python scripts/seed_preventive_health_screening.py --org-id <org-id> --dry-run
    uv run python scripts/seed_preventive_health_screening.py --org-id <org-id> --clean
"""

from __future__ import annotations

import argparse
import asyncio
import glob
import json
import os
import sys
from collections import Counter
from datetime import datetime
from typing import Any

# Ensure repository root is on sys.path
REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)

from app.core.config import settings
from app.models.activity_definition.activity_definition import ActivityDefinitionModel
from app.models.activity_definition.enums import (
    ActivityDefinitionIntent,
    ActivityDefinitionKind,
    PlanDefinitionStatus,
)
from app.models.plan_definition.plan_definition import (
    PlanDefinitionAction,
    PlanDefinitionModel,
)
from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine


# Bundle fields this script imports. Anything else found in the data triggers a warning.
HANDLED_AD_FIELDS = {
    "resourceType", "id", "url", "version", "name", "title", "status", "experimental", "description",
    "kind", "code", "intent", "doNotPerform", "date",
}
HANDLED_PD_FIELDS = {
    "resourceType", "id", "url", "version", "name", "title", "status", "experimental", "type",
    "description", "purpose", "date", "action",  # action[] is imported by the per-action loop (see HANDLED_ACTION_FIELDS)
}
HANDLED_ACTION_FIELDS = {"id", "title", "description", "textEquivalent", "definitionCanonical"}


def _parse_iso_datetime(dt_str: str | None) -> datetime | None:
    if not dt_str:
        return None
    try:
        # Normalize 'Z' to '+00:00'
        return datetime.fromisoformat(dt_str.replace("Z", "+00:00"))
    except ValueError as exc:
        raise ValueError(f"Invalid ISO date in bundle: {dt_str!r}") from exc


def _warn_unhandled(ads: dict[str, dict[str, Any]], plans: list[tuple[str, dict[str, Any]]]) -> None:
    """Report bundle fields this script does not import, so nothing is dropped silently."""
    skipped: Counter[str] = Counter()
    for res in ads.values():
        skipped.update(f"ActivityDefinition.{k}" for k in res if k not in HANDLED_AD_FIELDS)
    for _, res in plans:
        skipped.update(f"PlanDefinition.{k}" for k in res if k not in HANDLED_PD_FIELDS)
        for act in res.get("action", []):
            skipped.update(f"PlanDefinition.action.{k}" for k in act if k not in HANDLED_ACTION_FIELDS)
    if skipped:
        print("[WARN] Fields present in the bundles but NOT imported by this script:")
        for field, count in sorted(skipped.items()):
            print(f"  - {field} (x{count})")
        print()


async def clean_existing_data(
    session: AsyncSession,
    org_id: str,
    plan_names: set[str],
    activity_names: set[str],
) -> None:
    """Remove this org's previously seeded PlanDefinitions and ActivityDefinitions matching dataset names."""
    print(f"[CLEAN] Removing existing PlanDefinitions for org {org_id}...")
    stmt_pds = select(PlanDefinitionModel).where(
        PlanDefinitionModel.org_id == org_id,
        PlanDefinitionModel.name.in_(plan_names),
    )
    existing_pds = (await session.execute(stmt_pds)).scalars().all()
    for pd in existing_pds:
        print(f"  - Deleting PlanDefinition '{pd.name}' (ID: {pd.plan_definition_id})")
        await session.delete(pd)
    await session.flush()

    print("[CLEAN] Removing existing ActivityDefinitions...")
    stmt_ads = select(ActivityDefinitionModel).where(
        ActivityDefinitionModel.org_id == org_id,
        ActivityDefinitionModel.name.in_(activity_names),
    )
    existing_ads = (await session.execute(stmt_ads)).scalars().all()
    for ad in existing_ads:
        await session.delete(ad)
    await session.flush()
    print(
        f"[CLEAN] Removed {len(existing_pds)} plan definitions and {len(existing_ads)} activity definitions.\n"
    )


async def seed(
    data_dir: str,
    org_id: str,
    user_id: str | None = None,
    status: str = "active",
    clean: bool = False,
    dry_run: bool = False,
) -> None:
    abs_data_dir = (
        os.path.abspath(data_dir)
        if os.path.isabs(data_dir)
        else os.path.join(REPO_ROOT, data_dir)
    )
    pattern = os.path.join(abs_data_dir, "*.json")
    files = sorted(glob.glob(pattern))

    if not files:
        print(
            f"[ERROR] No JSON bundle files found matching: {pattern}", file=sys.stderr
        )
        sys.exit(1)

    print(f"[INFO] Found {len(files)} bundle files in: {abs_data_dir}")

    # Load all bundle files
    bundles: list[tuple[str, dict[str, Any]]] = []
    for f in files:
        with open(f, "r", encoding="utf-8") as fp:
            data = json.load(fp)
            bundles.append((os.path.basename(f), data))

    # Collect unique ActivityDefinitions and PlanDefinitions
    unique_ads: dict[str, dict[str, Any]] = {}  # mock_id -> resource_dict
    bundle_plans: list[tuple[str, dict[str, Any]]] = []  # [(filename, resource_dict)]

    for fname, bundle in bundles:
        bundle_timestamp = bundle.get("timestamp")
        for entry in bundle.get("entry", []):
            res = entry.get("resource", {})
            rtype = res.get("resourceType")
            if rtype == "ActivityDefinition":
                mock_id = res.get("id")
                if mock_id and mock_id not in unique_ads:
                    if "date" not in res and bundle_timestamp:
                        res["date"] = bundle_timestamp
                    unique_ads[mock_id] = res
            elif rtype == "PlanDefinition":
                if "date" not in res and bundle_timestamp:
                    res["date"] = bundle_timestamp
                bundle_plans.append((fname, res))

    _warn_unhandled(unique_ads, bundle_plans)

    plan_names = {res.get("name") for _, res in bundle_plans if res.get("name")}
    activity_names = {res.get("name") for res in unique_ads.values() if res.get("name")}

    engine = create_async_engine(settings.FHIR_DATABASE_URL, echo=False)
    session_maker = async_sessionmaker(
        bind=engine, class_=AsyncSession, expire_on_commit=False
    )

    async with session_maker() as session:
        effective_org_id = org_id
        print(f"[INFO] Seeding for organization org_id: {effective_org_id}")

        if clean:
            await clean_existing_data(session, effective_org_id, plan_names, activity_names)

        # Lookup any already-existing ActivityDefinitions in the database (for idempotency)
        existing_ads_stmt = select(ActivityDefinitionModel).where(
            ActivityDefinitionModel.org_id == effective_org_id,
            ActivityDefinitionModel.name.in_(activity_names),
        )
        existing_ads_rows = (await session.execute(existing_ads_stmt)).scalars().all()
        existing_ads_by_name = {ad.name: ad for ad in existing_ads_rows}

        # ad_map stores mock references -> database public activity_definition_id
        ad_map: dict[str, int] = {}
        inserted_ad_count = 0
        reused_ad_count = 0

        print(f"\n[SEED] Processing {len(unique_ads)} unique ActivityDefinitions...")
        for mock_id, res in unique_ads.items():
            name = res.get("name")
            mock_url = res.get("url")

            if name and name in existing_ads_by_name:
                existing_ad = existing_ads_by_name[name]
                pub_id = existing_ad.activity_definition_id
                ad_map[mock_id] = pub_id
                if mock_url:
                    ad_map[mock_url] = pub_id
                    ad_map[mock_url.split("|")[0]] = pub_id
                reused_ad_count += 1
                continue

            # Allocate public sequence ID
            pub_id = (
                await session.execute(
                    text("SELECT nextval('activity_definition_pub_seq')")
                )
            ).scalar()

            code_obj = res.get("code", {})
            code_coding = (
                code_obj.get("coding", [{}])[0] if code_obj.get("coding") else {}
            )

            status_enum = PlanDefinitionStatus(status)  # --status (default active), not the bundle's draft

            kind_val = res.get("kind")
            kind_enum = ActivityDefinitionKind(kind_val) if kind_val else None

            intent_val = res.get("intent")
            intent_enum = ActivityDefinitionIntent(intent_val) if intent_val else None

            ad_row = ActivityDefinitionModel(
                activity_definition_id=pub_id,
                url=f"ActivityDefinition/{pub_id}",
                version=res.get("version"),
                name=name,
                title=res.get("title"),
                status=status_enum,
                experimental=res.get("experimental"),
                description=res.get("description"),
                kind=kind_enum,
                intent=intent_enum,
                do_not_perform=res.get("doNotPerform"),
                code_system=code_coding.get("system"),
                code_code=code_coding.get("code"),
                code_display=code_coding.get("display"),
                code_text=code_obj.get("text") or code_coding.get("display"),
                date=_parse_iso_datetime(res.get("date")),
                user_id=user_id,
                org_id=effective_org_id,
                created_by=user_id,
            )
            session.add(ad_row)
            ad_map[mock_id] = pub_id
            if mock_url:
                ad_map[mock_url] = pub_id
                ad_map[mock_url.split("|")[0]] = pub_id
            inserted_ad_count += 1

        await session.flush()
        print(
            f"[SEED] ActivityDefinitions: {inserted_ad_count} created, {reused_ad_count} reused."
        )

        # Lookup any already-existing PlanDefinitions
        existing_pds_stmt = select(PlanDefinitionModel).where(
            PlanDefinitionModel.org_id == effective_org_id,
            PlanDefinitionModel.name.in_(plan_names),
        )
        existing_pds_rows = (await session.execute(existing_pds_stmt)).scalars().all()
        existing_pds_by_name = {pd.name: pd for pd in existing_pds_rows}

        print(f"\n[SEED] Processing {len(bundle_plans)} PlanDefinitions...")
        seeded_plans_summary: list[dict[str, Any]] = []

        for fname, res in bundle_plans:
            name = res.get("name")
            if name and name in existing_pds_by_name:
                existing_pd = existing_pds_by_name[name]
                print(
                    f"  [SKIP] PlanDefinition '{name}' already exists (ID: {existing_pd.plan_definition_id})"
                )
                seeded_plans_summary.append(
                    {
                        "file": fname,
                        "name": name,
                        "id": existing_pd.plan_definition_id,
                        "url": existing_pd.url,
                        "actions": len(res.get("action", [])),
                        "status": "Existing (reused)",
                    }
                )
                continue

            pub_id = (
                await session.execute(text("SELECT nextval('plan_definition_pub_seq')"))
            ).scalar()

            type_obj = res.get("type", {})
            type_coding = (
                type_obj.get("coding", [{}])[0] if type_obj.get("coding") else {}
            )

            status_enum = PlanDefinitionStatus(status)  # --status (default active), not the bundle's draft

            pd_row = PlanDefinitionModel(
                plan_definition_id=pub_id,
                url=f"PlanDefinition/{pub_id}",
                version=res.get("version"),
                name=name,
                title=res.get("title"),
                status=status_enum,
                experimental=res.get("experimental"),
                description=res.get("description"),
                purpose=res.get("purpose"),
                type_system=type_coding.get("system"),
                type_code=type_coding.get("code"),
                type_display=type_coding.get("display"),
                type_text=type_obj.get("text") or type_coding.get("display"),
                date=_parse_iso_datetime(res.get("date")),
                user_id=user_id,
                org_id=effective_org_id,
                created_by=user_id,
            )
            session.add(pd_row)

            # Insert PlanDefinition actions
            actions = res.get("action", [])
            for idx, a in enumerate(actions):
                canon = a.get("definitionCanonical", "")
                clean_canon = canon.split("|")[0]
                target_mock_id = clean_canon.split("/")[-1]

                target_pub_id = (
                    ad_map.get(canon)
                    or ad_map.get(clean_canon)
                    or ad_map.get(target_mock_id)
                )
                if not target_pub_id:
                    raise ValueError(
                        f"Unable to resolve target ActivityDefinition for action: '{canon}' (target_id: '{target_mock_id}')"
                    )

                action_row = PlanDefinitionAction(
                    plan_definition=pd_row,
                    position=idx + 1,
                    element_id=a.get("id"),
                    title=a.get("title"),
                    description=a.get("description"),
                    text_equivalent=a.get("textEquivalent"),
                    definition_canonical=f"ActivityDefinition/{target_pub_id}",
                    org_id=effective_org_id,
                )
                session.add(action_row)

            seeded_plans_summary.append(
                {
                    "file": fname,
                    "name": name,
                    "id": pub_id,
                    "url": f"PlanDefinition/{pub_id}",
                    "actions": len(actions),
                    "status": "Created",
                }
            )

        await session.flush()

        if dry_run:
            await session.rollback()
            print(
                "\n[DRY RUN] Simulation complete. Rolled back all changes without saving to DB."
            )
        else:
            await session.commit()
            print("\n[SUCCESS] All records committed successfully to database.")

    await engine.dispose()

    # Print summary report
    print("\n" + "=" * 80)
    print("                      SEEDING SUMMARY REPORT")
    print("=" * 80)
    print(f"{'Plan Name':<34} {'Public ID':<10} {'Actions':<8} {'Status':<18} {'URL'}")
    print("-" * 80)
    for s in seeded_plans_summary:
        print(
            f"{s['name']:<34} {s['id']:<10} {s['actions']:<8} {s['status']:<18} {s['url']}"
        )
    print("-" * 80)
    print(
        f"Total ActivityDefinitions : {inserted_ad_count + reused_ad_count} ({inserted_ad_count} created, {reused_ad_count} reused)"
    )
    print(f"Total PlanDefinitions     : {len(seeded_plans_summary)}")
    print("=" * 80 + "\n")


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Seed FHIR R4 PlanDefinition and ActivityDefinition from mock data."
    )
    parser.add_argument(
        "--data-dir",
        type=str,
        default="mock-data/sims-preventive-health-screening",
        help="Path to folder containing bundle JSON files (default: mock-data/sims-preventive-health-screening)",
    )
    parser.add_argument(
        "--org-id",
        type=str,
        required=True,
        help="Tenant organization ID to seed into (required; lookups and --clean are scoped to it)",
    )
    parser.add_argument(
        "--user-id",
        type=str,
        default=None,
        help="User ID for audit metadata (optional)",
    )
    parser.add_argument(
        "--status",
        choices=[e.value for e in PlanDefinitionStatus],
        default="active",
        help="Status given to every seeded definition (default: active; the bundles themselves say draft)",
    )
    parser.add_argument(
        "--clean",
        action="store_true",
        help="Delete existing seeded screening definitions before seeding fresh",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Run without committing to the database",
    )

    args = parser.parse_args()

    asyncio.run(
        seed(
            data_dir=args.data_dir,
            org_id=args.org_id,
            user_id=args.user_id,
            status=args.status,
            clean=args.clean,
            dry_run=args.dry_run,
        )
    )


if __name__ == "__main__":
    main()
