"""Pytest configuration for Victron Energy VRM API client tests."""

import logging

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)

# Configure pytest
def pytest_configure(config):
    """Configure pytest."""
    config.addinivalue_line("markers", "asyncio: mark test as an asyncio test")


# Define pytest plugins
pytest_plugins = ["pytest_asyncio"]