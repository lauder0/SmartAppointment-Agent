"""Application-level settings."""


class AppSettings:
    """Lightweight settings object for values shared across modules."""

    agent_backend: str = "langgraph"


settings = AppSettings()
