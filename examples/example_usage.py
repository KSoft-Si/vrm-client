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
            # Get all sites
            logger.info("Getting all sites...")
            sites = await client.get_sites()
            logger.info(f"Found {sites.total} sites")

            if not sites.sites:
                logger.warning("No sites found")
                return

            # Get the first site
            site = sites.sites[0]
            logger.info(f"Using site: {site.name} (ID: {site.id})")

            # Get all devices for the site
            logger.info(f"Getting devices for site {site.id}...")
            devices = await client.get_devices(site.id)
            logger.info(f"Found {devices.total} devices")

            if not devices.devices:
                logger.warning("No devices found")
                return

            # Get the first device
            device = devices.devices[0]
            logger.info(
                f"Using device: {device.name} (ID: {device.id}, Type: {device.device_type})"
            )

            # Get measurements for the device for the last 24 hours
            start_time = datetime.now() - timedelta(days=1)
            end_time = datetime.now()
            logger.info(
                f"Getting measurements for device {device.id} from {start_time} to {end_time}..."
            )
            measurements = await client.get_measurements(
                site.id, device.id, start=start_time, end=end_time
            )
            logger.info(f"Found {measurements.total} measurements")

            # Print the first 5 measurements
            for i, measurement in enumerate(measurements.measurements[:5]):
                logger.info(
                    f"Measurement {i+1}: {measurement.type} = {measurement.value} {measurement.unit or ''} at {measurement.timestamp}"
                )

            # Get the latest measurement of a specific type (if available)
            if measurements.measurements:
                measurement_type = measurements.measurements[0].type
                logger.info(f"Getting latest measurement of type {measurement_type}...")
                latest = await client.get_latest_measurement(
                    site.id, device.id, measurement_type
                )
                if latest:
                    logger.info(
                        f"Latest {latest.type} = {latest.value} {latest.unit or ''} at {latest.timestamp}"
                    )
                else:
                    logger.warning(f"No latest measurement found for type {measurement_type}")

            # Get system overview for the site
            logger.info(f"Getting system overview for site {site.id}...")
            system_overview = await client.get_system_overview(site.id)
            logger.info(f"Found {len(system_overview.devices)} devices in system overview")

            # Print the first 3 devices in the system overview
            for i, device in enumerate(system_overview.devices[:3]):
                logger.info(
                    f"System device {i+1}: {device.name} (Product: {device.product_name})"
                )

            # Get alarms for the site
            try:
                logger.info(f"Getting alarms for site {site.id}...")
                alarms = await client.get_alarms(site.id)
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

            # Get diagnostics for the site
            try:
                logger.info(f"Getting diagnostics for site {site.id}...")
                diagnostics = await client.get_diagnostics(site.id)
                logger.info(f"Found {diagnostics.total} diagnostics records")

                # Print the first 3 diagnostics records
                for i, record in enumerate(diagnostics.records[:3]):
                    logger.info(
                        f"Diagnostics record {i+1}: {record.description} = {record.formatted_value}"
                    )
            except Exception as e:
                logger.warning(f"Error getting diagnostics: {e}")

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
        # Get all sites
        logger.info("Getting all sites...")
        sites = await client.get_sites()
        logger.info(f"Found {sites.total} sites")

        if not sites.sites:
            logger.warning("No sites found")
            return

        # Get the first site
        site = sites.sites[0]
        logger.info(f"Using site: {site.name} (ID: {site.id})")

        # Get all devices for the site
        logger.info(f"Getting devices for site {site.id}...")
        devices = await client.get_devices(site.id)
        logger.info(f"Found {devices.total} devices")


if __name__ == "__main__":
    asyncio.run(main())
