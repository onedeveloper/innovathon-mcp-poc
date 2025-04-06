"""
Tool result formatting utilities for the MCP Server/Client application.

This module provides consistent formatting for tool results to ensure
uniform presentation across different parts of the application.
"""
from typing import Any, Dict, List, Union
import logging

# Set up logging
logger = logging.getLogger(__name__)

class ToolResultFormatter:
    """Formatter for tool results to ensure consistent presentation."""
    
    @staticmethod
    def format_result(tool_name: str, result: Any) -> str:
        """
        Format a tool result for consistent presentation.
        
        Args:
            tool_name: The name of the tool that produced the result
            result: The raw result from the tool
            
        Returns:
            A formatted string representation of the result
        """
        logger.info(f"Formatting result for tool: {tool_name}")
        
        if tool_name == "query_data":
            return ToolResultFormatter.format_query_result(result)
        elif tool_name == "list_tables":
            return ToolResultFormatter.format_table_list(result)
        elif tool_name == "get_database_schema":
            return ToolResultFormatter.format_schema(result)
        elif tool_name.startswith("get_current_time"):
            return ToolResultFormatter.format_time_result(result)
        elif tool_name == "calculate_time_difference":
            return ToolResultFormatter.format_time_result(result)
        elif tool_name == "format_timestamp":
            return ToolResultFormatter.format_time_result(result)
        elif tool_name == "get_time_in_timezone":
            return ToolResultFormatter.format_time_result(result)
        else:
            # Generic formatting for unknown tools
            return f"Tool execution result for {tool_name}: {result}"
    
    @staticmethod
    def format_query_result(result: str) -> str:
        """
        Format a SQL query result.
        
        Args:
            result: The raw query result string
            
        Returns:
            A formatted query result
        """
        # Check if the result is an error message
        if result.startswith("Error:"):
            return f"SQL Query Error: {result[7:]}"
        
        # Check if the result is empty
        if not result.strip():
            return "Query executed successfully. No results returned."
        
        # For non-empty results, return with a header
        return f"SQL Query Result:\n{result}"
    
    @staticmethod
    def format_table_list(result: str) -> str:
        """
        Format a table list result.
        
        Args:
            result: The raw table list string
            
        Returns:
            A formatted table list
        """
        # The table list is already well-formatted, just return it
        return result
    
    @staticmethod
    def format_schema(result: str) -> str:
        """
        Format a schema result.
        
        Args:
            result: The raw schema string
            
        Returns:
            A formatted schema
        """
        # The schema is already well-formatted, just return it
        return result
    
    @staticmethod
    def format_time_result(result: str) -> str:
        """
        Format a time-related result.
        
        Args:
            result: The raw time result string
            
        Returns:
            A formatted time result
        """
        # Check if the result is an error message
        if result.startswith("Error"):
            return f"Time Function Error: {result}"
        
        # For non-error results, return with a header if not already present
        if "Time" in result or "time" in result:
            return result
        else:
            return f"Time Information: {result}"
    
    @staticmethod
    def format_error(tool_name: str, error: str) -> str:
        """
        Format an error result.
        
        Args:
            tool_name: The name of the tool that produced the error
            error: The error message
            
        Returns:
            A formatted error message
        """
        logger.error(f"Error in tool {tool_name}: {error}")
        return f"Error executing {tool_name}: {error}"
