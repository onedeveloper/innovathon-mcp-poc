"""
Tool call handler for the MCP Server/Client application.

This module provides standardized methods for handling tool calls
from different sources to ensure consistency across the application.
"""
from typing import Dict, List, Tuple, Optional, Any
import logging
import json
import re

# Set up logging
logger = logging.getLogger(__name__)

class ToolCallHandler:
    """
    Handler for tool calls.
    
    This class provides standardized methods for handling tool calls
    from different sources.
    """
    
    @staticmethod
    def parse_tool_call(tool_call_data: Any) -> Tuple[Optional[str], Optional[Dict], Optional[str]]:
        """
        Parse a tool call from various formats.
        
        Args:
            tool_call_data: The tool call data to parse
            
        Returns:
            A tuple of (tool_name, tool_args, error_message)
        """
        try:
            # Case 1: Standard structured tool_calls format
            if isinstance(tool_call_data, dict) and 'function' in tool_call_data:
                tool_name = tool_call_data['function'].get('name')
                raw_args = tool_call_data['function'].get('arguments', {})
                
                # Handle arguments which might be a string or a dict
                if isinstance(raw_args, str):
                    try:
                        tool_args = json.loads(raw_args)
                    except json.JSONDecodeError:
                        return tool_name, {}, f"Failed to parse arguments: {raw_args}"
                elif isinstance(raw_args, dict):
                    tool_args = raw_args
                else:
                    return tool_name, {}, f"Unexpected argument type: {type(raw_args)}"
                
                return tool_name, tool_args, None
            
            # Case 2: Content with <toolcall> tags
            elif isinstance(tool_call_data, str) and '<toolcall>' in tool_call_data:
                # Extract JSON string between tags
                start_tag = '<toolcall>'
                end_tag = '</toolcall>'
                start_index = tool_call_data.find(start_tag) + len(start_tag)
                end_index = tool_call_data.find(end_tag)
                
                if start_index < 0 or end_index < 0:
                    return None, None, "Invalid toolcall tag format"
                
                tool_call_json_str = tool_call_data[start_index:end_index].strip()
                
                try:
                    # Parse the JSON
                    tool_call_json = json.loads(tool_call_json_str)
                    
                    # Extract tool name and arguments
                    tool_name = None
                    tool_args = {}
                    
                    if tool_call_json.get("type") == "function" and "arguments" in tool_call_json:
                        arguments_dict = tool_call_json["arguments"]
                        if isinstance(arguments_dict, dict):
                            # Case 1: Arguments contain {'name': 'tool_name'} for parameterless tools
                            potential_tool_name = arguments_dict.get("name")
                            if potential_tool_name in ["list_tables", "get_database_schema"]:
                                tool_name = potential_tool_name
                                tool_args = {}  # Ensure args are empty for these
                            # Case 2: Arguments contain {'sql': '...'} for query_data
                            elif "sql" in arguments_dict:
                                tool_name = "query_data"
                                tool_args = arguments_dict
                            else:
                                return None, None, f"Unrecognized arguments structure in <toolcall>: {arguments_dict}"
                        else:
                            return None, None, "Arguments field in <toolcall> JSON is not a dictionary"
                    else:
                        return None, None, "Unexpected JSON structure in <toolcall>"
                    
                    return tool_name, tool_args, None
                    
                except json.JSONDecodeError:
                    return None, None, f"Failed to parse JSON in toolcall tag: {tool_call_json_str}"
            
            # Case 3: Unknown format
            else:
                return None, None, f"Unsupported tool call format: {type(tool_call_data)}"
                
        except Exception as e:
            logger.error(f"Error parsing tool call: {e}")
            return None, None, f"Error parsing tool call: {str(e)}"
    
    @staticmethod
    def format_tool_result(tool_name: str, result: Any) -> Dict:
        """
        Format a tool result for return to the client.
        
        Args:
            tool_name: The name of the tool
            result: The result of the tool call
            
        Returns:
            A formatted tool result
        """
        # Convert result to string if it's not already
        if not isinstance(result, str):
            result_str = str(result)
        else:
            result_str = result
            
        return {
            "role": "tool",
            "content": f"Tool execution result for {tool_name}: {result_str}"
        }
