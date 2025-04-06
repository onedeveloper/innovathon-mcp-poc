# Implementation Plan for MCP Server/Client Application Improvements

## Phase 1: Tool Calling Standardization and Plugin Architecture

### 1.1 Tool Calling Standardization (Week 1)

#### 1.1.1 Create Unified Tool Call Handler
- Create a new module `tool_handler.py` with a unified approach to parse tool calls
- Implement a single parser that can handle both structured tool calls and tag-based formats
- Add comprehensive error handling and logging

```python
# Example structure for tool_handler.py
from typing import Dict, Any, List, Tuple, Optional
import json
import re

class ToolCallParser:
    @staticmethod
    def parse_tool_calls(message: Dict[str, Any]) -> List[Tuple[str, Dict[str, Any]]]:
        """
        Parse tool calls from an Ollama message, handling both structured and tag-based formats.
        Returns a list of (tool_name, tool_args) tuples.
        """
        tool_calls = []
        
        # Method 1: Parse structured tool_calls field
        if message.get('tool_calls'):
            for tool_call in message['tool_calls']:
                tool_name, tool_args = ToolCallParser._parse_structured_tool_call(tool_call)
                if tool_name:
                    tool_calls.append((tool_name, tool_args))
        
        # Method 2: Parse <toolcall> tags in content
        elif message.get('content') and '<toolcall>' in message['content']:
            tool_name, tool_args = ToolCallParser._parse_tag_based_tool_call(message['content'])
            if tool_name:
                tool_calls.append((tool_name, tool_args))
        
        return tool_calls
    
    @staticmethod
    def _parse_structured_tool_call(tool_call: Dict[str, Any]) -> Tuple[Optional[str], Dict[str, Any]]:
        """Parse a structured tool call from the tool_calls field"""
        try:
            tool_name = tool_call['function']['name']
            raw_args = tool_call['function']['arguments']
            
            # Handle string arguments (parse JSON)
            if isinstance(raw_args, str):
                try:
                    tool_args = json.loads(raw_args)
                except json.JSONDecodeError:
                    return None, {}
            # Handle dictionary arguments
            elif isinstance(raw_args, dict):
                tool_args = raw_args
            else:
                return None, {}
                
            return tool_name, tool_args
        except (KeyError, TypeError):
            return None, {}
    
    @staticmethod
    def _parse_tag_based_tool_call(content: str) -> Tuple[Optional[str], Dict[str, Any]]:
        """Parse a tool call from <toolcall> tags in content"""
        try:
            # Extract JSON string between tags
            start_tag = '<toolcall>'
            end_tag = '</toolcall>'
            start_index = content.find(start_tag) + len(start_tag)
            end_index = content.find(end_tag)
            
            if start_index < len(start_tag) or end_index < 0:
                return None, {}
                
            tool_call_json_str = content[start_index:end_index].strip()
            tool_call_data = json.loads(tool_call_json_str)
            
            # Extract tool name and arguments
            tool_name = None
            tool_args = {}
            
            if tool_call_data.get("type") == "function" and "arguments" in tool_call_data:
                arguments_dict = tool_call_data["arguments"]
                if isinstance(arguments_dict, dict):
                    # Handle parameterless tools
                    potential_tool_name = arguments_dict.get("name")
                    if potential_tool_name in ["list_tables", "get_database_schema"]:
                        tool_name = potential_tool_name
                        tool_args = {}
                    # Handle query_data tool
                    elif "sql" in arguments_dict:
                        tool_name = "query_data"
                        tool_args = arguments_dict
            
            return tool_name, tool_args
        except (ValueError, json.JSONDecodeError, KeyError, TypeError):
            return None, {}
```

#### 1.1.2 Standardize Tool Result Formatting
- Create a `tool_result.py` module for consistent formatting of tool results
- Implement functions to format different types of results (text, tables, errors)

