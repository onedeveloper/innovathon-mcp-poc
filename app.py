import asyncio
import threading
import queue
import os
import time
import sqlite3
import json
from typing import Union, cast, Optional, List, Dict, Any

import gradio as gr
import ollama # Replaced anthropic with ollama
# Removed Anthropic specific types
from dotenv import load_dotenv
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
from rich.console import Console
from rich.markdown import Markdown

# Load environment variables
load_dotenv()

# Initialize Ollama client
# Assuming Ollama server is running locally at default address http://localhost:11434
ollama_client = ollama.AsyncClient()

# Create a console for rich text formatting
console = Console()

# Create server parameters for stdio connection
server_params = StdioServerParameters(
    command="python",  # Executable
    args=["./mcp_server.py"],  # Optional command line arguments
    env=None,  # Optional environment variables
)

# Global message queue for async communication
message_queue = queue.Queue()

# Check if database exists, if not create a sample one
def initialize_database():
    if not os.path.exists("database.db"):
        conn = sqlite3.connect("database.db")
        cursor = conn.cursor()

        # Create sample tables
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY,
            name TEXT NOT NULL,
            email TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        ''')

        cursor.execute('''
        CREATE TABLE IF NOT EXISTS products (
            id INTEGER PRIMARY KEY,
            name TEXT NOT NULL,
            price REAL NOT NULL,
            stock INTEGER DEFAULT 0
        )
        ''')

        # Insert sample data
        cursor.executemany('''
        INSERT INTO users (name, email) VALUES (?, ?)
        ''', [
            ('John Doe', 'john@example.com'),
            ('Jane Smith', 'jane@example.com'),
            ('Bob Johnson', 'bob@example.com'),
        ])

        cursor.executemany('''
        INSERT INTO products (name, price, stock) VALUES (?, ?, ?)
        ''', [
            ('Laptop', 999.99, 10),
            ('Smartphone', 699.99, 20),
            ('Headphones', 149.99, 30),
            ('Monitor', 299.99, 15),
        ])

        conn.commit()
        conn.close()
        print("Created sample database with users and products tables")

class ChatProcessor:
    def __init__(self):
        self.messages: list[Dict[str, Any]] = [] # Changed message format for Ollama
        self.system_prompt: str = """You are a master SQLite assistant.
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

        # Start the MCP server and processing thread
        self.start_backend()

    def start_backend(self):
        """Start the backend processing thread that handles MCP communication"""
        threading.Thread(target=self._start_mcp_server, daemon=True).start()

    def _start_mcp_server(self):
        """Initialize and run the MCP server connection"""
        asyncio.run(self._run_server())

    async def _run_server(self):
        """Run the MCP server and initialize the connection"""
        async with stdio_client(server_params) as (read, write):
            async with ClientSession(read, write) as session:
                # Initialize the connection
                await session.initialize()

                # Process messages from the queue
                while True:
                    try:
                        # Check if there are any messages in the queue
                        if not message_queue.empty():
                            query, response_callback = message_queue.get()
                            result = await self._process_query(session, query)
                            response_callback(result)
                    except Exception as e:
                        print(f"Error processing message: {str(e)}")

                    # Short sleep to prevent CPU hogging
                    await asyncio.sleep(0.1)

    async def _process_query(self, session: ClientSession, query: str) -> List[str]:
        """Process a query using Ollama and return the response messages"""
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

        # Add the user message to the conversation
        self.messages.append({"role": "user", "content": query})

        # All Ollama responses will be collected here
        all_responses = []

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
            self.messages.append(assistant_message) # Add assistant's response (could be text or tool_calls)

            # --- Tool Call Handling ---
            tool_executed = False
            final_content_to_return = None

            # Option 1: Check structured tool_calls field (Standard way)
            if assistant_message.get('tool_calls'):
                print("--- Handling structured tool_calls ---")
                tool_executed = True
                for tool_call in assistant_message['tool_calls']:
                    tool_name = tool_call['function']['name']
                    # Handle arguments which might be a string (needs parsing) or already a dict
                    raw_args = tool_call['function']['arguments']
                    if isinstance(raw_args, str):
                        try:
                            tool_args = json.loads(raw_args)
                        except json.JSONDecodeError:
                            print(f"--- Warning: Failed to parse string arguments: {raw_args} ---")
                            # Decide how to handle - skip tool call? Pass raw string?
                            # For now, let's skip the tool call if args are unparsable string
                            tool_executed = False # Mark as failed for this specific call
                            final_content_to_return = f"Failed to parse tool arguments: {raw_args}"
                            break # Exit the loop over tool_calls as one failed
                    elif isinstance(raw_args, dict):
                        tool_args = raw_args # Use the dictionary directly
                    else:
                        print(f"--- Warning: Unexpected argument type: {type(raw_args)} ---")
                        tool_executed = False # Mark as failed for this specific call
                        final_content_to_return = f"Unexpected tool argument type: {type(raw_args)}"
                        break # Exit the loop over tool_calls as one failed

                    # If parsing failed and we set final_content_to_return, skip execution for this call
                    if not tool_executed:
                        break


                    print(f"Calling tool: {tool_name} with args: {tool_args}")
                    mcp_tool_result = await session.call_tool(tool_name, cast(dict, tool_args))
                    tool_result_content = getattr(mcp_tool_result.content[0], "text", "")
                    print(f"Tool result: {tool_result_content}")

                    # Append tool result with more context for the model
                    formatted_tool_result = f"Tool execution result for {tool_name}: {tool_result_content}"
                    self.messages.append({
                        "role": "tool",
                        "content": formatted_tool_result, # Use the formatted string
                        # "tool_call_id": tool_call.get('id')
                    })

            # Option 2: Check for <toolcall> tag in content (Workaround)
            elif assistant_message.get('content') and '<toolcall>' in assistant_message['content']:
                print("--- Handling <toolcall> tag in content ---")
                tool_executed = True
                content_str = assistant_message['content']
                try:
                    start_tag = '<toolcall>'
                    end_tag = '</toolcall>'
                    start_index = content_str.find(start_tag) + len(start_tag)
                    end_index = content_str.find(end_tag)
                    tool_call_json_str = content_str[start_index:end_index].strip()
                    tool_call_data = json.loads(tool_call_json_str)

                    # --- More Refined Tool Name and Argument Extraction from <toolcall> ---
                    tool_name = None
                    tool_args = {} # Default to empty args

                    if tool_call_data.get("type") == "function" and "arguments" in tool_call_data:
                        arguments_dict = tool_call_data["arguments"]
                        if isinstance(arguments_dict, dict):
                            # Case 1: Arguments contain {'name': 'tool_name'} for parameterless tools
                            potential_tool_name = arguments_dict.get("name")
                            if potential_tool_name in ["list_tables", "get_database_schema"]:
                                tool_name = potential_tool_name
                                tool_args = {} # Ensure args are empty for these
                            # Case 2: Arguments contain {'sql': '...'} for query_data
                            elif "sql" in arguments_dict:
                                tool_name = "query_data"
                                tool_args = arguments_dict # Pass the whole dict containing 'sql'
                            else:
                                raise ValueError(f"Unrecognized arguments structure in <toolcall>: {arguments_dict}")
                        else:
                            # Handle case where arguments might be a simple string (e.g., just the SQL for query_data)
                            # This is less likely based on current observations but good to consider
                            # if isinstance(arguments_dict, str) and is_likely_sql(arguments_dict):
                            #    tool_name = "query_data"
                            #    tool_args = {"sql": arguments_dict}
                            # else:
                            raise ValueError("Arguments field in <toolcall> JSON is not a dictionary or recognized string format")
                    else:
                        raise ValueError("Unexpected JSON structure in <toolcall>")

                    # Ensure tool_name was determined
                    if not tool_name:
                        raise ValueError("Could not determine tool name from <toolcall> tag")


                    print(f"--- Calling tool (from tag): {tool_name} with args: {tool_args} ---")
                    # Pass the extracted dictionary directly
                    mcp_tool_result = await session.call_tool(tool_name, cast(dict, tool_args))
                    tool_result_content = getattr(mcp_tool_result.content[0], "text", "")
                    print(f"Tool result: {tool_result_content}")

                    # Append tool result with more context for the model (for tag parsing path)
                    formatted_tool_result = f"Tool execution result for {tool_name}: {tool_result_content}"
                    self.messages.append({
                        "role": "tool",
                        "content": formatted_tool_result, # Use the formatted string
                    })
                except Exception as parse_error:
                    print(f"--- Error parsing <toolcall> tag: {parse_error} ---")
                    tool_executed = False # Reset flag as tool call failed
                    final_content_to_return = f"Error parsing tool call: {parse_error}" # Provide error feedback

            # --- Follow-up Call or Final Response ---
            if tool_executed:
                print("--- Making follow-up call to Ollama with tool results ---")
                final_response = await ollama_client.chat(
                    model=model_name,
                    messages=self.messages,
                    stream=False,
                )
                final_assistant_message = final_response['message']
                self.messages.append(final_assistant_message)
                if final_assistant_message.get('content'):
                    final_content_to_return = final_assistant_message['content']

            # If no tool call was attempted/parsed, use the original response content
            elif assistant_message.get('content'):
                 final_content_to_return = assistant_message['content']

            # Append the final content (either from follow-up or original response)
            if final_content_to_return:
                 all_responses.append(final_content_to_return)

        except Exception as e:
            print(f"Error during Ollama interaction: {e}")
            all_responses.append(f"Sorry, an error occurred: {e}")
            # Optionally remove the last user message and assistant attempt from history on error
            # self.messages = self.messages[:-2] # Or more sophisticated error handling

        # Limit message history length (optional)
        # max_history = 10
        # if len(self.messages) > max_history:
        #     self.messages = self.messages[-max_history:]

        return all_responses

def submit_query(query: str, chat_history: list) -> tuple[list, list]:
    """Submit a query to the chat processor and update the chat history"""
    if not query.strip():
        return chat_history, chat_history

    # Add user message to history immediately
    chat_history.append((query, None))

    # Create a result container
    result_container = []

    # Define callback for when the result is ready
    def on_result(responses):
        combined_response = "\n\n".join(responses)
        result_container.append(combined_response)

    # Submit the query to the processor
    message_queue.put((query, on_result))

    # Wait for the result
    while not result_container:
        time.sleep(0.1)

    # Update the last history entry with the response
    chat_history[-1] = (query, result_container[0])

    return chat_history, chat_history

def main():
    # Initialize the database with sample data if needed
    initialize_database()

    # Initialize the chat processor
    chat_processor = ChatProcessor()

    # Create the Gradio interface
    with gr.Blocks(title="AI SQL Assistant", theme=gr.themes.Soft(), css="footer {visibility: hidden}") as demo:
        gr.Markdown("# AI SQL Assistant")
        gr.Markdown("""This application allows you to interact with a SQLite database using natural language.
        Ask questions about the data or request SQL operations, and the AI will generate and execute the appropriate SQL queries.

        **Sample tables in the database:**
        - `users` (id, name, email, created_at)
        - `products` (id, name, price, stock)
        """)

        chatbot = gr.Chatbot(
            label="Chat",
            height=500,
            bubble_full_width=False,
            show_copy_button=True
        )

        with gr.Row():
            msg = gr.Textbox(
                label="Ask a question or request a SQL operation",
                placeholder="For example: 'Show me all users' or 'How many products do we have in stock?'",
                scale=9
            )
            submit = gr.Button("Submit", scale=1)

        with gr.Accordion("Example Queries", open=False):
            example_queries = [
                "List all tables in the database",
                "Show me all users",
                "Count how many products cost more than $300",
                "What's the total value of all products in stock?",
                "Insert a new product called 'Tablet' with price $499.99 and stock 5",
                "Update the price of Laptop to $1099.99"
            ]
            gr.Examples(
                examples=example_queries,
                inputs=msg
            )

        # Set up event handlers
        submit.click(submit_query, [msg, chatbot], [chatbot, chatbot]).then(
            lambda: "", None, [msg]  # Clear the input box after submission
        )
        msg.submit(submit_query, [msg, chatbot], [chatbot, chatbot]).then(
            lambda: "", None, [msg]  # Clear the input box after submission
        )

    # Launch the interface
    demo.launch(share=False, server_port=7860)

if __name__ == "__main__":
    main()
