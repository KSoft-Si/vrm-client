from victron_mqtt import Hub as VictronMQTTHub


class VRMMQTTClient(VictronMQTTHub):
    """VRM MQTT Client."""

    def __init__(
        self,
        host: str,
        username: str,
        password: str,
        vrm_id: str,
        port: int = 8883,
        use_ssl: bool = True,
    ):
        """Initialize VRM MQTT Client."""
        super().__init__(
            host=host,
            username=username,
            password=password,
            port=port,
            use_ssl=use_ssl,
            installation_id=vrm_id,
        )
