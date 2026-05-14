from fastapi import HTTPException, status, Request
from jwt import PyJWKClient
import jwt
from app.core.config import settings
from app.errors.auth import AuthenticationError

jwks_client = PyJWKClient(settings.IAM_JWKS_URL)


def decode_token(token: str):
    signing_key = jwks_client.get_signing_key_from_jwt(token)

    return jwt.decode(
        token,
        signing_key.key,
        audience=settings.IAM_ISSUER,
        issuer=settings.IAM_ISSUER,
        algorithms=["EdDSA", "RS256"],
        options={"verify_aud": True},
    )


async def get_current_user(request: Request):
    auth_header = request.headers.get("Authorization")

    if not auth_header or not auth_header.startswith("Bearer "):
        raise AuthenticationError("Missing authentication token")

    token = auth_header.split(" ")[1]

    try:
        payload = decode_token(token)
        request.state.user = payload
        request.state.token = token
        return payload

    except jwt.ExpiredSignatureError:
        raise AuthenticationError("Token expired")
    except jwt.InvalidTokenError:
        raise AuthenticationError("Invalid token")
    except Exception:
        raise AuthenticationError("Invalid or expired token")


# Permission
#   Resource = Patient
#   action = read
async def check_permission(user: str, resource: str, action: str):
    permissions = user.get("permissions", [])

    if f"{resource}:{action}" not in permissions:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Permission denied",
        )


def require_permission(resource: str, action: str):
    async def dependency(request: Request):
        user = request.state.user
        await check_permission(user, resource, action)

    dependency.required_permission = f"{resource}:{action}"
    return dependency
