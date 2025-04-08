from mcp.server.fastmcp import FastMCP
from datetime import datetime, timedelta
import calendar

# Initialize MCP server
mcp = FastMCP("TimeAgent")

@mcp.tool(description="Get the current weekday")
def get_current_day() -> str:
    """Returns the current weekday name."""
    return calendar.day_name[datetime.now().weekday()]

@mcp.tool(description="Get the current date in YYYY-MM-DD format")
def get_current_date() -> str:
    """Returns the current date in YYYY-MM-DD format."""
    return datetime.now().strftime("%Y-%m-%d")

@mcp.tool(description="Calculate days until a future date")
def days_until(target_date: str) -> int:
    """
    Calculate the number of days until a future date.
    
    Args:
        target_date: Future date in YYYY-MM-DD format
        
    Returns:
        Number of days until the target date
    """
    current_date = datetime.now().date()
    future_date = datetime.strptime(target_date, "%Y-%m-%d").date()
    
    if future_date < current_date:
        raise ValueError("Target date must be in the future")
        
    delta = future_date - current_date
    return delta.days

@mcp.tool(description="Calculate days since a past date")
def days_since(past_date: str) -> int:
    """
    Calculate the number of days since a past date.
    
    Args:
        past_date: Past date in YYYY-MM-DD format
        
    Returns:
        Number of days since the past date
    """
    current_date = datetime.now().date()
    past_date_obj = datetime.strptime(past_date, "%Y-%m-%d").date()
    
    if past_date_obj > current_date:
        raise ValueError("Past date must be in the past")
        
    delta = current_date - past_date_obj
    return delta.days

@mcp.tool(description="Calculate days between two dates")
def days_between(date1: str, date2: str) -> int:
    """
    Calculate the number of days between two dates.
    
    Args:
        date1: First date in YYYY-MM-DD format
        date2: Second date in YYYY-MM-DD format
        
    Returns:
        Absolute number of days between the two dates
    """
    date1_obj = datetime.strptime(date1, "%Y-%m-%d").date()
    date2_obj = datetime.strptime(date2, "%Y-%m-%d").date()
    
    delta = abs((date2_obj - date1_obj).days)
    return delta

# Run with: uvicorn server:mcp.app --port 8002
