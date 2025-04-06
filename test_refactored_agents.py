"""
Test script for the refactored SQLAgentPlugin and TimeAgentPlugin.

This script demonstrates how to use the plugin architecture to load and use
the refactored SQLAgentPlugin and TimeAgentPlugin.
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
    logger.info("Starting refactored agents test")
    
    # Create the MCP server
    server_name = "MCP Refactored Agents Test"
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
    
    # Test the SQLAgentPlugin tools
    logger.info("Testing SQLAgentPlugin tools")
    
    # Get the SQLAgentPlugin
    sql_agent = manager.get_plugin("SQLAgentPlugin")
    if not sql_agent:
        logger.error("SQLAgentPlugin not found")
    else:
        # Test list_tables
        logger.info("Testing list_tables tool")
        result = sql_agent.list_tables()
        logger.info(f"list_tables result: {result}")
        
        # Test get_database_schema
        logger.info("Testing get_database_schema tool")
        result = sql_agent.get_database_schema()
        logger.info(f"get_database_schema result: {result}")
        
        # Test query_data (if tables exist)
        logger.info("Testing query_data tool")
        result = sql_agent.query_data("SELECT sqlite_version();")
        logger.info(f"query_data result: {result}")
    
    # Test the TimeAgentPlugin tools
    logger.info("Testing TimeAgentPlugin tools")
    
    # Get the TimeAgentPlugin
    time_agent = manager.get_plugin("TimeAgentPlugin")
    if not time_agent:
        logger.error("TimeAgentPlugin not found")
    else:
        # Test get_current_time
        logger.info("Testing get_current_time tool")
        result = time_agent.get_current_time(format="human")
        logger.info(f"get_current_time result: {result}")
        
        # Test calculate_time_difference
        logger.info("Testing calculate_time_difference tool")
        from datetime import datetime, timedelta
        now = datetime.now().isoformat()
        one_hour_ago = (datetime.now() - timedelta(hours=1)).isoformat()
        result = time_agent.calculate_time_difference(
            start_time=one_hour_ago,
            end_time=now,
            unit="minutes"
        )
        logger.info(f"calculate_time_difference result: {result}")
        
        # Test format_timestamp
        logger.info("Testing format_timestamp tool")
        result = time_agent.format_timestamp(
            timestamp=now,
            format="human"
        )
        logger.info(f"format_timestamp result: {result}")
        
        # Test get_time_in_timezone
        logger.info("Testing get_time_in_timezone tool")
        result = time_agent.get_time_in_timezone(timezone="America/New_York")
        logger.info(f"get_time_in_timezone result: {result}")
    
    # Test the TimeFunctionsAgent tools
    logger.info("Testing TimeFunctionsAgent tools")
    
    # Get the TimeFunctionsAgent
    time_functions_agent = manager.get_plugin("TimeFunctionsAgent")
    if not time_functions_agent:
        logger.error("TimeFunctionsAgent not found")
    else:
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
    
    logger.info("Refactored agents test completed successfully")

if __name__ == "__main__":
    main()
