# Victron Energy VRM API Client

An async Python client for the Victron Energy VRM API. This client is designed to be modular, easy to use, and compatible with Home Assistant.

## Features

- Fully async API client using `httpx`
- Modular design organized by API categories
- Comprehensive error handling with custom exceptions
- Automatic token management and refresh
- Retry mechanism for failed requests
- Type hints and Pydantic models for data validation
- Compatible with Home Assistant

## Installation

```bash
pip install victron-vrm
```

## Usage

### Demo Script

The package includes a demo script that uses the Victron Energy VRM API demo account to demonstrate the basic functionality of the library. You can run it without needing to provide any credentials:

```bash
python examples/demo.py
```

This script will:
1. Get a demo token using the `/auth/loginAsDemo` endpoint
2. Get all sites available in the demo account
3. Get devices for the first site
4. Get measurements for the first device
5. Get system overview for the site
6. Get alarms for the site
7. Get diagnostics for the site

### Basic Usage

```python
import asyncio
from victron_vrm import VictronVRMClient

async def main():
    # Create the client with username and password
    async with VictronVRMClient(
        username="your_username",
        password="your_password",
        client_id="your_client_id",
    ) as client:
        # Get all sites
        sites = await client.get_sites()
        print(f"Found {sites.total} sites")

        # Get devices for a site
        if sites.sites:
            site = sites.sites[0]
            devices = await client.get_devices(site.id)
            print(f"Found {devices.total} devices for site {site.name}")

    # Alternatively, create the client with a token
    async with VictronVRMClient(
        token="your_token",
        token_type="Bearer",  # or "Token" for access tokens
    ) as client:
        # Get all sites
        sites = await client.get_sites()
        print(f"Found {sites.total} sites")

if __name__ == "__main__":
    asyncio.run(main())
```

### Using with Home Assistant

The client is designed to work with Home Assistant's async architecture. You can provide an existing `httpx.AsyncClient` session and use either username/password or token authentication:

```python
import httpx
from victron_vrm import VictronVRMClient

async def setup_victron_vrm(hass, config):
    # Use Home Assistant's existing httpx session
    session = httpx.AsyncClient()

    # Option 1: Using username and password
    if "username" in config and "password" in config and "client_id" in config:
        client = VictronVRMClient(
            username=config["username"],
            password=config["password"],
            client_id=config["client_id"],
            client_session=session,
        )
    # Option 2: Using a token
    elif "token" in config:
        client = VictronVRMClient(
            token=config["token"],
            token_type=config.get("token_type", "Bearer"),
            client_session=session,
        )
    else:
        raise ValueError("Either username/password/client_id or token must be provided")

    # Get data from the API
    sites = await client.get_sites()

    # Do something with the data
    # ...

    return True
```

## API Reference

### Client Initialization

```python
VictronVRMClient(
    username: Optional[str] = None,
    password: Optional[str] = None,
    client_id: Optional[str] = None,
    token: Optional[str] = None,
    token_type: str = "Bearer",
    client_session: Optional[httpx.AsyncClient] = None,
    request_timeout: int = 10,
    max_retries: int = 3,
    retry_delay: int = 1,
)
```

Either `username`, `password`, and `client_id` OR `token` must be provided. The `token_type` can be either "Bearer" (for JWT tokens) or "Token" (for access tokens).

### Available Methods

#### Sites

- `get_sites(page: int = 1, per_page: int = 100) -> SiteList`
- `get_site(site_id: Union[int, str]) -> Site`

#### Devices

- `get_devices(site_id: Union[int, str], page: int = 1, per_page: int = 100) -> DeviceList`
- `get_device(site_id: Union[int, str], device_id: Union[int, str]) -> Device`

#### Measurements

- `get_measurements(site_id: Union[int, str], device_id: Union[int, str], start: Optional[Union[datetime, str]] = None, end: Optional[Union[datetime, str]] = None, page: int = 1, per_page: int = 100) -> MeasurementList`
- `get_latest_measurement(site_id: Union[int, str], device_id: Union[int, str], measurement_type: str) -> Optional[Measurement]`

#### System Overview

- `get_system_overview(site_id: Union[int, str]) -> SystemOverview`

#### Alarms

- `get_alarms(site_id: Union[int, str]) -> Alarms`
- `clear_alarm(site_id: Union[int, str], alarm_id: Union[int, str]) -> bool`

#### Diagnostics

- `get_diagnostics(site_id: Union[int, str], page: int = 1, per_page: int = 100) -> DiagnosticsList`

## Error Handling

The client provides custom exceptions for different error scenarios:

```python
from victron_vrm.exceptions import (
    VictronVRMError,
    AuthenticationError,
    AuthorizationError,
    NotFoundError,
    RateLimitError,
    ServerError,
    ClientError,
    ConnectionError,
    TimeoutError,
    ParseError,
)

async def example_with_error_handling():
    try:
        async with VictronVRMClient(...) as client:
            sites = await client.get_sites()
    except AuthenticationError:
        print("Authentication failed")
    except ConnectionError:
        print("Connection error")
    except VictronVRMError as err:
        print(f"API error: {err}")
```

## License

MIT

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

### Development

To set up the development environment:

```bash
# Clone the repository
git clone https://github.com/KSoft-Si/victron-vrm.git
cd victron-vrm

# Install the package in development mode with test dependencies
pip install -e ".[test,dev]"

# Alternatively, if you have uv installed
uv pip install -e ".[test,dev]"
```

### Testing

The project includes a test suite that uses the Victron Energy VRM API demo account. To run the tests:

```bash
# Run all tests
pytest

# Run with coverage report
pytest --cov=victron_vrm

# Run a specific test
pytest tests/test_client.py::test_get_sites
```

See the [tests/README.md](tests/README.md) file for more information about the test suite.

### CI/CD Workflow

This project uses GitHub Actions for continuous integration and deployment:

- **Automated Testing**: All pull requests and pushes to the main branch are automatically tested against Python 3.11, 3.12, and 3.13.
- **Automatic Versioning**: When code is pushed to the main branch, the version is automatically incremented (patch version), a new tag is created, and a GitHub release is generated.
- **Package Publishing**: When a new version tag is created (either automatically or manually), the package is automatically built and published to PyPI.

The workflow uses `uv` instead of `pip` for faster and more reliable dependency management.

#### Automatic Releases

The project is configured with automatic versioning and releases:

1. When you push changes to the main branch, a GitHub Actions workflow automatically:
   - Increments the patch version in `pyproject.toml` (e.g., 0.1.0 → 0.1.1)
   - Commits the version change
   - Creates a new tag (e.g., v0.1.1)
   - Creates a GitHub release with automatically generated release notes
   - Triggers the CI/CD workflow to build and publish the package to PyPI

This means you don't need to manually update versions or create tags for routine updates.

#### Manual Releases

For major or minor version updates, you can still create releases manually:

1. Update the version in `pyproject.toml` (e.g., change 0.1.0 to 0.2.0 or 1.0.0)
2. Commit the changes: `git commit -am "Bump version to X.Y.Z"`
3. Create a new tag: `git tag vX.Y.Z`
4. Push the changes and tag: `git push && git push --tags`

The GitHub Actions workflow will automatically build and publish the new version to PyPI.
