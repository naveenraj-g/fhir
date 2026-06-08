# SMART on FHIR — Complete Implementation Guide

> Full implementation of SMART App Launch v2, Backend Services, PKCE, scope enforcement, Keycloak configuration, and integration with the existing FHIR server + Pulse middleware stack.

---

## What SMART on FHIR Is

SMART on FHIR (Substitutable Medical Applications, Reusable Technologies) is the **authorization layer** that sits on top of OAuth2 / OpenID Connect and makes it clinical-context-aware. It defines:

1. **How apps discover** the authorization server (`/.well-known/smart-configuration`)
2. **How apps launch** — EHR-embedded launch vs. standalone launch
3. **What scopes** control access (patient context, user context, system context)
4. **How backend services** authenticate without user interaction
5. **What context** is carried in the token (which patient, which encounter)

SMART App Launch v2 (HL7 SMART IG v2.0.0+) is what US Core v7+ and ONC (g)(10) require.

---

## 1. Keycloak Configuration for SMART

### 1.1 Realm Setup

```
Realm: healthcare-platform
    │
    ├── Clients
    │     ├── web-app              (public, authorization_code + PKCE)
    │     ├── mobile-app           (public, authorization_code + PKCE)
    │     ├── pulse-orchestrator   (confidential, client_credentials, system)
    │     ├── fhir-server          (bearer-only resource server)
    │     └── inferno-test         (public, PKCE, for Inferno test kit)
    │
    ├── Client Scopes (SMART v2 granular — created once, assigned to clients)
    │     ├── patient/Patient.r
    │     ├── patient/Patient.u
    │     ├── patient/Patient.s
    │     ├── patient/Observation.rs
    │     ├── patient/MedicationRequest.rs
    │     ├── patient/*.rs         (wildcard shorthand)
    │     ├── user/Patient.cruds
    │     ├── user/*.cruds
    │     ├── system/Patient.rs
    │     ├── system/*.cruds
    │     ├── launch               (EHR launch context)
    │     ├── launch/patient       (patient context binding)
    │     ├── launch/encounter     (encounter context binding)
    │     └── openid profile email
    │
    └── Protocol Mappers (on each client scope)
          ├── patient_id → token claim "launch_response.patient"
          ├── encounter_id → token claim "launch_response.encounter"
          ├── org_id → token claim "activeOrganizationId"
          └── fhir_user → token claim "fhirUser" (e.g. "Practitioner/30001")
```

### 1.2 Creating SMART Scopes in Keycloak

Keycloak's built-in scopes do not know about FHIR. Create them via Admin REST API or UI:

```python
# scripts/setup_keycloak_smart_scopes.py
from keycloak import KeycloakAdmin

admin = KeycloakAdmin(
    server_url="https://auth.yourplatform.com/",
    realm_name="healthcare-platform",
    client_id="admin-cli",
    client_secret="...",
)

SMART_SCOPES = [
    # Patient context scopes
    "patient/Patient.r", "patient/Patient.rs", "patient/Patient.cruds",
    "patient/Observation.rs", "patient/Condition.rs",
    "patient/MedicationRequest.rs", "patient/AllergyIntolerance.rs",
    "patient/Immunization.rs", "patient/Procedure.rs",
    "patient/DiagnosticReport.rs", "patient/Encounter.rs",
    "patient/DocumentReference.rs", "patient/CarePlan.rs",
    "patient/*.r", "patient/*.rs", "patient/*.cruds",
    # User context scopes
    "user/Patient.cruds", "user/Practitioner.cruds",
    "user/MedicationRequest.cruds", "user/Encounter.cruds",
    "user/*.r", "user/*.rs", "user/*.cruds",
    # System scopes
    "system/Patient.rs", "system/*.rs", "system/*.cruds",
    # Launch context
    "launch", "launch/patient", "launch/encounter",
]

for scope_name in SMART_SCOPES:
    admin.create_client_scope({
        "name": scope_name,
        "protocol": "openid-connect",
        "attributes": {
            "include.in.token.introspection": "true",
            "display.on.consent.screen": "true",
        },
    }, skip_exists=True)
```

