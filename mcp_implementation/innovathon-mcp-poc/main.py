"""
Main entry point for the MCP Server/Client application.

This module provides the main entry point for running the application
in either server or client mode.
"""
import os
import sys
import argparse
import logging
from core.config import Config
from core.server_factory import MCPServerFactory
from agents.sql_agent import SQLAgent
from agents.time_agent import TimeAgent

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s | %(levelname)-8s | %(name)s:%(funcName)s:%(lineno)d - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)

def main():
    """Main entry point for the application."""
    # Parse command line arguments
    parser = argparse.ArgumentParser(description="MCP Server/Client Application")
    parser.add_argument("--server-mode", action="store_true", help="Run in server mode")
    parser.add_argument("--client-mode", action="store_true", help="Run in client mode")
    parser.add_argument("--web-mode", action="store_true", help="Run in web interface mode")
    args = parser.parse_args()
    
    # Load configuration
    config = Config()
    
    # Determine the mode to run in
    if args.server_mode:
        run_server_mode(config)
    elif args.client_mode:
        run_client_mode(config)
    elif args.web_mode:
        run_web_mode(config)
    else:
        # Default to web mode if no mode is specified
        run_web_mode(config)

def run_server_mode(config):
    """
    Run the application in server mode.
    
    Args:
        config: The application configuration
    """
    logger.info("Starting in server mode")
    
    # Get the list of enabled agents
    enabled_agents = config.get("server.agents", ["SQLAgent", "TimeAgent"])
    logger.info(f"Enabled agents: {enabled_agents}")
    
    # Create the server with the enabled agents
    server_name = config.get("server.name", "MCP Demo")
    
    # Convert agent names to module paths
    agent_modules = []
    for agent_name in enabled_agents:
        if agent_name == "SQLAgent":
            agent_modules.append("agents.sql_agent.SQLAgent")
        elif agent_name == "TimeAgent":
            agent_modules.append("agents.time_agent.TimeAgent")
        else:
            logger.warning(f"Unknown agent: {agent_name}")
    
    # Create the server
    mcp = MCPServerFactory.create_server(server_name, agent_modules)
    
    # Start the server
    logger.info(f"Server {server_name} started with {len(agent_modules)} agents")
    
    # In a real implementation, we would start the server here
    # For now, this is just a placeholder as the server is started by the client

def run_client_mode(config):
    """
    Run the application in client mode.
    
    Args:
        config: The application configuration
    """
    logger.info("Starting in client mode")
    
    # Import the client module here to avoid circular imports
    from mcp_client import run_client
    
    # Run the client
    run_client()

def run_web_mode(config):
    """
    Run the application in web interface mode.
    
    Args:
        config: The application configuration
    """
    logger.info("Starting in web interface mode")
    
    # Import the app module here to avoid circular imports
    from app import run_app
    
    # Run the web interface
    run_app()

if __name__ == "__main__":
    main()
