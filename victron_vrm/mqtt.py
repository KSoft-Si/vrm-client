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
        """Initialize a VRM MQTT client for a specific installation.

        if update_frequency is not None:
            if not isinstance(update_frequency, int):
                raise TypeError("update_frequency must be an int or None")
            host: MQTT broker hostname or IP address.
            username: Username used to authenticate with the MQTT broker.
            password: Password used to authenticate with the MQTT broker.
            vrm_id: VRM installation identifier to subscribe/publish for.
            port: TCP port of the MQTT broker. Defaults to ``8883``.
            use_ssl: Whether to use SSL/TLS for the MQTT connection.
                Defaults to ``True``.
            update_frequency: Optional update frequency in seconds for
                periodic updates. If provided, values are clamped between
                0 and 3600 seconds. ``None`` (the default) lets the
                underlying :class:`victron_mqtt.Hub` use its own default
                update frequency.
            operation_mode: Operation mode for the MQTT client, controlling
                how data is fetched and published. Must be a member of
                :class:`victron_mqtt.OperationMode`. Defaults to
                :data:`OperationMode.FULL`.
        """
        # Safe update_frequency values between 0 and 3600 seconds
        if isinstance(update_frequency, int):
            update_frequency = max(0, min(update_frequency, 3600))
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
