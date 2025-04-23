"""Example usage of the Victron Energy VRM API client."""

import asyncio
import logging
from datetime import datetime, timedelta

import httpx

from victron_vrm import VictronVRMClient


async def main():
    """Run the example."""
    # Set up logging
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )
    logger = logging.getLogger(__name__)

    # Example 1: Using username and password authentication
    logger.info("Example 1: Using username and password authentication")

    # Replace with your credentials
    username = "your_username"
    password = "your_password"
    client_id = "your_client_id"

    # Create an httpx AsyncClient (optional, the VictronVRMClient can create its own)
    async with httpx.AsyncClient() as session:
        # Create the VictronVRMClient with username and password
        async with VictronVRMClient(
            username=username,
            password=password,
            client_id=client_id,
            client_session=session,
            request_timeout=30,
            max_retries=3,
        ) as client:
            # Get all sites using the users module
            logger.info("Getting all sites...")
            sites = await client.users.list_sites()
            logger.info(f"Found {len(sites)} sites")

            if not sites:
                logger.warning("No sites found")
                return

            # Get the first site
            site = sites[0]
            logger.info(f"Using site: {site.name} (ID: {site.id})")

            # Get user information
            logger.info("Getting current user information...")
            user = await client.users.get_me()
            logger.info(f"Current user: {user.name} (ID: {user.id}, Email: {user.email})")

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
            except Exception as e:
                logger.warning(f"Error getting alarms: {e}")

            # Get tags for the site
            try:
                logger.info(f"Getting tags for site {site.id}...")
                tags = await client.installations.get_tags(site.id)
                logger.info(f"Found {len(tags)} tags")

                # Print the tags
                for i, tag in enumerate(tags):
                    logger.info(f"Tag {i+1}: {tag}")
            except Exception as e:
                logger.warning(f"Error getting tags: {e}")

            # Get statistics for the site
            try:
                # Get statistics for the last 24 hours
                start_time = datetime.now() - timedelta(days=1)
                end_time = datetime.now()
                logger.info(f"Getting statistics for site {site.id} from {start_time} to {end_time}...")

                stats = await client.installations.stats(
                    site.id, 
                    start=start_time,
                    end=end_time,
                    interval="hours"
                )
                logger.info(f"Found statistics with {len(stats['records'])} records")

                # Print some statistics information
                if stats['records']:
                    logger.info(f"First record timestamp: {stats['records'][0].get('timestamp', 'N/A')}")
                if stats['totals']:
                    logger.info(f"Totals: {stats['totals']}")
            except Exception as e:
                logger.warning(f"Error getting statistics: {e}")

            # Get timezone for the site
            try:
                logger.info(f"Getting timezone for site {site.id}...")
                timezone = await client.installations.get_python_timezone(site.id)
                logger.info(f"Site timezone: {timezone}")
            except Exception as e:
                logger.warning(f"Error getting timezone: {e}")

            # Create an access token (example only - commented out to avoid creating tokens)
            # logger.info("Creating an access token...")
            # token_name = f"Example Token {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
            # token = await client.users.create_access_token(token_name)
            # logger.info(f"Created token: {token}")

            # List access tokens
            try:
                logger.info("Listing access tokens...")
                tokens = await client.users.list_access_tokens()
                logger.info(f"Found {len(tokens)} access tokens")

                # Print the first 3 tokens
                for i, token in enumerate(tokens[:3]):
                    logger.info(f"Token {i+1}: {token.get('name', 'N/A')} (ID: {token.get('id', 'N/A')})")
            except Exception as e:
                logger.warning(f"Error listing access tokens: {e}")

    # Example 2: Using token authentication
    logger.info("\nExample 2: Using token authentication")

    # Replace with your token
    token = "your_token"

    # Create the VictronVRMClient with token
    async with VictronVRMClient(
        token=token,
        token_type="Bearer",  # or "Token" for access tokens
        request_timeout=30,
        max_retries=3,
    ) as client:
        # Get all sites using the users module
        logger.info("Getting all sites...")
        sites = await client.users.list_sites()
        logger.info(f"Found {len(sites)} sites")

        if not sites:
            logger.warning("No sites found")
            return

        # Get the first site
        site = sites[0]
        logger.info(f"Using site: {site.name} (ID: {site.id})")

        # Get alarms for the site using the installations module
        try:
            logger.info(f"Getting alarms for site {site.id}...")
            alarms = await client.installations.get_alarms(site.id)
            logger.info(f"Found {len(alarms.alarms)} alarms")
        except Exception as e:
            logger.warning(f"Error getting alarms: {e}")


if __name__ == "__main__":
    asyncio.run(main())
