"""Diagnostics models for Victron Energy VRM API."""

from typing import List, Optional, Union

from pydantic import Field, field_validator

from .base import BaseModel


class DiagnosticsEnumValue(BaseModel):
    """Enum value model for diagnostics."""

    name: str = Field(..., alias="nameEnum", description="Enum name")
    value: int = Field(..., alias="valueEnum", description="Numeric enum value")


class DiagnosticsRecord(BaseModel):
    """Diagnostics record model."""

    site_id: int = Field(..., alias="idSite", description="Installation id")
    timestamp: int = Field(..., description="Timestamp at which this data was logged")
    device: str = Field(..., alias="Device", description="Logging device name")
    instance: int = Field(..., description="Log data instance")
    data_attribute_id: int = Field(..., alias="idDataAttribute", description="Log data attribute id")
    description: str = Field(..., description="Log data description")
    format_with_unit: str = Field(..., alias="formatWithUnit", description="Data attribute string format")
    dbus_service_type: Optional[str] = Field(None, alias="dbusServiceType", description="Device DBus Service type")
    dbus_path: Optional[str] = Field(None, alias="dbusPath", description="Device DBus path")
    code: str = Field(..., description="Data attribute code")
    bitmask: int = Field(..., description="1 if the data attribute is a bitmask, else 0")
    formatted_value: str = Field(..., alias="formattedValue", description="Log data value formatted as a string")
    raw_value: Union[str, int] = Field(..., alias="rawValue", description="Log data raw value")
    id: int = Field(..., description="Log data id")
    data_attribute_enum_values: Optional[List[DiagnosticsEnumValue]] = Field(
        None, alias="dataAttributeEnumValues", description="Data attribute enum values, only for data attributes of type enum"
    )

    @field_validator("site_id", "instance", "data_attribute_id", "bitmask", "id", mode="before")
    @classmethod
    def convert_id_to_int(cls, value):
        """Convert ID fields to integers."""
        if isinstance(value, str) and value.isdigit():
            return int(value)
        return value


class DiagnosticsList(BaseModel):
    """List of diagnostics records."""

    records: List[DiagnosticsRecord] = Field(default_factory=list, description="List of diagnostics records")
    total: int = Field(0, description="Total number of records")
    page: Optional[int] = Field(None, description="Current page number")
    per_page: Optional[int] = Field(None, description="Number of items per page")
    total_pages: Optional[int] = Field(None, description="Total number of pages")