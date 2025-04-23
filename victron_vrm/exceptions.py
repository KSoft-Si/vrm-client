"""Exceptions for the Victron Energy VRM API client."""

from typing import Any, Dict, Optional


class VictronVRMError(Exception):
    """Base exception for Victron Energy VRM API client."""

    def __init__(
        self,
        message: str,
        status_code: Optional[int] = None,
        response_data: Optional[Dict[str, Any]] = None,
    ):
        """Initialize the exception.

        Args:
            message: Error message
            status_code: HTTP status code
            response_data: Raw response data from the API
        """
        self.message = message
        self.status_code = status_code
        self.response_data = response_data or {}
        super().__init__(self.message)


class AuthenticationError(VictronVRMError):
    """Raised when authentication fails."""


class AuthorizationError(VictronVRMError):
    """Raised when the user is not authorized to access a resource."""


class NotFoundError(VictronVRMError):
    """Raised when a resource is not found."""


class RateLimitError(VictronVRMError):
    """Raised when the API rate limit is exceeded."""


class ServerError(VictronVRMError):
    """Raised when the server returns an error."""


class ClientError(VictronVRMError):
    """Raised when the client makes an invalid request."""


class ConnectionError(VictronVRMError):
    """Raised when there is a connection error."""


class TimeoutError(VictronVRMError):
    """Raised when a request times out."""


class ParseError(VictronVRMError):
    """Raised when the response cannot be parsed."""