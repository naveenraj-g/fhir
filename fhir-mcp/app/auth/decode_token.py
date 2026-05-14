from jwt import PyJWKClient
import jwt
from app.core.config import settings


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
