"""Tests for forecast aggregation day boundaries."""

from datetime import UTC, datetime
from unittest.mock import AsyncMock, MagicMock
from zoneinfo import ZoneInfo

import pytest

from victron_vrm.models.aggregations import ForecastAggregations
from victron_vrm.modules.installations import InstallationsModule


@pytest.mark.parametrize(
    ("now", "today_start", "tomorrow_start"),
    [
        (
            "2026-03-29T12:00:00+00:00",
            "2026-03-28T23:00:00+00:00",
            "2026-03-29T22:00:00+00:00",
        ),
        (
            "2026-10-25T12:00:00+00:00",
            "2026-10-24T22:00:00+00:00",
            "2026-10-25T23:00:00+00:00",
        ),
    ],
)
def test_local_day_ranges(now: str, today_start: str, tomorrow_start: str) -> None:
    """Local day ranges span 23 or 25 hours at DST transitions."""
    current = datetime.fromisoformat(now)
    start = int(datetime.fromisoformat(today_start).timestamp())
    end = int(datetime.fromisoformat(tomorrow_start).timestamp())
    forecast = ForecastAggregations(
        start=start,
        end=end,
        site_id=123,
        records=[(start, 2), (end - 3600, 3), (end, 4)],
        custom_dt_now=lambda: current,
        time_zone=ZoneInfo("Europe/Berlin"),
    )

    assert forecast.today_range == (start, end)
    assert forecast.today_left_range == (int(current.timestamp()), end)
    assert forecast.today_total == 5
    assert forecast.tomorrow_total == 4


def test_fall_back_hourly_ranges() -> None:
    """Hourly forecasts follow elapsed hours through the repeated hour."""
    first_hour = datetime(2026, 10, 25, 0, tzinfo=UTC)
    start = int(first_hour.timestamp())
    forecast = ForecastAggregations(
        start=start,
        end=start + 7200,
        site_id=123,
        records=[(start, 10), (start + 3600, 20), (start + 7200, 30)],
        custom_dt_now=lambda: first_hour.replace(minute=30),
        time_zone=ZoneInfo("Europe/Berlin"),
    )

    assert forecast.current_hour_total == 10
    assert forecast.next_hour_total == 20
    assert forecast.next_hour_timestamp == (start + 3600, start + 7200)


def test_default_day_ranges_remain_compatible() -> None:
    """Omitting a timezone retains the existing range behavior."""
    forecast = ForecastAggregations(
        start=0,
        end=172800,
        site_id=123,
        records=[(0, 1), (86400, 2), (172800, 3)],
        custom_dt_now=lambda: datetime.fromtimestamp(86400, UTC),
    )

    assert forecast.yesterday_range == (0, 86400)
    assert forecast.today_range == (86400, 172800)
    assert forecast.tomorrow_range == (172800, 259200)


@pytest.mark.asyncio
async def test_stats_passes_time_zone_to_aggregations() -> None:
    """The stats API builds timezone-aware forecast aggregations."""
    timestamp = int(datetime(2026, 10, 25, tzinfo=UTC).timestamp())
    client = MagicMock()
    client._request = AsyncMock(
        return_value={
            "records": {
                "solar_yield_forecast": [[timestamp * 1000, 2]],
                "vrm_consumption_fc": False,
            },
            "totals": {},
        }
    )
    time_zone = ZoneInfo("Europe/Berlin")

    result = await InstallationsModule(client).stats(
        123,
        start=timestamp,
        end=timestamp + 3600,
        type="forecast",
        return_aggregations=True,
        time_zone=time_zone,
    )

    assert result["solar_yield"] is not None
    assert result["solar_yield"].time_zone is time_zone
    assert result["consumption"] is None
