import uuid

from fastapi import Request

from app.core.request_context import request_id_ctx_var

# Header carrying an upstream-assigned correlation id. The AI agent (or
# whatever calls this service) can set it so a trace started upstream spans
# both systems in the log stream.
REQUEST_ID_HEADER = "X-Request-ID"


async def request_context_middleware(request: Request, call_next):
    """Establishes the per-request logging context and echoes the correlation
    id back to the caller.

    Inherits X-Request-ID when the caller supplies one and only mints a fresh
    uuid4 when it doesn't — so a trace started upstream isn't broken by this
    service silently generating its own id.
    """
    request_id = request.headers.get(REQUEST_ID_HEADER) or str(uuid.uuid4())

    request_id_ctx_var.set(request_id)

    # Also attach to request.state, for handlers that have the Request in hand.
    request.state.request_id = request_id

    response = await call_next(request)

    response.headers[REQUEST_ID_HEADER] = request_id

    return response
