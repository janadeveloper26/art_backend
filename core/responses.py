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


def success_response(data: Any = None, message: str = "Success") -> dict:
    return StandardResponse(success=True, message=message, data=data).model_dump()


def error_response(code: str, message: str) -> dict:
    return StandardResponse(
        success=False,
        message=message,
        error=ErrorDetail(code=code, message=message),
    ).model_dump()
