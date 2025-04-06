"""
Agent registry for the MCP Server/Client application.

This module provides a centralized registry for agents and tools,
allowing for dynamic registration and discovery.
"""
from typing import Dict, List, Callable, Any, Optional
import logging

# Set up logging
logger = logging.getLogger(__name__)

class AgentRegistry:
    """
    Singleton registry for agents and tools.
    
    This class provides a centralized registry for agents and tools,
    allowing for dynamic registration and discovery.
    """
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(AgentRegistry, cls).__new__(cls)
            cls._instance.agents = {}
            cls._instance.tools = {}
            logger.info("Created new AgentRegistry instance")
        return cls._instance
    
    def register_agent(self, name: str, agent_instance: Any) -> None:
        """
        Register an agent with the registry.
        
        Args:
            name: The name of the agent
            agent_instance: The agent instance to register
        """
        self.agents[name] = agent_instance
        logger.info(f"Registered agent: {name}")
        
    def register_tool(self, name: str, tool_function: Callable, description: str, schema: Dict) -> None:
        """
        Register a tool with the registry.
        
        Args:
            name: The name of the tool
            tool_function: The function implementing the tool
            description: A description of the tool
            schema: The JSON schema for the tool's input parameters
        """
        self.tools[name] = {
            "function": tool_function,
            "description": description,
            "schema": schema
        }
        logger.info(f"Registered tool: {name}")
    
    def get_all_tools(self) -> Dict[str, Dict]:
        """
        Get all registered tools.
        
        Returns:
            A dictionary of tool name to tool information
        """
        return self.tools
    
    def get_tool(self, name: str) -> Optional[Dict]:
        """
        Get a specific tool by name.
        
        Args:
            name: The name of the tool to retrieve
            
        Returns:
            The tool information or None if not found
        """
        return self.tools.get(name)
    
    def get_agent(self, name: str) -> Optional[Any]:
        """
        Get a specific agent by name.
        
        Args:
            name: The name of the agent to retrieve
            
        Returns:
            The agent instance or None if not found
        """
        return self.agents.get(name)
    
    def get_all_agents(self) -> Dict[str, Any]:
        """
        Get all registered agents.
        
        Returns:
            A dictionary of agent name to agent instance
        """
        return self.agents