```python
# Example structure for tool_result.py
from typing import Any, Dict, List, Union

class ToolResultFormatter:
    @staticmethod
    def format_result(tool_name: str, result: Any) -> str:
        """Format a tool result for consistent presentation"""
        if tool_name == "query_data":
            return ToolResultFormatter.format_query_result(result)
        elif tool_name == "list_tables":
            return ToolResultFormatter.format_table_list(result)
        elif tool_name == "get_database_schema":
            return ToolResultFormatter.format_schema(result)
        elif tool_name.startswith("get_current_time"):
            return ToolResultFormatter.format_time_result(result)
        else:
            return f"Tool execution result for {tool_name}: {result}"
    
    @staticmethod
    def format_query_result(result: str) -> str:
        """Format a SQL query result"""
        # Add special formatting for query results if needed
        return f"Query result:\n{result}"
    
    @staticmethod
    def format_table_list(result: str) -> str:
        """Format a table list result"""
        return result  # Already well-formatted
    
    @staticmethod
    def format_schema(result: str) -> str:
        """Format a schema result"""
        return result  # Already well-formatted
    
    @staticmethod
    def format_time_result(result: str) -> str:
        """Format a time-related result"""
        return f"Time information: {result}"
    
    @staticmethod
    def format_error(tool_name: str, error: str) -> str:
        """Format an error result"""
        return f"Error executing {tool_name}: {error}"
```

#### 1.1.3 Update Client and App Code
- Refactor `mcp_client.py` and `app.py` to use the new tool handling modules
- Remove duplicate code and standardize the approach

### 1.2 Plugin Architecture Implementation (Week 2)

#### 1.2.1 Create Core Registry Module
- Implement the agent and tool registry as designed in the multiple agent integration design
- Create a `registry.py` module for centralized registration

```python
# Example structure for registry.py
from typing import Dict, List, Callable, Any, Optional
import inspect

class AgentRegistry:
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(AgentRegistry, cls).__new__(cls)
            cls._instance.agents = {}
            cls._instance.tools = {}
        return cls._instance
    
    def register_agent(self, name: str, agent_instance: Any) -> None:
        """Register an agent with the registry"""
        self.agents[name] = agent_instance
        
    def register_tool(self, name: str, tool_function: Callable, description: str, schema: Dict) -> None:
        """Register a tool with the registry"""
        self.tools[name] = {
            "function": tool_function,
            "description": description,
            "schema": schema
        }
    
    def get_all_tools(self) -> Dict[str, Dict]:
        """Get all registered tools"""
        return self.tools
    
    def get_tool(self, name: str) -> Optional[Dict]:
        """Get a specific tool by name"""
        return self.tools.get(name)
    
    def get_agent(self, name: str) -> Optional[Any]:
        """Get a specific agent by name"""
        return self.agents.get(name)
    
    def get_all_agents(self) -> Dict[str, Any]:
        """Get all registered agents"""
        return self.agents
```

#### 1.2.2 Define Agent Interface
- Create an abstract base class for agents to implement
- Define standard methods for initialization, tool registration, and request processing

```python
# Example structure for agent_interface.py
from abc import ABC, abstractmethod
from typing import List, Dict, Any

class Agent(ABC):
    @abstractmethod
    def register_tools(self) -> None:
        """Register agent's tools with the registry"""
        pass
    
    @abstractmethod
    def initialize(self) -> None:
        """Initialize the agent"""
        pass
    
    @abstractmethod
    def process_request(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """Process a request directed to this agent"""
        pass
```

#### 1.2.3 Implement Base Agents
- Create base implementations for SQL and Time agents
- Refactor existing code to use the new agent structure

