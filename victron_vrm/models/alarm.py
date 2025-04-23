"""Alarm models for Victron Energy VRM API."""

from datetime import datetime
from typing import List, Optional, Any

from pydantic import Field, field_validator

from .base import BaseModel


class Attribute(BaseModel):
    """Data attribute model for alarms."""

    id: int = Field(..., alias="idDataAttribute", description="Data attribute ID")
    code: str = Field(..., description="Data attribute code")
    description: str = Field(..., description="Data attribute description")
    target_table: Optional[str] = Field(
        None, alias="targetTable", description="Target table"
    )
    device_type_id: Optional[int] = Field(
        None, alias="idDeviceType", description="Device type ID"
    )
    format_with_unit: Optional[str] = Field(
        None, alias="formatWithUnit", description="Format with unit"
    )
    data_type: Optional[str] = Field(None, alias="dataType", description="Data type")
    enum_values: Optional[Any] = Field(
        None, alias="enumValues", description="Enum values"
    )

    @field_validator("id", "device_type_id", mode="before")
    @classmethod
    def convert_id_to_int(cls, value):
        """Convert ID fields to integers."""
        if isinstance(value, str) and value.isdigit():
            return int(value)
        return value


class AlarmSettings(BaseModel):
    """Float alarm model."""

    alarm_enabled: int = Field(..., alias="AlarmEnabled", description="Alarm enabled")
    notify_after_seconds: int = Field(
        ..., alias="NotifyAfterSeconds", description="Notify after seconds"
    )
    high_alarm: Optional[float] = Field(
        None, alias="highAlarm", description="High alarm threshold"
    )
    high_alarm_hysteresis: Optional[float] = Field(
        None, alias="highAlarmHysteresis", description="High alarm hysteresis"
    )
    data_attribute_id: int = Field(
        ..., alias="idDataAttribute", description="Data attribute ID"
    )
    instance: int = Field(..., description="Instance")
    low_alarm: Optional[float] = Field(
        None, alias="lowAlarm", description="Low alarm threshold"
    )
    low_alarm_hysteresis: Optional[float] = Field(
        None, alias="lowAlarmHysteresis", description="Low alarm hysteresis"
    )
    data_attribute_limit_id: Optional[int] = Field(
        None, alias="idDataAttributeLimit", description="Data attribute limit ID"
    )

    @field_validator(
        "data_attribute_id", "instance", "data_attribute_limit_id", mode="before"
    )
    @classmethod
    def convert_id_to_int(cls, value):
        """Convert ID fields to integers."""
        if isinstance(value, str) and value.isdigit():
            return int(value)
        return value


class AlarmUser(BaseModel):
    """User model for alarms."""

    id: int = Field(..., alias="idUser", description="User ID")
    site_id: int = Field(..., alias="idSite", description="Site ID")
    access_level: int = Field(..., alias="accessLevel", description="Access level")
    receives_alarm_notifications: int = Field(
        ...,
        alias="receivesAlarmNotifications",
        description="Receives alarm notifications",
    )
    receives_reports: int = Field(
        ..., alias="receivesReports", description="Receives reports"
    )
    email: str = Field(..., description="Email")
    name: str = Field(..., description="Name")
    avatar_url: Optional[str] = Field(
        None, alias="avatar_url", description="Avatar URL"
    )
    muted: bool = Field(..., description="Muted")

    @field_validator(
        "id",
        "site_id",
        "access_level",
        "receives_alarm_notifications",
        "receives_reports",
        mode="before",
    )
    @classmethod
    def convert_id_to_int(cls, value):
        """Convert ID fields to integers."""
        if isinstance(value, str) and value.isdigit():
            return int(value)
        return value


class AlarmDevice(BaseModel):
    """Device model for alarms."""

    site_id: int = Field(..., alias="idSite", description="Site ID")
    instance: int = Field(..., description="Instance")
    last_connection: Optional[datetime] = Field(
        None, alias="lastConnection", description="Last connection timestamp"
    )
    seconds_ago: Optional[int] = Field(
        None, alias="secondsAgo", description="Seconds ago"
    )
    is_valid: Optional[int] = Field(None, alias="isValid", description="Is valid")
    device_type_id: Optional[int] = Field(
        None, alias="idDeviceType", description="Device type ID"
    )
    device_name: str = Field(..., alias="deviceName", description="Device name")
    product_id_as_received: Optional[int] = Field(
        None, alias="productIdAsReceived", description="Product ID as received"
    )
    product_name: str = Field(..., alias="productName", description="Product name")
    custom_product_name: Optional[str] = Field(
        None, alias="customProductName", description="Custom product name"
    )
    firmware_version: Optional[str] = Field(
        None, alias="firmwareVersion", description="Firmware version"
    )
    connection: Optional[str] = Field(None, description="Connection")
    custom_name: Optional[str] = Field(
        None, alias="customName", description="Custom name"
    )
    identifier: Optional[str] = Field(None, description="Identifier")

    @field_validator(
        "site_id", "instance", "device_type_id", "product_id_as_received", mode="before"
    )
    @classmethod
    def convert_id_to_int(cls, value):
        """Convert ID fields to integers."""
        if isinstance(value, str) and value.isdigit():
            return int(value)
        return value


class Alarms(BaseModel):
    """Alarms model."""

    alarms: List[AlarmSettings] = Field(
        default_factory=list, description="List of alarms"
    )
    devices: List[AlarmDevice] = Field(
        default_factory=list, description="List of devices"
    )
    users: List[AlarmUser] = Field(default_factory=list, description="List of users")
    attributes: List[Attribute] = Field(
        default_factory=list, description="List of attributes"
    )
    rate_limited: Optional[bool] = Field(
        None, alias="rateLimited", description="Rate limited"
    )
