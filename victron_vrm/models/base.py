"""Base model for Victron Energy VRM API data models."""

from datetime import datetime
from typing import Any

from pydantic import BaseModel as PydanticBaseModel
from pydantic import field_serializer, model_validator


class BaseModel(PydanticBaseModel):
    """Base model for all Victron Energy VRM API data models."""

    @model_validator(mode="before")
    @classmethod
    def _convert_empty_strings_to_none(cls, data: Any) -> Any:
        """Convert empty strings to None."""
        if isinstance(data, dict):
            for key, value in data.items():
                if value == "":
                    data[key] = None
                elif isinstance(value, dict):
                    data[key] = cls._convert_empty_strings_to_none(value)
                elif isinstance(value, list):
                    data[key] = [
                        cls._convert_empty_strings_to_none(item)
                        if isinstance(item, dict)
                        else item
                        for item in value
                    ]
        return data

    @field_serializer("*")
    def serialize_datetime(self, value: Any, _info):
        """Serialize datetime objects to ISO format."""
        if isinstance(value, datetime):
            return value.isoformat()
        return value