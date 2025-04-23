"""System overview models for Victron Energy VRM API."""

from typing import Dict, List, Optional, Any, Union

from pydantic import Field, field_validator

from .base import BaseModel


class DeviceSetting(BaseModel):
    """Device setting model."""

    description: str = Field(..., description="Setting description")
    enum_data: Optional[List[Dict[str, Any]]] = Field(None, alias="enumData", description="Possible enums")
    

class SystemOverviewDevice(BaseModel):
    """System overview device model."""

    name: str = Field(..., description="Device name")
    custom_name: Optional[str] = Field(None, alias="customName", description="Custom device name")
    product_code: str = Field(..., alias="productCode", description="Device product code")
    product_name: str = Field(..., alias="productName", description="Device product name")
    site_id: int = Field(..., alias="idSite", description="Installation to which the device belongs")
    firmware_version: Optional[str] = Field(None, alias="firmwareVersion", description="Detailed firmware version information")
    last_connection: Optional[Union[str, bool]] = Field(None, alias="lastConnection", description="Device last connected timestamp, false if no timestamp available")
    device_class: Optional[str] = Field(None, alias="class", description="Styling field used for VRM")
    connection: Optional[str] = Field(None, description="Device connection string")
    instance: Optional[int] = Field(None, description="Installation instance to which this device belongs")
    device_type_id: Optional[int] = Field(None, alias="idDeviceType", description="Device type id")
    settings: Optional[List[DeviceSetting]] = Field(None, description="Device settings")

    @field_validator("site_id", "instance", "device_type_id", mode="before")
    @classmethod
    def convert_id_to_int(cls, value):
        """Convert ID fields to integers."""
        if isinstance(value, str) and value.isdigit():
            return int(value)
        return value


class SystemOverview(BaseModel):
    """System overview model."""

    devices: List[SystemOverviewDevice] = Field(default_factory=list, description="List of devices")