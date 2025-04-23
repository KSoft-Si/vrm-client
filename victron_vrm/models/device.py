"""Device models for Victron Energy VRM API."""

from datetime import datetime
from typing import Dict, List, Optional, Any

from pydantic import Field, field_validator

from .base import BaseModel


class Device(BaseModel):
    """Victron Energy device model."""

    id: int = Field(..., description="Device ID")
    instance_id: int = Field(..., description="Device instance ID")
    site_id: int = Field(..., description="Site ID the device belongs to")
    name: str = Field(..., description="Device name")
    device_type: str = Field(..., description="Device type")
    model_name: Optional[str] = Field(None, description="Device model name")
    firmware_version: Optional[str] = Field(None, description="Device firmware version")
    hardware_version: Optional[str] = Field(None, description="Device hardware version")
    serial_number: Optional[str] = Field(None, description="Device serial number")
    last_seen: Optional[datetime] = Field(None, description="Last time device was seen online")
    status: Optional[str] = Field(None, description="Device status")
    connection_type: Optional[str] = Field(None, description="Device connection type")
    custom_name: Optional[str] = Field(None, description="User-defined device name")
    custom_group: Optional[str] = Field(None, description="User-defined device group")
    custom_icon: Optional[str] = Field(None, description="User-defined device icon")
    parameters: Optional[Dict[str, Any]] = Field(None, description="Device parameters")
    created_at: Optional[datetime] = Field(None, description="Device creation timestamp")
    updated_at: Optional[datetime] = Field(None, description="Device last update timestamp")

    @field_validator("id", "instance_id", "site_id", mode="before")
    @classmethod
    def convert_id_to_int(cls, value):
        """Convert ID fields to integers."""
        if isinstance(value, str) and value.isdigit():
            return int(value)
        return value


class DeviceList(BaseModel):
    """List of Victron Energy devices."""

    devices: List[Device] = Field(default_factory=list, description="List of devices")
    total: int = Field(0, description="Total number of devices")
    page: Optional[int] = Field(None, description="Current page number")
    per_page: Optional[int] = Field(None, description="Number of items per page")
    total_pages: Optional[int] = Field(None, description="Total number of pages")