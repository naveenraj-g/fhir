"""Per-request context, carried in a ContextVar rather than threaded through
function signatures.

Why a ContextVar: a repository method has no access to the `Request` object and
never will. `app.core.logging`'s formatters read this directly, so any log line
emitted anywhere below the router — service, repository, serializer —
automatically carries the request's correlation id with zero plumbing at the
call site.

Each asyncio task gets its own copy, so concurrent requests never bleed into
each other. Set by app.middleware.request_context.request_context_middleware.

Note for anyone porting more of fhir-server across: that project also carries
`actor_user_id`/`actor_org_id` here, bound from a verified JWT. This service
does not authenticate (see the plan's Context section), so there is no actor to
bind and those vars are deliberately absent. The `org_id`/`user_id` a request
carries are ordinary *data* columns on the row being written, not the identity
of the caller — logging them under an `actor_` key would be a lie.
"""

from contextvars import ContextVar

request_id_ctx_var: ContextVar[str | None] = ContextVar(
    "request_id",
    default=None,
)


def get_log_context() -> dict[str, str]:
    """Snapshot of the non-None context fields, for injection into a log
    record. Used by both the JSON and console formatters."""
    request_id = request_id_ctx_var.get()
    return {"request_id": request_id} if request_id else {}
