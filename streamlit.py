import streamlit as st
import json
import asyncio
import os
import openai # Use openai library
from azure.identity import DefaultAzureCredential, get_bearer_token_provider # Optional: for Entra ID auth
from mcp import ClientSession, StdioServerParameters, types as mcp_types
from mcp.client.stdio import stdio_client
from typing import List, Dict, Any, Optional, Tuple

# --- Configuration ---
CONFIG_FILE = "claude_desktop_config.json"

# --- Azure OpenAI Configuration ---
# Load from environment variables for better security, or define here for simplicity
AZURE_OPENAI_ENDPOINT = os.getenv("AZURE_OPENAI_ENDPOINT")
AZURE_OPENAI_API_KEY = os.getenv("AZURE_OPENAI_API_KEY") # Required if not using Entra ID/Managed Identity
AZURE_OPENAI_DEPLOYMENT_NAME = os.getenv("AZURE_OPENAI_DEPLOYMENT_NAME") # Your model deployment name
AZURE_OPENAI_API_VERSION = os.getenv("AZURE_OPENAI_API_VERSION", "2024-05-01-preview") # Use a recent API version supporting tools

# --- Initialize Azure OpenAI Client ---
# Use API Key Authentication (ensure AZURE_OPENAI_API_KEY is set)
# azure_openai_client = openai.AsyncAzureOpenAI(
#     api_key=AZURE_OPENAI_API_KEY,
#     azure_endpoint=AZURE_OPENAI_ENDPOINT,
#     api_version=AZURE_OPENAI_API_VERSION,
# )

# OR Use Microsoft Entra ID / Managed Identity Authentication (Recommended for production)
# Requires azure-identity library: pip install azure-identity
# Ensure the environment where Streamlit runs has appropriate credentials configured
# (e.g., logged in via Azure CLI, Managed Identity assigned, Service Principal env vars set)
try:
    token_provider = get_bearer_token_provider(DefaultAzureCredential(), "https://cognitiveservices.azure.com/.default")
    azure_openai_client = openai.AsyncAzureOpenAI(
        azure_endpoint=AZURE_OPENAI_ENDPOINT,
        api_version=AZURE_OPENAI_API_VERSION,
        azure_ad_token_provider=token_provider,
    )
    st.sidebar.info("Using Azure Entra ID / Managed Identity Auth")
except Exception as e:
    st.sidebar.warning(f"Entra ID/Managed Identity auth failed: {e}. Falling back to API Key auth.")
    if AZURE_OPENAI_API_KEY:
         azure_openai_client = openai.AsyncAzureOpenAI(
            api_key=AZURE_OPENAI_API_KEY,
            azure_endpoint=AZURE_OPENAI_ENDPOINT,
            api_version=AZURE_OPENAI_API_VERSION,
        )
         st.sidebar.info("Using API Key Auth")
    else:
         st.error("Azure OpenAI API Key not found. Please set AZURE_OPENAI_API_KEY environment variable.")
         azure_openai_client = None # Prevent app from running further if no auth method works

# Check if client initialization failed
if not azure_openai_client:
    st.stop()


# --- Helper Functions (MCP parts remain mostly the same) ---

def load_mcp_config(config_path: str) -> Dict[str, Dict]:
    """Loads MCP server configurations from a JSON file."""
    try:
        with open(config_path, 'r') as f:
            config = json.load(f)
        st.success(f"Loaded configuration from {config_path}")
        return config.get("mcpServers", {})
    except FileNotFoundError:
        st.warning(f"Configuration file not found at {config_path}. No MCP servers will be started.")
        return {}
    except json.JSONDecodeError:
        st.error(f"Error: Could not decode JSON from {config_path}")
        return {}
    except Exception as e:
        st.error(f"Error loading config: {e}")
        return {}

def convert_mcp_tool_to_openai_tool(mcp_tool: mcp_types.Tool) -> Dict:
    """
    Converts an MCP Tool object to the OpenAI/Azure OpenAI JSON tool format.
    (This function remains largely the same as the format is compatible)
    Ref: Based on Section 9, Replacing Claude Desktop with Ollama doc & Section 2/4 LLM Backend API Differences doc.
    """
    openai_params = {"type": "object", "properties": {}, "required": []}
    required_params = []

    if mcp_tool.inputSchema and isinstance(mcp_tool.inputSchema, dict):
        schema_props = mcp_tool.inputSchema.get('properties', {})
        if isinstance(schema_props, dict):
            for param_name, param_schema in schema_props.items():
                 if isinstance(param_schema, dict):
                    openai_params["properties"][param_name] = {
                        "type": param_schema.get("type", "string"),
                        "description": param_schema.get("description", "")
                    }
                    if "enum" in param_schema and isinstance(param_schema["enum"], list):
                         openai_params["properties"][param_name]["enum"] = param_schema["enum"]

        schema_required = mcp_tool.inputSchema.get('required', [])
        if isinstance(schema_required, list):
            required_params = schema_required
            if required_params:
                 openai_params["required"] = required_params

    return {
        "type": "function",
        "function": {
            "name": mcp_tool.name,
            "description": mcp_tool.description,
            "parameters": openai_params
        }
    }

