from keycloak import KeycloakOpenID
from app.core.config import settings
from app.core.logging import get_logger

logger = get_logger(__name__)


def _extract_server_url(discovery_url: str) -> str:
    """Extract the Keycloak server base URL from the OIDC discovery URL.

    Example:
        http://localhost:8080/realms/noname/.well-known/openid-configuration
        → http://localhost:8080/
    """
    # Find '/realms/' and take everything before it
    idx = discovery_url.find("/realms/")
    if idx == -1:
        raise ValueError(
            f"Cannot extract server URL from discovery URL: {discovery_url}. "
            "Expected format: http://<host>/realms/<realm>/.well-known/openid-configuration"
        )
    return discovery_url[:idx] + "/"


keycloak_server_url = _extract_server_url(settings.KEYCLOAK_DISCOVERY_URL)

keycloak_openid = KeycloakOpenID(
    server_url=keycloak_server_url,
    client_id=settings.KEYCLOAK_CLIENT_ID,
    realm_name=settings.KEYCLOAK_REALM_NAME,
    client_secret_key=settings.KEYCLOAK_CLIENT_SECRET,
)


async def get_keycloak_public_key() -> str:
    """Fetch and format the Keycloak realm's RSA public key for JWT verification."""
    raw_key = keycloak_openid.public_key()
    return "-----BEGIN PUBLIC KEY-----\n" f"{raw_key}\n" "-----END PUBLIC KEY-----"


def decode_token(token: str, public_key: str) -> dict:
    """Decode and validate a Keycloak access token.

    Returns the decoded token payload on success.
    Raises keycloak.exceptions.KeycloakAuthenticationError on failure.
    """
    options = {
        "verify_signature": True,
        "verify_aud": False,  # Audience verification handled by Keycloak
        "verify_exp": True,
    }
    return keycloak_openid.decode_token(token, key=public_key, options=options)
