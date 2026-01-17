"""Victron Energy VRM API client."""

import asyncio
import json
import logging
from datetime import datetime
from email.utils import parsedate_to_datetime
from typing import Any, Dict, Optional, Literal

import aiohttp
from pydantic import ValidationError

from victron_vrm.mqtt import VRMMQTTClient

from .consts import AUTH_URL, USER_ME_URL, FILTERED_SORTED_ATTRIBUTES_URL, BASE_URL
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
__all__ = ["VictronVRMClient"]


def is_jwt(token: str) -> bool:
    """Return True if token looks like a JWT."""
    return token.count(".") == 2


class VictronVRMClient:
    """Client for the Victron Energy VRM API."""

    USER_AGENT = "VictronVRMClient/1.0 Contact/user-first-otherwise/oss@ksoft.tech"

    def __init__(
        self,
        username: Optional[str] = None,
        password: Optional[str] = None,
        client_id: Optional[str] = None,
        token: Optional[str] = None,
        token_type: Optional[Literal["Bearer", "Token"]] = None,
        client_session: Optional[aiohttp.ClientSession] = None,
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
            client_session: Optional aiohttp ClientSession
            request_timeout: Request timeout in seconds
            max_retries: Maximum number of retries for failed requests
            retry_delay: Delay between retries in seconds
        """
        if not ((username and password and client_id) or token):
            raise ValueError(
                "Either username, password, and client_id OR token must be provided"
            )

        if token is not None and token_type is None:
            token_type = "Bearer" if is_jwt(token or "") else "Token"
        elif token_type is None:
            token_type = "Bearer"

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

    def _build_url(self, url: str) -> str:
        """Build an absolute URL from a relative API path or return as-is if absolute."""
        if url.startswith("http://") or url.startswith("https://"):
            return url
        return f"{BASE_URL.rstrip('/')}/{url.lstrip('/')}"

    async def __aenter__(self) -> "VictronVRMClient":
        """Async enter."""
        if self._client_session is None:
            self._client_session = aiohttp.ClientSession(
                timeout=aiohttp.ClientTimeout(total=self._request_timeout)
            )
            self._close_session = True
        return self

    async def __aexit__(self, *exc_info) -> None:
        """Async exit."""
        await self.close()

    async def close(self) -> None:
        """Close the underlying HTTP session if we own it."""
        if self._close_session and self._client_session:
            try:
                if not self._client_session.closed:
                    await self._client_session.close()
            except RuntimeError:
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
            self._client_session = aiohttp.ClientSession(
                timeout=aiohttp.ClientTimeout(total=self._request_timeout)
            )
            self._close_session = True

        # If a token was provided directly, create an AuthToken from it
        if self._token:
            self._auth_token = AuthToken(
                access_token=self._token,
                token_type=self._token_type,
                expires_in=(
                    3600 * 24 * 30
                    if self._token_type == "Bearer"
                    else 3600 * 24 * 365 * 999
                ),
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
            async with self._client_session.post(
                self._build_url(AUTH_URL),
                data=auth_data,
                headers={
                    "User-Agent": self.USER_AGENT,
                },
            ) as response:
                text = await response.text()
                status_code = response.status
                # Try to parse JSON if present
                try:
                    payload = json.loads(text) if text else {}
                except json.JSONDecodeError:
                    payload = {"raw": text}

                if 200 <= status_code < 300:
                    if not isinstance(payload, dict):
                        raise ParseError(
                            f"Expected JSON object for auth response, got: {type(payload)}"
                        )
                    self._auth_token = AuthToken(**payload)
                    return self._auth_token
                # Non-2xx -> build error
                error_message = (
                    payload.get("error")
                    if isinstance(payload, dict)
                    else (text or "Authentication failed")
                )
                raise AuthenticationError(
                    f"Authentication failed: {error_message}",
                    status_code=status_code,
                    response_data=(
                        payload if isinstance(payload, dict) else {"raw": text}
                    ),
                )
        except aiohttp.ClientError as err:
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
            url: Request URL (relative to BASE_URL or absolute)
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
            self._client_session = aiohttp.ClientSession(
                timeout=aiohttp.ClientTimeout(total=self._request_timeout)
            )
            self._close_session = True

        if not headers:
            headers = {}

        if params:
            # Remove None values from params
            params = {k: v for k, v in params.items() if v is not None}

        if auth_required:
            token = await self._get_auth_token()
            headers["X-Authorization"] = token.authorization_header
        headers["User-Agent"] = self.USER_AGENT

        request_headers = headers or {}
        request_params = params or {}
        request_data = data or {}
        request_json = json_data or {}

        full_url = self._build_url(url)

        for attempt in range(self._max_retries):
            try:
                async with self._client_session.request(
                    method,
                    full_url,
                    params=request_params,
                    data=request_data or None,
                    json=request_json or None,
                    headers=request_headers,
                ) as response:
                    status_code = response.status
                    text = await response.text()
                    # Try JSON parse either way
                    try:
                        response_data = json.loads(text) if text else {}
                    except json.JSONDecodeError:
                        response_data = {"raw": text}

                    # 2xx path
                    if 200 <= status_code < 300:
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
                                status_code=status_code,
                                response_data=response_data,
                            )
                        return response_data

                    # Non-2xx path: map errors by status code
                    # Prefer structured error from payload if available
                    if (
                        isinstance(response_data, dict)
                        and "success" in response_data
                        and not response_data["success"]
                    ):
                        errors = response_data.get("errors", "Unknown error")
                        error_code = response_data.get("error_code")
                        error_message = f"API error: {errors}"
                        if error_code:
                            error_message += f" (code: {error_code})"
                    else:
                        error_message = (
                            response_data.get("error")
                            if isinstance(response_data, dict)
                            else (text or f"HTTP error {status_code}")
                        )

                    if status_code == 401:
                        if auth_required and attempt < self._max_retries - 1:
                            self._auth_token = None
                            await asyncio.sleep(self._retry_delay)
                            continue
                        raise AuthenticationError(
                            f"Authentication failed: {error_message}",
                            status_code=status_code,
                            response_data=(
                                response_data
                                if isinstance(response_data, dict)
                                else {"raw": text}
                            ),
                        )
                    elif status_code == 403:
                        raise AuthorizationError(
                            f"Not authorized: {error_message}",
                            status_code=status_code,
                            response_data=(
                                response_data
                                if isinstance(response_data, dict)
                                else {"raw": text}
                            ),
                        )
                    elif status_code == 404:
                        raise NotFoundError(
                            f"Resource not found: {error_message}",
                            status_code=status_code,
                            response_data=(
                                response_data
                                if isinstance(response_data, dict)
                                else {"raw": text}
                            ),
                        )
                    elif status_code == 429:
                        if attempt < self._max_retries - 1:
                            # retry-after header or backoff
                            retry_after_hdr = response.headers.get("Retry-After")
                            retry_after: int
                            if retry_after_hdr and retry_after_hdr.isdigit():
                                retry_after = int(retry_after_hdr)
                            else:
                                try:
                                    dt = (
                                        parsedate_to_datetime(retry_after_hdr)
                                        if retry_after_hdr
                                        else None
                                    )
                                except (TypeError, ValueError):
                                    dt = None
                                if dt is not None:
                                    now = (
                                        datetime.now(tz=dt.tzinfo)
                                        if dt.tzinfo
                                        else datetime.utcnow()
                                    )
                                    delta = (dt - now).total_seconds()
                                    retry_after = max(0, int(delta))
                                else:
                                    retry_after = self._retry_delay
                            _LOGGER.debug(
                                "429 received, retrying after %s seconds (attempt %s)",
                                retry_after,
                                attempt + 1,
                            )
                            await asyncio.sleep(retry_after)
                            continue
                        raise RateLimitError(
                            f"Rate limit exceeded: {error_message}",
                            status_code=status_code,
                            response_data=(
                                response_data
                                if isinstance(response_data, dict)
                                else {"raw": text}
                            ),
                        )
                    elif 400 <= status_code < 500:
                        raise ClientError(
                            f"Client error: {error_message}",
                            status_code=status_code,
                            response_data=(
                                response_data
                                if isinstance(response_data, dict)
                                else {"raw": text}
                            ),
                        )
                    elif 500 <= status_code < 600:
                        if attempt < self._max_retries - 1:
                            await asyncio.sleep(self._retry_delay * (attempt + 1))
                            continue
                        raise ServerError(
                            f"Server error: {error_message}",
                            status_code=status_code,
                            response_data=(
                                response_data
                                if isinstance(response_data, dict)
                                else {"raw": text}
                            ),
                        )
                    else:
                        raise VictronVRMError(
                            f"HTTP error {status_code}: {error_message}",
                            status_code=status_code,
                            response_data=(
                                response_data
                                if isinstance(response_data, dict)
                                else {"raw": text}
                            ),
                        )
            except (asyncio.TimeoutError, aiohttp.ServerTimeoutError) as err:
                if attempt < self._max_retries - 1:
                    _LOGGER.debug(
                        "Timeout on %s %s, retrying (attempt %s)",
                        method,
                        full_url,
                        attempt + 1,
                    )
                    await asyncio.sleep(self._retry_delay * (attempt + 1))
                    continue
                raise TimeoutError(f"Request timed out: {err}") from err
            except aiohttp.ClientError as err:
                if attempt < self._max_retries - 1:
                    _LOGGER.debug(
                        "ClientError on %s %s, retrying (attempt %s): %s",
                        method,
                        full_url,
                        attempt + 1,
                        err,
                    )
                    await asyncio.sleep(self._retry_delay * (attempt + 1))
                    continue
                raise ConnectionError(f"Connection error: {err}") from err
            except VictronVRMError:
                # Bubble up already-mapped API errors without wrapping
                raise
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

    async def get_mqtt_client_for_installation(
        self,
        installation_id: int,
    ) -> "VRMMQTTClient":
        """Get an MQTT client for the specified installation.

        Args:
            installation_id: Installation ID

        Returns:
            VRMMQTTClient: MQTT client for the installation

        Raises:
            NotFoundError: If no installation with the given ID is found for the user.
            ClientError: If the installation does not have an MQTT hostname configured.
        """
        token, user_details, installations = await asyncio.gather(
            self._get_auth_token(),
            self.users.get_me(),
            self.users.list_sites(extended=True, site_id=installation_id),
        )
        mqtt_username = user_details.email
        mqtt_password = token.authorization_header

        if len(installations) == 0:
            raise NotFoundError(
                f"Installation with ID {installation_id} not found for user.",
            )
        installation = installations[0]

        # Check if MQTT hostname is available
        if not installation.mqtt_hostname:
            raise ClientError(
                f"Installation with ID {installation_id} does not have MQTT hostname configured.",
            )

        return VRMMQTTClient(
            host=installation.mqtt_hostname,
            username=mqtt_username,
            password=mqtt_password,
            vrm_id=installation.identifier,
        )
