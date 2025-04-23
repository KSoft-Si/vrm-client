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
        # Get all sites
        logger.info("Getting all sites...")
        sites = await client.get_sites()
        logger.info(f"Found {sites.total} sites")

        if not sites.sites:
            logger.warning("No sites available in the demo account")
            return

        # Get the first site
        site = sites.sites[0]
        logger.info(f"Using site: {site.name} (ID: {site.id})")

        # Get all devices for the site
        logger.info(f"Getting devices for site {site.id}...")
        devices = await client.get_devices(site.id)
        logger.info(f"Found {devices.total} devices")

        if not devices.devices:
            logger.warning("No devices available for this site")
            return

        # Get the first device
        device = devices.devices[0]
        logger.info(f"Using device: {device.name} (ID: {device.id}, Type: {device.device_type})")

        # Get measurements for the device
        try:
            logger.info(f"Getting measurements for device {device.id}...")
            measurements = await client.get_measurements(site.id, device.id)
            logger.info(f"Found {measurements.total} measurements")

            # Print the first 5 measurements
            for i, measurement in enumerate(measurements.measurements[:5]):
                logger.info(
                    f"Measurement {i+1}: {measurement.type} = {measurement.value} {measurement.unit or ''} at {measurement.timestamp}"
                )
        except VictronVRMError as e:
            logger.warning(f"Error getting measurements: {e}")

        # Get system overview for the site
        try:
            logger.info(f"Getting system overview for site {site.id}...")
            system_overview = await client.get_system_overview(site.id)
            logger.info(f"Found {len(system_overview.devices)} devices in system overview")

            # Print the first 3 devices in the system overview
            for i, device in enumerate(system_overview.devices[:3]):
                logger.info(
                    f"System device {i+1}: {device.name} (Product: {device.product_name})"
                )
        except VictronVRMError as e:
            logger.warning(f"Error getting system overview: {e}")

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
        except VictronVRMError as e:
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
        except VictronVRMError as e:
            logger.warning(f"Error getting diagnostics: {e}")


if __name__ == "__main__":
    asyncio.run(main())