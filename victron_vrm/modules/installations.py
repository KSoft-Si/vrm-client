from datetime import datetime
from typing import Literal, Any

import pytz

from ._base import BaseClientModule
from .. import consts
from ..models import Site, Alarms, AlarmSettings
from ..models.aggregations import ForecastAggregations
from ..utils import is_dt_timezone_aware


class InstallationsModule(BaseClientModule):
    BASE_URL = consts.INSTALLATIONS_URL

    async def get_alarms(self, site_id: int | Site) -> Alarms:
        """
        Get alarms for a specific site.

        :param site_id: The ID of the site or a Site object.
        :return: An Alarms object containing the alarms for the site.
        """
        if isinstance(site_id, Site):
            site_id = site_id.id

        request = await self._client._request(
            method="GET",
            url=f"{self.BASE_URL}/{site_id}/alarms",
        )
        return Alarms(**request)

    async def add_alarm(self, site_id: int | Site, alarm: AlarmSettings) -> None:
        """
        Add a new alarm to a specific site.

        :param site_id: The ID of the site or a Site object.
        :param alarm: An AlarmSettings object containing the alarm settings.
        """
        if isinstance(site_id, Site):
            site_id = site_id.id

        await self._client._request(
            method="POST",
            url=f"{self.BASE_URL}/{site_id}/alarms",
            json_data=alarm.model_dump(by_alias=True),
        )

    async def delete_alarm(self, site_id: int | Site, alarm: AlarmSettings) -> None:
        """
        Delete an alarm from a specific site.

        :param site_id: The ID of the site or a Site object.
        :param alarm: An AlarmSettings object containing the alarm settings.
        """
        if isinstance(site_id, Site):
            site_id = site_id.id

        await self._client._request(
            method="DELETE",
            url=f"{self.BASE_URL}/{site_id}/alarms",
            json_data={
                "idDataAttribute": alarm.data_attribute_id,
                "instance": alarm.instance,
            },
        )

    async def update_alarm(
        self, site_id: int | Site, alarm: AlarmSettings
    ) -> AlarmSettings:
        """
        Update an existing alarm for a specific site.

        :param site_id: The ID of the site or a Site object.
        :param alarm: An AlarmSettings object containing the updated alarm settings.
        :return: The updated AlarmSettings object.
        """
        if isinstance(site_id, Site):
            site_id = site_id.id

        request = await self._client._request(
            method="PUT",
            url=f"{self.BASE_URL}/{site_id}/alarms",
            json_data=alarm.model_dump(by_alias=True),
        )
        return AlarmSettings(**request["data"])

    async def clear_alarm(
        self, site_id: int | Site, alarm: AlarmSettings | int
    ) -> None:
        """
        Clear an alarm for a specific site.

        :param site_id: The ID of the site or a Site object.
        :param alarm: An AlarmSettings object containing the alarm settings.
        """
        if isinstance(site_id, Site):
            site_id = site_id.id

        if isinstance(alarm, AlarmSettings):
            alarm = alarm.data_attribute_id

        await self._client._request(
            method="DELETE",
            url=f"{self.BASE_URL}/{site_id}/clear-alarm",
            json_data={"alarmId": alarm},
        )

    # TODO: The following endpoints are not implemented yet:
    # Connected devices for a given installation - /system-overview
    # Diagnostic data for an installation - /diagnostics
    # Dynamic ESS GET and POST - /dynamic-ess-settings
    # GPS tracks for an installation - /gps-download

    async def get_tags(self, site_id: int | Site) -> list[str]:
        """
        Get the list of tags for installations.

        :return: A list of tags.
        """
        if isinstance(site_id, Site):
            site_id = site_id.id

        request = await self._client._request(
            method="GET",
            url=f"{self.BASE_URL}/{site_id}/tags",
        )
        return request["tags"]

    async def add_tag(self, site_id: int | Site, tag: str) -> None:
        """
        Add a new tag to the installation.

        :param site_id: The ID of the site or a Site object.
        :param tag: The tag to add.
        """
        if isinstance(site_id, Site):
            site_id = site_id.id

        await self._client._request(
            method="PUT",
            url=f"{self.BASE_URL}/{site_id}/tags",
            json_data={"tag": tag, "source": "user"},
        )

    async def delete_tag(self, site_id: int | Site, tag: str) -> None:
        """
        Delete a tag from the installation.

        :param site_id: The ID of the site or a Site object.
        :param tag: The tag to delete.
        """
        if isinstance(site_id, Site):
            site_id = site_id.id

        await self._client._request(
            method="DELETE",
            url=f"{self.BASE_URL}/{site_id}/tags",
            json_data={"tag": tag},
        )

    # TODO: The following endpoints are not implemented yet:
    # Download installations data - /data-download

    async def stats(
        self,
        site_id: int | Site,
        start: int | datetime | None = None,
        end: int | datetime | None = None,
        interval: Literal[
            "15mins", "hours", "2hours", "days", "weeks", "months", "years"
        ] = "hours",
        type: Literal[
            "venus",
            "live_feed",
            "consumption",
            "solar_yield",
            "kwh",
            "generator",
            "generator-runtime",
            "custom",
            "forecast",
        ] = "live_feed",
        attribute_codes: list[str] | None = None,
        return_aggregations: bool = False,
    ) -> (
        dict[Literal["records", "totals"], dict]
        | dict[Literal["solar_yield", "consumption"], ForecastAggregations | None]
    ):
        """
        Get statistics for a specific site.

        :param site_id: The ID of the site or a Site object.
        :param start: The start time for the statistics.
        :param end: The end time for the statistics.
        :param interval: The interval for the statistics.
        :param type: The type of statistics to retrieve.
        :param attribute_codes: Optional list of attribute codes to filter the statistics.
        :param return_aggregations: Whether to return a ForecastAggregations object (only valid when type is 'forecast').
        :return: A dictionary containing the statistics.
        """
        assert (
            type == "forecast" or not return_aggregations
        ), "return_aggregations can only be True when type is 'forecast'"
        if isinstance(site_id, Site):
            site_id = site_id.id

        if isinstance(start, datetime):
            if not is_dt_timezone_aware(start):
                raise ValueError("start datetime object must be timezone-aware")
            start = int(start.timestamp())

        if isinstance(end, datetime):
            if not is_dt_timezone_aware(end):
                raise ValueError("end datetime object must be timezone-aware")
            end = int(end.timestamp())

        request = await self._client._request(
            method="GET",
            url=f"{self.BASE_URL}/{site_id}/stats",
            params={
                "start": start,
                "end": end,
                "interval": interval,
                "type": type,
                "attributeCodes": attribute_codes,
            },
        )
        payload: dict[Literal["records", "totals"], dict] = {
            "records": request["records"],
            "totals": request["totals"],
        }
        if isinstance(payload["totals"], dict):
            for k, v in payload["totals"].items():
                if v is False:
                    payload["totals"][k] = None
        if isinstance(payload["records"], dict):
            for k, v in payload["records"].items():
                if v is False:
                    payload["records"][k] = None
        if type == "forecast" and return_aggregations:
            payload: dict[
                Literal["solar_yield", "consumption"], ForecastAggregations | None
            ] = {}
            for key, map_key in {
                "solar_yield_forecast": "solar_yield",
                "vrm_consumption_fc": "consumption",
            }.items():
                if key in request["records"] and request["records"][key] is not None:
                    if len(request["records"][key]) == 0:
                        payload[map_key] = None
                        continue
                    payload[map_key] = ForecastAggregations(
                        start=start,
                        end=end,
                        site_id=site_id,
                        records=[
                            (int(x / 1000), y) for x, y in request["records"][key]
                        ],
                    )
                else:
                    payload[map_key] = None
        return payload

    async def get_python_timezone(self, site_id: int | Site) -> Any:
        """
        Get the Python timezone for a specific site.

        :param site_id: The ID of the site or a Site object.
        :return: A PyTZ object representing the timezone.
        """
        if isinstance(site_id, int):
            site_id = await self._client.users.get_site(site_id)

        if site_id is None:
            raise ValueError("Site not found")

        return pytz.timezone(site_id.timezone)
