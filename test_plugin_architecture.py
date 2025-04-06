"""
Test script for the MCP Server/Client application with the new plugin architecture.

This script demonstrates how to use the plugin architecture to load and use
the TimeFunctionsAgent.
"""
import logging
import sys
from core.plugin_registry import PluginRegistry
from core.plugin_manager import PluginManager
from mcp.server.fastmcp import FastMCP

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s | %(levelname)-8s | %(name)s:%(funcName)s:%(lineno)d - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)

def main():
    """Main entry point for the test script."""
    logger.info("Starting plugin architecture test")
    
    # Create the MCP server
    server_name = "MCP Plugin Test"
    mcp = FastMCP(server_name)
    
    # Create the plugin registry and manager
    registry = PluginRegistry()
    manager = PluginManager(registry)
    
    # Discover, load, and initialize plugins
    logger.info("Loading and initializing plugins")
    success = manager.load_and_initialize_all()
    
    if not success:
        logger.error("Failed to load and initialize plugins")
        return
    
    # Get all tools from the registry
    tools = registry.get_all_tools()
    logger.info(f"Loaded {len(tools)} tools from {len(manager.get_all_plugins())} plugins")
    
    # Register tools with the MCP server
    for name, tool_info in tools.items():
        # Create a wrapper function to call the tool function
        def create_tool_wrapper(tool_func):
            def wrapper(*args, **kwargs):
                return tool_func(*args, **kwargs)
            return wrapper
        
        # Register the tool with the MCP server
        wrapper = create_tool_wrapper(tool_info["function"])
        mcp.tool(
            name=name,
            description=tool_info["description"],
            input_schema=tool_info["schema"]
        )(wrapper)
        
        logger.info(f"Registered tool: {name}")
    
    # Log the registered tools
    logger.info(f"Registered {len(tools)} tools with the MCP server")
    for name in tools.keys():
        logger.info(f"  - {name}")
    
    # Test the TimeFunctionsAgent tools
    logger.info("Testing TimeFunctionsAgent tools")
    
    # Get the TimeFunctionsAgent
    time_functions_agent = manager.get_plugin("TimeFunctionsAgent")
    if not time_functions_agent:
        logger.error("TimeFunctionsAgent not found")
        return
    
    # Test list_timezones
    logger.info("Testing list_timezones tool")
    result = time_functions_agent.list_timezones(region="US")
    logger.info(f"list_timezones result: {result[:100]}...")
    
    # Test convert_timezone
    logger.info("Testing convert_timezone tool")
    result = time_functions_agent.convert_timezone(
        from_timezone="UTC",
        to_timezone="America/New_York",
        time="now"
    )
    logger.info(f"convert_timezone result: {result}")
    
    # Test add_time
    logger.info("Testing add_time tool")
    result = time_functions_agent.add_time(
        timestamp="now",
        days=1,
        hours=2,
        minutes=30
    )
    logger.info(f"add_time result: {result}")
    
    # Test get_month_calendar
    logger.info("Testing get_month_calendar tool")
    result = time_functions_agent.get_month_calendar()
    logger.info(f"get_month_calendar result:\n{result}")
    
    # Test is_business_day
    logger.info("Testing is_business_day tool")
    result = time_functions_agent.is_business_day(date="today")
    logger.info(f"is_business_day result: {result}")
    
    logger.info("Plugin architecture test completed successfully")

if __name__ == "__main__":
    main()