### 1.3 Custom Protocol Mapper (inject SMART context claims)

Add a JavaScript mapper to the `launch/patient` scope that injects patient context:

```javascript
// Keycloak → Client Scope → launch/patient → Mappers → Add Mapper → Script Mapper
// Name: patient-launch-context
// Claim name: launch_response
// Claim value type: JSON

var patientId = user.getAttribute("lastPatientContext");
if (patientId) {
    token.setOtherClaims("launch_response", {"patient": patientId});
}
```

For `activeOrganizationId` and `fhirUser`:
```javascript
// Mapper: org-context
token.setOtherClaims("activeOrganizationId", user.getAttribute("activeOrganizationId") || "");

// Mapper: fhir-user
var practitionerId = user.getAttribute("fhirPractitionerId");
if (practitionerId) {
    token.setOtherClaims("fhirUser", "Practitioner/" + practitionerId);
}
```

---

## 2. SMART Discovery Endpoint

Add to the FHIR server (or nginx to proxy it to the auth server):

```python
# app/routers/smart_config.py
from fastapi import APIRouter
from fastapi.responses import JSONResponse
from app.core.config import settings

router = APIRouter()

@router.get(
    "/.well-known/smart-configuration",
    include_in_schema=False,
    response_class=JSONResponse,
)
async def smart_configuration():
    return JSONResponse(
        content={
            "issuer": settings.IAM_ISSUER,
            "jwks_uri": f"{settings.IAM_ISSUER}/protocol/openid-connect/certs",
            "authorization_endpoint": f"{settings.IAM_ISSUER}/protocol/openid-connect/auth",
            "token_endpoint": f"{settings.IAM_ISSUER}/protocol/openid-connect/token",
            "token_endpoint_auth_methods_supported": [
                "private_key_jwt",
                "client_secret_basic",
                "client_secret_post",
            ],
            "revocation_endpoint": f"{settings.IAM_ISSUER}/protocol/openid-connect/revoke",
            "introspection_endpoint": f"{settings.IAM_ISSUER}/protocol/openid-connect/token/introspect",
            "grant_types_supported": [
                "authorization_code",
                "client_credentials",
            ],
            "registration_endpoint": f"{settings.IAM_ISSUER}/clients-registrations/openid-connect",
            "scopes_supported": [
                "openid", "profile", "email", "offline_access",
                "launch", "launch/patient", "launch/encounter",
                "patient/*.r", "patient/*.rs", "patient/*.cruds",
                "user/*.r", "user/*.rs", "user/*.cruds",
                "system/*.r", "system/*.rs", "system/*.cruds",
            ],
            "response_types_supported": ["code"],
            "response_modes_supported": ["query"],
            "code_challenge_methods_supported": ["S256"],
            "capabilities": [
                "launch-ehr",
                "launch-standalone",
                "authorize-post",
                "client-public",
                "client-confidential-symmetric",
                "client-confidential-asymmetric",
                "context-banner",
                "context-style",
                "context-ehr-patient",
                "context-ehr-encounter",
                "context-standalone-patient",
                "permission-offline",
                "permission-patient",
                "permission-user",
                "permission-v2",
                "smart-app-state",
            ],
        },
        headers={"Content-Type": "application/json"},
    )
```

Mount it:
```python
# app/main.py
from app.routers.smart_config import router as smart_config_router
app.include_router(smart_config_router)  # no prefix — must be at root
```

---

## 3. SMART App Launch Flows

### 3.1 EHR Launch (Embedded App)

The EHR (your web portal) launches the SMART app with a `launch` token that encodes the patient/encounter context.

