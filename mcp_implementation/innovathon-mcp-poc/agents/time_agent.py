"""
Time Agent implementation for the MCP Server/Client application.

This module provides an agent that handles time-related operations.
"""
import time
import datetime
from typing import Dict, Any, Optional
import logging
from ..core.agent_interface import Agent
from ..core.registry import AgentRegistry

# Set up logging
logger = logging.getLogger(__name__)

class TimeAgent(Agent):
    """
    Agent for handling time-related operations.
    
    This agent provides tools for getting the current time, calculating time
    differences, formatting timestamps, and getting time in different timezones.
    """
    
    def __init__(self):
        """Initialize the Time agent."""
        self.registry = AgentRegistry()
        logger.info("Initialized TimeAgent")
        
    def register_tools(self) -> None:
        """Register time-related tools with the registry."""
        logger.info("Registering Time tools with registry")
        
        # Register get_current_time tool
        self.registry.register_tool(
            name="get_current_time",
            tool_function=self.get_current_time,
            description="Get the current time in a specified timezone and format",
            schema={
                "type": "object",
                "properties": {
                    "timezone": {
                        "type": "string",
                        "description": "Timezone (e.g., 'UTC', 'America/New_York'). Defaults to UTC if not specified."
                    },
                    "format": {
                        "type": "string",
                        "description": "Output format (e.g., 'iso', 'human'). Defaults to ISO format."
                    }
                }
            }
        )
        
        # Register calculate_time_difference tool
        self.registry.register_tool(
            name="calculate_time_difference",
            tool_function=self.calculate_time_difference,
            description="Calculate the difference between two timestamps",
            schema={
                "type": "object",
                "required": ["start_time", "end_time"],
                "properties": {
                    "start_time": {
                        "type": "string",
                        "description": "Start timestamp in ISO format"
                    },
                    "end_time": {
                        "type": "string",
                        "description": "End timestamp in ISO format"
                    },
                    "unit": {
                        "type": "string",
                        "description": "Unit for the result (seconds, minutes, hours, days). Defaults to seconds."
                    }
                }
            }
        )
        
        # Register format_timestamp tool
        self.registry.register_tool(
            name="format_timestamp",
            tool_function=self.format_timestamp,
            description="Format a timestamp in a specified format",
            schema={
                "type": "object",
                "required": ["timestamp"],
                "properties": {
                    "timestamp": {
                        "type": "string",
                        "description": "Timestamp to format (ISO format or Unix timestamp)"
                    },
                    "format": {
                        "type": "string",
                        "description": "Output format (e.g., '%Y-%m-%d %H:%M:%S', 'human'). Defaults to ISO format."
                    }
                }
            }
        )
        
        # Register get_time_in_timezone tool
        self.registry.register_tool(
            name="get_time_in_timezone",
            tool_function=self.get_time_in_timezone,
            description="Get the current time in a specific timezone",
            schema={
                "type": "object",
                "required": ["timezone"],
                "properties": {
                    "timezone": {
                        "type": "string",
                        "description": "Timezone (e.g., 'UTC', 'America/New_York')"
                    }
                }
            }
        )
    
    def initialize(self) -> None:
        """Initialize the Time agent."""
        logger.info("Initializing TimeAgent")
        # No special initialization needed for the time agent
    
    def process_request(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process a time-related request.
        
        Args:
            request: The request to process
            
        Returns:
            The response to the request
        """
        # This is a placeholder for future direct agent-to-agent communication
        # Currently not used as tools are called directly
        return {"status": "error", "message": "Direct request processing not implemented"}
    
    def get_current_time(self, timezone: Optional[str] = None, format: Optional[str] = None) -> str:
        """
        Get the current time in the specified timezone and format.
        
        Args:
            timezone: The timezone to use (defaults to UTC)
            format: The output format (defaults to ISO)
            
        Returns:
            The current time as a formatted string
        """
        logger.info(f"Getting current time with timezone={timezone}, format={format}")
        try:
            # Default to UTC
            tz = timezone or "UTC"
            
            # Get current time in the specified timezone
            if tz.lower() == "utc":
                current_time = datetime.datetime.now(datetime.timezone.utc)
            else:
                # This would use pytz or zoneinfo in a real implementation
                # For simplicity, we'll just use UTC here
                current_time = datetime.datetime.now(datetime.timezone.utc)
                logger.warning(f"Using UTC time instead of requested timezone: {tz}")
            
            # Format the time
            if format == "human":
                formatted_time = current_time.strftime("%A, %B %d, %Y %H:%M:%S %Z")
                logger.info(f"Formatted time in human-readable format: {formatted_time}")
                return formatted_time
            else:  # Default to ISO format
                formatted_time = current_time.isoformat()
                logger.info(f"Formatted time in ISO format: {formatted_time}")
                return formatted_time
        except Exception as e:
            logger.error(f"Error getting current time: {e}")
            return f"Error getting current time: {str(e)}"
    
    def calculate_time_difference(self, start_time: str, end_time: str, unit: Optional[str] = "seconds") -> str:
        """
        Calculate the difference between two timestamps.
        
        Args:
            start_time: The start timestamp in ISO format
            end_time: The end timestamp in ISO format
            unit: The unit for the result (defaults to seconds)
            
        Returns:
            The time difference as a formatted string
        """
        logger.info(f"Calculating time difference between {start_time} and {end_time} in {unit}")
        try:
            # Parse the timestamps
            start = datetime.datetime.fromisoformat(start_time)
            end = datetime.datetime.fromisoformat(end_time)
            
            # Calculate the difference in seconds
            diff_seconds = (end - start).total_seconds()
            
            # Convert to the requested unit
            if unit == "minutes":
                diff = diff_seconds / 60
                unit_str = "minutes"
            elif unit == "hours":
                diff = diff_seconds / 3600
                unit_str = "hours"
            elif unit == "days":
                diff = diff_seconds / 86400
                unit_str = "days"
            else:  # Default to seconds
                diff = diff_seconds
                unit_str = "seconds"
            
            logger.info(f"Time difference: {diff:.2f} {unit_str}")
            return f"Time difference: {diff:.2f} {unit_str}"
        except Exception as e:
            logger.error(f"Error calculating time difference: {e}")
            return f"Error calculating time difference: {str(e)}"
    
    def format_timestamp(self, timestamp: str, format: Optional[str] = None) -> str:
        """
        Format a timestamp in the specified format.
        
        Args:
            timestamp: The timestamp to format (ISO format or Unix timestamp)
            format: The output format (defaults to ISO)
            
        Returns:
            The formatted timestamp as a string
        """
        logger.info(f"Formatting timestamp {timestamp} with format {format}")
        try:
            # Parse the timestamp
            if timestamp.isdigit():
                # Unix timestamp
                dt = datetime.datetime.fromtimestamp(int(timestamp), tz=datetime.timezone.utc)
                logger.info(f"Parsed Unix timestamp: {dt}")
            else:
                # ISO format
                dt = datetime.datetime.fromisoformat(timestamp)
                logger.info(f"Parsed ISO timestamp: {dt}")
            
            # Format the timestamp
            if format == "human":
                formatted_time = dt.strftime("%A, %B %d, %Y %H:%M:%S %Z")
                logger.info(f"Formatted timestamp in human-readable format: {formatted_time}")
                return formatted_time
            elif format and format.startswith("%"):
                formatted_time = dt.strftime(format)
                logger.info(f"Formatted timestamp with custom format: {formatted_time}")
                return formatted_time
            else:  # Default to ISO format
                formatted_time = dt.isoformat()
                logger.info(f"Formatted timestamp in ISO format: {formatted_time}")
                return formatted_time
        except Exception as e:
            logger.error(f"Error formatting timestamp: {e}")
            return f"Error formatting timestamp: {str(e)}"
    
    def get_time_in_timezone(self, timezone: str) -> str:
        """
        Get the current time in a specific timezone.
        
        Args:
            timezone: The timezone to use
            
        Returns:
            The current time in the specified timezone as a formatted string
        """
        logger.info(f"Getting time in timezone {timezone}")
        try:
            # In a real implementation, we would use pytz or zoneinfo
            # For demonstration purposes, we'll just return a placeholder
            current_time = datetime.datetime.now(datetime.timezone.utc)
            logger.warning(f"Using UTC time instead of requested timezone: {timezone}")
            
            formatted_time = current_time.isoformat()
            return f"Current time in {timezone}: {formatted_time} (Note: This is UTC time, timezone conversion would be implemented in production)"
        except Exception as e:
            logger.error(f"Error getting time in timezone: {e}")
            return f"Error getting time in timezone: {str(e)}"
