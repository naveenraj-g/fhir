# FHIR Platform

A monorepo containing two services that together expose FHIR R4 healthcare data to AI agents via the Model Context Protocol (MCP).

```
fhir-server/   →   FHIR R4 REST API (FastAPI + PostgreSQL)
fhir-mcp/      →   MCP gateway — auto-generates AI tools from the FHIR OpenAPI spec
```

---

## How the pieces fit together

```
AI Agent (Claude, etc.)
        │  MCP (streamable-http)
        ▼
   fhir-mcp :8002
        │  HTTP + Bearer token
        ▼
   fhir-server :8000
        │  async SQL
        ▼
   PostgreSQL 15
```

1. **fhir-server** serves a FHIR R4 REST API and publishes an OpenAPI spec at `/openapi.json`.
2. **fhir-mcp** fetches that spec at startup, uses FastMCP to auto-generate one MCP tool per endpoint, and forwards every call (with the caller's JWT) to fhir-server.
3. AI agents connect to fhir-mcp over streamable-http MCP and gain typed, schema-validated access to all FHIR resources without any hand-written tool definitions.

---

## Services

### fhir-server

Production-ready FHIR R4 REST API.

| | |
|---|---|
| Port | `8000` |
| Framework | FastAPI + Uvicorn |
| Database | PostgreSQL 15 (async via asyncpg + SQLAlchemy 2.0) |
| Auth | JWT (JWKS-validated), per-resource permission scopes |
| Sessions / Rate limiting | Redis 7 |
| Package manager | uv |
| Python | 3.12+ |

**Supported FHIR resources:** Patient, Practitioner, PractitionerRole, Encounter, Appointment, QuestionnaireResponse, ServiceRequest, MedicationRequest, Procedure, DiagnosticReport, Condition, DeviceRequest, HealthcareService, Observation, Claim, ClaimResponse, Organization, Schedule, Invoice, Vitals (non-FHIR wearable metrics).

Every resource endpoint is mounted at `/api/fhir/v1/<resource>` and supports `POST /`, `GET /`, `GET /me`, `GET /{id}`, `PATCH /{id}`, `DELETE /{id}`.

Responses are dual-format — send `Accept: application/fhir+json` for FHIR R4 bundles or `Accept: application/json` for plain snake_case JSON.

→ See [`fhir-server/README.md`](fhir-server/README.md) for full setup, environment variables, migration commands, and deployment guide.

---

### fhir-mcp

MCP gateway that turns the fhir-server OpenAPI spec into AI tools at runtime.

| | |
|---|---|
| Port | `8002` |
| MCP endpoint | `http://localhost:8002/mcp` |
| Transport | Streamable-HTTP |
| Framework | FastAPI + FastMCP |
| Package manager | uv |
| Python | 3.14+ |

**How it works:**
- On startup, fhir-mcp fetches the OpenAPI spec from fhir-server (`OPENAPI_SPEC` env var) and calls `FastMCP.from_openapi()` to generate one MCP tool per endpoint.
- Every incoming MCP request must carry a `Bearer` JWT in the `Authorization` header. The `AuthForwardingMiddleware` validates the token against the JWKS endpoint and then propagates it to all upstream FHIR requests via `BearerAuth`.
- The MCP server mounts at `/mcp` on the FastAPI app, using the streamable-http transport.

**Environment variables:**

| Variable | Description |
|---|---|
| `HTTP_CLIENT` | Base URL of fhir-server, e.g. `http://localhost:8000` |
| `OPENAPI_SPEC` | Full URL to the OpenAPI spec, e.g. `http://localhost:8000/openapi.json` |
| `IAM_ISSUER` | JWT issuer URL |
| `IAM_JWKS_URL` | JWKS endpoint for token validation |
| `ENVIRONMENT` | `development` (default) or `production` |

**Local dev:**

```bash
cd fhir-mcp
cp .env.example .env   # fill in HTTP_CLIENT and OPENAPI_SPEC (point at fhir-server)
uv sync
uv run python -m app.main
```

MCP server available at `http://localhost:8002/mcp`.

**Docker:**

```bash
cd fhir-mcp
docker compose up
```

**Connect to Claude Desktop (example config):**

```json
{
  "mcpServers": {
    "fhir": {
      "url": "http://localhost:8002/mcp",
      "headers": {
        "Authorization": "Bearer <your-jwt>"
      }
    }
  }
}
```

**Inspect with MCP Inspector:**

```bash
npx @modelcontextprotocol/inspector
```

---

## Quick start (both services)

### Prerequisites

- Python 3.12+ (fhir-server), Python 3.14+ (fhir-mcp)
- PostgreSQL 15
- Redis 7
- [uv](https://github.com/astral-sh/uv)

### 1. Start fhir-server

```bash
cd fhir-server
cp .env.example .env        # fill in FHIR_DATABASE_URL, REDIS_URL, IAM_ISSUER, IAM_JWKS_URL
uv sync
uv run alembic upgrade head
uv run fastapi dev app/main.py
# → http://localhost:8000
```

### 2. Start fhir-mcp

```bash
cd fhir-mcp
cp .env.example .env        # set HTTP_CLIENT=http://localhost:8000, OPENAPI_SPEC=http://localhost:8000/openapi.json
uv sync
uv run python -m app.main
# → http://localhost:8002/mcp
```

### Or use Docker (each service has its own `docker-compose.yml`)

```bash
# Terminal 1
cd fhir-server && docker compose up

# Terminal 2
cd fhir-mcp && docker compose up
```

---

## Repository structure

```
fhir-server/
├── app/
│   ├── core/           # Config, DB engine, Redis, logging, content negotiation
│   ├── auth/           # JWT validation, permission guards
│   ├── di/             # Dependency injection container
│   ├── models/         # SQLAlchemy ORM models
│   ├── schemas/        # Pydantic input/output schemas
│   ├── fhir/mappers/   # FHIR ↔ plain dict converters
│   ├── repository/     # All DB I/O
│   ├── services/       # Orchestration layer
│   ├── routers/        # FastAPI route definitions
│   ├── middleware/      # Rate limiting, request context
│   └── errors/         # Error hierarchy, OperationOutcome handlers
└── migrations/         # Alembic migration versions

fhir-mcp/
└── app/
    ├── main.py         # FastMCP server + AuthForwardingMiddleware + FastAPI app
    ├── core/config.py  # pydantic-settings configuration
    └── auth/decode_token.py  # JWKS-based JWT validation
```
