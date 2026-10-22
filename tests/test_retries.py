"""Offline tests for retry and connection handling in VictronVRMClient."""

import asyncio

import aiohttp
import pytest

from victron_vrm import VictronVRMClient
from victron_vrm.exceptions import (
    AuthenticationError,
    RateLimitError,
    TimeoutError as VRMTimeoutError,
)

_real_sleep = asyncio.sleep


class _FakeResponse:
    def __init__(self, status, body="{}", headers=None):
        self.status = status
        self._body = body
        self.headers = headers or {}

    async def text(self):
        return self._body


class _FakeContext:
    def __init__(self, outcome):
        self._outcome = outcome

    async def __aenter__(self):
        await _real_sleep(0)  # yield so concurrent callers can interleave
        if isinstance(self._outcome, BaseException):
            raise self._outcome
        return self._outcome

    async def __aexit__(self, *exc_info):
        return False


class _FakeSession:
    """Replays scripted outcomes for request() and post() and records calls."""

    closed = False

    def __init__(self, requests=(), logins=()):
        self._requests = list(requests)
        self._logins = list(logins)
        self.request_calls = []
        self.login_calls = 0

    def request(self, method, url, **kwargs):
        self.request_calls.append((method, url, dict(kwargs["headers"])))
        return _FakeContext(self._requests.pop(0))

    def post(self, url, **kwargs):
        self.login_calls += 1
        return _FakeContext(self._logins.pop(0))


def _login_ok(token):
    return _FakeResponse(
        200,
        f'{{"access_token": "{token}", "token_type": "Bearer", '
        f'"expires_in": 3600, "scope": "read"}}',
    )


@pytest.fixture
def sleeps(monkeypatch):
    recorded = []

    async def _fake_sleep(delay):
        recorded.append(delay)

    monkeypatch.setattr(asyncio, "sleep", _fake_sleep)
    return recorded


def _password_client(session, **kwargs):
    return VictronVRMClient(
        username="u", password="p", client_id="c", client_session=session, **kwargs
    )


@pytest.mark.asyncio
async def test_401_retry_uses_refreshed_token(sleeps):
    session = _FakeSession(
        requests=[_FakeResponse(401), _FakeResponse(200, '{"ok": true}')],
        logins=[_login_ok("first"), _login_ok("second")],
    )
    client = _password_client(session)

    assert await client._request("GET", "/users/me") == {"ok": True}
    sent = [headers["X-Authorization"] for _, _, headers in session.request_calls]
    assert sent == ["Bearer first", "Bearer second"]


@pytest.mark.asyncio
async def test_401_with_static_token_fails_without_pointless_retries(sleeps):
    session = _FakeSession(requests=[_FakeResponse(401)])
    client = VictronVRMClient(token="static", client_session=session)

    with pytest.raises(AuthenticationError) as exc:
        await client._request("GET", "/users/me")
    assert exc.value.status_code == 401
    assert len(session.request_calls) == 1


@pytest.mark.asyncio
async def test_concurrent_requests_share_one_login(sleeps):
    session = _FakeSession(
        requests=[_FakeResponse(200) for _ in range(3)],
        logins=[_login_ok("shared")],
    )
    client = _password_client(session)

    await asyncio.gather(*(client._request("GET", "/x") for _ in range(3)))
    assert session.login_calls == 1


@pytest.mark.asyncio
async def test_login_retries_transient_server_error(sleeps):
    session = _FakeSession(
        requests=[_FakeResponse(200)],
        logins=[_FakeResponse(503), _login_ok("ok")],
    )
    client = _password_client(session)

    await client._request("GET", "/x")
    assert session.login_calls == 2


@pytest.mark.asyncio
async def test_login_still_raises_authentication_error_on_bad_credentials(sleeps):
    session = _FakeSession(logins=[_FakeResponse(401, '{"error": "bad"}')])
    client = _password_client(session)

    with pytest.raises(AuthenticationError):
        await client._request("GET", "/x")
    assert session.login_calls == 1


@pytest.mark.asyncio
async def test_non_idempotent_request_not_retried_on_timeout(sleeps):
    session = _FakeSession(requests=[asyncio.TimeoutError()])
    client = VictronVRMClient(token="static", client_session=session)

    with pytest.raises(VRMTimeoutError):
        await client._request("POST", "/create", idempotent=False)
    assert len(session.request_calls) == 1


@pytest.mark.asyncio
async def test_non_idempotent_request_retried_on_failed_connect(sleeps):
    connect_error = aiohttp.ClientConnectorError(
        connection_key=None, os_error=OSError("refused")
    )
    session = _FakeSession(requests=[connect_error, _FakeResponse(200)])
    client = VictronVRMClient(token="static", client_session=session)

    await client._request("POST", "/create", idempotent=False)
    assert len(session.request_calls) == 2


@pytest.mark.asyncio
async def test_idempotent_request_retried_on_timeout(sleeps):
    session = _FakeSession(requests=[asyncio.TimeoutError(), _FakeResponse(200)])
    client = VictronVRMClient(token="static", client_session=session)

    await client._request("GET", "/x")
    assert len(session.request_calls) == 2


@pytest.mark.asyncio
async def test_backoff_is_jittered(sleeps):
    session = _FakeSession(requests=[_FakeResponse(500), _FakeResponse(200)])
    client = VictronVRMClient(token="static", client_session=session, retry_delay=2)

    await client._request("GET", "/x")
    assert len(sleeps) == 1 and 1 <= sleeps[0] <= 3


@pytest.mark.asyncio
async def test_retry_after_is_honoured(sleeps):
    session = _FakeSession(
        requests=[_FakeResponse(429, headers={"Retry-After": "7"}), _FakeResponse(200)]
    )
    client = VictronVRMClient(token="static", client_session=session)

    await client._request("GET", "/x")
    assert sleeps == [7]


@pytest.mark.asyncio
async def test_excessive_retry_after_raises_instead_of_sleeping(sleeps):
    session = _FakeSession(
        requests=[_FakeResponse(429, headers={"Retry-After": "86400"})]
    )
    client = VictronVRMClient(token="static", client_session=session)

    with pytest.raises(RateLimitError):
        await client._request("GET", "/x")
    assert sleeps == []


@pytest.mark.asyncio
async def test_zero_max_retries_still_makes_one_attempt(sleeps):
    session = _FakeSession(requests=[_FakeResponse(200, '{"ok": true}')])
    client = VictronVRMClient(token="static", client_session=session, max_retries=0)

    assert await client._request("GET", "/x") == {"ok": True}


@pytest.mark.asyncio
async def test_caller_headers_are_not_mutated(sleeps):
    session = _FakeSession(requests=[_FakeResponse(200)])
    client = VictronVRMClient(token="static", client_session=session)
    headers = {"X-Custom": "1"}

    await client._request("GET", "/x", headers=headers)
    assert headers == {"X-Custom": "1"}
