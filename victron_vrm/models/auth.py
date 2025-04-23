"""Authentication models for Victron Energy VRM API."""

from datetime import datetime, timedelta
from typing import Optional

from pydantic import Field, field_validator

from .base import BaseModel


class AuthToken(BaseModel):
    """Authentication token model."""

    access_token: str = Field(..., description="OAuth2 access token")
    token_type: str = Field(..., description="Token type, usually 'Bearer'")
    expires_in: int = Field(..., description="Token expiration time in seconds")
    refresh_token: Optional[str] = Field(None, description="OAuth2 refresh token")
    scope: str = Field(..., description="Token scope")
    created_at: datetime = Field(
        default_factory=datetime.now, description="Token creation timestamp"
    )

    @property
    def expires_at(self) -> datetime:
        """Calculate token expiration datetime."""
        return self.created_at + timedelta(seconds=self.expires_in)

    @property
    def is_expired(self) -> bool:
        """Check if the token is expired."""
        return datetime.now() > self.expires_at

    @property
    def authorization_header(self) -> str:
        """Get authorization header value."""
        return f"{self.token_type} {self.access_token}"


class AccessToken(BaseModel):
    """Access token model."""

    id: int = Field(..., alias="idAccessToken", description="Access token ID")
    name: str = Field(..., description="Access token name")
    scope: str = Field(..., description="Access token scope")
    expires_at: datetime = Field(
        ..., alias="expires", description="Token expiration time in seconds"
    )
    created_at: datetime = Field(
        ..., alias="createdOn", description="Token creation timestamp"
    )

    @field_validator("id", mode="before")
    @classmethod
    def convert_id_to_int(cls, value):
        """Convert ID fields to integers."""
        if isinstance(value, str) and value.isdigit():
            return int(value)
        return value
