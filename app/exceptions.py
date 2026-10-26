"""Business/domain failures independent of HTTP and FastAPI."""

class AppError(Exception):
    """Base class for anticipated domain failures."""


class ResourceNotFoundError(AppError):
    def __init__(self, resource: str, resource_id: str) -> None:
        self.resource = resource
        self.resource_id = resource_id
        super().__init__(f"{resource} '{resource_id}' not found")


class ServiceUnavailableError(AppError):
    def __init__(self, message: str = "Service is not ready") -> None:
        super().__init__(message)
