from pydantic_settings import SettingsConfigDict


def agent_config_dict():
    """Return the configuration dictionary for the agent."""
    return SettingsConfigDict(
        env_prefix="agent_", 
        env_nested_delimiter="__"
    )