```
EHR Portal                     Keycloak                    SMART App
    │                              │                             │
    │  1. User opens patient chart │                             │
    │  2. Clicks "Open SMART App"  │                             │
    │─────────────────────────────►│                             │
    │                              │  3. EHR calls launch API    │
    │                              │  POST /launch               │
    │                              │  { patient_id, encounter_id,│
    │                              │    practitioner_id }        │
    │                              │  → returns launch_token     │
    │                              │                             │
    │  4. Redirect app with:       │                             │
    │  ?iss=https://fhir.platform  │                             │
    │  &launch={launch_token}      │                             │
    │─────────────────────────────────────────────────────────►  │
    │                              │                             │
    │                              │  5. App discovers smart-cfg │
    │                              │◄────────────────────────────│
    │                              │  GET /.well-known/smart-cfg  │
    │                              │                             │
    │                              │  6. App builds auth URL     │
    │                              │◄────────────────────────────│
    │                              │  GET /auth?                 │
    │                              │    client_id=smart-app      │
    │                              │    response_type=code       │
    │                              │    scope=launch openid      │
    │                              │      patient/Patient.rs     │
    │                              │    launch={launch_token}    │
    │                              │    code_challenge={S256}    │
    │                              │    redirect_uri=app.com/cb  │
    │                              │                             │
    │  7. Keycloak validates launch │                             │
    │     Validates user session   │                             │
    │     Shows consent screen     │                             │
    │─────────────────────────────►│                             │
    │                              │  8. Redirect to app with    │
    │                              │     authorization_code      │
    │                              │────────────────────────────►│
    │                              │                             │
    │                              │  9. App exchanges code      │
    │                              │◄────────────────────────────│
    │                              │  POST /token                │
    │                              │    code=...                 │
    │                              │    code_verifier=...        │
    │                              │────────────────────────────►│
    │                              │  Returns access_token,      │
    │                              │  id_token, refresh_token    │
    │                              │  + patient context:         │
    │                              │  { "patient": "10001",      │
    │                              │    "encounter": "20001" }   │
    └──────────────────────────────┴─────────────────────────────┘
```

#### EHR Launch API (in Pulse middleware)

```python
# pulse/routers/smart_launch.py

@router.post("/smart/launch", operation_id="create_ehr_launch_context")
async def create_ehr_launch(
    body: EHRLaunchRequest,
    auth: AuthContext = Depends(get_auth_context),
):
    """
    Called by EHR portal before redirecting to a SMART app.
    Creates a launch token that encodes patient/encounter context.
    Stores it in Redis with short TTL (60 seconds — single use).
    """
    launch_token = secrets.token_urlsafe(32)

    launch_context = {
        "patient_id": body.patient_id,
        "encounter_id": body.encounter_id,
        "practitioner_id": auth.user_id,
        "org_id": auth.org_id,
        "created_at": datetime.utcnow().isoformat(),
    }

    # Store with 60s TTL — Keycloak must consume it quickly
    await redis.setex(
        f"smart_launch:{launch_token}",
        60,
        json.dumps(launch_context),
    )

    return JSONResponse({"launch": launch_token, "iss": settings.FHIR_BASE_URL})
```

#### Keycloak Launch Token Validator (Event Listener SPI)

In Keycloak, implement a custom SPI that validates the `launch` parameter against Redis before issuing the authorization code. This SPI:
1. Reads the `launch` parameter from the auth request
2. Looks up the launch context in Redis
3. Sets patient/encounter context on the user session
4. Marks the launch token as consumed (Redis DELETE)

```java
// Pseudocode — implement as Keycloak Authenticator SPI (Java)
public class SmartLaunchAuthenticator implements Authenticator {
    @Override
    public void authenticate(AuthenticationFlowContext context) {
        String launchToken = context.getAuthenticationSession().getClientNote("launch");
        if (launchToken == null) {
            context.success();  // standalone launch — no launch token required
            return;
        }
        LaunchContext lc = redisClient.getAndDelete("smart_launch:" + launchToken);
        if (lc == null) {
            context.failure(AuthenticationFlowError.INVALID_CREDENTIALS);
            return;
        }
        // Inject patient context into session notes (becomes JWT claim)
        context.getAuthenticationSession().setUserSessionNote("smart_patient", lc.patientId);
        context.getAuthenticationSession().setUserSessionNote("smart_encounter", lc.encounterId);
        context.success();
    }
}
```

---

