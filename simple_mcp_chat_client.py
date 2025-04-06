"""
Simplified CLI Chat Client for the MCP Server/Client application.

This module provides a command-line interface for interacting with the local MCP Server
implementation without relying on external mcp-server package.
"""
import asyncio
import argparse
import os
import json
import logging
import subprocess
import sys
from typing import Dict, Any, List, Optional

# Try to import rich for enhanced console output
try:
    from rich.console import Console
    from rich.markdown import Markdown
    from rich.panel import Panel
    from rich.prompt import Prompt
    from rich.syntax import Syntax
    from rich.table import Table
    from rich.text import Text
    RICH_AVAILABLE = True
except ImportError:
    RICH_AVAILABLE = False
    print("Rich library not available. Using standard console output.")
    print("To install Rich: uv add rich")

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s | %(levelname)-8s | %(name)s:%(funcName)s:%(lineno)d - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)

# Initialize Rich console if available
if RICH_AVAILABLE:
    console = Console()

class SimpleMCPClient:
    """
    Simple client for interacting with the MCP Server.
    
    This class provides a simplified interface for calling tools on the MCP Server
    without relying on the external mcp-server package.
    """
    
    def __init__(self, server_script: str = "./mcp_server.py"):
        """
        Initialize the Simple MCP Client.
        
        Args:
            server_script: Path to the MCP Server script
        """
        self.server_script = server_script
        self.server_process = None
    
    async def start_server(self):
        """Start the MCP Server in a separate process."""
        try:
            # Start the server process
            self.server_process = subprocess.Popen(
                [sys.executable, self.server_script],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )
            logger.info(f"Started MCP Server with PID {self.server_process.pid}")
            
            # Wait a moment for the server to initialize
            await asyncio.sleep(2)
            
            return True
        except Exception as e:
            logger.error(f"Error starting MCP Server: {e}")
            return False
    
    def stop_server(self):
        """Stop the MCP Server process."""
        if self.server_process:
            self.server_process.terminate()
            logger.info("Stopped MCP Server")
    
    async def list_tools(self):
        """
        List available tools on the MCP Server.
        
        Returns:
            A list of available tools
        """
        # This is a simplified implementation that parses the server script
        # to extract tool information
        tools = []
        
        try:
            with open(self.server_script, 'r') as f:
                server_code = f.read()
            
            # Look for tool registrations in the server code
            import re
            tool_registrations = re.findall(r'mcp\.tool\(\s*name=[\'"]([^\'"]+)[\'"],\s*description=[\'"]([^\'"]+)[\'"]', server_code)
            
            for name, description in tool_registrations:
                tools.append({
                    "name": name,
                    "description": description
                })
            
            # If no tools found in the server code, provide some default tools
            if not tools:
                tools = [
                    {"name": "get_current_time", "description": "Get the current time"},
                    {"name": "list_tables", "description": "List database tables"},
                    {"name": "get_database_schema", "description": "Get database schema"},
                    {"name": "query_data", "description": "Execute SQL query"}
                ]
            
            logger.info(f"Found {len(tools)} tools")
            return tools
        except Exception as e:
            logger.error(f"Error listing tools: {e}")
            return []
    
    async def call_tool(self, tool_name: str, tool_args: Dict[str, Any] = None):
        """
        Call a tool on the MCP Server.
        
        Args:
            tool_name: The name of the tool to call
            tool_args: The arguments to pass to the tool
            
        Returns:
            The result of the tool call
        """
        tool_args = tool_args or {}
        
        # This is a simplified implementation that directly calls the tool functions
        # In a real implementation, this would communicate with the server process
        
        # Import the necessary modules
        try:
            # Try to import from the agents directory
            if tool_name in ["get_current_time", "calculate_time_difference", "format_timestamp", "get_time_in_timezone"]:
                # Try to import the TimeAgentPlugin
                try:
                    from agents.time.plugin import TimeAgentPlugin
                    time_agent = TimeAgentPlugin()
                    
                    if tool_name == "get_current_time":
                        result = time_agent.get_current_time(**tool_args)
                    elif tool_name == "calculate_time_difference":
                        result = time_agent.calculate_time_difference(**tool_args)
                    elif tool_name == "format_timestamp":
                        result = time_agent.format_timestamp(**tool_args)
                    elif tool_name == "get_time_in_timezone":
                        result = time_agent.get_time_in_timezone(**tool_args)
                    
                    return result
                except ImportError:
                    logger.warning("TimeAgentPlugin not found, trying TimeAgent")
                    # Fall back to the original TimeAgent
                    import sys
                    sys.path.append('.')
                    from agents.time_agent import TimeAgent
                    time_agent = TimeAgent()
                    
                    if tool_name == "get_current_time":
                        result = time_agent.get_current_time(**tool_args)
                    elif tool_name == "calculate_time_difference":
                        result = time_agent.calculate_time_difference(**tool_args)
                    elif tool_name == "format_timestamp":
                        result = time_agent.format_timestamp(**tool_args)
                    elif tool_name == "get_time_in_timezone":
                        result = time_agent.get_time_in_timezone(**tool_args)
                    
                    return result
            
            elif tool_name in ["list_timezones", "convert_timezone", "add_time", "get_month_calendar", "is_business_day"]:
                # Try to import the TimeFunctionsAgent
                try:
                    from agents.time_functions.plugin import TimeFunctionsAgent
                    time_functions_agent = TimeFunctionsAgent()
                    
                    if tool_name == "list_timezones":
                        result = time_functions_agent.list_timezones(**tool_args)
                    elif tool_name == "convert_timezone":
                        result = time_functions_agent.convert_timezone(**tool_args)
                    elif tool_name == "add_time":
                        result = time_functions_agent.add_time(**tool_args)
                    elif tool_name == "get_month_calendar":
                        result = time_functions_agent.get_month_calendar(**tool_args)
                    elif tool_name == "is_business_day":
                        result = time_functions_agent.is_business_day(**tool_args)
                    
                    return result
                except ImportError:
                    logger.error(f"TimeFunctionsAgent not found for tool {tool_name}")
                    return f"Error: TimeFunctionsAgent not found for tool {tool_name}"
            
            elif tool_name in ["query_data", "list_tables", "get_database_schema"]:
                # Try to import the SQLAgentPlugin
                try:
                    from agents.sql.plugin import SQLAgentPlugin
                    sql_agent = SQLAgentPlugin()
                    
                    if tool_name == "query_data":
                        result = sql_agent.query_data(**tool_args)
                    elif tool_name == "list_tables":
                        result = sql_agent.list_tables()
                    elif tool_name == "get_database_schema":
                        result = sql_agent.get_database_schema()
                    
                    return result
                except ImportError:
                    logger.warning("SQLAgentPlugin not found, trying SQLAgent")
                    # Fall back to the original SQLAgent
                    import sys
                    sys.path.append('.')
                    from agents.sql_agent import SQLAgent
                    sql_agent = SQLAgent()
                    
                    if tool_name == "query_data":
                        result = sql_agent.query_data(**tool_args)
                    elif tool_name == "list_tables":
                        result = sql_agent.list_tables()
                    elif tool_name == "get_database_schema":
                        result = sql_agent.get_database_schema()
                    
                    return result
            
            else:
                logger.error(f"Unknown tool: {tool_name}")
                return f"Error: Unknown tool {tool_name}"
        
        except Exception as e:
            logger.error(f"Error calling tool {tool_name}: {e}")
            return f"Error calling tool {tool_name}: {str(e)}"

