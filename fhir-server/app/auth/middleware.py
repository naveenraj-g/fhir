from fastapi import Request, HTTPException, status
from .dependencies import decode_token


# @app.middleware("http")
async def fhir_auth_middleware(request: Request, call_next):

    if request.url.path.startswith("/api/fhir/v1"):

        auth_header = request.headers.get("Authorization")

        if not auth_header or not auth_header.startswith("Bearer "):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Missing token",
            )

        token = auth_header.split(" ")[1]

        try:
            payload = decode_token(token)
            request.state.user = payload
        except Exception:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid or expired token",
            )

    response = await call_next(request)
    return response
