# Copilot instructions for vrm-client

## Architecture overview
- Core HTTP client is `VictronVRMClient` in [victron_vrm/client.py](../victron_vrm/client.py). It owns auth/token refresh, retry/backoff, error mapping, and builds absolute URLs from [victron_vrm/consts.py](../victron_vrm/consts.py).
- API surface is modular: each module in [victron_vrm/modules](../victron_vrm/modules) subclasses `BaseClientModule` and calls `client._request(...)` (see [victron_vrm/modules/_base.py](../victron_vrm/modules/_base.py)). Keep new endpoints in a module, not in the client directly.
- Data parsing uses Pydantic models in [victron_vrm/models](../victron_vrm/models). `BaseModel` converts empty strings to `None` and serializes `datetime` to ISO (see [victron_vrm/models/base.py](../victron_vrm/models/base.py)). Follow existing `Field(..., alias=...)` patterns as in [victron_vrm/models/site.py](../victron_vrm/models/site.py).
- MQTT support is a thin wrapper around `victron-mqtt` in [victron_vrm/mqtt.py](../victron_vrm/mqtt.py); `VictronVRMClient.get_mqtt_client_for_installation()` wires auth + installation details (see [victron_vrm/client.py](../victron_vrm/client.py)).

## Request/response conventions (project-specific)
- All API calls go through `VictronVRMClient._request()` which:
  - Adds `X-Authorization` header using `AuthToken.authorization_header` and `User-Agent`.
  - Retries on 401/429/5xx/timeout with backoff (see [victron_vrm/client.py](../victron_vrm/client.py)).
  - Treats `{ "success": false }` payloads as errors unless `skip_success_check=True`.
- `InstallationsModule.stats()` normalizes API `False` values to `None` in `records`/`totals` and optionally builds `ForecastAggregations` (see [victron_vrm/modules/installations.py](../victron_vrm/modules/installations.py)).
- This library backs the Home Assistant “Victron Remote Monitoring” integration, so prefer conservative changes: preserve error mapping behavior in `VictronVRMClient._request()` and avoid breaking public APIs without tests.

## Stability expectations for Home Assistant usage
- Keep exception mapping stable in [victron_vrm/exceptions.py](../victron_vrm/exceptions.py) and the status-code handling in [victron_vrm/client.py](../victron_vrm/client.py); HA relies on those types for error handling.
- Prefer additive changes (new module methods/models) over modifying existing response shapes; update or add tests in [tests/test_client.py](../tests/test_client.py) when behavior changes.
- Be mindful of rate limits: tests and demo scripts use the demo token and can 429, so avoid extra API calls in hot paths (see [tests/README.md](../tests/README.md)).
- When handling inconsistent API payloads, normalize in module methods (like `stats()` in [victron_vrm/modules/installations.py](../victron_vrm/modules/installations.py)) rather than altering `_request()`.

## Developer workflows
- Install dev/test deps: `pip install -e ".[test,dev]"` (or `uv pip install -e ".[test,dev]"`). See [README.md](../README.md).
- Run demo against VRM demo account: `python examples/demo.py` (uses `/auth/loginAsDemo`).
- Run tests: `pytest` or `pytest --cov=victron_vrm` (tests use demo token, so no credentials required). See [tests/README.md](../tests/README.md).

## Integration points & dependencies
- HTTP layer uses `aiohttp` (async) and Pydantic v2 models. MQTT uses `victron-mqtt` (Hub-based client).
- External API endpoints are in [victron_vrm/consts.py](../victron_vrm/consts.py); add new endpoints there when expanding modules.

## Examples to follow
- New module method pattern: check [victron_vrm/modules/users.py](../victron_vrm/modules/users.py) for `_request` usage and returning typed models.
- Error handling expectations: map status codes to custom exceptions in [victron_vrm/exceptions.py](../victron_vrm/exceptions.py), and let `_request` raise them.