```python
# Example structure for sql_agent.py
import sqlite3
from typing import Dict, Any
from .agent_interface import Agent
from .registry import AgentRegistry

class SQLAgent(Agent):
    def __init__(self, db_path: str = "./database.db"):
        self.registry = AgentRegistry()
        self.db_path = db_path
        
    def register_tools(self) -> None:
        """Register SQL-related tools with the registry"""
        self.registry.register_tool(
            name="query_data",
            tool_function=self.query_data,
            description="Execute SQL queries safely",
            schema={
                "type": "object",
                "required": ["sql"],
                "properties": {
                    "sql": {
                        "type": "string",
                        "description": "SQL query to execute"
                    }
                }
            }
        )
        
        self.registry.register_tool(
            name="list_tables",
            tool_function=self.list_tables,
            description="Lists all non-system tables in the database.",
            schema={
                "type": "object",
                "properties": {}
            }
        )
        
        self.registry.register_tool(
            name="get_database_schema",
            tool_function=self.get_database_schema,
            description="Retrieves the CREATE TABLE statements for all tables in the database.",
            schema={
                "type": "object",
                "properties": {}
            }
        )
    
    def initialize(self) -> None:
        """Initialize the SQL agent"""
        # Check if database exists, create if needed
        pass
    
    def process_request(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """Process a SQL-related request"""
        return {"status": "error", "message": "Direct request processing not implemented"}
    
    def query_data(self, sql: str) -> str:
        """Execute SQL queries safely"""
        conn = sqlite3.connect(self.db_path)
        try:
            result = conn.execute(sql).fetchall()
            conn.commit()
            return "\n".join(str(row) for row in result)
        except Exception as e:
            return f"Error: {str(e)}"
        finally:
            conn.close()
    
    def list_tables(self) -> str:
        """Lists all non-system tables in the database."""
        conn = sqlite3.connect(self.db_path)
        try:
            cursor = conn.cursor()
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%';")
            tables = cursor.fetchall()
            if not tables:
                return "No tables found in the database."
            # Format the list of tables
            table_list = "\n".join([f"- {table[0]}" for table in tables])
            return f"Tables in the database:\n{table_list}"
        except Exception as e:
            return f"Error listing tables: {str(e)}"
        finally:
            conn.close()
    
    def get_database_schema(self) -> str:
        """Retrieves the CREATE TABLE statements for all tables in the database."""
        conn = sqlite3.connect(self.db_path)
        try:
            cursor = conn.cursor()
            # Query sqlite_master for table creation SQL
            cursor.execute("SELECT sql FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%';")
            schema_rows = cursor.fetchall()
            # Format the schema string
            schema_str = "\n\n".join([row[0] for row in schema_rows if row[0]])
            if not schema_str:
                return "No tables found in the database."
            return f"Database Schema:\n```sql\n{schema_str}\n```"
        except Exception as e:
            return f"Error retrieving schema: {str(e)}"
        finally:
            conn.close()
```

```python
# Example structure for time_agent.py
import time
import datetime
from typing import Dict, Any, Optional
from .agent_interface import Agent
from .registry import AgentRegistry

class TimeAgent(Agent):
    def __init__(self):
        self.registry = AgentRegistry()
        
    def register_tools(self) -> None:
        """Register time-related tools with the registry"""
        self.registry.register_tool(
            name="get_current_time",
            tool_function=self.get_current_time,
            description="Get the current time in a specified timezone and format",
            schema={
                "type": "object",
                "properties": {
                    "timezone": {
                        "type": "string",
                        "description": "Timezone (e.g., 'UTC', 'America/New_York'). Defaults to UTC if not specified."
                    },
                    "format": {
                        "type": "string",
                        "description": "Output format (e.g., 'iso', 'human'). Defaults to ISO format."
                    }
                }
            }
        )
        
        # Register other time tools...
    
    def initialize(self) -> None:
        """Initialize the time agent"""
        # No special initialization needed
        pass
    
    def process_request(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """Process a time-related request"""
        return {"status": "error", "message": "Direct request processing not implemented"}
    
    def get_current_time(self, timezone: Optional[str] = None, format: Optional[str] = None) -> str:
        """Get the current time in the specified timezone and format"""
        try:
            # Implementation as in mcp_server_timefunctions.py
            # ...
            return "Current time implementation"
        except Exception as e:
            return f"Error getting current time: {str(e)}"
    
    # Implement other time-related tools...
```

