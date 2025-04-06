"""
Tool call parsing utilities for the MCP Server/Client application.

This module provides a unified approach to parse tool calls from Ollama responses,
handling both structured tool_calls and tag-based formats.
"""
from typing import Dict, Any, List, Tuple, Optional
import json
import re
import logging

# Set up logging
logger = logging.getLogger(__name__)

class ToolCallParser:
    """Parser for tool calls from Ollama responses."""
    
    @staticmethod
    def parse_tool_calls(message: Dict[str, Any]) -> List[Tuple[str, Dict[str, Any]]]:
        """
        Parse tool calls from an Ollama message, handling both structured and tag-based formats.
        
        Args:
            message: The Ollama response message dictionary
            
        Returns:
            A list of (tool_name, tool_args) tuples
        """
        tool_calls = []
        
        # Method 1: Parse structured tool_calls field
        if message.get('tool_calls'):
            logger.info("Parsing structured tool_calls field")
            for tool_call in message['tool_calls']:
                tool_name, tool_args = ToolCallParser._parse_structured_tool_call(tool_call)
                if tool_name:
                    tool_calls.append((tool_name, tool_args))
        
        # Method 2: Parse <toolcall> tags in content
        elif message.get('content') and '<toolcall>' in message['content']:
            logger.info("Parsing <toolcall> tags in content")
            tool_name, tool_args = ToolCallParser._parse_tag_based_tool_call(message['content'])
            if tool_name:
                tool_calls.append((tool_name, tool_args))
        
        # Log the results
        if tool_calls:
            logger.info(f"Found {len(tool_calls)} tool call(s)")
            for tool_name, tool_args in tool_calls:
                logger.info(f"Tool: {tool_name}, Args: {tool_args}")
        else:
            logger.info("No tool calls found in message")
            
        return tool_calls
    
    @staticmethod
    def _parse_structured_tool_call(tool_call: Dict[str, Any]) -> Tuple[Optional[str], Dict[str, Any]]:
        """
        Parse a structured tool call from the tool_calls field.
        
        Args:
            tool_call: A tool call dictionary from the tool_calls field
            
        Returns:
            A tuple of (tool_name, tool_args) or (None, {}) if parsing fails
        """
        try:
            tool_name = tool_call['function']['name']
            raw_args = tool_call['function']['arguments']
            
            # Handle string arguments (parse JSON)
            if isinstance(raw_args, str):
                try:
                    tool_args = json.loads(raw_args)
                except json.JSONDecodeError as e:
                    logger.error(f"Failed to parse JSON arguments: {e}")
                    return None, {}
            # Handle dictionary arguments
            elif isinstance(raw_args, dict):
                tool_args = raw_args
            else:
                logger.error(f"Unexpected argument type: {type(raw_args)}")
                return None, {}
                
            return tool_name, tool_args
        except (KeyError, TypeError) as e:
            logger.error(f"Error parsing structured tool call: {e}")
            return None, {}
    
    @staticmethod
    def _parse_tag_based_tool_call(content: str) -> Tuple[Optional[str], Dict[str, Any]]:
        """
        Parse a tool call from <toolcall> tags in content.
        
        Args:
            content: The content string containing <toolcall> tags
            
        Returns:
            A tuple of (tool_name, tool_args) or (None, {}) if parsing fails
        """
        try:
            # Extract JSON string between tags
            start_tag = '<toolcall>'
            end_tag = '</toolcall>'
            start_index = content.find(start_tag) + len(start_tag)
            end_index = content.find(end_tag)
            
            if start_index < len(start_tag) or end_index < 0:
                logger.error("Invalid toolcall tag format")
                return None, {}
                
            tool_call_json_str = content[start_index:end_index].strip()
            tool_call_data = json.loads(tool_call_json_str)
            
            # Extract tool name and arguments
            tool_name = None
            tool_args = {}
            
            if tool_call_data.get("type") == "function" and "arguments" in tool_call_data:
                arguments_dict = tool_call_data["arguments"]
                if isinstance(arguments_dict, dict):
                    # Handle parameterless tools
                    potential_tool_name = arguments_dict.get("name")
                    if potential_tool_name in ["list_tables", "get_database_schema"]:
                        tool_name = potential_tool_name
                        tool_args = {}
                    # Handle query_data tool
                    elif "sql" in arguments_dict:
                        tool_name = "query_data"
                        tool_args = arguments_dict
                    else:
                        logger.error(f"Unrecognized arguments structure: {arguments_dict}")
                        return None, {}
                else:
                    logger.error(f"Arguments field is not a dictionary: {type(arguments_dict)}")
                    return None, {}
            else:
                logger.error("Unexpected JSON structure in <toolcall>")
                return None, {}
            
            return tool_name, tool_args
        except (ValueError, json.JSONDecodeError, KeyError, TypeError) as e:
            logger.error(f"Error parsing tag-based tool call: {e}")
            return None, {}
