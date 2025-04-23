from typing import Iterable

from pydantic import BaseModel, Field


class VRMAttribute(BaseModel):
    code: str
    description: str
    format_with_unit: str = Field(..., alias="formatWithUnit")
    data_type: str = Field(..., alias="dataType")

    def format_value(self, value):
        """
        Format the value based on the attribute's format_with_unit.
        This is a placeholder for actual formatting logic.
        """
        # Example formatting logic
        if self.data_type == "number":
            if not isinstance(value, (int, float)):
                try:
                    value = float(value)
                except ValueError as err:
                    raise ValueError("Invalid value for number type") from err
            return self.format_with_unit % value
        elif self.data_type == "float":
            if not isinstance(value, (int, float)):
                try:
                    value = float(value)
                except ValueError as err:
                    raise ValueError("Invalid value for float type") from err
            return self.format_with_unit % value
        elif self.data_type == "string" or self.data_type == "enum":
            return self.format_with_unit % value
        # Add more formatting options as needed
        return value


class VRMAttributes:
    """
    Filtered and sorted attributes from VRM API.
    """

    def __init__(self, attributes: dict):
        self.attributes = {x: VRMAttribute(**y) for x, y in attributes.items()}

        # Search dictionaries:
        self._by_code = {x.code: x for x in self.attributes.values()}

    def __getitem__(self, item) -> VRMAttribute:
        return self.attributes[item]

    def __iter__(self) -> Iterable[VRMAttribute]:
        return iter(self.attributes.values())

    def __len__(self):
        return len(self.attributes)

    def __repr__(self):
        return f"VRMAttributes({self.attributes})"

    def get_by_code(self, code) -> VRMAttribute | None:
        """
        Get attribute by code.
        """
        return self._by_code.get(code)