#### 1.2.4 Create Server Factory
- Implement a server factory that loads and initializes agents
- Update the MCP server to use the registry for tool registration

```python
# Example structure for server_factory.py
from typing import List, Dict, Any
from mcp.server.fastmcp import FastMCP
from .registry import AgentRegistry

class MCPServerFactory:
    @staticmethod
    def create_server(name: str, agent_modules: List[str]) -> FastMCP:
        """Create and configure an MCP server with the specified agents"""
        # Create the MCP server
        mcp = FastMCP(name)
        
        # Get the registry
        registry = AgentRegistry()
        
        # Load and initialize agents
        for agent_module in agent_modules:
            try:
                # Import the agent module
                module_parts = agent_module.split('.')
                module = __import__('.'.join(module_parts[:-1]), fromlist=[module_parts[-1]])
                agent_class = getattr(module, module_parts[-1])
                
                # Create an instance of the agent
                agent = agent_class()
                
                # Register the agent
                registry.register_agent(agent_module, agent)
                
                # Initialize the agent
                agent.initialize()
                
                # Register the agent's tools
                agent.register_tools()
            except (ImportError, AttributeError) as e:
                print(f"Error loading agent {agent_module}: {e}")
        
        # Register all tools with the MCP server
        tools = registry.get_all_tools()
        for name, tool_info in tools.items():
            # Register the tool with the MCP server
            @mcp.tool(name=name, description=tool_info["description"])
            def tool_wrapper(*args, **kwargs):
                return tool_info["function"](*args, **kwargs)
        
        return mcp
```

## Phase 2: Modularization and Code Restructuring

### 2.1 Project Structure Reorganization (Week 3)

#### 2.1.1 Create Package Structure
- Reorganize the codebase into a proper package structure
- Create separate modules for different components

```
mcp_app/
├── __init__.py
├── agents/
│   ├── __init__.py
│   ├── base.py          # Agent interface
│   ├── sql_agent.py     # SQL agent implementation
│   └── time_agent.py    # Time agent implementation
├── core/
│   ├── __init__.py
│   ├── registry.py      # Agent and tool registry
│   ├── server.py        # Server factory and core functionality
│   └── config.py        # Configuration management
├── utils/
│   ├── __init__.py
│   ├── tool_handler.py  # Tool call parsing
│   ├── tool_result.py   # Result formatting
│   └── db.py            # Database utilities
├── client/
│   ├── __init__.py
│   ├── cli.py           # Command-line client
│   └── web.py           # Web interface
├── main.py              # Entry point
└── setup.py             # Package setup
```

#### 2.1.2 Create Configuration Module
- Implement a centralized configuration system
- Support environment variables and configuration files

```python
# Example structure for config.py
import os
from typing import Dict, Any, Optional
import json
from dotenv import load_dotenv

class Config:
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(Config, cls).__new__(cls)
            cls._instance._load_config()
        return cls._instance
    
    def _load_config(self):
        """Load configuration from environment variables and config file"""
        # Load environment variables
        load_dotenv()
        
        # Default configuration
        self.config = {
            "ollama": {
                "model": os.getenv("OLLAMA_MODEL_NAME", "llama3.2:1b"),
                "api_url": os.getenv("OLLAMA_API_URL", "http://localhost:11434"),
            },
            "database": {
                "path": os.getenv("DATABASE_PATH", "./database.db"),
            },
            "server": {
                "name": os.getenv("SERVER_NAME", "MCP Demo"),
                "agents": os.getenv("ENABLED_AGENTS", "SQLAgent,TimeAgent").split(","),
            },
            "web": {
                "port": int(os.getenv("WEB_PORT", "7860")),
                "share": os.getenv("SHARE_APP", "false").lower() == "true",
            }
        }
        
        # Load from config file if it exists
        config_file = os.getenv("CONFIG_FILE", "config.json")
        if os.path.exists(config_file):
            try:
                with open(config_file, 'r') as f:
                    file_config = json.load(f)
                    # Update config with file values
                    self._update_dict(self.config, file_config)
            except Exception as e:
                print(f"Error loading config file: {e}")
    
    def _update_dict(self, target: Dict, source: Dict) -> None:
        """Recursively update a dictionary"""
        for key, value in source.items():
            if key in target and isinstance(target[key], dict) and isinstance(value, dict):
                self._update_dict(target[key], value)
            else:
                target[key] = value
    
    def get(self, key: str, default: Any = None) -> Any:
        """Get a configuration value by key"""
        keys = key.split('.')
        value = self.config
        for k in keys:
            if isinstance(value, dict) and k in value:
                value = value[k]
            else:
                return default
        return value
```

