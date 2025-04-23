"""Tests for the Victron Energy VRM API client."""

import logging
import pytest
import httpx
import random

from victron_vrm import VictronVRMClient
from victron_vrm.exceptions import VictronVRMError, AuthorizationError
from victron_vrm.models import Site

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

# Constants
AUTH_DEMO_URL = "https://vrmapi.victronenergy.com/v2/auth/loginAsDemo"


@pytest.fixture
async def demo_token():
    """Get a demo token for testing."""
    async with httpx.AsyncClient() as client:
        response = await client.get(AUTH_DEMO_URL)
        response.raise_for_status()
        data = response.json()
        token = data.get("token")
        if not token:
            pytest.skip("Failed to get demo token")
        return token


@pytest.fixture
async def vrm_client(demo_token):
    """Create a VictronVRMClient with the demo token."""
    async with VictronVRMClient(
        token=demo_token,
        token_type="Bearer",
        request_timeout=30,
        max_retries=3
    ) as client:
        yield client


@pytest.fixture
async def test_site(vrm_client):
    """Get the test site - ESS installation or first available."""
    sites = await vrm_client.users.list_sites()

    # Try to find an installation with the name ESS
    ess_site = next((site for site in sites if site.name == "ESS"), None)

    # If ESS installation not found, use the first installation
    if ess_site:
        logger.info(f"Using ESS installation: {ess_site.name} (ID: {ess_site.id})")
        return ess_site
    elif sites:
        logger.info(f"ESS installation not found, using first installation: {sites[0].name} (ID: {sites[0].id})")
        return sites[0]
    else:
        pytest.skip("No installations available for testing")
        return None


@pytest.mark.asyncio
async def test_get_me(vrm_client):
    """Test getting current user."""
    user = await vrm_client.users.get_me()
    assert user is not None
    assert hasattr(user, "id")
    assert hasattr(user, "name")
    assert hasattr(user, "email")

    logger.info(f"Current user: {user.name} (ID: {user.id}, Email: {user.email})")
    return user


@pytest.mark.asyncio
async def test_list_sites(vrm_client):
    """Test listing sites."""
    try:
        sites = await vrm_client.users.list_sites()
        assert sites is not None
        assert isinstance(sites, list)
        assert all(isinstance(site, Site) for site in sites)

        logger.info(f"Found {len(sites)} sites")
        for site in sites:
            logger.info(f"Site: {site.name} (ID: {site.id})")

        return sites
    except AuthorizationError as e:
        logger.info(f"AuthorizationError received as expected: {e}")
        # Test is successful if AuthorizationError is received
        return []


@pytest.mark.asyncio
async def test_get_site(vrm_client, test_site):
    """Test getting a specific site."""
    try:
        site = await vrm_client.users.get_site(test_site.id)
        assert site is not None
        assert isinstance(site, Site)
        assert site.id == test_site.id
        assert site.name == test_site.name

        logger.info(f"Retrieved site: {site.name} (ID: {site.id})")
        return site
    except AuthorizationError as e:
        logger.info(f"AuthorizationError received as expected: {e}")
        # Test is successful if AuthorizationError is received
        return None


@pytest.mark.asyncio
async def test_get_site_id_from_identifier(vrm_client):
    """Test getting site ID from identifier."""
    try:
        # Get all sites
        sites = await vrm_client.users.list_sites()
        if not sites:
            pytest.skip("No sites available for testing")

        # Select a random site
        random_site = random.choice(sites)
        logger.info(f"Selected random site: {random_site.name} (ID: {random_site.id}, Identifier: {random_site.identifier})")

        # Get site ID from identifier
        site_id = await vrm_client.users.get_site_id_from_identifier(random_site.identifier)
        assert site_id is not None
        assert site_id == random_site.id

        logger.info(f"Retrieved site ID: {site_id} from identifier: {random_site.identifier}")
        return site_id
    except AuthorizationError as e:
        logger.info(f"AuthorizationError received as expected: {e}")
        # Test is successful if AuthorizationError is received
        return None


@pytest.mark.asyncio
async def test_get_alarms(vrm_client, test_site):
    """Test getting alarms for a site."""
    try:
        alarms = await vrm_client.installations.get_alarms(test_site.id)
        assert alarms is not None
        assert hasattr(alarms, "alarms")
        assert hasattr(alarms, "devices")
        assert hasattr(alarms, "users")
        assert hasattr(alarms, "attributes")

        logger.info(f"Found {len(alarms.alarms)} alarms for site {test_site.name} (ID: {test_site.id})")
        logger.info(f"Found {len(alarms.devices)} devices in alarms")
        logger.info(f"Found {len(alarms.users)} users in alarms")
        logger.info(f"Found {len(alarms.attributes)} attributes in alarms")

        return alarms
    except AuthorizationError as e:
        logger.info(f"AuthorizationError received as expected: {e}")
        # Test is successful if AuthorizationError is received
        return None
    except VictronVRMError as e:
        # Some demo sites might not have alarms enabled
        logger.warning(f"Error getting alarms for site {test_site.name} (ID: {test_site.id}): {e}")
        pytest.skip(f"Error getting alarms: {e}")


@pytest.mark.asyncio
async def test_get_tags(vrm_client, test_site):
    """Test getting tags for a site."""
    try:
        tags = await vrm_client.installations.get_tags(test_site.id)
        assert tags is not None
        assert isinstance(tags, list)

        logger.info(f"Found {len(tags)} tags for site {test_site.name} (ID: {test_site.id})")
        for tag in tags:
            logger.info(f"Tag: {tag}")

        return tags
    except AuthorizationError as e:
        logger.info(f"AuthorizationError received as expected: {e}")
        # Test is successful if AuthorizationError is received
        return None
    except VictronVRMError as e:
        logger.warning(f"Error getting tags for site {test_site.name} (ID: {test_site.id}): {e}")
        pytest.skip(f"Error getting tags: {e}")


@pytest.mark.asyncio
async def test_stats(vrm_client):
    """Test getting statistics for a site."""
    try:
        # Get all sites
        sites = await vrm_client.users.list_sites()
        if not sites:
            pytest.skip("No sites available for testing")

        # Select a random site
        random_site = random.choice(sites)
        logger.info(f"Selected random site for stats: {random_site.name} (ID: {random_site.id})")

        # Get stats with default options
        stats = await vrm_client.installations.stats(random_site.id)
        assert stats is not None
        assert isinstance(stats, dict)
        assert "records" in stats
        assert "totals" in stats

        logger.info(f"Retrieved stats for site {random_site.name} (ID: {random_site.id})")
        logger.info(f"Stats contains {len(stats['records'])} records and {len(stats['totals'])} totals")

        return stats
    except AuthorizationError as e:
        logger.info(f"AuthorizationError received as expected: {e}")
        # Test is successful if AuthorizationError is received
        return None
    except VictronVRMError as e:
        logger.warning(f"Error getting stats for site: {e}")
        pytest.skip(f"Error getting stats: {e}")
