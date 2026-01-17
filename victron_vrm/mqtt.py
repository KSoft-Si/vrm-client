from victron_mqtt import Hub as VictronMQTTHub, OperationMode


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
        update_frequency: int | None = None,
        operation_mode: OperationMode = OperationMode.FULL,
    ):
        """Initialize VRM MQTT Client."""
        # Safe update_frequency values between 0 and 300 seconds
        if isinstance(update_frequency, int):
            update_frequency = max(0, min(update_frequency, 300))
        super().__init__(
            host=host,
            username=username,
            password=password,
            port=port,
            use_ssl=use_ssl,
            installation_id=vrm_id,
            update_frequency_seconds=update_frequency,
            operation_mode=operation_mode,
        )
