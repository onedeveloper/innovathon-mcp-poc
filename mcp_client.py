import asyncio
import json # Added for parsing Ollama tool args
import os # Added for environment variable access
from dataclasses import dataclass, field
from typing import Union, cast, List, Dict, Any # Added Dict, Any

import ollama # Replaced anthropic with ollama
# Removed Anthropic specific types
from dotenv import load_dotenv
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
from core.tool_handler import ToolCallHandler

load_dotenv()


# Initialize Ollama client
# Assuming Ollama server is running locally at default address http://localhost:11434
ollama_client = ollama.AsyncClient() 


# Create server parameters for stdio connection
server_params = StdioServerParameters(
    command="python",  # Executable
    args=["./mcp_server.py"],  # Optional command line arguments
    env=None,  # Optional environment variables
)


@dataclass
class Chat:
    messages: list[Dict[str, Any]] = field(default_factory=list) # Changed message format for Ollama

    system_prompt: str = """You are a master SQLite assistant.
        You have access to three tools:
        - `query_data`: Execute general SQL queries. Requires a parameter 'sql' containing the SQL string.
        - `get_database_schema`: Retrieve the CREATE TABLE statements for all tables. Takes no parameters.
        - `list_tables`: List the names of all tables in the database. Takes no parameters.

        **IMPORTANT INSTRUCTIONS:**
        1.  **To list tables:** Use the `list_tables` tool.
        2.  **To understand table structure (columns/types):** Use the `get_database_schema` tool.
        3.  **For queries requiring column knowledge** (e.g., SELECT *, INSERT, UPDATE, WHERE on specific columns, ORDER BY specific columns):
            a. **First, call `get_database_schema`** (unless you have *just* retrieved it in the immediately preceding turn).
            b. **Then, use the schema** to construct an accurate SQL query for the `query_data` tool. Only use columns present in the schema.
        4.  **For simple SELECT queries on known columns** (if schema was recently retrieved) or general queries not needing specific column names: Use the `query_data` tool directly.
        5.  When displaying query results, format them in a nice markdown table if appropriate.
        6.  Always explain the results of your query, the schema, or the table list clearly.
        7.  If a `query_data` call fails, explain the error using the schema information (if available) and suggest a valid query or the use of `get_database_schema`.
        """

    async def process_query(self, session: ClientSession, query: str) -> None:
        """Process a query using Ollama and print the response"""
        # Get available tools from MCP server
        mcp_response = await session.list_tools()
        # Format tools for Ollama API
        available_tools = [
            {
                "type": "function",
                "function": {
                    "name": tool.name,
                    "description": tool.description or "",
                    "parameters": tool.inputSchema,
                },
            }
            for tool in mcp_response.tools
        ]

        # Add system prompt if messages list is empty
        if not self.messages:
             self.messages.append({"role": "system", "content": self.system_prompt})

        # Add the user message (already added in chat_loop, so no need here)
        # self.messages.append({"role": "user", "content": query}) # Already added in chat_loop

        # Specify the Ollama model to use (e.g., llama3, change if needed)
        # Read model name from environment variable, default if not set
        model_name = os.getenv("OLLAMA_MODEL_NAME", "llama3.2:1b") # Updated default model

        try:
            # Initial Ollama API call
            response = await ollama_client.chat(
                model=model_name,
                messages=self.messages,
                tools=available_tools,
                stream=False, # Keep stream=False for simpler tool handling initially
            )

            assistant_message = response['message']
            self.messages.append(assistant_message) # Add assistant's response

            # --- Tool Call Handling ---
            tool_executed = False
            
            # Use the standardized ToolCallHandler to parse tool calls
            if assistant_message.get('tool_calls'):
                print("--- Handling tool calls ---")
                tool_executed = True
                for tool_call in assistant_message['tool_calls']:
                    tool_name, tool_args, error = ToolCallHandler.parse_tool_call(tool_call)
                    
                    if error:
                        print(f"--- Error parsing tool call: {error} ---")
                        continue
                        
                    if not tool_name:
                        print("--- Warning: No tool name found in tool call ---")
                        continue
                        
                    print(f"--- Calling tool: {tool_name} with args: {tool_args} ---")
                    mcp_tool_result = await session.call_tool(tool_name, cast(dict, tool_args))
                    tool_result_content = getattr(mcp_tool_result.content[0], "text", "")
                    print(f"--- Tool result: {tool_result_content} ---")
                    
                    # Format the tool result using the standardized handler
                    formatted_result = ToolCallHandler.format_tool_result(tool_name, tool_result_content)
                    self.messages.append(formatted_result)
            
            # Check for <toolcall> tag in content
            elif assistant_message.get('content') and '<toolcall>' in assistant_message['content']:
                print("--- Handling <toolcall> tag in content ---")
                content_str = assistant_message['content']
                
                # Use the standardized ToolCallHandler to parse tool calls
                tool_name, tool_args, error = ToolCallHandler.parse_tool_call(content_str)
                
                if error:
                    print(f"--- Error parsing <toolcall> tag: {error} ---")
                else:
                    tool_executed = True
                    print(f"--- Calling tool (from tag): {tool_name} with args: {tool_args} ---")
                    mcp_tool_result = await session.call_tool(tool_name, cast(dict, tool_args))
                    tool_result_content = getattr(mcp_tool_result.content[0], "text", "")
                    print(f"--- Tool result: {tool_result_content} ---")
                    
                    # Format the tool result using the standardized handler
                    formatted_result = ToolCallHandler.format_tool_result(tool_name, tool_result_content)
                    self.messages.append(formatted_result)

            # --- Follow-up Call or Final Response ---
            if tool_executed:
                # Make a second call to Ollama with the tool results
                print("--- Making follow-up call to Ollama with tool results ---")
                final_response = await ollama_client.chat(
                    model=model_name,
                    messages=self.messages,
                    stream=False,
                )
                final_assistant_message = final_response['message']
                self.messages.append(final_assistant_message)
                if final_assistant_message.get('content'):
                    print(f"\nAssistant: {final_assistant_message['content']}")

            # If no tool call was attempted or parsed, print the original response content
            elif assistant_message.get('content'):
                 print(f"\nAssistant: {assistant_message['content']}")

        except Exception as e:
            print(f"\nError during Ollama interaction: {e}")
            # Optionally remove the last user message and assistant attempt from history on error
            # self.messages = self.messages[:-2]

    async def chat_loop(self, session: ClientSession):
        while True:
            query = input("\nQuery: ").strip()

            # Check for exit commands
            if query.lower() in ["quit", "stop", "exit"]:
                print("Exiting chat...")
                break

            # Add user message in Ollama format
            self.messages.append({"role": "user", "content": query})

            await self.process_query(session, query)

    async def run(self):
        async with stdio_client(server_params) as (read, write):
            async with ClientSession(read, write) as session:
                # Initialize the connection
                await session.initialize()

                await self.chat_loop(session)


chat = Chat()