async def connect_and_init_mcp_server(server_name: str, config: Dict) -> Optional[ClientSession]:
    """Connects to a single MCP server via stdio and initializes the session."""
    # (This function is identical to the previous version)
    try:
        server_params = StdioServerParameters(
            command=config["command"],
            args=config.get("args"),
            env=config.get("env"),
            cwd=config.get("cwd")
        )
        read, write = await asyncio.wait_for(stdio_client(server_params).__aenter__(), timeout=15.0)
        session = ClientSession(read, write)
        await asyncio.wait_for(session.initialize(), timeout=10.0)
        st.session_state.mcp_raw_streams[server_name] = (read, write)
        st.sidebar.success(f"Connected: {server_name}")
        return session
    except asyncio.TimeoutError:
        st.sidebar.error(f"Timeout connecting/initializing {server_name}")
        if server_name in st.session_state.get('mcp_raw_streams', {}):
            read, write = st.session_state.mcp_raw_streams[server_name]
            if write and not write.is_closing(): write.close()
            del st.session_state.mcp_raw_streams[server_name]
        return None
    except Exception as e:
        st.sidebar.error(f"Failed to connect {server_name}: {e}")
        if server_name in st.session_state.get('mcp_raw_streams', {}):
             read, write = st.session_state.mcp_raw_streams[server_name]
             if write and not write.is_closing(): write.close()
             del st.session_state.mcp_raw_streams[server_name]
        return None


async def discover_tools(session: ClientSession, server_name: str) -> List[mcp_types.Tool]:
    """Discovers tools from a connected MCP session."""
    # (This function is identical to the previous version)
    try:
        tools_response = await asyncio.wait_for(session.list_tools(), timeout=10.0)
        st.session_state.mcp_server_tools[server_name] = {tool.name: tool for tool in tools_response.tools}
        return tools_response.tools
    except asyncio.TimeoutError:
         st.warning(f"Timeout discovering tools from {server_name}")
         return []
    except Exception as e:
        st.warning(f"Error discovering tools from {server_name}: {e}")
        return []

async def call_mcp_tool(server_name: str, tool_name: str, args: Dict) -> Any:
    """Calls a specific tool on a specific MCP server."""
    # (This function is identical to the previous version)
    if server_name not in st.session_state.mcp_sessions:
        return f"Error: No active session for server '{server_name}'"
    session = st.session_state.mcp_sessions[server_name]
    try:
        if not session.read or session.read.at_eof():
             raise ConnectionError(f"Session for {server_name} appears closed.")
        st.info(f"Calling tool '{tool_name}' on server '{server_name}' with args: {args}")
        result = await asyncio.wait_for(
            session.call_tool(tool_name=tool_name, arguments=args),
            timeout=60.0
        )
        if isinstance(result, (dict, list)): return json.dumps(result)
        else: return str(result)
    except asyncio.TimeoutError:
        st.error(f"Timeout calling tool '{tool_name}' on {server_name}")
        return f"Error: Timeout calling tool '{tool_name}'"
    except ConnectionError as e:
        st.error(f"Connection error calling tool '{tool_name}' on {server_name}: {e}")
        return f"Error: Connection lost calling tool '{tool_name}'"
    except Exception as e:
        st.error(f"Error calling tool '{tool_name}' on {server_name}: {e}")
        return f"Error calling tool '{tool_name}': {e}"

async def get_azure_openai_response(messages: List[Dict], available_tools: List[Dict]) -> Dict:
    """Gets a response from Azure OpenAI, potentially requesting tool use."""
    try:
        response = await azure_openai_client.chat.completions.create(
            model=AZURE_OPENAI_DEPLOYMENT_NAME,
            messages=messages,
            tools=available_tools if available_tools else None, # Pass tools if any
            tool_choice="auto" # Let the model decide whether to use tools
        )
        # Return the assistant's message object (openai v1.x format)
        return response.choices[0].message.model_dump() # Convert Pydantic model to dict
    except openai.APIError as e:
        st.error(f"Azure OpenAI API Error: {e.message} (Status: {e.status_code}, Type: {e.type})")
        return {"role": "assistant", "content": f"Error contacting Azure OpenAI: {e.message}"}
    except openai.AuthenticationError as e:
        st.error(f"Azure OpenAI Authentication Error: {e.message}. Check your API key or Entra ID/Managed Identity setup.")
        return {"role": "assistant", "content": f"Azure Authentication Error. Please check configuration."}
    except Exception as e:
        st.error(f"Error during Azure OpenAI call: {e}")
        return {"role": "assistant", "content": f"Error during Azure OpenAI call: {e}"}