#### 2.1.3 Refactor Database Access
- Create a database utility module with connection pooling
- Implement parameterized queries for security

```python
# Example structure for db.py
import sqlite3
from typing import List, Dict, Any, Tuple, Optional
import threading
from contextlib import contextmanager

class DatabasePool:
    _instance = None
    _lock = threading.Lock()
    
    def __new__(cls, db_path: str = "./database.db", pool_size: int = 5):
        with cls._lock:
            if cls._instance is None:
                cls._instance = super(DatabasePool, cls).__new__(cls)
                cls._instance.db_path = db_path
                cls._instance.pool_size = pool_size
                cls._instance._connections = []
                cls._instance._in_use = set()
        return cls._instance
    
    @contextmanager
    def get_connection(self):
        """Get a connection from the pool"""
        conn = self._get_connection()
        try:
            yield conn
        finally:
            self._release_connection(conn)
    
    def _get_connection(self) -> sqlite3.Connection:
        """Get a connection from the pool or create a new one"""
        with self._lock:
            # Check for available connections
            for conn in self._connections:
                if conn not in self._in_use:
                    self._in_use.add(conn)
                    return conn
            
            # Create a new connection if pool is not full
            if len(self._connections) < self.pool_size:
                conn = sqlite3.connect(self.db_path)
                self._connections.append(conn)
                self._in_use.add(conn)
                return conn
            
            # Wait for a connection to become available
            # In a real implementation, we would use a condition variable
            # For simplicity, we'll just create a new connection
            conn = sqlite3.connect(self.db_path)
            return conn
    
    def _release_connection(self, conn: sqlite3.Connection) -> None:
        """Release a connection back to the pool"""
        with self._lock:
            if conn in self._in_use:
                self._in_use.remove(conn)

class Database:
    def __init__(self, db_path: str = "./database.db"):
        self.pool = DatabasePool(db_path)
    
    def execute_query(self, query: str, params: Tuple = ()) -> List[Tuple]:
        """Execute a query with parameters and return the results"""
        with self.pool.get_connection() as conn:
            try:
                cursor = conn.cursor()
                cursor.execute(query, params)
                result = cursor.fetchall()
                conn.commit()
                return result
            except Exception as e:
                conn.rollback()
                raise e
    
    def execute_update(self, query: str, params: Tuple = ()) -> int:
        """Execute an update query and return the number of affected rows"""
        with self.pool.get_connection() as conn:
            try:
                cursor = conn.cursor()
                cursor.execute(query, params)
                conn.commit()
                return cursor.rowcount
            except Exception as e:
                conn.rollback()
                raise e
    
    def get_tables(self) -> List[str]:
        """Get a list of all tables in the database"""
        with self.pool.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%';")
            return [row[0] for row in cursor.fetchall()]
    
    def get_schema(self) -> Dict[str, str]:
        """Get the schema for all tables in the database"""
        with self.pool.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT name, sql FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%';")
            return {row[0]: row[1] for row in cursor.fetchall()}
```

### 2.2 Client and Web Interface Refactoring (Week 4)

#### 2.2.1 Refactor Command-Line Client
- Create a modular CLI client using the new architecture
- Implement better error handling and user feedback

