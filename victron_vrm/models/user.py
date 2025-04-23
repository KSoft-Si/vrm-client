from typing import Optional

from pydantic import Field, field_validator

from .base import BaseModel


class User(BaseModel):
    id: int = Field(..., description="User ID")
    name: str = Field(..., description="User name")
    email: str = Field(..., description="User email")
    country: str = Field(..., description="User country")
    id_access_token: Optional[int] = Field(
        None, alias="idAccessToken", description="User access token ID"
    )

    @field_validator("id", "id_access_token", mode="before")
    @classmethod
    def convert_id_to_int(cls, value):
        """Convert ID fields to integers."""
        if isinstance(value, str) and value.isdigit():
            return int(value)
        return value
