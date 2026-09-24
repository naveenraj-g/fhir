#!/usr/bin/env bash
#
# reset_fhir_tables.sh
#
# Truncates every table in the FHIR schema EXCEPT the "master data" resources
# (patient, organization, location, healthcare_service, practitioner,
# practitioner_role, schedule, slot) and the terminology_* reference tables.
# Auto-increment sequences are restarted so new test data starts at id 1.
#
# Supports two ways of reaching Postgres — pick one with CONN_MODE:
#   - "docker": exec into a running Postgres container (no local psql needed)
#   - "direct": connect over the network with a local `psql` client
#
# Usage:
#   1. Fill in the variables below (or export them before running).
#   2. ./reset_fhir_tables.sh          # interactive, asks for confirmation
#   3. ./reset_fhir_tables.sh --yes    # skip the confirmation prompt

set -euo pipefail

# ── Fill these in ───────────────────────────────────────────────────────────
CONN_MODE="${CONN_MODE:-docker}"   # "docker" or "direct"

# Used when CONN_MODE=docker
DB_CONTAINER="${DB_CONTAINER:-}"   # e.g. fhir-db-1 (local) / fhir-postgres (vps)

# Used when CONN_MODE=direct
DB_HOST="${DB_HOST:-}"             # e.g. localhost
DB_PORT="${DB_PORT:-}"             # e.g. 5436

# Used by both modes
DB_USER="${DB_USER:-}"             # e.g. user
DB_PASSWORD="${DB_PASSWORD:-}"     # e.g. password
DB_NAME="${DB_NAME:-}"             # e.g. fhir-server

# Tables (and their child tables, matched by "<name>_%" prefix) to KEEP.
KEEP_TABLES=(organization location healthcare_service practitioner_role practitioner schedule slot patient)

# ── psql dispatch ────────────────────────────────────────────────────────────
# Runs a psql invocation against either a docker container or a direct host
# connection, depending on CONN_MODE. Extra args (e.g. -c "...", -f -) are
# forwarded as-is. Reading SQL from stdin (-f -) works in both modes.
run_psql() {
  if [[ "$CONN_MODE" == "docker" ]]; then
    # No -i here: none of our calls feed psql via stdin (-c/-Atqc only), and
    # attaching stdin would otherwise steal input meant for the confirmation
    # prompt in main().
    docker exec -e PGPASSWORD="$DB_PASSWORD" "$DB_CONTAINER" \
      psql -U "$DB_USER" -d "$DB_NAME" "$@"
  else
    PGPASSWORD="$DB_PASSWORD" psql -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "$DB_NAME" "$@"
  fi
}

# ── Connection check ────────────────────────────────────────────────────────
# Verifies the script can actually authenticate and run a query before doing
# anything destructive.
check_connection() {
  local target
  if [[ "$CONN_MODE" == "docker" ]]; then
    target="container ${DB_CONTAINER}, db ${DB_NAME}"
  else
    target="${DB_HOST}:${DB_PORT}/${DB_NAME}"
  fi
  echo "Checking connection to ${target} as ${DB_USER} (mode: ${CONN_MODE})..."

  if run_psql -v ON_ERROR_STOP=1 -Atqc "SELECT 1;" >/dev/null 2>&1; then
    echo "Connection OK."
    return 0
  else
    echo "ERROR: could not connect to ${target} as ${DB_USER}." >&2
    if [[ "$CONN_MODE" == "docker" ]]; then
      echo "Check DB_CONTAINER/DB_USER/DB_PASSWORD/DB_NAME and that the container is running." >&2
    else
      echo "Check DB_HOST/DB_PORT/DB_USER/DB_PASSWORD/DB_NAME and that the DB is reachable (and psql is installed)." >&2
    fi
    return 1
  fi
}

# ── Build the list of tables to truncate ────────────────────────────────────
# Queries pg_tables directly so this stays correct even if new resource
# tables get added by future migrations — nothing is hardcoded here besides
# the keep-list and the terminology_* / alembic_version exclusions.
build_reset_table_list() {
  local keep_array_sql
  keep_array_sql=$(printf "'%s'," "${KEEP_TABLES[@]}")
  keep_array_sql="ARRAY[${keep_array_sql%,}]"

  run_psql -v ON_ERROR_STOP=1 -Atqc "
    SELECT string_agg(quote_ident(tablename), ', ' ORDER BY tablename)
    FROM pg_tables
    WHERE schemaname='public'
      AND tablename <> 'alembic_version'
      AND tablename NOT LIKE 'terminology\_%'
      AND NOT EXISTS (
        SELECT 1 FROM unnest(${keep_array_sql}) AS k
        WHERE tablename = k OR tablename LIKE k || '\_%'
      );
  "
}

# ── Run the reset ────────────────────────────────────────────────────────────
reset_tables() {
  local table_list="$1"

  if [[ -z "$table_list" ]]; then
    echo "Nothing to truncate — table list came back empty." >&2
    return 1
  fi

  echo "Truncating:"
  echo "$table_list" | tr ',' '\n' | sed 's/^/  - /'
  echo

  run_psql -v ON_ERROR_STOP=1 -c "TRUNCATE TABLE ${table_list} RESTART IDENTITY CASCADE;"

  echo "Done."
}

main() {
  local skip_confirm=false
  [[ "${1:-}" == "--yes" ]] && skip_confirm=true

  local required_vars=(DB_USER DB_PASSWORD DB_NAME)
  if [[ "$CONN_MODE" == "docker" ]]; then
    required_vars+=(DB_CONTAINER)
  elif [[ "$CONN_MODE" == "direct" ]]; then
    required_vars+=(DB_HOST DB_PORT)
  else
    echo "ERROR: CONN_MODE must be 'docker' or 'direct', got '${CONN_MODE}'." >&2
    exit 1
  fi

  for var in "${required_vars[@]}"; do
    if [[ -z "${!var}" ]]; then
      echo "ERROR: $var is not set. Fill it in at the top of the script (or export it)." >&2
      exit 1
    fi
  done

  check_connection || exit 1

  local table_list
  table_list=$(build_reset_table_list)

  if [[ "$skip_confirm" != true ]]; then
    echo
    echo "This will permanently delete all data in the tables listed above from"
    echo "database ${DB_NAME}. Tables kept: ${KEEP_TABLES[*]} (+ terminology_*)."
    read -r -p "Type RESET to continue: " confirm
    if [[ "$confirm" != "RESET" ]]; then
      echo "Aborted."
      exit 1
    fi
  fi

  reset_tables "$table_list"
}

main "$@"
