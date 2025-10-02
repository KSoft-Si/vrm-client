import datetime
from dataclasses import dataclass
from typing import Callable

from victron_vrm.utils import is_dt_timezone_aware


@dataclass
class ForecastAggregations:
    """Class to hold and calculate forecast estimates."""

    start: int
    end: int
    site_id: int
    records: list[tuple[int, float]]
    custom_dt_now: Callable[[], datetime.datetime] | None = None

    def __post_init__(self) -> None:
        """Post-initialize the ForecastEstimates class."""
        if len(self.records) == 0:
            return
        if self.start != min(x[0] for x in self.records):
            self.start = min(x[0] for x in self.records)
        if self.end != max(x[0] for x in self.records):
            self.end = max(x[0] for x in self.records)

    @property
    def dt_now(self) -> datetime.datetime:
        """Get the current datetime."""
        if self.custom_dt_now is not None:
            dt = self.custom_dt_now()
            if not is_dt_timezone_aware(dt):
                raise ValueError("custom_dt_now must return a timezone-aware datetime")
            return dt
        return datetime.datetime.now(tz=datetime.UTC)

    @property
    def start_date(self) -> datetime.datetime:
        """Get the start date."""
        return datetime.datetime.fromtimestamp(self.start, tz=datetime.UTC)

    @property
    def end_date(self) -> datetime.datetime:
        """Get the end date."""
        return datetime.datetime.fromtimestamp(self.end, tz=datetime.UTC)

    @property
    def get_dict_isoformat(self) -> dict[str, float]:
        """Get the dictionary with ISO formatted timestamps."""
        return {
            datetime.datetime.fromtimestamp(x, tz=datetime.UTC).isoformat(): y
            for x, y in self.records
        }

    @property
    def yesterday_range(self) -> tuple[int, int]:
        """Get the range of yesterday."""
        end = self.start + (3600 * 24)
        return self.start, end

    @property
    def today_range(self) -> tuple[int, int]:
        """Get the range of today."""
        start = self.start + (3600 * 24)
        end = start + (3600 * 24)
        return start, end

    @property
    def tomorrow_range(self) -> tuple[int, int]:
        """Get the range of tomorrow."""
        start = self.start + (3600 * 48)
        end = start + (3600 * 24)
        return start, end

    @property
    def next_48_hours_range(self) -> tuple[int, int]:
        """Get the range of the next 48 hours."""
        start = int(self.dt_now.replace(minute=0, second=0, microsecond=0).timestamp())
        end = start + (3600 * 48)
        return start, end

    @property
    def next_hour_timestamp(self) -> tuple[int, int]:
        """Get the range of the next hour."""
        start = int(
            (
                self.dt_now.replace(minute=0, second=0, microsecond=0)
                + datetime.timedelta(hours=1)
            ).timestamp()
        )
        end = start + 3600
        return start, end

    @property
    def current_hour_timestamp(self) -> tuple[int, int]:
        """Get the range of the current hour."""
        start = int(self.dt_now.replace(minute=0, second=0, microsecond=0).timestamp())
        end = start + 3600
        return start, end

    @property
    def today_left_range(self) -> tuple[int, int]:
        """Get the range of today left."""
        start = int(self.dt_now.timestamp())
        end = int(
            (
                self.dt_now.replace(hour=0, minute=0, second=0, microsecond=0)
                + datetime.timedelta(days=1)
            ).timestamp()
        )
        return start, end

    @property
    def yesterday_total(self) -> float:
        """Get the total solar yield for yesterday."""
        return sum(
            y
            for x, y in self.records
            if self.yesterday_range[0] <= x < self.yesterday_range[1]
        )

    @property
    def yesterday_by_hour(self) -> dict[datetime.datetime, float]:
        """Get the solar yield for yesterday by hour."""
        return {
            datetime.datetime.fromtimestamp(x, tz=datetime.UTC): y
            for x, y in self.records
            if self.yesterday_range[0] <= x < self.yesterday_range[1]
        }

    @property
    def yesterday_peak_time(self) -> datetime.datetime:
        """Get the peak time for yesterday."""
        return sorted(
            [
                (datetime.datetime.fromtimestamp(x, tz=datetime.UTC), y)
                for x, y in self.records
                if self.yesterday_range[0] <= x < self.yesterday_range[1]
            ],
            key=lambda x: x[1],
            reverse=True,
        )[0][0]

    @property
    def today_total(self) -> float:
        """Get the total solar yield for today."""
        return sum(
            y for x, y in self.records if self.today_range[0] <= x < self.today_range[1]
        )

    @property
    def today_by_hour(self) -> dict[datetime.datetime, float]:
        """Get the solar yield for today by hour."""
        return {
            datetime.datetime.fromtimestamp(x, tz=datetime.UTC): y
            for x, y in self.records
            if self.today_range[0] <= x < self.today_range[1]
        }

    @property
    def today_peak_time(self) -> datetime.datetime:
        """Get the peak time for today."""
        return sorted(
            [
                (datetime.datetime.fromtimestamp(x, tz=datetime.UTC), y)
                for x, y in self.records
                if self.today_range[0] <= x < self.today_range[1]
            ],
            key=lambda x: x[1],
            reverse=True,
        )[0][0]

    @property
    def today_left_total(self) -> float:
        """Get the total solar yield for today left."""
        return sum(
            y
            for x, y in self.records
            if self.today_left_range[0] <= x < self.today_left_range[1]
        )

    @property
    def tomorrow_total(self) -> float:
        """Get the total solar yield for tomorrow."""
        return sum(
            y
            for x, y in self.records
            if self.tomorrow_range[0] <= x < self.tomorrow_range[1]
        )

    @property
    def tomorrow_by_hour(self) -> dict[datetime.datetime, float]:
        """Get the solar yield for tomorrow by hour."""
        return {
            datetime.datetime.fromtimestamp(x, tz=datetime.UTC): y
            for x, y in self.records
            if self.tomorrow_range[0] <= x < self.tomorrow_range[1]
        }

    @property
    def tomorrow_peak_time(self) -> datetime.datetime:
        """Get the peak time for tomorrow."""
        return sorted(
            [
                (datetime.datetime.fromtimestamp(x, tz=datetime.UTC), y)
                for x, y in self.records
                if self.tomorrow_range[0] <= x < self.tomorrow_range[1]
            ],
            key=lambda x: x[1],
            reverse=True,
        )[0][0]

    @property
    def current_hour_total(self) -> float:
        """Get the total solar yield for the current hour."""
        return sum(
            y
            for x, y in self.records
            if self.current_hour_timestamp[0] <= x < self.current_hour_timestamp[1]
        )

    @property
    def next_hour_total(self) -> float:
        """Get the total solar yield for the next hour."""
        return sum(
            y
            for x, y in self.records
            if self.next_hour_timestamp[0] <= x < self.next_hour_timestamp[1]
        )
