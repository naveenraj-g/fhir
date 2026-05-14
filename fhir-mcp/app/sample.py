import json
import httpx
import uvicorn
from contextlib import asynccontextmanager
from contextvars import ContextVar
from typing import Any, Dict

from fastapi import FastAPI
from fastmcp import FastMCP
from starlette.requests import Request
from starlette.responses import Response
from starlette.types import ASGIApp, Receive, Scope, Send

from app.core.config import settings

# ---------------------------------------------------------------------------
# 1. ContextVar for per-request auth token (concurrency-safe)
# ---------------------------------------------------------------------------
current_token: ContextVar[str | None] = ContextVar("current_token", default=None)


class BearerAuth(httpx.Auth):
    """Inject Authorization header from request context."""

    def auth_flow(self, request: httpx.Request):
        token = current_token.get()
        if token:
            request.headers["Authorization"] = token
        yield request


# ---------------------------------------------------------------------------
# 2. HTTP client pointed at FHIR backend
# ---------------------------------------------------------------------------
client = httpx.AsyncClient(
    base_url=settings.HTTP_CLIENT,
    auth=BearerAuth(),
)

# ---------------------------------------------------------------------------
# 3. Load OpenAPI spec manually
# ---------------------------------------------------------------------------
openapi_spec = httpx.get(settings.OPENAPI_SPEC).json()

mcp = FastMCP("FHIR MCP")


# ---------------------------------------------------------------------------
# 4. Helpers to manually convert OpenAPI → MCP tools
# ---------------------------------------------------------------------------


def iter_operations(spec: Dict[str, Any]):
    """Yield (method, path, operation) for each OpenAPI operation."""
    for path, path_item in spec.get("paths", {}).items():
        for method, operation in path_item.items():
            if method.lower() in {"get", "post", "put", "patch", "delete"}:
                yield method.upper(), path, operation


def build_input_schema(operation: Dict[str, Any]) -> Dict[str, Any]:
    """
    Convert OpenAPI parameters + requestBody into MCP input schema.
    This is simplified — production version should fully merge schemas.
    """
    properties = {}
    required = []

    # Parameters (query/path/header)
    for param in operation.get("parameters", []):
        name = param["name"]
        schema = param.get("schema", {"type": "string"})
        properties[name] = schema
        if param.get("required"):
            required.append(name)

    # Request body (application/json)
    request_body = operation.get("requestBody", {})
    content = request_body.get("content", {})
    json_schema = content.get("application/json", {}).get("schema")

    if json_schema:
        properties["body"] = json_schema
        if request_body.get("required"):
            required.append("body")

    return {
        "type": "object",
        "properties": properties,
        "required": required,
    }


def handler_factory(method: str, path: str, operation: Dict[str, Any]):
    """
    Create an MCP handler that calls the downstream FHIR API.
    """

    async def handler(args: Dict[str, Any]):
        # Split parameters
        path_params = {}
        query_params = {}
        body = args.get("body")

        for param in operation.get("parameters", []):
            name = param["name"]
            location = param["in"]

            if name in args:
                if location == "path":
                    path_params[name] = args[name]
                elif location == "query":
                    query_params[name] = args[name]

        # Replace path params
        formatted_path = path
        for key, value in path_params.items():
            formatted_path = formatted_path.replace(f"{{{key}}}", str(value))

        # Call downstream API
        response = await client.request(
            method=method,
            url=formatted_path,
            params=query_params,
            json=body,
        )

        # Raise if error
        response.raise_for_status()

        return response.json()

    return handler


# ---------------------------------------------------------------------------
# 5. Register MCP tools dynamically
# ---------------------------------------------------------------------------

for method, path, operation in iter_operations(openapi_spec):
    operation_id = operation.get("operationId")
    if not operation_id:
        continue

    input_schema = build_input_schema(operation)

    mcp.tool(
        name=operation_id,
        description=operation.get("summary") or operation.get("description") or "",
        # input_schema=input_schema,
    )(handler_factory(method, path, operation))


# ---------------------------------------------------------------------------
# 6. Build MCP Starlette sub-app
# ---------------------------------------------------------------------------
mcp_app = mcp.http_app(path="/", transport="streamable-http")


# ---------------------------------------------------------------------------
# 7. Middleware: Forward Authorization header → ContextVar
# ---------------------------------------------------------------------------


class AuthForwardingMiddleware:
    """
    Extract Authorization header and store in ContextVar.
    Enforce auth on /mcp routes.
    """

    def __init__(self, app: ASGIApp):
        self.app = app

    async def __call__(self, scope: Scope, receive: Receive, send: Send):
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        request = Request(scope)
        auth_header = request.headers.get("authorization")

        if request.url.path.startswith("/mcp"):
            if not auth_header:
                response = Response(
                    "Missing Authorization header",
                    status_code=401,
                )
                await response(scope, receive, send)
                return

        token = current_token.set(auth_header)

        try:
            await self.app(scope, receive, send)
        finally:
            current_token.reset(token)


# ---------------------------------------------------------------------------
# 8. FastAPI wrapper
# ---------------------------------------------------------------------------


@asynccontextmanager
async def lifespan(app: FastAPI):
    async with mcp_app.lifespan(mcp_app):
        yield


app = FastAPI(lifespan=lifespan)
app.add_middleware(AuthForwardingMiddleware)  # type: ignore[arg-type]
app.mount("/mcp", mcp_app)


# ---------------------------------------------------------------------------
# 9. Entrypoint
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8002)
