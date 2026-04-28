from ninja.errors import HttpError

class APIError(HttpError):
    def __init__(self, status_code: int, message: str):
        super().__init__(status_code, message)

class NotFoundError(APIError):
    def __init__(self, message="Resource not found"):
        super().__init__(404, message)

class UnauthorizedError(APIError):
    def __init__(self, message="Unauthorized"):
        super().__init__(401, message)
