from fastapi import HTTPException, status


class MSuiteException(HTTPException):
    def __init__(self, detail: str, status_code: int = status.HTTP_400_BAD_REQUEST):
        super().__init__(status_code=status_code, detail=detail)


class NotFoundException(MSuiteException):
    def __init__(self, detail: str = "Resource not found"):
        super().__init__(detail=detail, status_code=status.HTTP_404_NOT_FOUND)


class UnauthorizedException(MSuiteException):
    def __init__(self, detail: str = "Unauthorized"):
        super().__init__(detail=detail, status_code=status.HTTP_401_UNAUTHORIZED)


class ForbiddenException(MSuiteException):
    def __init__(self, detail: str = "Forbidden"):
        super().__init__(detail=detail, status_code=status.HTTP_403_FORBIDDEN)
