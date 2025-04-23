# Victron Energy VRM API Client Tests

This directory contains tests for the Victron Energy VRM API client.

## Running Tests

To run the tests, you'll need to install the test dependencies:

```bash
pip install -e ".[test]"
```

Then you can run the tests using pytest:

```bash
pytest
```

Or to run with coverage:

```bash
pytest --cov=victron_vrm
```

## Test Structure

The tests are organized as follows:

- `conftest.py`: Contains pytest configuration and fixtures
- `test_client.py`: Tests for the VictronVRMClient class

## Test Coverage

The tests cover the following functionality:

1. Authentication using the demo account
2. Getting sites
3. Getting devices for a site
4. Getting system overview for a site
5. Getting alarms for a site
6. Getting diagnostics for a site
7. Getting measurements for a device

## Notes

- The tests use the demo account provided by Victron Energy, so they don't require any credentials.
- Some tests may be skipped if the demo account doesn't have access to certain features or if there are no sites/devices available.
- The tests include logging to help with debugging.