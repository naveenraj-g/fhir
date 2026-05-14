from keycloak.exceptions import KeycloakAuthenticationError
from app.errors.auth import (
    InvalidCredentialsError,
    UserAlreadyExistsError,
    SessionExpiredError,
    AccountNotFoundError,
)
from app.errors.infrastructure import InfrastructureError


def map_keycloak_error(error: Exception, context: str) -> None:
    """
    Translates Keycloak SDK errors into domain errors.
    """
    if isinstance(error, KeycloakAuthenticationError):
        # Inspect error.response_code / error.error_message if needed
        raise InvalidCredentialsError()

    # Fallback — unknown infra failure
    raise InfrastructureError(context, cause=error)
