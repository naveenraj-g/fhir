from app.errors.base import ApplicationError


class PermissionDeniedError(ApplicationError):
    def __init__(self, permission: str):
        super().__init__(
            name="PermissionDeniedError",
            message=f"Missing required permission: {permission}",
            status_code=403,
            code="PERMISSION_DENIED",
            metadata={"required_permission": permission},
        )
