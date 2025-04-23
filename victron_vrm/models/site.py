"""Site models for Victron Energy VRM API."""

from datetime import datetime
from typing import Dict, List, Optional, Any

from pydantic import Field, field_validator

from .base import BaseModel


class SitePerrmission(BaseModel):
    """Victron Energy site view permissions model."""

    update_settings: bool
    settings: bool
    diagnostics: bool
    share: bool
    vnc: bool
    mqtt_rpc: bool
    vebus: bool
    two_way: bool = Field(..., alias="twoway")
    exact_location: bool
    nodered: bool
    nodered_dash: bool
    signalk: bool


class SiteImage(BaseModel):
    """Victron Energy site images model."""

    id: int = Field(..., alias="idSiteImage", description="Image ID")
    url: str = Field(..., description="Image URL")
    name: str = Field(..., alias="imageName", description="Image name")


class SiteTag(BaseModel):
    """Victron Energy site tags model."""

    id: int = Field(..., alias="idTag", description="Tag ID")
    name: str = Field(..., description="Tag name")
    automatic: str = Field(..., description="If tag is automatic")


class Site(BaseModel):
    """Victron Energy installation site model."""

    id: int = Field(..., alias="idSite", description="Site ID")
    access_level: Optional[int] = Field(
        None, alias="accessLevel", description="User's access level to this site"
    )
    name: str = Field(..., description="Site name")
    owner_id: Optional[int] = Field(None, alias="idUser", description="Site owner ID")
    identifier: str = Field(..., description="Site identifier")
    pv_max: Optional[int] = Field(0, alias="pvMax", description="Site PV max value")
    timezone: str = Field(..., description="Site timezone")
    phone_number: Optional[str] = Field(
        None, alias="phonenumber", description="Site phone number"
    )
    notes: Optional[str] = Field(None, description="Site notes")
    geofence: Optional[str] = Field(None, description="Site geofence data")
    geofence_enabled: bool = Field(
        ..., alias="geofenceEnabled", description="Whether geofence is enabled"
    )
    location: Optional[Dict] = Field(None, description="Site location data")
    realtime_updates: bool = Field(
        ..., alias="realtimeUpdates", description="Whether realtime updates are enabled"
    )
    has_mains: bool = Field(..., alias="hasMains", description="Whether site has mains")
    has_generator: bool = Field(
        ..., alias="hasGenerator", description="Whether site has generator"
    )
    no_data_alarm_timeout: Optional[int] = Field(
        None, alias="noDataAlarmTimeout", description="No data alarm timeout in minutes"
    )
    alarm_monitoring: int = Field(
        ..., alias="alarmMonitoring", description="Whether alarm monitoring is enabled"
    )
    is_admin: Optional[bool] = Field(
        None, description="Whether user is admin for this site"
    )
    owner: Optional[bool] = Field(
        None, description="Whether user is owner of this site"
    )
    invalid_vrm_auth_token_used_in_log_request: bool = Field(
        ...,
        alias="invalidVRMAuthTokenUsedInLogRequest",
        description="Whether invalid VRM auth token was used in log request",
    )
    created_at: datetime = Field(
        ..., alias="syscreated", description="System created date"
    )
    shared: bool = Field(..., description="Whether site is shared")
    device_icon: Optional[str] = Field(
        None, alias="deviceIcon", description="Device icon for the site"
    )

    # Fields included only in the extended version
    alarm: Optional[bool] = Field(None, description="Whether alarm is enabled")
    last_timestamp: Optional[datetime] = Field(
        None, alias="lastTimestamp", description="Last timestamp of data"
    )
    current_time: Optional[str] = Field(
        None, alias="currentTime", description="Current time of the site in hh:mm"
    )
    timezone_offset: Optional[int] = Field(
        None, alias="timezoneOffset", description="Timezone offset in minutes"
    )
    demo_mode: Optional[bool] = Field(
        None, alias="demoMode", description="Whether demo mode is enabled"
    )
    mqtt_webhost: Optional[str] = Field(
        None, alias="mqttWebhost", description="MQTT web host"
    )
    mqtt_hostname: Optional[str] = Field(
        None, alias="mqttHost", description="MQTT hostname"
    )
    high_workload: Optional[bool] = Field(
        None, alias="highWorkload", description="Whether high workload is enabled"
    )
    current_alarms: Optional[List[str]] = Field(
        None, alias="currentAlarms", description="List of current alarms"
    )
    number_of_alarms: Optional[int] = Field(
        None, alias="num_alarms", description="Number of alarms"
    )
    avatar_url: Optional[str] = Field(
        None, alias="avatarUrl", description="Avatar URL for the site"
    )
    tags: Optional[List[SiteTag]] = Field(
        [], description="List of tags associated with the site"
    )
    images: Optional[List[SiteImage]] = Field(
        [], description="List of images associated with the site"
    )
    view_permissions: Optional[List[SitePerrmission]] = Field([])
    extended: Optional[List[Dict[str, Any]]] = Field(
        [], description="Extended information about the site"
    )

    @field_validator("id", "owner_id", mode="before")
    @classmethod
    def convert_id_to_int(cls, value):
        """Convert ID fields to integers."""
        if isinstance(value, str) and value.isdigit():
            return int(value)
        return value
