# =============================================================================
# FHIR Terminology Loader — run from project root
# =============================================================================
# Run all loaders in order (each is idempotent — safe to re-run).
# Uncomment the loaders for the files you have downloaded.
#
# Usage:
#   .\scripts\load_terminology.ps1
#
# Or run a single loader directly:
#   uv run python -m app.terminology.import_.cli --source icd10cm --file <path>
# =============================================================================


# -----------------------------------------------------------------------------
# FHIR R4 Built-in Code Systems + Value Sets
# Already loaded — re-run anytime to pick up HL7 spec updates.
#
# Download:
#   curl -L https://hl7.org/fhir/R4/definitions.json.zip -o fhir-r4.zip
#   unzip fhir-r4.zip valuesets.json v3-codesystems.json
# -----------------------------------------------------------------------------

Write-Host "[1/5] FHIR R4 built-in code systems (valuesets.json)..." -ForegroundColor Cyan
uv run python -m app.terminology.import_.cli --source fhir-r4 --file terminology_data\valuesets.json

Write-Host "[1/5] FHIR R4 v3 code systems (v3-codesystems.json)..." -ForegroundColor Cyan
uv run python -m app.terminology.import_.cli --source fhir-r4 --file terminology_data\v3-codesystems.json


# -----------------------------------------------------------------------------
# ICD-10-CM — ~72k diagnosis codes
# Free, no account required.
#
# Download:
#   https://www.cms.gov/medicare/coding-billing/icd-10-codes
#   -> "FY2025 Code Descriptions in Tabular Order" ZIP
#   Extract: icd10cm_codes_2025.txt
# -----------------------------------------------------------------------------

Write-Host "[2/5] ICD-10-CM (~72k codes, ~2 min)..." -ForegroundColor Cyan
uv run python -m app.terminology.import_.cli `
    --source icd10cm `
    --file terminology_data\icd10cm_codes_2026.txt


# -----------------------------------------------------------------------------
# RxNorm — ~100k drug concepts (ingredients, brands, clinical drugs)
# Free, no account required.
#
# Download:
#   https://www.nlm.nih.gov/research/umls/rxnorm/docs/rxnormfiles.html
#   -> "RxNorm Full Monthly Release" ZIP
#   Extract the rrf/ folder — key file: rrf\RXNCONSO.RRF
# -----------------------------------------------------------------------------

Write-Host "[3/5] RxNorm (~100k drugs, ~3 min)..." -ForegroundColor Cyan
uv run python -m app.terminology.import_.cli `
    --source rxnorm `
    --file terminology_data\rrf\RXNCONSO.RRF


# -----------------------------------------------------------------------------
# LOINC — ~100k lab, clinical, and imaging codes
# Free, requires registration at loinc.org.
#
# Download:
#   https://loinc.org/downloads/
#   -> "LOINC Table Core (CSV)"
#   Extract: Loinc_2.78.csv (version number may differ)
# -----------------------------------------------------------------------------

Write-Host "[4/5] LOINC (~100k codes, ~3 min)..." -ForegroundColor Cyan
uv run python -m app.terminology.import_.cli `
    --source loinc `
    --file terminology_data\Loinc_2.78.csv


# -----------------------------------------------------------------------------
# SNOMED CT — ~350k clinical concepts + full IS-A hierarchy
# Free for US users via NLM UMLS account (free to register).
#
# Download:
#   https://www.nlm.nih.gov/healthit/snomedct/us_edition.html
#   -> Register for UMLS -> download US Edition RF2 ZIP
#   Extract the SnomedCT_*/ folder.
#   Point --dir at the Terminology/ subfolder inside Snapshot/:
#     SnomedCT_USEdition_PRODUCTION_*/Snapshot/Terminology/
# -----------------------------------------------------------------------------

Write-Host "[5/5] SNOMED CT (~350k concepts + IS-A hierarchy, ~15 min)..." -ForegroundColor Cyan
uv run python -m app.terminology.import_.cli `
    --source snomed `
    --dir terminology_data\SnomedCT_USEdition\Snapshot\Terminology


Write-Host ""
Write-Host "All terminology loaders complete." -ForegroundColor Green
Write-Host "Verify counts:" -ForegroundColor Green
Write-Host "  SELECT cs.name, COUNT(tc.id) FROM terminology_code_system cs JOIN terminology_concept tc ON tc.code_system_id = cs.id GROUP BY cs.name ORDER BY COUNT DESC;" -ForegroundColor DarkGray
