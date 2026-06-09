from typing import Any, Optional
from pydantic import BaseModel


class ErrorDetail(BaseModel):
    code: str
    message: str


class StandardResponse(BaseModel):
    success: bool
    message: Optional[str] = None
    data: Optional[Any] = None
    error: Optional[ErrorDetail] = None


def success_response(data: Any = None, message: str = "Success") -> StandardResponse:
    return StandardResponse(success=True, message=message, data=data)


def error_response(code: str, message: str) -> StandardResponse:
    return StandardResponse(
        success=False,
        message=message,
        error=ErrorDetail(code=code, message=message),
    )
