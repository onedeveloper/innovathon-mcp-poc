"""
Server factory for the MCP Server/Client application.

This module provides a factory for creating and configuring MCP servers
with registered agents and tools.
"""
from typing import List, Dict, Any, Optional, Callable
import importlib
import logging
from mcp.server.fastmcp import FastMCP
from .registry import AgentRegistry

# Set up logging
logger = logging.getLogger(__name__)

class MCPServerFactory:
    """
    Factory for creating and configuring MCP servers.
    
    This class provides methods for creating MCP servers with
    registered agents and tools.
    """
    
    @staticmethod
    def create_server(name: str, agent_modules: List[str]) -> FastMCP:
        """
        Create and configure an MCP server with the specified agents.
        
        Args:
            name: The name of the server
            agent_modules: A list of agent module paths to load
            
        Returns:
            A configured FastMCP server instance
        """
        # Create the MCP server
        logger.info(f"Creating MCP server: {name}")
        mcp = FastMCP(name)
        
        # Get the registry
        registry = AgentRegistry()
        
        # Load and initialize agents
        for agent_module in agent_modules:
            try:
                logger.info(f"Loading agent module: {agent_module}")
                
                # Import the agent module
                module_parts = agent_module.split('.')
                if len(module_parts) > 1:
                    # For module paths like 'agents.sql_agent.SQLAgent'
                    module_path = '.'.join(module_parts[:-1])
                    class_name = module_parts[-1]
                    module = importlib.import_module(module_path)
                    agent_class = getattr(module, class_name)
                else:
                    # For simple module names like 'SQLAgent'
                    # Assume it's in a default location
                    module = importlib.import_module(f"agents.{agent_module.lower()}")
                    agent_class = getattr(module, agent_module)
                
                # Create an instance of the agent
                agent = agent_class()
                
                # Register the agent
                registry.register_agent(agent_module, agent)
                
                # Initialize the agent
                agent.initialize()
                
                # Register the agent's tools
                agent.register_tools()
                
                logger.info(f"Successfully loaded and initialized agent: {agent_module}")
            except (ImportError, AttributeError) as e:
                logger.error(f"Error loading agent {agent_module}: {e}")
        
        # Register all tools with the MCP server
        tools = registry.get_all_tools()
        for name, tool_info in tools.items():
            logger.info(f"Registering tool with MCP server: {name}")
            
            # Create a wrapper function to call the tool function
            def create_tool_wrapper(tool_func):
                def wrapper(*args, **kwargs):
                    return tool_func(*args, **kwargs)
                return wrapper
            
            # Register the tool with the MCP server
            wrapper = create_tool_wrapper(tool_info["function"])
            mcp.tool(
                name=name,
                description=tool_info["description"],
                input_schema=tool_info["schema"]
            )(wrapper)
        
        return mcp
    
    @staticmethod
    def register_additional_agent(mcp: FastMCP, agent_module: str) -> bool:
        """
        Register an additional agent with an existing MCP server.
        
        Args:
            mcp: The MCP server to register the agent with
            agent_module: The agent module path to load
            
        Returns:
            True if the agent was successfully registered, False otherwise
        """
        try:
            logger.info(f"Loading additional agent module: {agent_module}")
            
            # Get the registry
            registry = AgentRegistry()
            
            # Import the agent module
            module_parts = agent_module.split('.')
            if len(module_parts) > 1:
                module_path = '.'.join(module_parts[:-1])
                class_name = module_parts[-1]
                module = importlib.import_module(module_path)
                agent_class = getattr(module, class_name)
            else:
                module = importlib.import_module(f"agents.{agent_module.lower()}")
                agent_class = getattr(module, agent_module)
            
            # Create an instance of the agent
            agent = agent_class()
            
            # Register the agent
            registry.register_agent(agent_module, agent)
            
            # Initialize the agent
            agent.initialize()
            
            # Register the agent's tools
            agent.register_tools()
            
            # Register the agent's tools with the MCP server
            tools = registry.get_all_tools()
            for name, tool_info in tools.items():
                # Only register tools that haven't been registered yet
                if not mcp.has_tool(name):
                    logger.info(f"Registering tool with MCP server: {name}")
                    
                    # Create a wrapper function to call the tool function
                    def create_tool_wrapper(tool_func):
                        def wrapper(*args, **kwargs):
                            return tool_func(*args, **kwargs)
                        return wrapper
                    
                    # Register the tool with the MCP server
                    wrapper = create_tool_wrapper(tool_info["function"])
                    mcp.tool(
                        name=name,
                        description=tool_info["description"],
                        input_schema=tool_info["schema"]
                    )(wrapper)
            
            logger.info(f"Successfully registered additional agent: {agent_module}")
            return True
        except (ImportError, AttributeError) as e:
            logger.error(f"Error registering additional agent {agent_module}: {e}")
            return False
