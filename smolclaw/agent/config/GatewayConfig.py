"""Gateway configuration."""


class GatewayConfig:
    def __init__(self):
        self.host: str = "0.0.0.0"
        self.port: int = 8000
        self.max_connections: int = 10
        self.ping_interval: int = 30
        self.ping_timeout: int = 10
        self.max_message_size: int = 1048576
