"""
Retry utilities for the MCP Server/Client application.

This module provides decorators and utilities for implementing retry logic
with exponential backoff for operations that might fail temporarily.
"""
import time
import random
import logging
import functools
from typing import Callable, Type, List, Optional, Any, Union
from .exceptions import MCPError, TimeoutError

# Set up logging
logger = logging.getLogger(__name__)

def retry(
    exceptions: Union[Type[Exception], List[Type[Exception]]] = Exception,
    max_tries: int = 3,
    delay: float = 1.0,
    backoff: float = 2.0,
    jitter: float = 0.1,
    logger_func: Optional[Callable] = None
):
    """
    Retry decorator with exponential backoff.
    
    Args:
        exceptions: Exception or list of exceptions to catch and retry on
        max_tries: Maximum number of attempts
        delay: Initial delay between retries in seconds
        backoff: Backoff multiplier (e.g. value of 2 will double the delay each retry)
        jitter: Jitter factor to randomize delay (0 to disable)
        logger_func: Function to use for logging (defaults to module logger)
    
    Returns:
        Decorated function with retry logic
    """
    if logger_func is None:
        logger_func = logger.warning
    
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            mtries, mdelay = max_tries, delay
            
            # Convert single exception to list
            exc_list = exceptions
            if not isinstance(exc_list, list):
                exc_list = [exc_list]
            
            # Try the function up to max_tries times
            last_exception = None
            for i in range(mtries):
                try:
                    return func(*args, **kwargs)
                except tuple(exc_list) as e:
                    last_exception = e
                    
                    # Don't retry on the last attempt
                    if i == mtries - 1:
                        break
                    
                    # Calculate next delay with jitter
                    sleep_time = mdelay
                    if jitter:
                        sleep_time = random.uniform(mdelay * (1 - jitter), mdelay * (1 + jitter))
                    
                    # Log the retry
                    logger_func(f"Retry {i+1}/{mtries} for {func.__name__} after {sleep_time:.2f}s delay: {str(e)}")
                    
                    # Sleep before next attempt
                    time.sleep(sleep_time)
                    
                    # Increase delay for next attempt
                    mdelay *= backoff
            
            # If we get here, all retries failed
            if last_exception:
                logger_func(f"All {mtries} retries failed for {func.__name__}: {str(last_exception)}")
                raise last_exception
        
        return wrapper
    
    return decorator

def retry_async(
    exceptions: Union[Type[Exception], List[Type[Exception]]] = Exception,
    max_tries: int = 3,
    delay: float = 1.0,
    backoff: float = 2.0,
    jitter: float = 0.1,
    logger_func: Optional[Callable] = None
):
    """
    Async retry decorator with exponential backoff.
    
    Args:
        exceptions: Exception or list of exceptions to catch and retry on
        max_tries: Maximum number of attempts
        delay: Initial delay between retries in seconds
        backoff: Backoff multiplier (e.g. value of 2 will double the delay each retry)
        jitter: Jitter factor to randomize delay (0 to disable)
        logger_func: Function to use for logging (defaults to module logger)
    
    Returns:
        Decorated async function with retry logic
    """
    if logger_func is None:
        logger_func = logger.warning
    
    def decorator(func):
        @functools.wraps(func)
        async def wrapper(*args, **kwargs):
            import asyncio
            
            mtries, mdelay = max_tries, delay
            
            # Convert single exception to list
            exc_list = exceptions
            if not isinstance(exc_list, list):
                exc_list = [exc_list]
            
            # Try the function up to max_tries times
            last_exception = None
            for i in range(mtries):
                try:
                    return await func(*args, **kwargs)
                except tuple(exc_list) as e:
                    last_exception = e
                    
                    # Don't retry on the last attempt
                    if i == mtries - 1:
                        break
                    
                    # Calculate next delay with jitter
                    sleep_time = mdelay
                    if jitter:
                        sleep_time = random.uniform(mdelay * (1 - jitter), mdelay * (1 + jitter))
                    
                    # Log the retry
                    logger_func(f"Async retry {i+1}/{mtries} for {func.__name__} after {sleep_time:.2f}s delay: {str(e)}")
                    
                    # Sleep before next attempt
                    await asyncio.sleep(sleep_time)
                    
                    # Increase delay for next attempt
                    mdelay *= backoff
            
            # If we get here, all retries failed
            if last_exception:
                logger_func(f"All {mtries} async retries failed for {func.__name__}: {str(last_exception)}")
                raise last_exception
        
        return wrapper
    
    return decorator

