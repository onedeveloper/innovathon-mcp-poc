"""
Time Functions Agent implementation for the MCP Server/Client application.

This module provides an agent that handles advanced time-related operations
beyond the basic functionality provided by the TimeAgent.
"""
import time
import datetime
import calendar
import pytz
from typing import Dict, Any, Optional, List
import logging
from ..core.agent_plugin import AgentPlugin
from ..core.registry import AgentRegistry
from ..core.tool_schema import ToolSchemaHandler

# Set up logging
logger = logging.getLogger(__name__)

class TimeFunctionsAgent(AgentPlugin):
    """
    Agent for handling advanced time-related operations.
    
    This agent provides tools for working with time zones, date calculations,
    calendar operations, and time formatting beyond the basic functionality
    provided by the TimeAgent.
    """
    
    def __init__(self):
        """Initialize the Time Functions agent."""
        self.registry = AgentRegistry()
        logger.info("Initialized TimeFunctionsAgent")
    
    @property
    def name(self) -> str:
        """
        Get the name of the agent plugin.
        
        Returns:
            The name of the agent plugin
        """
        return "TimeFunctionsAgent"
    
    @property
    def version(self) -> str:
        """
        Get the version of the agent plugin.
        
        Returns:
            The version of the agent plugin
        """
        return "1.0.0"
    
    @property
    def dependencies(self) -> List[str]:
        """
        Get the dependencies of the agent plugin.
        
        Returns:
            A list of agent plugin names that this plugin depends on
        """
        # This agent doesn't depend on any other agents
        return []
    
    def register_tools(self) -> None:
        """Register time-related tools with the registry."""
        logger.info("Registering Time Functions tools with registry")
        
        # Register list_timezones tool
        self.registry.register_tool(
            name="list_timezones",
            tool_function=self.list_timezones,
            description="List all available time zones",
            schema=ToolSchemaHandler.create_schema(
                properties={
                    "region": {
                        "type": "string",
                        "description": "Optional region filter (e.g., 'US', 'Europe')"
                    }
                }
            )
        )
        
        # Register convert_timezone tool
        self.registry.register_tool(
            name="convert_timezone",
            tool_function=self.convert_timezone,
            description="Convert a time from one timezone to another",
            schema=ToolSchemaHandler.create_schema(
                properties={
                    "time": {
                        "type": "string",
                        "description": "Time to convert (ISO format or 'now')"
                    },
                    "from_timezone": {
                        "type": "string",
                        "description": "Source timezone"
                    },
                    "to_timezone": {
                        "type": "string",
                        "description": "Target timezone"
                    }
                },
                required=["from_timezone", "to_timezone"]
            )
        )
        
        # Register add_time tool
        self.registry.register_tool(
            name="add_time",
            tool_function=self.add_time,
            description="Add a specified amount of time to a timestamp",
            schema=ToolSchemaHandler.create_schema(
                properties={
                    "timestamp": {
                        "type": "string",
                        "description": "Base timestamp (ISO format or 'now')"
                    },
                    "years": {
                        "type": "integer",
                        "description": "Number of years to add"
                    },
                    "months": {
                        "type": "integer",
                        "description": "Number of months to add"
                    },
                    "days": {
                        "type": "integer",
                        "description": "Number of days to add"
                    },
                    "hours": {
                        "type": "integer",
                        "description": "Number of hours to add"
                    },
                    "minutes": {
                        "type": "integer",
                        "description": "Number of minutes to add"
                    },
                    "seconds": {
                        "type": "integer",
                        "description": "Number of seconds to add"
                    },
                    "timezone": {
                        "type": "string",
                        "description": "Timezone for the calculation (defaults to UTC)"
                    }
                },
                required=["timestamp"]
            )
        )
        
        # Register get_month_calendar tool
        self.registry.register_tool(
            name="get_month_calendar",
            tool_function=self.get_month_calendar,
            description="Get a calendar for a specific month",
            schema=ToolSchemaHandler.create_schema(
                properties={
                    "year": {
                        "type": "integer",
                        "description": "Year (defaults to current year)"
                    },
                    "month": {
                        "type": "integer",
                        "description": "Month (1-12, defaults to current month)"
                    }
                }
            )
        )
        
        # Register is_business_day tool
        self.registry.register_tool(
            name="is_business_day",
            tool_function=self.is_business_day,
            description="Check if a date is a business day (Monday-Friday)",
            schema=ToolSchemaHandler.create_schema(
                properties={
                    "date": {
                        "type": "string",
                        "description": "Date to check (ISO format or 'today')"
                    },
                    "country": {
                        "type": "string",
                        "description": "Country code for holiday checking (not implemented yet)"
                    }
                },
                required=["date"]
            )
        )
    
    def initialize(self) -> None:
        """Initialize the Time Functions agent."""
        logger.info("Initializing TimeFunctionsAgent")
        # No special initialization needed for this agent
    
    def process_request(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process a time-related request.
        
        Args:
            request: The request to process
            
        Returns:
            The response to the request
        """
        # This is a placeholder for future direct agent-to-agent communication
        return {"status": "error", "message": "Direct request processing not implemented"}
    
    def list_timezones(self, region: Optional[str] = None) -> str:
        """
        List all available time zones, optionally filtered by region.
        
        Args:
            region: Optional region filter (e.g., 'US', 'Europe')
            
        Returns:
            A formatted string listing available time zones
        """
        logger.info(f"Listing time zones with region filter: {region}")
        try:
            all_timezones = pytz.all_timezones
            
            # Filter by region if specified
            if region:
                filtered_timezones = [tz for tz in all_timezones if region.lower() in tz.lower()]
                if not filtered_timezones:
                    return f"No time zones found for region: {region}"
                timezones_to_display = filtered_timezones
            else:
                timezones_to_display = all_timezones
            
            # Format the output
            if len(timezones_to_display) > 50:
                # If there are too many, just show a sample
                sample = timezones_to_display[:50]
                result = "Available time zones (showing first 50):\n"
                result += "\n".join(sample)
                result += f"\n\nTotal: {len(timezones_to_display)} time zones"
            else:
                result = "Available time zones:\n"
                result += "\n".join(timezones_to_display)
                result += f"\n\nTotal: {len(timezones_to_display)} time zones"
            
            logger.info(f"Listed {len(timezones_to_display)} time zones")
            return result
        except Exception as e:
            logger.error(f"Error listing time zones: {e}")
            return f"Error listing time zones: {str(e)}"
    
    def convert_timezone(self, from_timezone: str, to_timezone: str, time: Optional[str] = "now") -> str:
        """
        Convert a time from one timezone to another.
        
        Args:
            from_timezone: Source timezone
            to_timezone: Target timezone
            time: Time to convert (ISO format or 'now')
            
        Returns:
            The converted time as a formatted string
        """
        logger.info(f"Converting time {time} from {from_timezone} to {to_timezone}")
        try:
            # Get the timezone objects
            try:
                source_tz = pytz.timezone(from_timezone)
                target_tz = pytz.timezone(to_timezone)
            except pytz.exceptions.UnknownTimeZoneError as e:
                return f"Unknown timezone: {str(e)}"
            
            # Parse the time
            if time == "now":
                # Use current time
                dt = datetime.datetime.now(source_tz)
            else:
                # Parse ISO format
                try:
                    naive_dt = datetime.datetime.fromisoformat(time)
                    dt = source_tz.localize(naive_dt)
                except ValueError:
                    return f"Invalid time format: {time}. Please use ISO format (YYYY-MM-DDTHH:MM:SS)."
            
            # Convert to target timezone
            converted_dt = dt.astimezone(target_tz)
            
            # Format the result
            result = f"Time in {from_timezone}: {dt.strftime('%Y-%m-%d %H:%M:%S %Z%z')}\n"
            result += f"Time in {to_timezone}: {converted_dt.strftime('%Y-%m-%d %H:%M:%S %Z%z')}"
            
            logger.info(f"Converted time: {result}")
            return result
        except Exception as e:
            logger.error(f"Error converting timezone: {e}")
            return f"Error converting timezone: {str(e)}"
    
    def add_time(self, timestamp: str, years: int = 0, months: int = 0, days: int = 0, 
                hours: int = 0, minutes: int = 0, seconds: int = 0, 
                timezone: Optional[str] = "UTC") -> str:
        """
        Add a specified amount of time to a timestamp.
        
        Args:
            timestamp: Base timestamp (ISO format or 'now')
            years: Number of years to add
            months: Number of months to add
            days: Number of days to add
            hours: Number of hours to add
            minutes: Number of minutes to add
            seconds: Number of seconds to add
            timezone: Timezone for the calculation
            
        Returns:
            The resulting timestamp as a formatted string
        """
        logger.info(f"Adding time to {timestamp}: years={years}, months={months}, days={days}, "
                   f"hours={hours}, minutes={minutes}, seconds={seconds}, timezone={timezone}")
        try:
            # Get the timezone object
            try:
                tz = pytz.timezone(timezone)
            except pytz.exceptions.UnknownTimeZoneError:
                return f"Unknown timezone: {timezone}"
            
            # Parse the timestamp
            if timestamp == "now":
                # Use current time
                dt = datetime.datetime.now(tz)
            else:
                # Parse ISO format
                try:
                    naive_dt = datetime.datetime.fromisoformat(timestamp)
                    dt = tz.localize(naive_dt)
                except ValueError:
                    return f"Invalid timestamp format: {timestamp}. Please use ISO format (YYYY-MM-DDTHH:MM:SS)."
            
            # Add the specified time
            # Handle years and months separately since they can change the number of days in a month
            if years != 0 or months != 0:
                # Get the year, month, and day
                year = dt.year + years
                month = dt.month + months
                
                # Adjust for month overflow
                if month > 12:
                    year += month // 12
                    month = month % 12
                    if month == 0:
                        month = 12
                        year -= 1
                
                # Adjust for month underflow
                if month < 1:
                    year -= (abs(month) // 12) + 1
                    month = 12 - (abs(month) % 12)
                
                # Adjust for day overflow (e.g., adding 1 month to January 31 should be February 28/29)
                day = min(dt.day, calendar.monthrange(year, month)[1])
                
                # Create a new datetime with the adjusted year, month, and day
                dt = dt.replace(year=year, month=month, day=day)
            
            # Add the remaining time components
            dt = dt + datetime.timedelta(days=days, hours=hours, minutes=minutes, seconds=seconds)
            
            # Format the result
            result = f"Original timestamp: {timestamp}\n"
            result += f"Time added: {years} years, {months} months, {days} days, "
            result += f"{hours} hours, {minutes} minutes, {seconds} seconds\n"
            result += f"Result: {dt.strftime('%Y-%m-%d %H:%M:%S %Z%z')}"
            
            logger.info(f"Added time: {result}")
            return result
        except Exception as e:
            logger.error(f"Error adding time: {e}")
            return f"Error adding time: {str(e)}"
    
    def get_month_calendar(self, year: Optional[int] = None, month: Optional[int] = None) -> str:
        """
        Get a calendar for a specific month.
        
        Args:
            year: Year (defaults to current year)
            month: Month (1-12, defaults to current month)
            
        Returns:
            A formatted calendar for the specified month
        """
        logger.info(f"Getting calendar for year={year}, month={month}")
        try:
            # Use current year/month if not specified
            now = datetime.datetime.now()
            year = year if year is not None else now.year
            month = month if month is not None else now.month
            
            # Validate month
            if month < 1 or month > 12:
                return f"Invalid month: {month}. Month must be between 1 and 12."
            
            # Get the calendar
            cal = calendar.monthcalendar(year, month)
            
            # Get the month name
            month_name = calendar.month_name[month]
            
            # Format the calendar
            result = f"{month_name} {year}\n"
            result += "Mo Tu We Th Fr Sa Su\n"
            
            for week in cal:
                for day in week:
                    if day == 0:
                        result += "   "
                    else:
                        result += f"{day:2d} "
                result += "\n"
            
            logger.info(f"Generated calendar for {month_name} {year}")
            return result
        except Exception as e:
            logger.error(f"Error getting month calendar: {e}")
            return f"Error getting month calendar: {str(e)}"
    
    def is_business_day(self, date: str, country: Optional[str] = None) -> str:
        """
        Check if a date is a business day (Monday-Friday).
        
        Args:
            date: Date to check (ISO format or 'today')
            country: Country code for holiday checking (not implemented yet)
            
        Returns:
            A string indicating whether the date is a business day
        """
        logger.info(f"Checking if {date} is a business day for country={country}")
        try:
            # Parse the date
            if date == "today":
                # Use current date
                dt = datetime.datetime.now().date()
            else:
                # Parse ISO format
                try:
                    dt = datetime.datetime.fromisoformat(date).date()
                except ValueError:
                    return f"Invalid date format: {date}. Please use ISO format (YYYY-MM-DD)."
            
            # Check if it's a weekday (Monday=0, Sunday=6)
            weekday = dt.weekday()
            is_weekday = weekday < 5  # Monday-Friday
            
            # Format the result
            weekday_name = calendar.day_name[weekday]
            result = f"Date: {dt.isoformat()} ({weekday_name})\n"
            
            if is_weekday:
                result += "This is a business day (Monday-Friday)."
            else:
                result += "This is not a business day (weekend)."
            
            # Note about holidays
            if country:
                result += f"\nNote: Holiday checking for {country} is not implemented yet."
            
            logger.info(f"Business day check result: {is_weekday}")
            return result
        except Exception as e:
            logger.error(f"Error checking business day: {e}")
            return f"Error checking business day: {str(e)}"