### 3.2 Standalone Launch

App launches from outside the EHR (e.g., patient portal, mobile app). No `launch` parameter — app must ask the user to select a patient.

```
Patient App                   Keycloak                    FHIR Server
    │                             │                            │
    │  1. User taps "Open App"    │                            │
    │                             │                            │
    │  2. App discovers smart-cfg │                            │
    │─────────────────────────────────────────────────────────►│
    │◄─────────────────────────────────────────────────────────│
    │  Returns .well-known/smart-configuration                 │
    │                             │                            │
    │  3. PKCE: generate verifier + challenge                  │
    │  verifier = random(32 bytes)                             │
    │  challenge = BASE64URL(SHA256(verifier))                 │
    │                             │                            │
    │  4. Auth redirect:          │                            │
    │─────────────────────────────►                            │
    │  GET /auth?                 │                            │
    │    client_id=patient-app    │                            │
    │    response_type=code       │                            │
    │    scope=openid profile     │                            │
    │      launch/patient         │                            │
    │      patient/Patient.r      │                            │
    │      patient/Observation.rs │                            │
    │    code_challenge={S256}    │                            │
    │    code_challenge_method=S256│                           │
    │    redirect_uri=app://cb    │                            │
    │                             │                            │
    │  5. User authenticates (MFA for staff)                   │
    │  6. Consent screen shown    │                            │
    │  7. Redirect with code      │                            │
    │◄────────────────────────────│                            │
    │                             │                            │
    │  8. POST /token             │                            │
    │─────────────────────────────►                            │
    │    code, code_verifier      │                            │
    │◄────────────────────────────│                            │
    │  Returns:                   │                            │
    │  { access_token,            │                            │
    │    token_type: "Bearer",    │                            │
    │    expires_in: 300,         │                            │
    │    refresh_token,           │                            │
    │    patient: "10001",  ←── patient selected during login │
    │    id_token }               │                            │
    └─────────────────────────────┴────────────────────────────┘
```

---

### 3.3 SMART Backend Services (System-Level Access)

Used by the Pulse orchestrator, HL7v2 adapters, bulk export jobs — no user interaction.

```python
# pulse/auth/backend_services.py
import jwt
import time
import uuid
from cryptography.hazmat.primitives import serialization

class SMARTBackendAuth:
    """
    Implements SMART Backend Services (RFC 7523 — JWT Bearer client assertion).
    The client proves identity with a private key instead of a client secret.
    """

    def __init__(self, client_id: str, private_key_path: str, token_endpoint: str):
        self.client_id = client_id
        self.token_endpoint = token_endpoint
        with open(private_key_path, "rb") as f:
            self.private_key = serialization.load_pem_private_key(f.read(), password=None)

    def _build_client_assertion(self) -> str:
        """Build a signed JWT to present as client_assertion."""
        now = int(time.time())
        payload = {
            "iss": self.client_id,
            "sub": self.client_id,
            "aud": self.token_endpoint,
            "jti": str(uuid.uuid4()),    # unique ID — prevents replay
            "iat": now,
            "exp": now + 300,            # 5-minute window
        }
        return jwt.encode(payload, self.private_key, algorithm="RS384")

    async def get_access_token(self, scopes: list[str]) -> str:
        """Exchange client assertion for access token."""
        assertion = self._build_client_assertion()

        async with httpx.AsyncClient() as client:
            resp = await client.post(
                self.token_endpoint,
                data={
                    "grant_type": "client_credentials",
                    "client_assertion_type": "urn:ietf:params:oauth:client-assertion-type:jwt-bearer",
                    "client_assertion": assertion,
                    "scope": " ".join(scopes),
                },
            )
            resp.raise_for_status()
            return resp.json()["access_token"]
```

Register the public key in Keycloak:
```
Keycloak Admin → Clients → pulse-orchestrator → Keys → Import
→ Use JWKS URL: https://pulse.yourplatform.com/.well-known/jwks.json
   (or upload the PEM public key directly)
→ Client Authenticator: Signed JWT
```

---

## 4. JWT Validation Middleware

