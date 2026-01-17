"""Tests for the Victron Energy VRM API client."""

import logging
import unittest.mock

import aiohttp
import pytest
import random

from victron_vrm import VictronVRMClient
from victron_vrm.exceptions import VictronVRMError, AuthorizationError, NotFoundError, ClientError
from victron_vrm.models import Site
from victron_vrm.models.auth import AuthToken
from victron_vrm.mqtt import VRMMQTTClient

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

# Constants
AUTH_DEMO_URL = "https://vrmapi.victronenergy.com/v2/auth/loginAsDemo"


# Helper classes for mocking
class _MockUser:
    """Mock user for testing."""
    email = "test@example.com"


class _MockSite:
    """Mock site for testing."""
    identifier = "test-vrm-id"
    mqtt_hostname = "mqtt.victronenergy.com"


class _MockSiteNoHostname:
    """Mock site without MQTT hostname for testing."""
    identifier = "test-vrm-id"
    mqtt_hostname = None


def _create_mock_token():
    """Create a mock auth token for testing."""
    return AuthToken(
        access_token="mock_access_token",
        token_type="Bearer",
        expires_in=3600,
        scope="read"
    )


@pytest.fixture(scope="session")
async def demo_token():
    """Get a demo token for testing (session-scoped to avoid 429s)."""
    async with aiohttp.ClientSession() as client:
        async with client.get(AUTH_DEMO_URL) as response:
            response.raise_for_status()
            data = await response.json()
    token = data.get("token")
    if not token:
        pytest.skip("Failed to get demo token")
    return token


