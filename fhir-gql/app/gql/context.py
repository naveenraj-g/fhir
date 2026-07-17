"""
Per-request context for the GraphQL endpoint.

Strawberry calls `get_context()` on *every* HTTP request to the endpoint —
including the plain `GET /graphql` that serves the GraphiQL IDE's HTML/JS
shell — and does so before it decides whether to render that IDE or execute
an operation (see `should_render_graphql_ide` in
strawberry/http/base.py). That ordering is why auth can't simply be a
router-level FastAPI dependency the way REST's
`dependencies=[Depends(get_current_user)]` is on `api_router`: gating the
whole router would 401 a browser's bare navigation to `GET /graphql`, which
cannot attach an `Authorization` header.

Instead, this module mirrors Strawberry's own IDE-vs-operation predicate:
skip auth only for the exact request shape that renders the IDE (`GET` with
no `query` parameter); authenticate everything else. Combined with
`allow_queries_via_get=False` (app/gql/schema.py) — which stops a GraphQL
operation from ever being smuggled in as `GET /graphql?query=...` to dodge
this check — every real query/mutation still goes through the identical
`get_current_user` REST uses, just called from here instead of as a
Depends().
"""

import strawberry
from fastapi import Request
from strawberry.fastapi import BaseContext

from app.auth.dependencies import get_current_user
from app.di.container import Container


class GraphQLContext(BaseContext):
    """
    Object exposed to every resolver as `info.context`.

    Must inherit from strawberry's `BaseContext` (a plain dataclass is
    rejected with `InvalidCustomContext`) — `strawberry.fastapi.GraphQLRouter`
    sets `.request` / `.background_tasks` / `.response` on it automatically
    after `get_context()` returns, so no `__init__` override is needed here.

    `request.state.user` (set on the base `.request` above) holds the
    decoded JWT payload set by `get_current_user` below — resolvers read it
    indirectly via `app.gql.permissions.require_gql_permission`.
    """


def get_container(info: strawberry.types.Info) -> Container:
    """
    Resolve the app-wide DI container for use inside a resolver, e.g.
    `get_container(info).patient.patient_service()`.

    Deliberately reads `request.app.container` (set once in app/main.py:
    `app.container = container`) rather than calling the `get_<x>_service()`
    FastAPI-dependency functions in app/di/dependencies/*.py directly.
    Those functions only resolve correctly *after* `dependency_injector`'s
    package-wide wiring has run, which happens as a side effect of importing
    app.main — reusing them here would make every resolver's correctness
    depend on that import having already happened somewhere in the process,
    which is exactly the kind of import-order fragility that broke in
    testing (calling them from a process that only imported app.gql.schema,
    never app.main, silently returned the unresolved `Depends(...)` sentinel
    instead of a service instance). `request.app.container` has no such
    dependency: by the time any request reaches a resolver, `app.main` has
    necessarily already run to construct the ASGI app being served.
    """
    return info.context.request.app.container


async def get_context(request: Request) -> GraphQLContext:
    """
    Strawberry `context_getter` — authenticates real GraphQL operations
    (reusing the exact same `get_current_user` REST uses) while letting the
    bare GraphiQL IDE shell load unauthenticated. Raises `AuthenticationError`
    (-> 401) on missing or invalid tokens, same as REST.
    """
    # Mirrors strawberry.http.base.BaseView.should_render_graphql_ide's
    # request-shape check: a bare `GET` with no `query` param is the IDE
    # asking for its own HTML/JS, not a GraphQL operation.
    is_ide_page_load = request.method == "GET" and "query" not in request.query_params
    if not is_ide_page_load:
        await get_current_user(request)
    return GraphQLContext()