```python
# Example structure for cli.py
import asyncio
import json
from typing import Dict, Any, List
import ollama
from ..core.config import Config
from ..utils.tool_handler import ToolCallParser
from ..utils.tool_result import ToolResultFormatter
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

class CLIClient:
    def __init__(self):
        self.config = Config()
        self.messages = []
        self.ollama_client = ollama.AsyncClient(host=self.config.get("ollama.api_url"))
        self.system_prompt = self._get_system_prompt()
        
        # Server parameters
        self.server_params = StdioServerParameters(
            command="python",
            args=["./main.py", "--server-mode"],
            env=None,
        )
    
    def _get_system_prompt(self) -> str:
        """Get the system prompt based on available tools"""
        # This would be more sophisticated in a real implementation
        return """You are an assistant with access to various tools.
        Use the appropriate tool for each task.
        For SQL queries, first check the schema if needed, then execute the query.
        For time-related operations, use the time tools."""
    
    async def run(self):
        """Run the CLI client"""
        # Initialize the messages with the system prompt
        self.messages = [{"role": "system", "content": self.system_prompt}]
        
        # Connect to the MCP server
        async with stdio_client(self.server_params) as (read, write):
            async with ClientSession(read, write) as session:
                # Initialize the connection
                await session.initialize()
                
                # Start the chat loop
                await self._chat_loop(session)
    
    async def _chat_loop(self, session: ClientSession):
        """Main chat loop"""
        print("CLI Client started. Type 'exit' to quit.")
        
        while True:
            # Get user input
            user_input = input("\nQuery: ").strip()
            
            # Check for exit command
            if user_input.lower() in ["exit", "quit", "q"]:
                print("Exiting...")
                break
            
            # Add user message to history
            self.messages.append({"role": "user", "content": user_input})
            
            # Process the query
            await self._process_query(session, user_input)
    
    async def _process_query(self, session: ClientSession, query: str):
        """Process a user query"""
        try:
            # Get available tools
            mcp_response = await session.list_tools()
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
            
            # Call Ollama
            model_name = self.config.get("ollama.model")
            response = await self.ollama_client.chat(
                model=model_name,
                messages=self.messages,
                tools=available_tools,
                stream=False,
            )
            
            # Process the response
            assistant_message = response['message']
            self.messages.append(assistant_message)
            
            # Check for tool calls
            tool_calls = ToolCallParser.parse_tool_calls(assistant_message)
            
            if tool_calls:
                # Execute each tool call
                for tool_name, tool_args in tool_calls:
                    print(f"\nCalling tool: {tool_name}")
                    
                    # Call the tool
                    tool_result = await session.call_tool(tool_name, tool_args)
                    result_text = getattr(tool_result.content[0], "text", "")
                    
                    # Format the result
                    formatted_result = ToolResultFormatter.format_result(tool_name, result_text)
                    print(f"Tool result: {formatted_result}")
                    
                    # Add tool result to messages
                    self.messages.append({
                        "role": "tool",
                        "content": formatted_result,
                    })
                
                # Make a follow-up call to Ollama
                final_response = await self.ollama_client.chat(
                    model=model_name,
                    messages=self.messages,
                    stream=False,
                )
                
                # Process the final response
                final_message = final_response['message']
                self.messages.append(final_message)
                print(f"\nAssistant: {final_message.get('content', '')}")
            else:
                # No tool calls, just print the response
                print(f"\nAssistant: {assistant_message.get('content', '')}")
        
        except Exception as e:
            print(f"\nError: {str(e)}")
```

#### 2.2.2 Refactor Web Interface
- Update the Gradio web interface to use the new architecture
- Implement better error handling and user feedback

