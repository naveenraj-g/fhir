"""
GraphQL adapter for RBAC.

REST enforces permissions per-route via `require_permission()`, a FastAPI
Depends() factory (app/auth/rbac.py). GraphQL fields are not routes, so there
is no per-field Depends() equivalent — each resolver instead calls
`require_gql_permission(info, resource, action)` explicitly as its first
line, exactly mirroring the `resource:action` check REST performs. Both
paths funnel through `check_permission()` so there is exactly one place the
permission rule itself is defined.
"""

import strawberry

from app.auth.models import AuthUser
from app.auth.rbac import check_permission


def require_gql_permission(info: strawberry.types.Info, resource: str, action: str) -> AuthUser:
    """
    Check that the caller has `resource:action` and return their AuthUser.

    Reads the JWT payload from `request.state.user`, populated by
    `get_current_user` before the GraphQL router ever runs (see the
    `dependencies=[Depends(get_current_user)]` on the `/graphql` mount in
    app/main.py). Raises HTTPException(403) on failure — the resolver's
    `@translate_errors` decorator (app.gql.errors) converts that into a
    GraphQLError so the client sees the same 403 semantics REST would give.

    Args:
        info:     Strawberry's resolver info object — carries `info.context`.
        resource: Permission resource name, e.g. "patient".
        action:   Permission action, e.g. "read" | "create" | "update" | "delete".

    Returns:
        A typed AuthUser for the authenticated caller.
    """
    request = info.context.request
    user: dict = request.state.user
    return check_permission(user, resource, action)