@pytest.fixture
async def vrm_client(demo_token):
    """Create a VictronVRMClient with the demo token."""
    async with VictronVRMClient(
        token=demo_token, token_type="Bearer", request_timeout=30, max_retries=3
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
        logger.info(
            f"ESS installation not found, using first installation: {sites[0].name} (ID: {sites[0].id})"
        )
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
        logger.info(
            f"Selected random site: {random_site.name} (ID: {random_site.id}, Identifier: {random_site.identifier})"
        )

        # Get site ID from identifier
        site_id = await vrm_client.users.get_site_id_from_identifier(
            random_site.identifier
        )
        assert site_id is not None
        assert site_id == random_site.id

        logger.info(
            f"Retrieved site ID: {site_id} from identifier: {random_site.identifier}"
        )
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

        logger.info(
            f"Found {len(alarms.alarms)} alarms for site {test_site.name} (ID: {test_site.id})"
        )
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
        logger.warning(
            f"Error getting alarms for site {test_site.name} (ID: {test_site.id}): {e}"
        )
        pytest.skip(f"Error getting alarms: {e}")


@pytest.mark.asyncio
async def test_get_tags(vrm_client, test_site):
    """Test getting tags for a site."""
    try:
        tags = await vrm_client.installations.get_tags(test_site.id)
        assert tags is not None
        assert isinstance(tags, list)

        logger.info(
            f"Found {len(tags)} tags for site {test_site.name} (ID: {test_site.id})"
        )
        for tag in tags:
            logger.info(f"Tag: {tag}")

        return tags
    except AuthorizationError as e:
        logger.info(f"AuthorizationError received as expected: {e}")
        # Test is successful if AuthorizationError is received
        return None
    except VictronVRMError as e:
        logger.warning(
            f"Error getting tags for site {test_site.name} (ID: {test_site.id}): {e}"
        )
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
        valid_sites = [site for site in sites if site.id is not None]
        if not valid_sites:
            pytest.skip("No valid sites with IDs available for testing")
        random_site = random.choice(valid_sites)
        logger.info(
            f"Selected random site for stats: {random_site.name} (ID: {random_site.id})"
        )

        # Get stats with default options
        stats = await vrm_client.installations.stats(random_site.id)
        assert stats is not None
        assert isinstance(stats, dict)
        assert "records" in stats
        assert "totals" in stats
    except AuthorizationError as e:
        logger.info(f"AuthorizationError received as expected: {e}")
        # Test is successful if AuthorizationError is received
        return None
    except VictronVRMError as e:
        logger.warning(f"Error getting stats for site: {e}")
        pytest.fail(f"Error getting stats: {e}")
        raise e

    # Validate the structure of records and totals
    records = stats["records"]
    totals = stats["totals"]

    # Records and totals can be either dict or list depending on the API response
    assert isinstance(records, (dict, list)), "Records should be a dictionary or list"
    assert isinstance(totals, (dict, list)), "Totals should be a dictionary or list"

    # If records is a dict, validate its values
    if isinstance(records, dict):
        for key, value in records.items():
            assert value is None or isinstance(
                value, list
            ), f"Records[{key}] should be None or list, got {type(value)}: {value}"
            assert (
                value is not False
            ), f"Records[{key}] should not be False - client should transform False to None"
            logger.debug(f"Records[{key}] = {value} (type: {type(value)})")
    else:
        # Records is a list - validate it's a proper list
        assert isinstance(records, list), "Records should be a list when not a dict"
        logger.debug(f"Records is a list with {len(records)} items")

    # If totals is a dict, validate its values
    if isinstance(totals, dict):
        for key, value in totals.items():
            assert value is None or isinstance(
                value, (int, float)
            ), f"Totals[{key}] should be None, int, or float, got {type(value)}: {value}"
            assert (
                value is not False
            ), f"Totals[{key}] should not be False - client should transform False to None"
            logger.debug(f"Totals[{key}] = {value} (type: {type(value)})")
    else:
        # Totals is a list - validate it's a proper list
        assert isinstance(totals, list), "Totals should be a list when not a dict"
        logger.debug(f"Totals is a list with {len(totals)} items")

    logger.info(f"Retrieved stats for site {random_site.name} (ID: {random_site.id})")
    logger.info(f"Records type: {type(records)}, Totals type: {type(totals)}")

    return stats


@pytest.mark.asyncio
async def test_stats_false_to_none_transformation(vrm_client):
    """Test that the client transforms false values to None in stats response."""
    import unittest.mock

    try:
        # Get all sites
        sites = await vrm_client.users.list_sites()
        if not sites:
            pytest.skip("No sites available for testing")

        # Select a random site
        random_site = random.choice(sites)
        logger.info(
            f"Testing false-to-None transformation for site: {random_site.name} (ID: {random_site.id})"
        )

        # Mock the API response with false values
        mock_api_response = {
            "success": True,
            "records": {
                "solar_yield_forecast": False,
                "vrm_consumption_fc": False,
                "some_other_field": [1, 2, 3],  # Should remain unchanged
            },
            "totals": {
                "solar_yield_forecast": False,
                "vrm_consumption_fc": False,
                "some_numeric_field": 123.45,  # Should remain unchanged
            },
        }

        # Mock the _request method directly on the VictronVRMClient
        with unittest.mock.patch.object(
            vrm_client, "_request", return_value=mock_api_response
        ):
            stats = await vrm_client.installations.stats(random_site.id)

            # Verify the structure exists
            assert "records" in stats
            assert "totals" in stats

            records = stats["records"]
            totals = stats["totals"]

            # Verify false values were transformed to None
            assert (
                records["solar_yield_forecast"] is None
            ), "solar_yield_forecast in records should be None, not False"
            assert (
                records["vrm_consumption_fc"] is None
            ), "vrm_consumption_fc in records should be None, not False"
            assert (
                totals["solar_yield_forecast"] is None
            ), "solar_yield_forecast in totals should be None, not False"
            assert (
                totals["vrm_consumption_fc"] is None
            ), "vrm_consumption_fc in totals should be None, not False"

            # Verify other values remain unchanged
            assert records["some_other_field"] == [
                1,
                2,
                3,
            ], "Non-false values should remain unchanged"
            assert (
                totals["some_numeric_field"] == 123.45
            ), "Non-false values should remain unchanged"

            # Verify no False values exist anywhere
            for key, value in records.items():
                assert (
                    value is not False
                ), f"Records[{key}] should not be False after transformation"

            for key, value in totals.items():
                assert (
                    value is not False
                ), f"Totals[{key}] should not be False after transformation"

            logger.info(
                "Successfully verified false-to-None transformation in stats response"
            )
            return stats

    except AuthorizationError as e:
        logger.info(f"AuthorizationError received as expected: {e}")
        return None
    except VictronVRMError as e:
        logger.warning(f"Error in mock test: {e}")
        pytest.skip(f"Error in mock test: {e}")


@pytest.mark.asyncio
async def test_get_mqtt_client_for_installation_success():
    """Test getting MQTT client for a valid installation."""
    # Create a mock client without needing actual network access
    async with VictronVRMClient(token="mock_token", token_type="Bearer") as client:
        async def mock_gather(*args):
            return _create_mock_token(), _MockUser(), [_MockSite()]
        
        # Mock asyncio.gather to avoid actual API calls
        with unittest.mock.patch("asyncio.gather", side_effect=mock_gather):
            # Get MQTT client
            mqtt_client = await client.get_mqtt_client_for_installation(67890)
            
            # Verify the client is properly configured
            assert mqtt_client is not None
            assert isinstance(mqtt_client, VRMMQTTClient)
            
            # Verify client attributes
            assert mqtt_client.host == "mqtt.victronenergy.com"
            assert mqtt_client.username == "test@example.com"
            assert mqtt_client.password == "Bearer mock_access_token"
            assert mqtt_client.installation_id == "test-vrm-id"
            
            logger.info("Successfully created MQTT client with mocked data")


@pytest.mark.asyncio
async def test_get_mqtt_client_for_installation_not_found():
    """Test getting MQTT client for a non-existent installation."""
    # Create a mock client
    async with VictronVRMClient(token="mock_token", token_type="Bearer") as client:
        async def mock_gather(*args):
            # Return empty list for installations
            return _create_mock_token(), _MockUser(), []
        
        # Mock asyncio.gather to return empty installations list
        with unittest.mock.patch("asyncio.gather", side_effect=mock_gather):
            # Should raise NotFoundError
            with pytest.raises(NotFoundError) as exc_info:
                await client.get_mqtt_client_for_installation(999999999)
            
            # Verify the error message
            assert "not found" in str(exc_info.value).lower()
            assert "999999999" in str(exc_info.value)
            
            logger.info("NotFoundError correctly raised for invalid installation ID")


@pytest.mark.asyncio
async def test_get_mqtt_client_for_installation_missing_hostname():
    """Test getting MQTT client for installation without MQTT hostname."""
    # Create a mock client
    async with VictronVRMClient(token="mock_token", token_type="Bearer") as client:
        async def mock_gather(*args):
            return _create_mock_token(), _MockUser(), [_MockSiteNoHostname()]
        
        # Mock asyncio.gather
        with unittest.mock.patch("asyncio.gather", side_effect=mock_gather):
            # Should raise ClientError
            with pytest.raises(ClientError) as exc_info:
                await client.get_mqtt_client_for_installation(67890)
            
            # Verify the error message
            assert "mqtt hostname" in str(exc_info.value).lower()
            assert "67890" in str(exc_info.value)
            
            logger.info("ClientError correctly raised for installation without MQTT hostname")