async def orchestrate_conversation_turn(user_prompt: str) -> None:
    """Handles one turn of the conversation using Azure OpenAI."""
    # 1. Add user message
    st.session_state.messages.append({"role": "user", "content": user_prompt})

    # 2. Discover tools (same as before)
    ollama_tools_list = [] # Rename variable for clarity, format is OpenAI compatible
    st.session_state.tool_map = {}
    with st.spinner("Discovering tools..."):
        all_mcp_tools = []
        tasks = []
        active_sessions = list(st.session_state.mcp_sessions.items())
        for server_name, session in active_sessions:
             if session and session.read and not session.read.at_eof():
                 tasks.append(discover_tools(session, server_name))
             else:
                 st.warning(f"Session for {server_name} seems inactive.")
        results = await asyncio.gather(*tasks)
        for i, tools in enumerate(results):
            server_name = active_sessions[i][0]
            all_mcp_tools.extend(tools)
            for tool in tools:
                st.session_state.tool_map[tool.name] = server_name

    if all_mcp_tools:
        st.sidebar.write("Discovered Tools:")
        for tool in all_mcp_tools:
             st.sidebar.caption(f"- {tool.name} ({st.session_state.tool_map.get(tool.name, 'Unknown')})")
        openai_tools_list = [convert_mcp_tool_to_openai_tool(tool) for tool in all_mcp_tools]
    else:
         st.sidebar.write("No tools discovered.")
         openai_tools_list = []

    # 3. Call Azure OpenAI
    with st.spinner(f"Asking Azure OpenAI ({AZURE_OPENAI_DEPLOYMENT_NAME})..."):
        # Pass the dict version of the message history
        api_messages = [msg for msg in st.session_state.messages]
        assistant_response_dict = await get_azure_openai_response(api_messages, openai_tools_list)

    # Convert back to Message object potentially needed if adding directly? No, dict is fine for history.
    assistant_response_message = assistant_response_dict # Keep as dict for history

    # 4. Check for tool calls (OpenAI format)
    tool_calls = assistant_response_message.get("tool_calls")

    if tool_calls:
        # 5. Execute Tool Calls
        st.session_state.messages.append(assistant_response_message) # Add assistant's msg

        tool_results_messages = []
        for tool_call in tool_calls:
            tool_call_id = tool_call['id'] # Required for OpenAI response
            tool_name = tool_call['function']['name']
            # Arguments are a JSON *string* in OpenAI response, needs parsing
            try:
                tool_args_str = tool_call['function']['arguments']
                tool_args = json.loads(tool_args_str)
            except json.JSONDecodeError:
                st.error(f"Error: Could not decode JSON arguments for tool '{tool_name}': {tool_args_str}")
                tool_args = None
                tool_result_content = f"Error: Invalid arguments received for tool '{tool_name}'."
            except Exception as e:
                 st.error(f"Error parsing arguments for tool '{tool_name}': {e}")
                 tool_args = None
                 tool_result_content = f"Error: Could not parse arguments for tool '{tool_name}'."


            if tool_args is not None:
                server_name = st.session_state.tool_map.get(tool_name)
                if server_name:
                    tool_result_content = await call_mcp_tool(server_name, tool_name, tool_args)
                else:
                    st.error(f"Error: Tool '{tool_name}' requested but no providing server found.")
                    tool_result_content = f"Error: Could not find server for tool '{tool_name}'"

            # Append result for this specific tool call, including tool_call_id
            tool_results_messages.append({
                "role": "tool",
                "tool_call_id": tool_call_id, # Crucial for OpenAI
                "name": tool_name, # Optional but good practice? Check API spec.
                "content": tool_result_content,
            })

        # Add all tool results to messages
        st.session_state.messages.extend(tool_results_messages)

        # 6. Call Azure OpenAI again with tool results
        with st.spinner("Processing tool results..."):
            # Pass the updated dict version of the message history
            api_messages_with_results = [msg for msg in st.session_state.messages]
            final_response_dict = await get_azure_openai_response(api_messages_with_results, []) # No tools needed

        st.session_state.messages.append(final_response_dict) # Add final response dict
    else:
        # No tool calls, just add the direct response dict
        st.session_state.messages.append(assistant_response_message)

    st.rerun()


