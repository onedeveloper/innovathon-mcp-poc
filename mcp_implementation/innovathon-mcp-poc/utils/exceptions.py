"""
Custom exceptions for the MCP Server/Client application.

This module defines custom exceptions for different error scenarios
to enable more specific error handling throughout the application.
"""
import logging

# Set up logging
logger = logging.getLogger(__name__)

class MCPError(Exception):
    """Base exception class for all MCP application errors."""
    
    def __init__(self, message: str, *args, **kwargs):
        super().__init__(message, *args, **kwargs)
        logger.error(f"{self.__class__.__name__}: {message}")


class ConfigurationError(MCPError):
    """Exception raised for errors in the application configuration."""
    pass


class DatabaseError(MCPError):
    """Exception raised for database-related errors."""
    pass


class ToolExecutionError(MCPError):
    """Exception raised when a tool execution fails."""
    
    def __init__(self, tool_name: str, message: str, *args, **kwargs):
        self.tool_name = tool_name
        super().__init__(f"Error executing tool '{tool_name}': {message}", *args, **kwargs)


class ToolParsingError(MCPError):
    """Exception raised when parsing tool calls fails."""
    pass


class AgentError(MCPError):
    """Exception raised for agent-related errors."""
    
    def __init__(self, agent_name: str, message: str, *args, **kwargs):
        self.agent_name = agent_name
        super().__init__(f"Error in agent '{agent_name}': {message}", *args, **kwargs)


class AgentInitializationError(AgentError):
    """Exception raised when agent initialization fails."""
    
    def __init__(self, agent_name: str, message: str, *args, **kwargs):
        super().__init__(agent_name, f"Initialization failed: {message}", *args, **kwargs)


class AgentRegistrationError(AgentError):
    """Exception raised when agent registration fails."""
    
    def __init__(self, agent_name: str, message: str, *args, **kwargs):
        super().__init__(agent_name, f"Registration failed: {message}", *args, **kwargs)


class ModelError(MCPError):
    """Exception raised for model-related errors."""
    
    def __init__(self, model_name: str, message: str, *args, **kwargs):
        self.model_name = model_name
        super().__init__(f"Error with model '{model_name}': {message}", *args, **kwargs)


class ModelConnectionError(ModelError):
    """Exception raised when connection to the model service fails."""
    
    def __init__(self, model_name: str, message: str, *args, **kwargs):
        super().__init__(model_name, f"Connection failed: {message}", *args, **kwargs)


class ModelResponseError(ModelError):
    """Exception raised when the model response is invalid or unexpected."""
    
    def __init__(self, model_name: str, message: str, *args, **kwargs):
        super().__init__(model_name, f"Invalid response: {message}", *args, **kwargs)


class TimeoutError(MCPError):
    """Exception raised when an operation times out."""
    
    def __init__(self, operation: str, timeout: float, *args, **kwargs):
        self.operation = operation
        self.timeout = timeout
        super().__init__(f"Operation '{operation}' timed out after {timeout} seconds", *args, **kwargs)