Full implementation for the FHIR server (fills the critical P0 gap):

```python
# app/middleware/jwt_auth.py
import jwt
from jwt import PyJWKClient
from fastapi import Request
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from app.core.config import settings
from app.core.logging import get_logger

logger = get_logger(__name__)

EXCLUDED_PATHS = frozenset({
    "/health", "/health/ready", "/favicon.ico",
    "/openapi.json", "/.well-known/smart-configuration",
    "/api/fhir/v1/metadata",
})
EXCLUDED_PREFIXES = ("/docs", "/redoc")


class JWTAuthMiddleware(BaseHTTPMiddleware):
    def __init__(self, app):
        super().__init__(app)
        # PyJWKClient caches JWKS with a 5-minute refresh
        self._jwks_client = PyJWKClient(
            settings.IAM_JWKS_URL,
            cache_jwk_set=True,
            lifespan=300,
        )

    async def dispatch(self, request: Request, call_next):
        path = request.url.path

        if path in EXCLUDED_PATHS or any(path.startswith(p) for p in EXCLUDED_PREFIXES):
            return await call_next(request)

        auth_header = request.headers.get("Authorization", "")
        if not auth_header.startswith("Bearer "):
            return self._error(401, "security", "Missing or invalid Authorization header")

        token = auth_header[7:]

        try:
            signing_key = self._jwks_client.get_signing_key_from_jwt(token)
            payload = jwt.decode(
                token,
                signing_key.key,
                algorithms=["RS256", "RS384"],
                audience=settings.IAM_AUDIENCE,
                issuer=settings.IAM_ISSUER,
                options={"verify_exp": True, "verify_aud": True},
            )
        except jwt.ExpiredSignatureError:
            return self._error(401, "security", "Token expired")
        except jwt.InvalidAudienceError:
            return self._error(401, "security", "Token audience mismatch")
        except jwt.InvalidIssuerError:
            return self._error(401, "security", "Token issuer mismatch")
        except jwt.InvalidTokenError as e:
            logger.warning("JWT validation failed", extra={"error": str(e)})
            return self._error(401, "security", "Invalid token")

        # Attach decoded claims to request state
        request.state.user = payload

        # Extract scopes as a set for fast O(1) lookups
        scope_str = payload.get("scope", "")
        request.state.scopes = set(scope_str.split()) if scope_str else set()

        # Extract SMART launch context
        launch = payload.get("launch_response", {})
        request.state.smart_patient = launch.get("patient")
        request.state.smart_encounter = launch.get("encounter")

        return await call_next(request)

    @staticmethod
    def _error(status: int, code: str, msg: str) -> JSONResponse:
        return JSONResponse(
            status_code=status,
            content={
                "resourceType": "OperationOutcome",
                "issue": [{"severity": "error", "code": code, "diagnostics": msg}],
            },
        )
```

Add to `main.py`:
```python
from app.middleware.jwt_auth import JWTAuthMiddleware

app.add_middleware(JWTAuthMiddleware)   # runs after rate limit
```

---

## 5. SMART Scope Enforcement

