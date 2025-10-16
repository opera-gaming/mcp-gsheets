"""Custom exceptions for mcp-gsheets application."""

from fastapi import HTTPException, status


class MCPGSheetsException(Exception):
    """Base exception for all mcp-gsheets errors."""
    pass


class AuthenticationError(MCPGSheetsException):
    """Raised when authentication fails."""

    def __init__(self, message: str = "Authentication failed"):
        self.message = message
        super().__init__(self.message)

    def to_http_exception(self) -> HTTPException:
        return HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=self.message
        )


class TokenExpiredError(AuthenticationError):
    """Raised when JWT token has expired."""

    def __init__(self):
        super().__init__("Token has expired")


class InvalidTokenError(AuthenticationError):
    """Raised when JWT token is invalid."""

    def __init__(self, message: str = "Invalid token"):
        super().__init__(message)


class CredentialsNotFoundError(AuthenticationError):
    """Raised when user credentials are not found."""

    def __init__(self):
        super().__init__("User credentials not found")


class DatabaseError(MCPGSheetsException):
    """Raised when database operations fail."""

    def __init__(self, message: str = "Database operation failed"):
        self.message = message
        super().__init__(self.message)

    def to_http_exception(self) -> HTTPException:
        return HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Service temporarily unavailable"
        )
