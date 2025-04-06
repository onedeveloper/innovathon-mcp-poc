"""
Graceful degradation utilities for the MCP Server/Client application.

This module provides utilities for implementing graceful degradation
patterns to handle failures in a way that maintains partial functionality.
"""
import logging
import functools
from typing import Callable, Any, Optional, Dict, List, Union

# Set up logging
logger = logging.getLogger(__name__)

class Fallback:
    """
    Fallback pattern implementation.
    
    This class implements the fallback pattern to provide alternative
    implementations when the primary one fails.
    """
    
    def __init__(self, fallback_func: Callable, exceptions: Union[Type[Exception], List[Type[Exception]]] = Exception):
        """
        Initialize the fallback.
        
        Args:
            fallback_func: The fallback function to call when the primary function fails
            exceptions: Exception or list of exceptions to catch and trigger fallback
        """
        self.fallback_func = fallback_func
        
        # Convert single exception to list
        self.exceptions = exceptions
        if not isinstance(self.exceptions, list):
            self.exceptions = [self.exceptions]
    
    def __call__(self, primary_func):
        """
        Decorator to apply fallback to a function.
        
        Args:
            primary_func: The primary function to wrap with fallback
            
        Returns:
            Decorated function with fallback logic
        """
        @functools.wraps(primary_func)
        def wrapper(*args, **kwargs):
            try:
                return primary_func(*args, **kwargs)
            except tuple(self.exceptions) as e:
                logger.warning(f"Primary function {primary_func.__name__} failed, using fallback: {str(e)}")
                return self.fallback_func(*args, **kwargs)
        
        return wrapper

def with_fallback(fallback_value: Any, exceptions: Union[Type[Exception], List[Type[Exception]]] = Exception):
    """
    Decorator to provide a fallback value when a function fails.
    
    Args:
        fallback_value: The value to return when the function fails
        exceptions: Exception or list of exceptions to catch and trigger fallback
        
    Returns:
        Decorated function with fallback value
    """
    # Convert single exception to list
    exc_list = exceptions
    if not isinstance(exc_list, list):
        exc_list = [exc_list]
    
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except tuple(exc_list) as e:
                logger.warning(f"Function {func.__name__} failed, using fallback value: {str(e)}")
                return fallback_value
        
        return wrapper
    
    return decorator

def graceful_degradation(degraded_func: Optional[Callable] = None, exceptions: Union[Type[Exception], List[Type[Exception]]] = Exception):
    """
    Decorator to implement graceful degradation.
    
    Args:
        degraded_func: Function to call for degraded operation (if None, returns None)
        exceptions: Exception or list of exceptions to catch and trigger degradation
        
    Returns:
        Decorated function with graceful degradation
    """
    # Convert single exception to list
    exc_list = exceptions
    if not isinstance(exc_list, list):
        exc_list = [exc_list]
    
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except tuple(exc_list) as e:
                logger.warning(f"Function {func.__name__} failed, using degraded operation: {str(e)}")
                if degraded_func:
                    return degraded_func(*args, **kwargs)
                return None
        
        return wrapper
    
    return decorator

class FeatureToggle:
    """
    Feature toggle implementation.
    
    This class implements feature toggles to enable or disable features
    based on configuration or runtime conditions.
    """
    
    _features = {}
    
    @classmethod
    def set_feature(cls, feature_name: str, enabled: bool):
        """
        Set the state of a feature.
        
        Args:
            feature_name: The name of the feature
            enabled: Whether the feature is enabled
        """
        cls._features[feature_name] = enabled
        logger.info(f"Feature '{feature_name}' {'enabled' if enabled else 'disabled'}")
    
    @classmethod
    def is_enabled(cls, feature_name: str, default: bool = False) -> bool:
        """
        Check if a feature is enabled.
        
        Args:
            feature_name: The name of the feature
            default: Default state if the feature is not configured
            
        Returns:
            True if the feature is enabled, False otherwise
        """
        return cls._features.get(feature_name, default)
    
    @classmethod
    def when_enabled(cls, feature_name: str, default: bool = False):
        """
        Decorator to conditionally execute a function based on feature state.
        
        Args:
            feature_name: The name of the feature
            default: Default state if the feature is not configured
            
        Returns:
            Decorated function that only executes when the feature is enabled
        """
        def decorator(func):
            @functools.wraps(func)
            def wrapper(*args, **kwargs):
                if cls.is_enabled(feature_name, default):
                    return func(*args, **kwargs)
                logger.debug(f"Feature '{feature_name}' is disabled, skipping {func.__name__}")
                return None
            
            return wrapper
        
        return decorator
    
    @classmethod
    def with_alternative(cls, feature_name: str, alternative_func: Callable, default: bool = False):
        """
        Decorator to use an alternative function when a feature is disabled.
        
        Args:
            feature_name: The name of the feature
            alternative_func: Function to call when the feature is disabled
            default: Default state if the feature is not configured
            
        Returns:
            Decorated function that uses an alternative when the feature is disabled
        """
        def decorator(func):
            @functools.wraps(func)
            def wrapper(*args, **kwargs):
                if cls.is_enabled(feature_name, default):
                    return func(*args, **kwargs)
                logger.debug(f"Feature '{feature_name}' is disabled, using alternative for {func.__name__}")
                return alternative_func(*args, **kwargs)
            
            return wrapper
        
        return decorator
