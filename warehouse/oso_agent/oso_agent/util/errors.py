class AgentError(Exception):
    """Base exception for agent-related errors."""
    pass

class AgentMissingError(AgentError):
    """Exception for non-existent agent errors."""
    pass

class AgentConfigError(AgentError):
    """Exception for configuration-related errors."""
    pass

class AgentRuntimeError(AgentError):
    """Exception for agent runtime errors."""
    pass
