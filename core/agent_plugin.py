"""
Agent plugin base class for the MCP Server/Client application.

This module defines the base class that all agent plugins must implement
to ensure consistent behavior and integration with the registry.
"""
from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
import logging

# Set up logging
logger = logging.getLogger(__name__)

class AgentPlugin(ABC):
    """
    Base class for all agent plugins.
    
    This class extends the Agent interface and provides common
    functionality for all agent plugins.
    """
    
    @property
    @abstractmethod
    def name(self) -> str:
        """
        Get the name of the agent plugin.
        
        Returns:
            The name of the agent plugin
        """
        pass
    
    @property
    @abstractmethod
    def version(self) -> str:
        """
        Get the version of the agent plugin.
        
        Returns:
            The version of the agent plugin
        """
        pass
    
    @property
    def dependencies(self) -> List[str]:
        """
        Get the dependencies of the agent plugin.
        
        Returns:
            A list of agent plugin names that this plugin depends on
        """
        return []
    
    @abstractmethod
    def register_tools(self) -> None:
        """
        Register agent's tools with the registry.
        
        This method should register all tools provided by the agent
        with the central registry.
        """
        pass
    
    @abstractmethod
    def initialize(self) -> None:
        """
        Initialize the agent.
        
        This method should perform any necessary initialization steps
        such as setting up connections or loading resources.
        """
        pass
    
    def validate(self) -> bool:
        """
        Validate that the agent plugin is properly configured.
        
        Returns:
            True if the agent plugin is valid, False otherwise
        """
        return True
    
    @abstractmethod
    def process_request(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process a request directed to this agent.
        
        Args:
            request: The request to process
            
        Returns:
            The response to the request
        """
        pass