```python
# app/core/smart_scopes.py

from functools import lru_cache
from fastapi import HTTPException, Request

# FHIR HTTP method → SMART action letter
METHOD_TO_ACTION = {
    "GET":    "r",   # read / search
    "POST":   "c",   # create
    "PUT":    "u",   # update (full)
    "PATCH":  "u",   # update (partial)
    "DELETE": "d",   # delete
}

# Scope context priority: if patient scope AND user scope both present, use patient
# System scope is for backend services only

def _required_scopes(resource_type: str, method: str) -> list[set[str]]:
    """
    Return a list of scope sets — request passes if ANY set is fully present.
    This implements the SMART v2 "any of these scope combinations is sufficient" rule.
    """
    action = METHOD_TO_ACTION.get(method, "r")
    rt = resource_type  # e.g. "Patient"

    return [
        # patient-level: specific resource
        {f"patient/{rt}.{action}", f"patient/{rt}.cruds"},
        # patient-level: wildcard
        {f"patient/*.{action}"}, {f"patient/*.cruds"},
        # user-level: specific resource
        {f"user/{rt}.{action}"}, {f"user/{rt}.cruds"},
        # user-level: wildcard
        {f"user/*.{action}"}, {f"user/*.cruds"},
        # system-level: specific resource
        {f"system/{rt}.{action}"}, {f"system/{rt}.cruds"},
        # system-level: wildcard
        {f"system/*.{action}"}, {f"system/*.cruds"},
    ]


def require_smart_scope(resource_type: str):
    """
    FastAPI dependency factory. Usage:
        @router.get("/{id}", dependencies=[Depends(require_smart_scope("Patient"))])
    """
    async def _check(request: Request):
        token_scopes: set[str] = getattr(request.state, "scopes", set())
        method = request.method

        for required_set in _required_scopes(resource_type, method):
            if required_set.issubset(token_scopes):
                return  # pass

        raise HTTPException(
            status_code=403,
            detail={
                "resourceType": "OperationOutcome",
                "issue": [{
                    "severity": "error",
                    "code": "forbidden",
                    "diagnostics": (
                        f"Insufficient scope for {method} on {resource_type}. "
                        f"Token scopes: {sorted(token_scopes)}"
                    ),
                }],
            },
        )

    return _check
```

### Using scope enforcement in routers

```python
# app/routers/patient.py  (updated)
from app.core.smart_scopes import require_smart_scope

_SCOPE_READ   = Depends(require_smart_scope("Patient"))
_SCOPE_WRITE  = Depends(require_smart_scope("Patient"))

@router.get(
    "/{patient_id}",
    dependencies=[_SCOPE_READ],
    ...
)
async def get_patient(...): ...

@router.post(
    "/",
    dependencies=[_SCOPE_WRITE],
    ...
)
async def create_patient(...): ...
```

---

## 6. Patient-Scoped Context Enforcement

When a token carries a `launch_response.patient`, all resource access must be restricted to that patient:

```python
# app/middleware/patient_context.py

class PatientContextMiddleware(BaseHTTPMiddleware):
    """
    If the token contains a patient launch context (patient scope),
    enforce that all resource requests belong to that patient.
    Prevents a patient-scoped token from accessing another patient's data.
    """

    async def dispatch(self, request: Request, call_next):
        smart_patient = getattr(request.state, "smart_patient", None)
        scopes = getattr(request.state, "scopes", set())

        # Only enforce if token carries a patient-context scope
        is_patient_scoped = any(s.startswith("patient/") for s in scopes)

        if smart_patient and is_patient_scoped:
            # Inject patient_id filter so repos always constrain to this patient
            request.state.patient_context_id = int(smart_patient)

        return await call_next(request)
```

In the repository, every query that touches patient-owned resources checks this:
```python
# In any repository's _apply_list_filters:
patient_context = getattr(request.state, "patient_context_id", None)
if patient_context:
    stmt = stmt.where(Model.patient_id == patient_context)
```

---

## 7. Token Refresh Flow

```python
# pulse/auth/token_refresh.py

class TokenRefreshService:
    """
    Handles proactive token refresh before expiry.
    Called by the web/mobile client every 4 minutes (for 5-minute tokens).
    """

    async def refresh(self, session_id: str) -> dict:
        session = await self.session_manager.get_session(session_id)
        if not session:
            raise SessionExpiredError("Session not found or expired")

        refresh_token = session.get("refresh_token")
        if not refresh_token:
            raise SessionExpiredError("No refresh token in session")

        # Exchange refresh token for new tokens
        async with httpx.AsyncClient() as client:
            resp = await client.post(
                settings.IAM_TOKEN_ENDPOINT,
                data={
                    "grant_type": "refresh_token",
                    "refresh_token": refresh_token,
                    "client_id": settings.IAM_CLIENT_ID,
                    "client_secret": settings.IAM_CLIENT_SECRET,
                },
            )

        if resp.status_code == 400:
            # Refresh token expired — force re-login
            await self.session_manager.delete_session(session_id)
            raise SessionExpiredError("Refresh token expired. Please log in again.")

        resp.raise_for_status()
        new_tokens = resp.json()

        # Decode new access token for user_info
        new_payload = jwt.decode(new_tokens["access_token"], options={"verify_signature": False})

        # Update session with new tokens
        await self.session_manager.update_session(
            session_id,
            user_info=new_payload,
            tokens=new_tokens,
        )

        return {
            "access_token": new_tokens["access_token"],
            "expires_in": new_tokens.get("expires_in", 300),
        }
```