class SimpleMCPChatClient:
    """
    Simplified CLI Chat Client for interacting with the MCP Server.
    
    This class provides a command-line interface for sending messages to the MCP Server
    and displaying the responses in a chat-like format.
    """
    
    def __init__(self, server_script: str = "./mcp_server.py", model: str = None):
        """
        Initialize the Simplified MCP Chat Client.
        
        Args:
            server_script: Path to the MCP Server script
            model: The model to use for the chat (if using Ollama)
        """
        self.server_script = server_script
        self.model = model or os.getenv("OLLAMA_MODEL_NAME", "llama3.2:1b")
        self.messages = []
        self.system_prompt = """You are a helpful assistant with access to various tools.
        You can use these tools to help the user with their questions and tasks.
        Always use the appropriate tool when needed, and explain your reasoning.
        """
        
        # Create the MCP client
        self.mcp_client = SimpleMCPClient(server_script)
        
        # Initialize Ollama client if available and requested
        self.use_ollama = False
        if model:
            try:
                import ollama
                self.ollama_client = ollama.AsyncClient()
                self.use_ollama = True
                logger.info(f"Using Ollama with model: {self.model}")
            except ImportError:
                logger.warning("Ollama not available, using direct tool calls only")
    
    async def start(self):
        """Start the Simplified MCP Chat Client."""
        if RICH_AVAILABLE:
            console.print(Panel.fit(
                "[bold blue]Simplified MCP Chat Client[/bold blue]\n"
                "Type your messages to interact with the MCP Server and its agents.\n"
                "Type [bold]exit[/bold], [bold]quit[/bold], or [bold]bye[/bold] to exit.",
                title="Welcome",
                border_style="blue"
            ))
        else:
            print("=" * 80)
            print("Simplified MCP Chat Client")
            print("Type your messages to interact with the MCP Server and its agents.")
            print("Type 'exit', 'quit', or 'bye' to exit.")
            print("=" * 80)
        
        # Add system prompt to messages
        self.messages.append({"role": "system", "content": self.system_prompt})
        
        # Start the MCP Server
        server_started = await self.mcp_client.start_server()
        if not server_started:
            if RICH_AVAILABLE:
                console.print("[bold red]Failed to start MCP Server. Exiting...[/bold red]")
            else:
                print("Failed to start MCP Server. Exiting...")
            return
        
        try:
            # Get available tools
            tools = await self.mcp_client.list_tools()
            available_tools = [
                {
                    "type": "function",
                    "function": {
                        "name": tool["name"],
                        "description": tool["description"],
                        "parameters": {"type": "object", "properties": {}},
                    },
                }
                for tool in tools
            ]
            
            # Display available tools
            self.display_available_tools(tools)
            
            # Start the chat loop
            await self.chat_loop(available_tools)
        
        finally:
            # Stop the MCP Server
            self.mcp_client.stop_server()
    
    def display_available_tools(self, tools):
        """
        Display the available tools.
        
        Args:
            tools: The list of available tools
        """
        if RICH_AVAILABLE:
            table = Table(title="Available Tools")
            table.add_column("Name", style="cyan")
            table.add_column("Description", style="green")
            
            for tool in tools:
                table.add_row(tool["name"], tool["description"])
            
            console.print(table)
            console.print()
        else:
            print("\nAvailable Tools:")
            print("-" * 80)
            for tool in tools:
                print(f"{tool['name']}: {tool['description']}")
            print("-" * 80)
            print()
    
    async def chat_loop(self, available_tools):
        """
        Run the chat loop.
        
        Args:
            available_tools: The list of available tools
        """
        while True:
            # Get user input
            if RICH_AVAILABLE:
                user_input = Prompt.ask("[bold blue]You[/bold blue]")
            else:
                user_input = input("You: ")
            
            # Check for exit commands
            if user_input.lower() in ["exit", "quit", "bye"]:
                if RICH_AVAILABLE:
                    console.print("[bold blue]Exiting chat...[/bold blue]")
                else:
                    print("Exiting chat...")
                break
            
            # Add user message to history
            self.messages.append({"role": "user", "content": user_input})
            
            # Process the message
            await self.process_message(user_input, available_tools)
    
    async def process_message(self, message, available_tools):
        """
        Process a user message.
        
        Args:
            message: The user message
            available_tools: The list of available tools
        """
        if self.use_ollama:
            # Use Ollama for processing
            await self.process_with_ollama(available_tools)
        else:
            # Use direct tool calls
            await self.process_direct_tool_call(message)
    
    async def process_with_ollama(self, available_tools):
        """
        Process a message using Ollama.
        
        Args:
            available_tools: The list of available tools
        """
        try:
            # Call Ollama API
            if RICH_AVAILABLE:
                console.print("[bold yellow]Assistant is thinking...[/bold yellow]")
            else:
                print("Assistant is thinking...")
                
            response = await self.ollama_client.chat(
                model=self.model,
                messages=self.messages,
                tools=available_tools,
                stream=False,
            )
            
            assistant_message = response['message']
            self.messages.append(assistant_message)
            
            # Handle tool calls
            tool_executed = False
            
            if assistant_message.get('tool_calls'):
                for tool_call in assistant_message['tool_calls']:
                    # Extract tool name and arguments
                    tool_name = tool_call.get('function', {}).get('name')
                    tool_args_str = tool_call.get('function', {}).get('arguments', '{}')
                    
                    if not tool_name:
                        if RICH_AVAILABLE:
                            console.print("[bold red]Warning: No tool name found in tool call[/bold red]")
                        else:
                            print("Warning: No tool name found in tool call")
                        continue
                    
                    # Parse tool arguments
                    try:
                        tool_args = json.loads(tool_args_str) if isinstance(tool_args_str, str) else tool_args_str
                    except json.JSONDecodeError:
                        if RICH_AVAILABLE:
                            console.print(f"[bold red]Error parsing tool arguments: {tool_args_str}[/bold red]")
                        else:
                            print(f"Error parsing tool arguments: {tool_args_str}")
                        continue
                    
                    # Display tool call
                    if RICH_AVAILABLE:
                        console.print(f"[bold yellow]Calling tool: {tool_name}[/bold yellow]")
                        syntax = Syntax(json.dumps(tool_args, indent=2), "json", theme="monokai")
                        console.print(syntax)
                    else:
                        print(f"Calling tool: {tool_name}")
                        print(f"Arguments: {json.dumps(tool_args, indent=2)}")
                    
                    # Call the tool
                    tool_result = await self.mcp_client.call_tool(tool_name, tool_args)
                    
                    # Display tool result
                    if RICH_AVAILABLE:
                        console.print(f"[bold green]Tool result:[/bold green]")
                        console.print(Markdown(str(tool_result)))
                    else:
                        print(f"Tool result:")
                        print(str(tool_result))
                    
                    # Add tool result to messages
                    self.messages.append({
                        "role": "tool",
                        "content": f"Tool execution result for {tool_name}: {str(tool_result)}"
                    })
                    tool_executed = True
            
            # Make follow-up call if tool was executed
            if tool_executed:
                if RICH_AVAILABLE:
                    console.print("[bold yellow]Assistant is thinking...[/bold yellow]")
                else:
                    print("Assistant is thinking...")
                    
                final_response = await self.ollama_client.chat(
                    model=self.model,
                    messages=self.messages,
                    stream=False,
                )
                final_assistant_message = final_response['message']
                self.messages.append(final_assistant_message)
                
                # Display final response
                if final_assistant_message.get('content'):
                    if RICH_AVAILABLE:
                        console.print(f"[bold green]Assistant:[/bold green]")
                        console.print(Markdown(final_assistant_message['content']))
                    else:
                        print(f"Assistant:")
                        print(final_assistant_message['content'])
            
            # Display original response if no tool was executed
            elif assistant_message.get('content'):
                if RICH_AVAILABLE:
                    console.print(f"[bold green]Assistant:[/bold green]")
                    console.print(Markdown(assistant_message['content']))
                else:
                    print(f"Assistant:")
                    print(assistant_message['content'])
        
        except Exception as e:
            if RICH_AVAILABLE:
                console.print(f"[bold red]Error during Ollama interaction: {e}[/bold red]")
            else:
                print(f"Error during Ollama interaction: {e}")
    
    async def process_direct_tool_call(self, message):
        """
        Process a message using direct tool calls.
        
        Args:
            message: The user message
        """
        # Simple parsing for direct tool calls
        # Format: "tool:tool_name{arg1:value1,arg2:value2}"
        if message.startswith("tool:"):
            try:
                # Parse the tool call
                tool_part = message[5:]  # Remove "tool:" prefix
                tool_name_end = tool_part.find("{")
                
                if tool_name_end == -1:
                    # No arguments
                    tool_name = tool_part
                    tool_args = {}
                else:
                    # With arguments
                    tool_name = tool_part[:tool_name_end]
                    args_str = tool_part[tool_name_end:]
                    
                    # Parse arguments
                    if args_str.startswith("{") and args_str.endswith("}"):
                        args_str = args_str[1:-1]  # Remove { and }
                        args_parts = args_str.split(",")
                        tool_args = {}
                        
                        for part in args_parts:
                            if ":" in part:
                                key, value = part.split(":", 1)
                                tool_args[key.strip()] = value.strip()
                    else:
                        tool_args = {}
                
                # Display tool call
                if RICH_AVAILABLE:
                    console.print(f"[bold yellow]Calling tool: {tool_name}[/bold yellow]")
                    syntax = Syntax(json.dumps(tool_args, indent=2), "json", theme="monokai")
                    console.print(syntax)
                else:
                    print(f"Calling tool: {tool_name}")
                    print(f"Arguments: {json.dumps(tool_args, indent=2)}")
                
                # Call the tool
                tool_result = await self.mcp_client.call_tool(tool_name, tool_args)
                
                # Display tool result
                if RICH_AVAILABLE:
                    console.print(f"[bold green]Tool result:[/bold green]")
                    console.print(Markdown(str(tool_result)))
                else:
                    print(f"Tool result:")
                    print(str(tool_result))
            
            except Exception as e:
                if RICH_AVAILABLE:
                    console.print(f"[bold red]Error calling tool: {e}[/bold red]")
                else:
                    print(f"Error calling tool: {e}")
        else:
            if RICH_AVAILABLE:
                console.print("[bold yellow]Direct message mode (no LLM):[/bold yellow]")
                console.print("To call a tool, use the format: tool:tool_name{arg1:value1,arg2:value2}")
                console.print("Example: tool:get_current_time{format:human}")
                console.print("Example: tool:query_data{sql:SELECT sqlite_version();}")
            else:
                print("Direct message mode (no LLM):")
                print("To call a tool, use the format: tool:tool_name{arg1:value1,arg2:value2}")
                print("Example: tool:get_current_time{format:human}")
                print("Example: tool:query_data{sql:SELECT sqlite_version();}")

def main():
    """Main entry point for the Simplified CLI Chat Client."""
    parser = argparse.ArgumentParser(description="Simplified MCP Chat Client")
    parser.add_argument("--server-script", default="./mcp_server.py", help="Path to the MCP Server script")
    parser.add_argument("--model", default=None, help="Model to use (if using Ollama)")
    args = parser.parse_args()
    
    # Create and start the chat client
    chat_client = SimpleMCPChatClient(
        server_script=args.server_script,
        model=args.model,
    )
    
    # Run the chat client
    asyncio.run(chat_client.start())

if __name__ == "__main__":
    main()

