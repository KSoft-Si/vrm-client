"""Demo script for the Victron Energy VRM API client using the demo account."""

import asyncio
import logging

import httpx

from victron_vrm import VictronVRMClient
from victron_vrm.exceptions import VictronVRMError

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

# Constants
AUTH_DEMO_URL = "https://vrmapi.victronenergy.com/v2/auth/loginAsDemo"


async def get_demo_token():
    """Get a demo token for testing."""
    async with httpx.AsyncClient() as client:
        response = await client.get(AUTH_DEMO_URL)
        response.raise_for_status()
        data = response.json()
        token = data.get("token")
        if not token:
            raise ValueError("Failed to get demo token")
        return token


async def main():
    """Run the demo."""
    # Get a demo token
    logger.info("Getting demo token...")
    token = await get_demo_token()
    logger.info("Got demo token")

    # Create the VictronVRMClient with the demo token
    async with VictronVRMClient(
        token=token,
        token_type="Bearer",
        request_timeout=30,
        max_retries=3,
    ) as client:
        # Get all sites using the users module
        logger.info("Getting all sites...")
        sites = await client.users.list_sites()
        logger.info(f"Found {len(sites)} sites")

        if not sites:
            logger.warning("No sites available in the demo account")
            return

        # Get the first site
        site = sites[0]
        logger.info(f"Using site: {site.name} (ID: {site.id})")

        # Get user information
        try:
            logger.info("Getting current user information...")
            user = await client.users.get_me()
            logger.info(f"Current user: {user.name} (ID: {user.id}, Email: {user.email})")
        except VictronVRMError as e:
            logger.warning(f"Error getting user information: {e}")

        # Get alarms for the site using the installations module
        try:
            logger.info(f"Getting alarms for site {site.id}...")
            alarms = await client.installations.get_alarms(site.id)
            logger.info(f"Found {len(alarms.alarms)} alarms")
            logger.info(f"Found {len(alarms.devices)} devices in alarms")
            logger.info(f"Found {len(alarms.users)} users in alarms")
            logger.info(f"Found {len(alarms.attributes)} attributes in alarms")

            # Print the first 3 alarms
            for i, alarm in enumerate(alarms.alarms[:3]):
                logger.info(
                    f"Alarm {i+1}: Data attribute ID: {alarm.data_attribute_id}, Instance: {alarm.instance}"
                )
        except VictronVRMError as e:
            logger.warning(f"Error getting alarms: {e}")

        # Get tags for the site
        try:
            logger.info(f"Getting tags for site {site.id}...")
            tags = await client.installations.get_tags(site.id)
            logger.info(f"Found {len(tags)} tags")

            # Print the tags
            for i, tag in enumerate(tags):
                logger.info(f"Tag {i+1}: {tag}")
        except VictronVRMError as e:
            logger.warning(f"Error getting tags: {e}")

        # Get statistics for the site
        try:
            logger.info(f"Getting statistics for site {site.id}...")
            stats = await client.installations.stats(site.id)
            logger.info(f"Found statistics with {len(stats['records'])} records")

            # Print some statistics information
            if stats['records']:
                logger.info(f"First record timestamp: {stats['records'][0].get('timestamp', 'N/A')}")
            if stats['totals']:
                logger.info(f"Totals: {stats['totals']}")
        except VictronVRMError as e:
            logger.warning(f"Error getting statistics: {e}")

        # Get timezone for the site
        try:
            logger.info(f"Getting timezone for site {site.id}...")
            timezone = await client.installations.get_python_timezone(site.id)
            logger.info(f"Site timezone: {timezone}")
        except VictronVRMError as e:
            logger.warning(f"Error getting timezone: {e}")


if __name__ == "__main__":
    asyncio.run(main())
