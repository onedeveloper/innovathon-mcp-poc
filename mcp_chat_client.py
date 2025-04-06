"""
CLI Chat Client for the MCP Server/Client application.

This module provides a command-line interface for interacting with the MCP Server
and its agents through a chat-like interface.
"""
import asyncio
import argparse
import os
import json
import logging
from typing import Dict, Any, List, Optional
from rich.console import Console
from rich.markdown import Markdown
from rich.panel import Panel
from rich.prompt import Prompt
from rich.syntax import Syntax
from rich.table import Table
from rich.text import Text
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
from core.tool_handler import ToolCallHandler

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s | %(levelname)-8s | %(name)s:%(funcName)s:%(lineno)d - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)

# Initialize Rich console
console = Console()

class MCPChatClient:
    """
    CLI Chat Client for interacting with the MCP Server.
    
    This class provides a command-line interface for sending messages to the MCP Server
    and displaying the responses in a chat-like format.
    """
    
    def __init__(self, server_command: str = "python", server_args: List[str] = None, model: str = None):
        """
        Initialize the MCP Chat Client.
        
        Args:
            server_command: The command to start the MCP Server
            server_args: The arguments to pass to the server command
            model: The model to use for the chat (if using Ollama)
        """
        self.server_command = server_command
        self.server_args = server_args or ["./mcp_server.py"]
        self.model = model or os.getenv("OLLAMA_MODEL_NAME", "llama3.2:1b")
        self.messages = []
        self.system_prompt = """You are a helpful assistant with access to various tools.
        You can use these tools to help the user with their questions and tasks.
        Always use the appropriate tool when needed, and explain your reasoning.
        """
        
        # Create server parameters for stdio connection
        self.server_params = StdioServerParameters(
            command=self.server_command,
            args=self.server_args,
            env=None,
        )
        
        # Initialize Ollama client if available
        try:
            import ollama
            self.ollama_client = ollama.AsyncClient()
            self.use_ollama = True
            logger.info(f"Using Ollama with model: {self.model}")
        except ImportError:
            self.use_ollama = False
            logger.warning("Ollama not available, using direct tool calls only")
    
    async def start(self):
        """Start the MCP Chat Client."""
        console.print(Panel.fit(
            "[bold blue]MCP Chat Client[/bold blue]\n"
            "Type your messages to interact with the MCP Server and its agents.\n"
            "Type [bold]exit[/bold], [bold]quit[/bold], or [bold]bye[/bold] to exit.",
            title="Welcome",
            border_style="blue"
        ))
        
        # Add system prompt to messages
        self.messages.append({"role": "system", "content": self.system_prompt})
        
        # Connect to the MCP Server
        async with stdio_client(self.server_params) as (read, write):
            async with ClientSession(read, write) as session:
                # Initialize the connection
                await session.initialize()
                
                # Get available tools
                tools_response = await session.list_tools()
                available_tools = [
                    {
                        "type": "function",
                        "function": {
                            "name": tool.name,
                            "description": tool.description or "",
                            "parameters": tool.inputSchema,
                        },
                    }
                    for tool in tools_response.tools
                ]
                
                # Display available tools
                self.display_available_tools(tools_response.tools)
                
                # Start the chat loop
                await self.chat_loop(session, available_tools)
    
    def display_available_tools(self, tools):
        """
        Display the available tools in a table.
        
        Args:
            tools: The list of available tools
        """
        table = Table(title="Available Tools")
        table.add_column("Name", style="cyan")
        table.add_column("Description", style="green")
        
        for tool in tools:
            table.add_row(tool.name, tool.description or "")
        
        console.print(table)
        console.print()
    
    async def chat_loop(self, session, available_tools):
        """
        Run the chat loop.
        
        Args:
            session: The MCP client session
            available_tools: The list of available tools
        """
        while True:
            # Get user input
            user_input = Prompt.ask("[bold blue]You[/bold blue]")
            
            # Check for exit commands
            if user_input.lower() in ["exit", "quit", "bye"]:
                console.print("[bold blue]Exiting chat...[/bold blue]")
                break
            
            # Add user message to history
            self.messages.append({"role": "user", "content": user_input})
            
            # Process the message
            await self.process_message(session, user_input, available_tools)
    
    async def process_message(self, session, message, available_tools):
        """
        Process a user message.
        
        Args:
            session: The MCP client session
            message: The user message
            available_tools: The list of available tools
        """
        if self.use_ollama:
            # Use Ollama for processing
            await self.process_with_ollama(session, available_tools)
        else:
            # Use direct tool calls
            await self.process_direct_tool_call(session, message)
    
    async def process_with_ollama(self, session, available_tools):
        """
        Process a message using Ollama.
        
        Args:
            session: The MCP client session
            available_tools: The list of available tools
        """
        try:
            # Call Ollama API
            console.print("[bold yellow]Assistant is thinking...[/bold yellow]")
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
                    tool_name, tool_args, error = ToolCallHandler.parse_tool_call(tool_call)
                    
                    if error:
                        console.print(f"[bold red]Error parsing tool call: {error}[/bold red]")
                        continue
                    
                    if not tool_name:
                        console.print("[bold red]Warning: No tool name found in tool call[/bold red]")
                        continue
                    
                    # Display tool call
                    console.print(f"[bold yellow]Calling tool: {tool_name}[/bold yellow]")
                    syntax = Syntax(json.dumps(tool_args, indent=2), "json", theme="monokai")
                    console.print(syntax)
                    
                    # Call the tool
                    mcp_tool_result = await session.call_tool(tool_name, tool_args)
                    tool_result_content = getattr(mcp_tool_result.content[0], "text", "")
                    
                    # Display tool result
                    console.print(f"[bold green]Tool result:[/bold green]")
                    console.print(Markdown(tool_result_content))
                    
                    # Format the tool result
                    formatted_result = ToolCallHandler.format_tool_result(tool_name, tool_result_content)
                    self.messages.append(formatted_result)
                    tool_executed = True
            
            # Check for <toolcall> tag in content
            elif assistant_message.get('content') and '<toolcall>' in assistant_message['content']:
                content_str = assistant_message['content']
                
                # Parse tool call
                tool_name, tool_args, error = ToolCallHandler.parse_tool_call(content_str)
                
                if error:
                    console.print(f"[bold red]Error parsing <toolcall> tag: {error}[/bold red]")
                else:
                    # Display tool call
                    console.print(f"[bold yellow]Calling tool (from tag): {tool_name}[/bold yellow]")
                    syntax = Syntax(json.dumps(tool_args, indent=2), "json", theme="monokai")
                    console.print(syntax)
                    
                    # Call the tool
                    mcp_tool_result = await session.call_tool(tool_name, tool_args)
                    tool_result_content = getattr(mcp_tool_result.content[0], "text", "")
                    
                    # Display tool result
                    console.print(f"[bold green]Tool result:[/bold green]")
                    console.print(Markdown(tool_result_content))
                    
                    # Format the tool result
                    formatted_result = ToolCallHandler.format_tool_result(tool_name, tool_result_content)
                    self.messages.append(formatted_result)
                    tool_executed = True
            
            # Make follow-up call if tool was executed
            if tool_executed:
                console.print("[bold yellow]Assistant is thinking...[/bold yellow]")
                final_response = await self.ollama_client.chat(
                    model=self.model,
                    messages=self.messages,
                    stream=False,
                )
                final_assistant_message = final_response['message']
                self.messages.append(final_assistant_message)
                
                # Display final response
                if final_assistant_message.get('content'):
                    console.print(f"[bold green]Assistant:[/bold green]")
                    console.print(Markdown(final_assistant_message['content']))
            
            # Display original response if no tool was executed
            elif assistant_message.get('content'):
                console.print(f"[bold green]Assistant:[/bold green]")
                console.print(Markdown(assistant_message['content']))
        
        except Exception as e:
            console.print(f"[bold red]Error during Ollama interaction: {e}[/bold red]")
    
    async def process_direct_tool_call(self, session, message):
        """
        Process a message using direct tool calls.
        
        Args:
            session: The MCP client session
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
                console.print(f"[bold yellow]Calling tool: {tool_name}[/bold yellow]")
                syntax = Syntax(json.dumps(tool_args, indent=2), "json", theme="monokai")
                console.print(syntax)
                
                # Call the tool
                mcp_tool_result = await session.call_tool(tool_name, tool_args)
                tool_result_content = getattr(mcp_tool_result.content[0], "text", "")
                
                # Display tool result
                console.print(f"[bold green]Tool result:[/bold green]")
                console.print(Markdown(tool_result_content))
            
            except Exception as e:
                console.print(f"[bold red]Error calling tool: {e}[/bold red]")
        else:
            console.print("[bold yellow]Direct message mode (no LLM):[/bold yellow]")
            console.print("To call a tool, use the format: tool:tool_name{arg1:value1,arg2:value2}")
            console.print("Example: tool:get_current_time{format:human}")
            console.print("Example: tool:query_data{sql:SELECT sqlite_version();}")

def main():
    """Main entry point for the CLI Chat Client."""
    parser = argparse.ArgumentParser(description="MCP Chat Client")
    parser.add_argument("--server", default="python", help="Server command")
    parser.add_argument("--server-args", nargs="+", default=["./mcp_server.py"], help="Server arguments")
    parser.add_argument("--model", default=None, help="Model to use (if using Ollama)")
    args = parser.parse_args()
    
    # Create and start the chat client
    chat_client = MCPChatClient(
        server_command=args.server,
        server_args=args.server_args,
        model=args.model,
    )
    
    # Run the chat client
    asyncio.run(chat_client.start())

if __name__ == "__main__":
    main()