---

## 8. SMART App Registration

For third-party SMART apps (Epic App Orchard-style), implement dynamic client registration:

```python
# pulse/routers/smart_register.py

@router.post(
    "/smart/register",
    operation_id="register_smart_app",
    summary="Dynamic SMART app client registration (RFC 7591)",
)
async def register_smart_app(
    body: SmartAppRegistrationRequest,
    auth: AuthContext = Depends(require_admin),
):
    """
    Register a new SMART app client in Keycloak.
    Only org admins can register apps.
    """
    keycloak_admin = get_keycloak_admin()

    client_id = str(uuid.uuid4())
    client = {
        "clientId": client_id,
        "name": body.app_name,
        "description": body.description,
        "publicClient": not body.confidential,
        "redirectUris": body.redirect_uris,
        "webOrigins": body.launch_url and [body.launch_url],
        "standardFlowEnabled": True,
        "implicitFlowEnabled": False,
        "directAccessGrantsEnabled": False,
        "attributes": {
            "pkce.code.challenge.method": "S256",
            "smart.launch.url": body.launch_url or "",
            "smart.app.description": body.description,
            "smart.app.logo_uri": body.logo_uri or "",
        },
        "defaultClientScopes": ["openid", "profile"],
        "optionalClientScopes": body.requested_scopes,
    }

    keycloak_admin.create_client(client)

    # Store registration for display in app gallery
    await app_registry.register(
        client_id=client_id,
        org_id=auth.org_id,
        app_name=body.app_name,
        approved=False,  # requires admin approval before activation
    )

    return {
        "client_id": client_id,
        "client_secret": None if not body.confidential else keycloak_admin.get_client_secret(client_id),
        "registration_access_token": str(uuid.uuid4()),
        "status": "pending_approval",
    }
```

---

## 9. SMART on FHIR in the CapabilityStatement

The CapabilityStatement must advertise SMART support:

```python
# app/routers/metadata.py (update security section)

SMART_SECURITY = {
    "cors": True,
    "service": [{
        "coding": [{
            "system": "http://terminology.hl7.org/CodeSystem/restful-security-service",
            "code": "SMART-on-FHIR",
            "display": "SMART on FHIR",
        }]
    }],
    "description": "OAuth2 via SMART App Launch v2",
    "extension": [{
        "url": "http://fhir-registry.smarthealthit.org/StructureDefinition/oauth-uris",
        "extension": [
            {
                "url": "authorize",
                "valueUri": f"{settings.IAM_ISSUER}/protocol/openid-connect/auth",
            },
            {
                "url": "token",
                "valueUri": f"{settings.IAM_ISSUER}/protocol/openid-connect/token",
            },
            {
                "url": "introspect",
                "valueUri": f"{settings.IAM_ISSUER}/protocol/openid-connect/token/introspect",
            },
            {
                "url": "revoke",
                "valueUri": f"{settings.IAM_ISSUER}/protocol/openid-connect/revoke",
            },
            {
                "url": "register",
                "valueUri": f"{settings.PULSE_BASE_URL}/smart/register",
            },
        ],
    }],
}
```

---

## 10. Inferno SMART Test Preparation

### Test Group: SMART App Launch v2

Inferno tests these in order:

