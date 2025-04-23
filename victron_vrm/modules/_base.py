from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from victron_vrm import VictronVRMClient


class BaseClientModule:
    """
    Base class for all client modules.
    """

    def __init__(self, client: "VictronVRMClient"):
        """
        Initialize the module with the client.

        :param client: The client instance.
        """
        self._client: "VictronVRMClient" = client
        assert hasattr(self, "BASE_URL"), "BASE_URL must be defined in the subclass"
