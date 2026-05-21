"""Terminology import CLI.

Usage examples:
  # FHIR R4 built-in code systems (smallest — start here)
  uv run python -m app.terminology.import_.cli --source fhir-r4 --file codesystems.json

  # ICD-10-CM (free, no account — ~72k codes)
  uv run python -m app.terminology.import_.cli --source icd10cm --file icd10cm_codes_2025.txt

  # RxNorm (free, no account — ~100k drug concepts)
  uv run python -m app.terminology.import_.cli --source rxnorm --file rrf/RXNCONSO.RRF

  # LOINC (free registration — ~100k lab/clinical codes)
  uv run python -m app.terminology.import_.cli --source loinc --file Loinc_2.78.csv

  # SNOMED CT (UMLS account required — ~350k concepts + IS-A hierarchy)
  uv run python -m app.terminology.import_.cli --source snomed --dir SnomedCT_RF2/Snapshot/Terminology/

  # Load all at once
  uv run python -m app.terminology.import_.cli --source all \\
    --fhir-r4-file codesystems.json \\
    --icd10cm-file icd10cm_codes_2025.txt \\
    --rxnorm-file rrf/RXNCONSO.RRF \\
    --loinc-file Loinc_2.78.csv \\
    --snomed-dir SnomedCT_RF2/Snapshot/Terminology/
"""
import argparse
import asyncio
import sys
import time


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        description="FHIR Terminology Import CLI",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    p.add_argument(
        "--source",
        required=True,
        choices=["fhir-r4", "loinc", "icd10cm", "rxnorm", "snomed", "all"],
        help="Which terminology to import",
    )
    p.add_argument("--file", help="Input file path (fhir-r4 / loinc / icd10cm / rxnorm)")
    p.add_argument("--dir", help="Input directory path (snomed RF2 Terminology/)")

    # --all mode individual paths
    p.add_argument("--fhir-r4-file", help="codesystems.json  [for --source all]")
    p.add_argument("--icd10cm-file", help="icd10cm_codes.txt [for --source all]")
    p.add_argument("--rxnorm-file", help="RXNCONSO.RRF       [for --source all]")
    p.add_argument("--loinc-file", help="Loinc_x.xx.csv     [for --source all]")
    p.add_argument("--snomed-dir", help="RF2 Terminology/   [for --source all]")
    return p


async def run(args: argparse.Namespace) -> None:
    from app.core.config import settings

    db_url = settings.FHIR_DATABASE_URL
    source = args.source

    tasks: list[tuple] = []  # (loader_class, path_or_dir, is_dir)

    if source == "fhir-r4":
        _require(args.file, "--file", source)
        from app.terminology.import_.loaders.fhir_r4 import FhirR4Loader
        tasks.append((FhirR4Loader, args.file, False))

    elif source == "loinc":
        _require(args.file, "--file", source)
        from app.terminology.import_.loaders.loinc import LoincLoader
        tasks.append((LoincLoader, args.file, False))

    elif source == "icd10cm":
        _require(args.file, "--file", source)
        from app.terminology.import_.loaders.icd10cm import Icd10cmLoader
        tasks.append((Icd10cmLoader, args.file, False))

    elif source == "rxnorm":
        _require(args.file, "--file", source)
        from app.terminology.import_.loaders.rxnorm import RxnormLoader
        tasks.append((RxnormLoader, args.file, False))

    elif source == "snomed":
        _require(args.dir, "--dir", source)
        from app.terminology.import_.loaders.snomed import SnomedLoader
        tasks.append((SnomedLoader, args.dir, True))

    elif source == "all":
        if args.fhir_r4_file:
            from app.terminology.import_.loaders.fhir_r4 import FhirR4Loader
            tasks.append((FhirR4Loader, args.fhir_r4_file, False))
        if args.icd10cm_file:
            from app.terminology.import_.loaders.icd10cm import Icd10cmLoader
            tasks.append((Icd10cmLoader, args.icd10cm_file, False))
        if args.rxnorm_file:
            from app.terminology.import_.loaders.rxnorm import RxnormLoader
            tasks.append((RxnormLoader, args.rxnorm_file, False))
        if args.loinc_file:
            from app.terminology.import_.loaders.loinc import LoincLoader
            tasks.append((LoincLoader, args.loinc_file, False))
        if args.snomed_dir:
            from app.terminology.import_.loaders.snomed import SnomedLoader
            tasks.append((SnomedLoader, args.snomed_dir, True))
        if not tasks:
            print("ERROR: --source all requires at least one file/dir argument.", file=sys.stderr)
            sys.exit(1)

    for loader_cls, path, is_dir in tasks:
        async with loader_cls(db_url) as loader:
            if is_dir:
                await loader.load(path)
            else:
                await loader.load(path)


def _require(value: str | None, flag: str, source: str) -> None:
    if not value:
        print(f"ERROR: --source {source} requires {flag}", file=sys.stderr)
        sys.exit(1)


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()
    t0 = time.monotonic()
    asyncio.run(run(args))
    print(f"\nTotal elapsed: {time.monotonic() - t0:.1f}s")


if __name__ == "__main__":
    main()