| Test | What It Checks | Common Failure |
|---|---|---|
| Discovery | `/.well-known/smart-configuration` valid JSON with required fields | Missing `code_challenge_methods_supported` or `capabilities` |
| Authorization request | Auth endpoint accepts PKCE parameters | `code_challenge_method` not echoed back in token |
| Token exchange | `POST /token` with `code` + `code_verifier` returns valid access token | Keycloak not validating `code_verifier` (enable PKCE in client settings) |
| Token contains patient context | `patient` claim present in token response | Launch context mapper not configured in Keycloak |
| Scope filtering | Token only grants requested scopes | Keycloak granting all scopes by default — configure scope consent |
| Refresh token | `offline_access` scope allows token refresh | `offline_access` scope not optional on client |
| Token revocation | `POST /revoke` invalidates token | Revocation endpoint not advertised in `.well-known` |

### Quick-Start Inferno Test Sequence

```bash
# 1. Start Inferno locally
docker pull healthlake/inferno:latest
docker run -p 4567:4567 healthlake/inferno:latest

# 2. Open http://localhost:4567
# 3. Create new test session:
#    FHIR Server URL: https://yourplatform.com/api/fhir/v1
#    Client ID:       inferno-test
#    Redirect URI:    http://localhost:4567/inferno/oauth2/static/redirect

# 4. Run "SMART App Launch" test group first
# 5. Fix failures, re-run
# 6. Then run "Single Patient US Core API"
```

### Pre-Inferno Verification Checklist

```bash
# Verify .well-known returns valid JSON
curl -s https://yourplatform.com/.well-known/smart-configuration | jq .

# Verify metadata has SMART security extensions
curl -s -H "Accept: application/fhir+json" \
  https://yourplatform.com/api/fhir/v1/metadata | jq '.rest[0].security'

# Manual PKCE flow test
VERIFIER=$(openssl rand -base64 32 | tr -d '=+/' | cut -c1-43)
CHALLENGE=$(echo -n "$VERIFIER" | openssl dgst -sha256 -binary | base64 | tr '+/' '-_' | tr -d '=')

# Auth URL
echo "https://auth.yourplatform.com/auth?client_id=inferno-test&response_type=code&scope=openid+patient/Patient.rs&code_challenge=${CHALLENGE}&code_challenge_method=S256&redirect_uri=http://localhost:4567/callback"

# After redirect, exchange code:
curl -X POST https://auth.yourplatform.com/token \
  -d "grant_type=authorization_code&code=XXXX&code_verifier=${VERIFIER}&client_id=inferno-test&redirect_uri=http://localhost:4567/callback"
```

---

## 11. SMART Configuration Table

```python
# app/core/config.py — add these settings
class Settings(BaseSettings):
    # ... existing fields ...

    # Auth / Keycloak
    IAM_ISSUER: str                      # https://auth.yourplatform.com/realms/healthcare-platform
    IAM_JWKS_URL: str                    # {IAM_ISSUER}/protocol/openid-connect/certs
    IAM_AUDIENCE: str = "fhir-server"
    IAM_TOKEN_ENDPOINT: str              # {IAM_ISSUER}/protocol/openid-connect/token
    IAM_AUTH_ENDPOINT: str               # {IAM_ISSUER}/protocol/openid-connect/auth
    IAM_REVOKE_ENDPOINT: str             # {IAM_ISSUER}/protocol/openid-connect/revoke
    IAM_INTROSPECT_ENDPOINT: str         # {IAM_ISSUER}/protocol/openid-connect/token/introspect
    IAM_CLIENT_ID: str                   # fhir-server (for token validation)
    IAM_CLIENT_SECRET: str               # (store in Secrets Manager)

    # SMART backend service (for Pulse → FHIR server)
    PULSE_CLIENT_ID: str                 # pulse-orchestrator
    PULSE_PRIVATE_KEY_PATH: str          # /secrets/pulse_private_key.pem

    # FHIR server public URL
    FHIR_BASE_URL: str                   # https://yourplatform.com/api/fhir/v1
    PULSE_BASE_URL: str                  # https://pulse.yourplatform.com

    # Session
    SESSION_TTL_SECONDS: int = 900       # 15 minutes
    SESSION_COOKIE_SECURE: bool = True
    SESSION_COOKIE_SAMESITE: str = "lax"
```
