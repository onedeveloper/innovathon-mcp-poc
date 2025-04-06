"""
Updated MCP server implementation with support for multiple agents.

This module provides an updated MCP server implementation that uses the
plugin architecture to support multiple agents.
"""
import sqlite3
import logging
from loguru import logger
from mcp.server.fastmcp import FastMCP
from core.config import Config
from core.registry import AgentRegistry
from core.tool_schema import ToolSchemaHandler
from agents.sql_agent import SQLAgent
from agents.time_agent import TimeAgent

# Set up logging
logging_logger = logging.getLogger(__name__)

# Create an MCP server
config = Config()
server_name = config.get("server.name", "MCP Demo")
mcp = FastMCP(server_name)

# Initialize the registry
registry = AgentRegistry()

# Initialize and register agents
sql_agent = SQLAgent(config.get("database.path", "./database.db"))
sql_agent.initialize()
sql_agent.register_tools()

time_agent = TimeAgent()
time_agent.initialize()
time_agent.register_tools()

# Register agents with the registry
registry.register_agent("SQLAgent", sql_agent)
registry.register_agent("TimeAgent", time_agent)

# Register tools with the MCP server
tools = registry.get_all_tools()
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
        input_schema=tool_info["schema"]  # Fixed: Now properly passing the schema
    )(wrapper)

# Log the registered tools
logging_logger.info(f"Registered {len(tools)} tools with the MCP server")
for name in tools.keys():
    logging_logger.info(f"  - {name}")

if __name__ == "__main__":
    print("Starting server...")
    # Initialize and run the server
    # In a real implementation, we would start the server here
    # For now, this is just a placeholder as the server is started by the client
