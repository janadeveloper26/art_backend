from typing import Any, Optional
from pydantic import BaseModel

class StandardResponse(BaseModel):
    status: str
    message: Optional[str] = None
    data: Optional[Any] = None

def success_response(data: Any = None, message: str = "Success") -> StandardResponse:
    return StandardResponse(status="success", message=message, data=data)

def error_response(message: str = "Error", data: Any = None) -> StandardResponse:
    return StandardResponse(status="error", message=message, data=data)
