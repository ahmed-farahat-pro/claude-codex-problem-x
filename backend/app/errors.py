from typing import Any


class ApiError(Exception):
    """An error with a stable machine-readable code. Rendered as {"error": {"code", "message", ...}}."""

    def __init__(self, status: int, code: str, message: str, **extra: Any):
        super().__init__(message)
        self.status = status
        self.code = code
        self.message = message
        self.extra = extra

    def body(self) -> dict[str, Any]:
        return {"error": {"code": self.code, "message": self.message, **self.extra}}


def not_found(what: str) -> ApiError:
    # Same answer for "missing" and "belongs to someone else": never confirm another learner's ids exist.
    return ApiError(404, "not_found", f"{what} not found")
