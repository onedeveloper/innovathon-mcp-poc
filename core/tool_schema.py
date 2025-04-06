"""
Tool schema handler for the MCP Server/Client application.

This module provides standardized methods for creating and validating
tool schemas to ensure consistency across the application.
"""
from typing import Dict, List, Tuple, Optional, Any
import logging
import json
import jsonschema

# Set up logging
logger = logging.getLogger(__name__) 

class ToolSchemaHandler:
    """
    Handler for tool schemas.
    
    This class provides standardized methods for creating and validating
    tool schemas.
    """
    
    @staticmethod
    def create_schema(properties: Dict[str, Dict], required: List[str] = None) -> Dict:
        """
        Create a standardized tool schema.
        
        Args:
            properties: The properties of the schema
            required: The required properties
            
        Returns:
            A standardized tool schema
        """
        schema = {
            "type": "object",
            "properties": properties
        }
        
        if required:
            schema["required"] = required
            
        return schema
    
    @staticmethod
    def validate_args(schema: Dict, args: Dict) -> Tuple[bool, Optional[str]]:
        """
        Validate arguments against a schema.
        
        Args:
            schema: The schema to validate against
            args: The arguments to validate
            
        Returns:
            A tuple of (is_valid, error_message)
        """
        try:
            jsonschema.validate(instance=args, schema=schema)
            return True, None
        except jsonschema.exceptions.ValidationError as e:
            logger.error(f"Schema validation error: {e}")
            return False, str(e)
        except Exception as e:
            logger.error(f"Unexpected error during schema validation: {e}")
            return False, f"Unexpected error during validation: {str(e)}"
    
    @staticmethod
    def format_schema_for_client(schema: Dict) -> Dict:
        """
        Format a schema for client consumption.
        
        Args:
            schema: The schema to format
            
        Returns:
            A formatted schema suitable for client consumption
        """
        # For now, just return the schema as is
        # This method can be expanded in the future if needed
        return schema
