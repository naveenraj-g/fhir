from app.errors.base import ApplicationError


class AuthenticationError(ApplicationError):
    def __init__(self, message="Authentication required"):
        super().__init__(
            name="AuthenticationError",
            message=message,
            status_code=401,
            code="AUTHENTICATION_ERROR",
        )


class InvalidTokenError(ApplicationError):
    def __init__(self, message="Invalid or malformed token"):
        super().__init__(
            name="InvalidTokenError",
            message=message,
            status_code=401,
            code="INVALID_TOKEN",
        )
