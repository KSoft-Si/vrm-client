"""Victron Energy VRM API client."""

import asyncio
import logging
from datetime import datetime
from typing import Any, Dict, Optional, Literal

import httpx
from pydantic import ValidationError

from .consts import AUTH_URL, USER_ME_URL, FILTERED_SORTED_ATTRIBUTES_URL
from .exceptions import (
    AuthenticationError,
    AuthorizationError,
    ClientError,
    ConnectionError,
    NotFoundError,
    ParseError,
    RateLimitError,
    ServerError,
    TimeoutError,
    VictronVRMError,
)
from .models import VRMAttributes, AuthToken
from .modules import UsersModule, InstallationsModule

_LOGGER = logging.getLogger(__name__)


class VictronVRMClient:
    """Client for the Victron Energy VRM API."""

    USER_AGENT = "VictronVRMClient/1.0 Contact/user-first-otherwise/oss@ksoft.tech"

    def __init__(
        self,
        username: Optional[str] = None,
        password: Optional[str] = None,
        client_id: Optional[str] = None,
        token: Optional[str] = None,
        token_type: Literal["Bearer", "Token"] = "Bearer",
        client_session: Optional[httpx.AsyncClient] = None,
        request_timeout: int = 10,
        max_retries: int = 3,
        retry_delay: int = 1,
    ) -> None:
        """Initialize the Victron VRM API client.

        Args:
            username: VRM Portal username (required if token not provided)
            password: VRM Portal password (required if token not provided)
            client_id: VRM API client ID (required if token not provided)
            token: Authentication token (required if username/password not provided)
            token_type: Token type, either 'Bearer' or 'Token' (default: 'Bearer')
            client_session: Optional httpx AsyncClient session
            request_timeout: Request timeout in seconds
            max_retries: Maximum number of retries for failed requests
            retry_delay: Delay between retries in seconds
        """
        if not ((username and password and client_id) or token):
            raise ValueError(
                "Either username, password, and client_id OR token must be provided"
            )

        if token_type not in ["Bearer", "Token"]:
            raise ValueError("token_type must be either 'Bearer' or 'Token'")

        self._username = username
        self._password = password
        self._client_id = client_id
        self._token = token
        self._token_type = token_type
        self._client_session = client_session
        self._request_timeout = request_timeout
        self._max_retries = max_retries
        self._retry_delay = retry_delay
        self._auth_token: Optional[AuthToken] = None
        self._close_session = False
        self._user_id: Optional[int] = None
        self._filtered_sorted_attributes: Optional[VRMAttributes] = None

    async def __aenter__(self) -> "VictronVRMClient":
        """Async enter."""
        if self._client_session is None:
            self._client_session = httpx.AsyncClient()
            self._close_session = True
        return self

    async def __aexit__(self, *exc_info) -> None:
        """Async exit."""
        if self._close_session and self._client_session:
            try:
                if not self._client_session.is_closed:
                    await self._client_session.aclose()
            except RuntimeError:
                # Ignore RuntimeError if the session is already closed
                _LOGGER.debug("Client session or asyncio loop already closed")
            self._client_session = None
            self._close_session = False

    async def _get_auth_token(self) -> AuthToken:
        """Get authentication token.

        Returns:
            AuthToken: Authentication token

        Raises:
            AuthenticationError: If authentication fails
        """
        if self._auth_token and not self._auth_token.is_expired:
            return self._auth_token

        if not self._client_session:
            self._client_session = httpx.AsyncClient()
            self._close_session = True

        # If a token was provided directly, create an AuthToken from it
        if self._token:
            # Create a simple AuthToken with a long expiration time
            self._auth_token = AuthToken(
                access_token=self._token,
                token_type=self._token_type,
                expires_in=(
                    3600 * 24 * 30
                    if self._token_type == "Bearer"
                    else 3600 * 24 * 365 * 999
                ),  # 30 days
                scope="read",
                created_at=datetime.now(),
            )
            return self._auth_token

        # Otherwise, authenticate with username and password
        auth_data = {
            "username": self._username,
            "password": self._password,
            "grant_type": "password",
            "client_id": self._client_id,
        }

        try:
            response = await self._client_session.post(
                AUTH_URL,
                data=auth_data,
                timeout=self._request_timeout,
                headers={
                    "User-Agent": self.USER_AGENT,
                },
            )
            response.raise_for_status()
            token_data = response.json()
            self._auth_token = AuthToken(**token_data)
            return self._auth_token
        except httpx.HTTPStatusError as err:
            status_code = err.response.status_code
            try:
                response_data = err.response.json()
            except ValueError:
                response_data = {"error": err.response.text}

            error_message = response_data.get("error", "Authentication failed")
            raise AuthenticationError(
                f"Authentication failed: {error_message}",
                status_code=status_code,
                response_data=response_data,
            ) from err
        except httpx.RequestError as err:
            raise ConnectionError(f"Connection error: {err}") from err
        except ValidationError as err:
            raise ParseError(f"Failed to parse authentication response: {err}") from err

    async def _get_user_id(self) -> int:
        """Get the user ID from the /users/me endpoint.

        Returns:
            int: User ID

        Raises:
            AuthenticationError: If authentication fails
            NotFoundError: If the user is not found
        """
        if self._user_id is not None:
            return self._user_id

        response = await self._request("GET", USER_ME_URL)
        user_data = response.get("user", {})
        self._user_id = user_data.get("id")

        if not self._user_id:
            raise NotFoundError("User ID not found in response")

        return self._user_id

    async def _request(
        self,
        method: str,
        url: str,
        params: Optional[Dict[str, Any]] = None,
        data: Optional[Dict[str, Any]] = None,
        json_data: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None,
        auth_required: bool = True,
        skip_success_check: bool = False,
    ) -> Dict[str, Any]:
        """Make an API request.

        Args:
            method: HTTP method
            url: Request URL
            params: Query parameters
            data: Form data
            json_data: JSON data
            headers: Request headers
            auth_required: Whether authentication is required

        Returns:
            Dict[str, Any]: Response data

        Raises:
            VictronVRMError: If the request fails
        """
        if not self._client_session:
            self._client_session = httpx.AsyncClient()
            self._close_session = True

        if not headers:
            headers = {}

        if auth_required:
            token = await self._get_auth_token()
            headers["X-Authorization"] = token.authorization_header
        headers["User-Agent"] = self.USER_AGENT

        request_headers = headers or {}
        request_params = params or {}
        request_data = data or {}
        request_json = json_data or {}

        for attempt in range(self._max_retries):
            try:
                response = await self._client_session.request(
                    method,
                    url,
                    params=request_params,
                    data=request_data or None,
                    json=request_json or None,
                    headers=request_headers,
                    timeout=self._request_timeout,
                )
                response.raise_for_status()
                response_data = response.json()

                # Check the success key in the response
                if (
                    "success" in response_data
                    and not response_data["success"]
                    and not skip_success_check
                ):
                    errors = response_data.get("errors", "Unknown error")
                    error_code = response_data.get("error_code")
                    error_message = f"API error: {errors}"
                    if error_code:
                        error_message += f" (code: {error_code})"

                    raise VictronVRMError(
                        error_message,
                        status_code=response.status_code,
                        response_data=response_data,
                    )

                return response_data
            except httpx.HTTPStatusError as err:
                status_code = err.response.status_code
                try:
                    response_data = err.response.json()
                    # Check for success key and error details in error responses
                    if "success" in response_data and not response_data["success"]:
                        errors = response_data.get("errors", "Unknown error")
                        error_code = response_data.get("error_code")
                        error_message = f"API error: {errors}"
                        if error_code:
                            error_message += f" (code: {error_code})"
                    else:
                        error_message = response_data.get(
                            "error", f"HTTP error {status_code}"
                        )
                except ValueError:
                    response_data = {"error": err.response.text}
                    error_message = f"HTTP error {status_code}: {err.response.text}"

                # Handle specific error codes
                if status_code == 401:
                    # Token might be expired, try to refresh and retry
                    if auth_required and attempt < self._max_retries - 1:
                        self._auth_token = None
                        await asyncio.sleep(self._retry_delay)
                        continue
                    raise AuthenticationError(
                        f"Authentication failed: {error_message}",
                        status_code=status_code,
                        response_data=response_data,
                    ) from err
                elif status_code == 403:
                    raise AuthorizationError(
                        f"Not authorized: {error_message}",
                        status_code=status_code,
                        response_data=response_data,
                    ) from err
                elif status_code == 404:
                    raise NotFoundError(
                        f"Resource not found: {error_message}",
                        status_code=status_code,
                        response_data=response_data,
                    ) from err
                elif status_code == 429:
                    if attempt < self._max_retries - 1:
                        retry_after = int(
                            err.response.headers.get("Retry-After", self._retry_delay)
                        )
                        await asyncio.sleep(retry_after)
                        continue
                    raise RateLimitError(
                        f"Rate limit exceeded: {error_message}",
                        status_code=status_code,
                        response_data=response_data,
                    ) from err
                elif 400 <= status_code < 500:
                    raise ClientError(
                        f"Client error: {error_message}",
                        status_code=status_code,
                        response_data=response_data,
                    ) from err
                elif 500 <= status_code < 600:
                    if attempt < self._max_retries - 1:
                        await asyncio.sleep(self._retry_delay * (attempt + 1))
                        continue
                    raise ServerError(
                        f"Server error: {error_message}",
                        status_code=status_code,
                        response_data=response_data,
                    ) from err
                else:
                    raise VictronVRMError(
                        f"HTTP error {status_code}: {error_message}",
                        status_code=status_code,
                        response_data=response_data,
                    ) from err
            except httpx.TimeoutException as err:
                if attempt < self._max_retries - 1:
                    await asyncio.sleep(self._retry_delay * (attempt + 1))
                    continue
                raise TimeoutError(f"Request timed out: {err}") from err
            except httpx.RequestError as err:
                if attempt < self._max_retries - 1:
                    await asyncio.sleep(self._retry_delay * (attempt + 1))
                    continue
                raise ConnectionError(f"Connection error: {err}") from err
            except Exception as err:
                raise VictronVRMError(f"Unexpected error: {err}") from err

        # This should never be reached due to the exception handling above
        raise VictronVRMError("Maximum retries exceeded")

    async def get_filtered_sorted_attributes(self) -> VRMAttributes:
        """Get filtered and sorted attributes.

        Returns:
            VRMAttributes: Filtered and sorted attributes
        """
        if self._filtered_sorted_attributes is not None:
            return self._filtered_sorted_attributes
        response = await self._request("GET", FILTERED_SORTED_ATTRIBUTES_URL)
        self._filtered_sorted_attributes = VRMAttributes(response)
        return self._filtered_sorted_attributes

    @property
    def users(self) -> "UsersModule":
        """Get the UsersModule."""
        return UsersModule(self)

    @property
    def installations(self) -> "InstallationsModule":
        """Get the InstallationsModule."""
        return InstallationsModule(self)
