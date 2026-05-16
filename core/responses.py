from typing import Any, Optional
from pydantic import BaseModel

class ErrorDetail(BaseModel):
    code: str
    message: str

class StandardResponse(BaseModel):
    success: bool
    data: Optional[Any] = None
    error: Optional[ErrorDetail] = None

def success_response(data: Any = None) -> StandardResponse:
    return StandardResponse(success=True, data=data)

def error_response(code: str, message: str) -> StandardResponse:
    return StandardResponse(
        success=False, 
        error=ErrorDetail(code=code, message=message)
    )
