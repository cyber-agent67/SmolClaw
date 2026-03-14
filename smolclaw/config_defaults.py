"""Default configuration values for SmolClaw."""

DEFAULT_CONFIG: dict = {
    "agents": {
        "defaults": {
            "model": "openai/gpt-4o",
            "max_tokens": 8192,
            "temperature": 0.1,
            "max_iterations": 10,
        }
    },
    "gateway": {
        "host": "0.0.0.0",
        "port": 18790,
    },
    "browser": {
        "headless": False,
        "window_width": 1280,
        "window_height": 900,
    },
    "tools": {
        "exec": {
            "timeout": 30,
        }
    },
    "memory": {
        "max_history": 50,
        "consolidation_threshold": 100,
    },
}
