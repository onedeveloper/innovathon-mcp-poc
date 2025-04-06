"""
Agent interface for the MCP Server/Client application.

This module defines the abstract base class that all agents must implement
to ensure consistent behavior and integration with the registry.
"""
from abc import ABC, abstractmethod
from typing import List, Dict, Any
import logging

# Set up logging
logger = logging.getLogger(__name__)

class Agent(ABC):
    """
    Abstract base class for all agents.
    
    All agents must implement this interface to ensure consistent
    behavior and integration with the registry.
    """
    
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