```python
# Example structure for web.py
import asyncio
import threading
import queue
import time
from typing import Dict, Any, List, Tuple
import gradio as gr
import ollama
from ..core.config import Config
from ..utils.tool_handler import ToolCallParser
from ..utils.tool_result import ToolResultFormatter
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

class WebInterface:
    def __init__(self):
        self.config = Config()
        self.message_queue = queue.Queue()
        self.ollama_client = ollama.AsyncClient(host=self.config.get("ollama.api_url"))
        self.system_prompt = self._get_system_prompt()
        
        # Server parameters
        self.server_params = StdioServerParameters(
            command="python",
            args=["./main.py", "--server-mode"],
            env=None,
        )
        
        # Start the backend
        self._start_backend()
    
    def _get_system_prompt(self) -> str:
        """Get the system prompt based on available tools"""
        # This would be more sophisticated in a real implementation
        return """You are an assistant with access to various tools.
        Use the appropriate tool for each task.
        For SQL queries, first check the schema if needed, then execute the query.
        For time-related operations, use the time tools."""
    
    def _start_backend(self):
        """Start the backend processing thread"""
        threading.Thread(target=self._start_mcp_server, daemon=True).start()
    
    def _start_mcp_server(self):
        """Initialize and run the MCP server connection"""
        asyncio.run(self._run_server())
    
    async def _run_server(self):
        """Run the MCP server and initialize the connection"""
        async with stdio_client(self.server_params) as (read, write):
            async with ClientSession(read, write) as session:
                # Initialize the connection
                await session.initialize()
                
                # Process messages from the queue
                while True:
                    try:
                        # Check if there are any messages in the queue
                        if not self.message_queue.empty():
                            query, response_callback = self.message_queue.get()
                            result = await self._process_query(session, query)
                            response_callback(result)
                    except Exception as e:
                        print(f"Error processing message: {str(e)}")
                    
                    # Short sleep to prevent CPU hogging
                    await asyncio.sleep(0.1)
    
    async def _process_query(self, session: ClientSession, query: str) -> List[str]:
        """Process a query and return the response messages"""
        all_responses = []
        messages = [{"role": "system", "content": self.system_prompt}]
        
        try:
            # Add user message
            messages.append({"role": "user", "content": query})
            
            # Get available tools
            mcp_response = await session.list_tools()
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
            
            # Call Ollama
            model_name = self.config.get("ollama.model")
            response = await self.ollama_client.chat(
                model=model_name,
                messages=messages,
                tools=available_tools,
                stream=False,
            )
            
            # Process the response
            assistant_message = response['message']
            messages.append(assistant_message)
            
            # Check for tool calls
            tool_calls = ToolCallParser.parse_tool_calls(assistant_message)
            
            if tool_calls:
                # Execute each tool call
                for tool_name, tool_args in tool_calls:
                    # Call the tool
                    tool_result = await session.call_tool(tool_name, tool_args)
                    result_text = getattr(tool_result.content[0], "text", "")
                    
                    # Format the result
                    formatted_result = ToolResultFormatter.format_result(tool_name, result_text)
                    
                    # Add tool result to messages
                    messages.append({
                        "role": "tool",
                        "content": formatted_result,
                    })
                
                # Make a follow-up call to Ollama
                final_response = await self.ollama_client.chat(
                    model=model_name,
                    messages=messages,
                    stream=False,
                )
                
                # Process the final response
                final_message = final_response['message']
                messages.append(final_message)
                all_responses.append(final_message.get('content', ''))
            else:
                # No tool calls, just add the response
                all_responses.append(assistant_message.get('content', ''))
        
        except Exception as e:
            all_responses.append(f"Error: {str(e)}")
        
        return all_responses
    
    def submit_query(self, query: str, chat_history: list) -> Tuple[list, list]:
        """Submit a query and update the chat history"""
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
        self.message_queue.put((query, on_result))
        
        # Wait for the result
        while not result_container:
            time.sleep(0.1)
        
        # Update the last history entry with the response
        chat_history[-1] = (query, result_container[0])
        
        return chat_history, chat_history
    
    def launch(self):
        """Launch the web interface"""
        # Create the Gradio interface
        with gr.Blocks(title="AI Assistant", theme=gr.themes.Soft(), css="footer {visibility: hidden}") as demo:
            gr.Markdown("# AI Assistant")
            gr.Markdown("""This application allows you to interact with various tools through natural language.
            Ask questions about data, time, or other supported domains.""")
            
            chatbot = gr.Chatbot(
                label="Chat",
                height=500,
                bubble_full_width=False,
                show_copy_button=True
            )
            
            with gr.Row():
                msg = gr.Textbox(
                    label="Ask a question",
                    placeholder="For example: 'What time is it?' or 'Show me all users'",
                    scale=9
                )
                submit = gr.Button("Submit", scale=1)
            
            with gr.Accordion("Example Queries", open=False):
                example_queries = [
                    "What time is it in UTC?",
                    "List all tables in the database",
                    "Show me all users",
                    "Calculate the time difference between 2023-01-01T00:00:00Z and 2023-01-02T12:30:45Z"
                ]
                gr.Examples(
                    examples=example_queries,
                    inputs=msg
                )
            
            # Set up event handlers
            submit.click(self.submit_query, [msg, chatbot], [chatbot, chatbot]).then(
                lambda: "", None, [msg]  # Clear the input box after submission
            )
            msg.submit(self.submit_query, [msg, chatbot], [chatbot, chatbot]).then(
                lambda: "", None, [msg]  # Clear the input box after submission
            )
        
        # Launch the interface
        port = self.config.get("web.port")
        share = self.config.get("web.share")
        demo.launch(share=share, server_port=port)
```

