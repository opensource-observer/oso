import logging
import typing as t

from pydantic import Field, SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict

ENV_PREFIX = "mcp_"
ENV_NESTED_DELIMITER = "__" 

def mcp_config_dict():
    """Return the configuration dictionary for the MCP server."""
    return SettingsConfigDict(
        env_prefix=ENV_PREFIX, 
        env_nested_delimiter=ENV_NESTED_DELIMITER
    )


class MCPConfig(BaseSettings):
    """Configuration for the MCP server."""

    model_config = mcp_config_dict()

    oso_api_key: SecretStr = Field(
        default=SecretStr(""), 
        description="API key for the OSO API",
        json_schema_extra={"required": True} # This is the key to make the field required
    )

    host: str = Field(
        default="127.0.0.1",
        description="Host for the mcp server to run on",
    )

    port: int = Field(
        default=8000, description="Port for the mcp server to run on"
    )

    transport: t.Literal['sse', 'stdio'] = Field(
        default="sse",
        description="The MCP transport.",
    )

    def __init__(self, **kwargs):
        """Initialize MCPConfig with enhanced error reporting."""
        super().__init__(**kwargs)
        self._log_configuration_status()
    
    def _get_env_var_name(self, field_name: str) -> str:
        """Get the actual environment variable name for a field."""
        return f"{ENV_PREFIX.upper()}{field_name.upper()}"
    
    def _log_configuration_status(self):
        """Log the environment variables on startup."""
        logger = logging.getLogger("oso-mcp")
        
        logger.info("=" * 50)
        logger.info("MCP Server Environment Variables")
        logger.info("=" * 50)

        for field_name, field_info in self.__class__.model_fields.items():
            env_var = self._get_env_var_name(field_name)
            value = getattr(self, field_name)
            
            # Check if field is required by looking at custom metadata
            json_extra = field_info.json_schema_extra
            is_required = (isinstance(json_extra, dict) and 
                          json_extra.get("required", False))
                    
            if isinstance(value, SecretStr):
                if value.get_secret_value():
                    logger.info(f"{env_var} = [SECRET SET]")
                    logger.debug(f"    (DEBUG): {value.get_secret_value()}")
                else:
                    if is_required:
                        logger.error(f"{env_var} = MISSING (REQUIRED)")
                    else:
                        logger.warning(f"{env_var} = MISSING (OPTIONAL)")
                    logger.debug("    (DEBUG): [EMPTY]")
            else:
                if value is not None:
                    logger.info(f"{env_var} = {value}")
                    # check if the value is the default value
                    if value == field_info.default:
                        logger.debug("    (DEBUG): [DEFAULT]")
                    else:
                        logger.debug("    (DEBUG): [SET]")
                else:
                    if is_required:
                        logger.error(f"{env_var} = MISSING (REQUIRED)")
                    else:
                        logger.warning(f"{env_var} = MISSING (OPTIONAL)")
                    
        
        logger.info("=" * 50)
    
    @classmethod
    def print_env_schema(cls):
        """Print the environment variable setup for this config."""
        print("=" * 50)
        print("MCP Server Environment Setup")
        print("=" * 50)
        
        for field_name, field_info in cls.model_fields.items():
            env_var = f"MCP_{field_name.upper()}"
            
            # Check if field is required by looking at custom metadata
            json_extra = field_info.json_schema_extra
            is_required = (isinstance(json_extra, dict) and 
                          json_extra.get("required_for_operation", False))
            
            if is_required:
                print(f"{env_var}: REQUIRED")
            else:
                # Get the default value
                default_value = field_info.default
                if isinstance(default_value, SecretStr):
                    default_display = "[empty secret]"
                else:
                    default_display = str(default_value)
                print(f"{env_var}: OPTIONAL (DEFAULT={default_display})")
        
        print("=" * 50)
