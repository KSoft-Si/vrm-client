from datetime import datetime, timedelta

import pytz


def is_dt_timezone_aware(dt: datetime) -> bool:
    """
    Check if a datetime object is timezone-aware.

    Args:
        dt (datetime): The datetime object to check.

    Returns:
        bool: True if the datetime object is timezone-aware, False otherwise.
    """
    return dt.tzinfo is not None and dt.tzinfo.utcoffset(dt) is not None


def get_local_utc_offset() -> timedelta:
    """
    Get the local UTC offset.

    Returns:
        timedelta: The local UTC offset.
    """
    now = datetime.now()
    local_timezone = datetime.now().astimezone().tzinfo
    return local_timezone.utcoffset(now)


def dt_now() -> datetime:
    """
    Get the current UTC datetime.

    Returns:
        datetime: The current UTC datetime.
    """
    return datetime.now(tz=pytz.FixedOffset(get_local_utc_offset().seconds // 60))