## Phase 3: Time Agent Integration and Error Handling

### 3.1 Time Agent Integration (Week 5)

#### 3.1.1 Implement Time Agent
- Create the time agent using the new architecture
- Implement all time-related tools

#### 3.1.2 Update System Prompt
- Update the system prompt to include information about time tools
- Add examples of how to use the time tools

#### 3.1.3 Test Time Agent Integration
- Test the time agent with various queries
- Fix any issues that arise

### 3.2 Error Handling Improvements (Week 6)

#### 3.2.1 Implement Custom Exceptions
- Create a hierarchy of custom exceptions
- Use specific exception types for different error scenarios

#### 3.2.2 Add Retry Mechanisms
- Implement exponential backoff for external service calls
- Add retry decorators for database operations

#### 3.2.3 Implement Graceful Degradation
- Add fallback strategies for when services are unavailable
- Implement circuit breakers for critical components

## Phase 4: Security Enhancements and Testing

### 4.1 Security Improvements (Week 7)

#### 4.1.1 Implement SQL Parameterization
- Update all SQL queries to use parameterized queries
- Add input validation for all user-provided data

#### 4.1.2 Add Input Validation
- Implement comprehensive input validation
- Add schema validation for tool arguments

### 4.2 Testing and Documentation (Week 8)

#### 4.2.1 Add Automated Tests
- Implement unit tests for core components
- Add integration tests for the full system

#### 4.2.2 Create Comprehensive Documentation
- Document the architecture and design
- Create user and developer guides

## Implementation Timeline

| Week | Phase | Tasks |
|------|-------|-------|
| 1 | 1.1 | Tool Calling Standardization |
| 2 | 1.2 | Plugin Architecture Implementation |
| 3 | 2.1 | Project Structure Reorganization |
| 4 | 2.2 | Client and Web Interface Refactoring |
| 5 | 3.1 | Time Agent Integration |
| 6 | 3.2 | Error Handling Improvements |
| 7 | 4.1 | Security Improvements |
| 8 | 4.2 | Testing and Documentation |

## Getting Started

To begin implementing this plan:

1. Create a new branch from `feat/rearchitect-app`
2. Start with Phase 1.1: Tool Calling Standardization
   - Create the `tool_handler.py` module
   - Create the `tool_result.py` module
   - Update the client and app code to use these modules
3. Continue with Phase 1.2: Plugin Architecture Implementation
   - Create the registry and agent interface
   - Implement the base agents
   - Create the server factory

This phased approach allows for incremental improvements while maintaining a working application throughout the process.