async def cleanup_mcp_session(server_name: str):
    """Gracefully shuts down a single MCP session and cleans up resources."""
    # (This function is identical to the previous version)
    st.sidebar.write(f"Cleaning up session: {server_name}...")
    session = st.session_state.mcp_sessions.pop(server_name, None)
    streams = st.session_state.mcp_raw_streams.pop(server_name, None)
    if session:
        try: pass # SDK context manager handles shutdown
        except Exception as e: st.sidebar.warning(f"Error during shutdown for {server_name}: {e}")
    if streams:
        read, write = streams
        try:
            if write and not write.is_closing():
                write.close()
                await write.wait_closed()
        except Exception as e: st.sidebar.warning(f"Error closing streams for {server_name}: {e}")
    st.sidebar.success(f"Cleaned up: {server_name}")


async def cleanup_all_mcp_sessions():
    """Cleans up all active MCP sessions."""
    # (This function is identical to the previous version)
    st.sidebar.write("Cleaning up all MCP sessions...")
    server_names = list(st.session_state.mcp_sessions.keys())
    tasks = [cleanup_mcp_session(name) for name in server_names]
    await asyncio.gather(*tasks)
    st.session_state.mcp_sessions = {}
    st.session_state.mcp_server_tools = {}
    st.session_state.tool_map = {}
    st.session_state.mcp_raw_streams = {}
    st.sidebar.write("Cleanup complete.")


# --- Streamlit App ---

st.set_page_config(page_title="Streamlit MCP Host (Azure)", layout="wide")
st.title(" разговаривать Streamlit MCP Host (Azure OpenAI) 🤖")
st.caption(f"Using Azure OpenAI Deployment: {AZURE_OPENAI_DEPLOYMENT_NAME}")

# --- Initialization ---
if 'initialized' not in st.session_state:
    st.session_state.messages = [{"role": "assistant", "content": "Hello! How can I help you today using Azure OpenAI?"}]
    st.session_state.mcp_sessions = {}
    st.session_state.mcp_server_tools = {}
    st.session_state.tool_map = {}
    st.session_state.mcp_raw_streams = {}

    st.sidebar.header("MCP Server Status")
    mcp_configs = load_mcp_config(CONFIG_FILE)

    async def connect_all():
        tasks = []
        for server_name, config in mcp_configs.items():
             st.sidebar.write(f"Connecting to {server_name}...")
             tasks.append(connect_and_init_mcp_server(server_name, config))
        results = await asyncio.gather(*tasks)
        for i, session in enumerate(results):
            server_name = list(mcp_configs.keys())[i]
            if session: st.session_state.mcp_sessions[server_name] = session
            else: st.sidebar.error(f"Connection failed for {server_name}")

    try:
        asyncio.run(connect_all())
    except RuntimeError as e:
        if "cannot run event loop while another loop is running" in str(e):
             st.warning("Could not auto-connect MCP servers (event loop running).")
        else: st.error(f"Error during initial connection: {e}")

    st.session_state.initialized = True
    st.rerun()

# --- Display Chat History ---
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        # Display tool calls differently (OpenAI format)
        if message["role"] == "assistant" and message.get("tool_calls"):
            st.write("Requesting tool calls:")
            for tc in message["tool_calls"]:
                 # Arguments are a string, display as is or try to pretty-print JSON
                 args_display = tc['function']['arguments']
                 try:
                     args_display = json.dumps(json.loads(args_display), indent=2)
                 except:
                     pass # Keep as string if not valid JSON
                 st.code(f"ID: {tc['id']}\nTool: {tc['function']['name']}\nArgs: {args_display}", language="json")
            if message.get("content"):
                 st.markdown(message["content"])
        elif message["role"] == "tool":
             st.markdown(f"**Tool Result (ID: {message.get('tool_call_id')})**:\n```\n{message['content']}\n```")
        else:
            st.markdown(message.get("content", "*No content*")) # Handle potential null content


# --- Chat Input ---
if prompt := st.chat_input("Ask Azure OpenAI..."):
    with st.chat_message("user"):
        st.markdown(prompt)
    try:
         asyncio.run(orchestrate_conversation_turn(prompt))
    except Exception as e:
         st.error(f"An error occurred: {e}")


# --- Cleanup Logic ---
if st.sidebar.button("Disconnect All MCP Servers"):
     try:
         asyncio.run(cleanup_all_mcp_sessions())
         st.session_state.initialized = False
         st.rerun()
     except Exception as e:
         st.error(f"Error during cleanup: {e}")