class CircuitBreaker:
    """
    Circuit breaker pattern implementation.
    
    This class implements the circuit breaker pattern to prevent repeated calls
    to a failing service, allowing it time to recover.
    """
    
    def __init__(
        self,
        failure_threshold: int = 5,
        recovery_timeout: float = 30.0,
        expected_exceptions: Union[Type[Exception], List[Type[Exception]]] = Exception
    ):
        """
        Initialize the circuit breaker.
        
        Args:
            failure_threshold: Number of failures before opening the circuit
            recovery_timeout: Time in seconds to wait before trying again
            expected_exceptions: Exception or list of exceptions to count as failures
        """
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        
        # Convert single exception to list
        self.expected_exceptions = expected_exceptions
        if not isinstance(self.expected_exceptions, list):
            self.expected_exceptions = [self.expected_exceptions]
        
        # Circuit state
        self.failures = 0
        self.open_time = None
        self.state = "CLOSED"  # CLOSED, OPEN, HALF-OPEN
    
    def __call__(self, func):
        """
        Decorator to apply circuit breaker to a function.
        
        Args:
            func: The function to wrap with circuit breaker
            
        Returns:
            Decorated function with circuit breaker logic
        """
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            return self.call(func, *args, **kwargs)
        
        return wrapper
    
    def call(self, func, *args, **kwargs):
        """
        Call the function with circuit breaker logic.
        
        Args:
            func: The function to call
            *args: Positional arguments for the function
            **kwargs: Keyword arguments for the function
            
        Returns:
            The result of the function call
            
        Raises:
            Exception: If the circuit is open or the function call fails
        """
        if self.state == "OPEN":
            # Check if recovery timeout has elapsed
            if time.time() - self.open_time > self.recovery_timeout:
                logger.info(f"Circuit half-open for {func.__name__}, attempting recovery")
                self.state = "HALF-OPEN"
            else:
                # Circuit is open, fail fast
                raise MCPError(f"Circuit breaker open for {func.__name__}, failing fast")
        
        try:
            # Call the function
            result = func(*args, **kwargs)
            
            # If successful and in half-open state, reset the circuit
            if self.state == "HALF-OPEN":
                logger.info(f"Circuit closed for {func.__name__}, recovery successful")
                self.reset()
            
            return result
        except tuple(self.expected_exceptions) as e:
            # Count the failure
            self.record_failure()
            
            # If in half-open state, immediately open the circuit again
            if self.state == "HALF-OPEN":
                logger.warning(f"Circuit reopened for {func.__name__}, recovery failed")
                self.state = "OPEN"
                self.open_time = time.time()
            
            # If failure threshold reached, open the circuit
            elif self.state == "CLOSED" and self.failures >= self.failure_threshold:
                logger.warning(f"Circuit opened for {func.__name__} after {self.failures} failures")
                self.state = "OPEN"
                self.open_time = time.time()
            
            # Re-raise the exception
            raise
    
    def reset(self):
        """Reset the circuit breaker to closed state."""
        self.failures = 0
        self.open_time = None
        self.state = "CLOSED"
    
    def record_failure(self):
        """Record a failure and update the circuit state."""
        self.failures += 1
        logger.debug(f"Circuit breaker recorded failure {self.failures}/{self.failure_threshold}")
