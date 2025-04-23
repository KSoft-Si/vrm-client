"""Measurement models for Victron Energy VRM API."""

from datetime import datetime
from typing import Dict, List, Optional, Any, Union

from pydantic import Field, field_validator

from .base import BaseModel


class Measurement(BaseModel):
    """Victron Energy measurement model."""

    id: Optional[int] = Field(None, description="Measurement ID")
    device_id: int = Field(..., description="Device ID the measurement belongs to")
    instance_id: Optional[int] = Field(None, description="Device instance ID")
    timestamp: datetime = Field(..., description="Measurement timestamp")
    type: str = Field(..., description="Measurement type")
    value: Union[float, int, str, bool] = Field(..., description="Measurement value")
    unit: Optional[str] = Field(None, description="Measurement unit")
    description: Optional[str] = Field(None, description="Measurement description")
    category: Optional[str] = Field(None, description="Measurement category")
    attributes: Optional[Dict[str, Any]] = Field(None, description="Additional attributes")

    @field_validator("id", "device_id", "instance_id", mode="before")
    @classmethod
    def convert_id_to_int(cls, value):
        """Convert ID fields to integers."""
        if isinstance(value, str) and value.isdigit():
            return int(value)
        return value

    @field_validator("value", mode="before")
    @classmethod
    def convert_value(cls, value):
        """Convert value to appropriate type."""
        if isinstance(value, str):
            # Try to convert to number if possible
            try:
                if "." in value:
                    return float(value)
                else:
                    return int(value)
            except ValueError:
                # Check for boolean values
                if value.lower() in ("true", "yes", "1"):
                    return True
                elif value.lower() in ("false", "no", "0"):
                    return False
        return value


class MeasurementList(BaseModel):
    """List of Victron Energy measurements."""

    measurements: List[Measurement] = Field(default_factory=list, description="List of measurements")
    total: int = Field(0, description="Total number of measurements")
    page: Optional[int] = Field(None, description="Current page number")
    per_page: Optional[int] = Field(None, description="Number of items per page")
    total_pages: Optional[int] = Field(None, description="Total number of pages")
    start_timestamp: Optional[datetime] = Field(None, description="Start timestamp of the data range")
    end_timestamp: Optional[datetime] = Field(None, description="End timestamp of the data range")