"""
Security utilities for the MCP Server/Client application.

This module provides utilities for implementing security best practices
including SQL injection prevention, input validation, and sanitization.
"""
import re
import logging
import functools
import sqlite3
from typing import Any, Dict, List, Callable, Optional, Union, Tuple

# Set up logging
logger = logging.getLogger(__name__)

class SQLSecurity:
    """
    SQL security utilities for preventing SQL injection.
    
    This class provides methods for safely executing SQL queries
    with proper parameterization.
    """
    
    @staticmethod
    def is_safe_query(query: str) -> bool:
        """
        Check if a SQL query is potentially unsafe.
        
        Args:
            query: The SQL query to check
            
        Returns:
            True if the query appears safe, False otherwise
        """
        # Check for common SQL injection patterns
        unsafe_patterns = [
            r';\s*DROP\s+TABLE',
            r';\s*DELETE\s+FROM',
            r';\s*UPDATE\s+.+\s*SET',
            r';\s*INSERT\s+INTO',
            r'UNION\s+SELECT',
            r'--',
            r'/\*.*\*/',
            r'EXEC\s+\w+',
            r'xp_\w+',
        ]
        
        for pattern in unsafe_patterns:
            if re.search(pattern, query, re.IGNORECASE):
                logger.warning(f"Potentially unsafe SQL query detected: {query}")
                return False
        
        return True
    
    @staticmethod
    def parameterize_query(query: str, params: Dict[str, Any]) -> Tuple[str, Tuple]:
        """
        Convert a query with named parameters to a parameterized query.
        
        Args:
            query: The SQL query with named parameters (e.g., :param)
            params: Dictionary of parameter names to values
            
        Returns:
            Tuple of (parameterized query, parameter tuple)
        """
        # Replace named parameters with ? placeholders
        param_pattern = r':(\w+)'
        param_names = re.findall(param_pattern, query)
        
        # Check that all parameters are provided
        for name in param_names:
            if name not in params:
                raise ValueError(f"Missing parameter '{name}' for query")
        
        # Replace named parameters with ? and build parameter tuple
        param_values = tuple(params[name] for name in param_names)
        parameterized_query = re.sub(param_pattern, '?', query)
        
        return parameterized_query, param_values
    
    @staticmethod
    def safe_execute(conn: sqlite3.Connection, query: str, params: Dict[str, Any] = None) -> List[Tuple]:
        """
        Safely execute a SQL query with parameters.
        
        Args:
            conn: SQLite connection
            query: The SQL query with named parameters
            params: Dictionary of parameter names to values
            
        Returns:
            Query results as a list of tuples
        """
        if params is None:
            params = {}
        
        # Check if the query is potentially unsafe
        if not SQLSecurity.is_safe_query(query):
            raise ValueError("Potentially unsafe SQL query rejected")
        
        # Parameterize the query
        parameterized_query, param_values = SQLSecurity.parameterize_query(query, params)
        
        # Execute the query
        cursor = conn.cursor()
        cursor.execute(parameterized_query, param_values)
        
        # Return the results
        return cursor.fetchall()

def validate_input(schema: Dict[str, Any]):
    """
    Decorator for validating function input against a schema.
    
    Args:
        schema: JSON Schema-like dictionary defining expected parameters
        
    Returns:
        Decorated function with input validation
    """
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            # Extract parameter names from function signature
            import inspect
            sig = inspect.signature(func)
            param_names = list(sig.parameters.keys())
            
            # Build a dictionary of parameter values
            param_values = {}
            for i, arg in enumerate(args):
                if i < len(param_names):
                    param_values[param_names[i]] = arg
            param_values.update(kwargs)
            
            # Validate required parameters
            if 'required' in schema:
                for param in schema['required']:
                    if param not in param_values:
                        raise ValueError(f"Missing required parameter: {param}")
            
            # Validate parameter types
            if 'properties' in schema:
                for param, value in param_values.items():
                    if param in schema['properties']:
                        prop_schema = schema['properties'][param]
                        
                        # Check type
                        if 'type' in prop_schema:
                            expected_type = prop_schema['type']
                            if expected_type == 'string' and not isinstance(value, str):
                                raise TypeError(f"Parameter '{param}' must be a string")
                            elif expected_type == 'number' and not isinstance(value, (int, float)):
                                raise TypeError(f"Parameter '{param}' must be a number")
                            elif expected_type == 'integer' and not isinstance(value, int):
                                raise TypeError(f"Parameter '{param}' must be an integer")
                            elif expected_type == 'boolean' and not isinstance(value, bool):
                                raise TypeError(f"Parameter '{param}' must be a boolean")
                            elif expected_type == 'array' and not isinstance(value, list):
                                raise TypeError(f"Parameter '{param}' must be an array")
                            elif expected_type == 'object' and not isinstance(value, dict):
                                raise TypeError(f"Parameter '{param}' must be an object")
                        
                        # Check enum values
                        if 'enum' in prop_schema and value not in prop_schema['enum']:
                            raise ValueError(f"Parameter '{param}' must be one of: {prop_schema['enum']}")
                        
                        # Check string pattern
                        if 'pattern' in prop_schema and isinstance(value, str):
                            pattern = re.compile(prop_schema['pattern'])
                            if not pattern.match(value):
                                raise ValueError(f"Parameter '{param}' does not match pattern: {prop_schema['pattern']}")
            
            # Call the function with validated parameters
            return func(*args, **kwargs)
        
        return wrapper
    
    return decorator

def sanitize_html(html: str) -> str:
    """
    Sanitize HTML to prevent XSS attacks.
    
    Args:
        html: The HTML string to sanitize
        
    Returns:
        Sanitized HTML string
    """
    # Replace potentially dangerous characters
    sanitized = html
    sanitized = re.sub(r'<script.*?>.*?</script>', '', sanitized, flags=re.IGNORECASE | re.DOTALL)
    sanitized = re.sub(r'<style.*?>.*?</style>', '', sanitized, flags=re.IGNORECASE | re.DOTALL)
    sanitized = re.sub(r'<iframe.*?>.*?</iframe>', '', sanitized, flags=re.IGNORECASE | re.DOTALL)
    sanitized = re.sub(r'<object.*?>.*?</object>', '', sanitized, flags=re.IGNORECASE | re.DOTALL)
    sanitized = re.sub(r'<embed.*?>.*?</embed>', '', sanitized, flags=re.IGNORECASE | re.DOTALL)
    
    # Replace potentially dangerous attributes
    sanitized = re.sub(r'on\w+\s*=\s*["\'][^"\']*["\']', '', sanitized, flags=re.IGNORECASE)
    sanitized = re.sub(r'javascript:', '', sanitized, flags=re.IGNORECASE)
    
    return sanitized

def sanitize_filename(filename: str) -> str:
    """
    Sanitize a filename to prevent path traversal attacks.
    
    Args:
        filename: The filename to sanitize
        
    Returns:
        Sanitized filename
    """
    # Remove path separators and other potentially dangerous characters
    sanitized = re.sub(r'[/\\]', '', filename)
    sanitized = re.sub(r'\.\.', '', sanitized)
    
    # Ensure the filename is not empty
    if not sanitized:
        sanitized = 'unnamed_file'
    
    return sanitized
