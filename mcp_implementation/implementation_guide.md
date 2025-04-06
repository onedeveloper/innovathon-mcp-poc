# MCP Server/Client Application Implementation Guide

## Introduction

This guide provides detailed instructions for implementing the improvements to the MCP Server/Client application. The improvements focus on creating a more modular, extensible, and robust application with better error handling and security.

## Table of Contents

1. [Project Structure](#project-structure)
2. [Tool Calling Standardization](#tool-calling-standardization)
3. [Plugin Architecture](#plugin-architecture)
4. [Modularization](#modularization)
5. [Time Functionality Agent](#time-functionality-agent)
6. [Error Handling](#error-handling)
7. [Security Enhancements](#security-enhancements)
8. [Testing and Deployment](#testing-and-deployment)

## Project Structure

The improved application follows a modular package structure:

```
mcp_app/
├── __init__.py
├── agents/
│   ├── __init__.py
│   ├── sql_agent.py
│   └── time_agent.py
├── core/
│   ├── __init__.py
│   ├── agent_interface.py
│   ├── config.py
│   ├── registry.py
│   └── server_factory.py
├── utils/
│   ├── __init__.py
│   ├── db.py
│   ├── degradation.py
│   ├── exceptions.py
│   ├── retry.py
│   ├── security.py
│   ├── tool_handler.py
│   └── tool_result.py
├── main.py
├── mcp_server.py
└── mcp_client.py
```

## Tool Calling Standardization

The tool calling standardization components provide a unified approach to parsing tool calls from Ollama responses and formatting tool results.

### Tool Handler

The `tool_handler.py` module provides a `ToolCallParser` class that can parse tool calls from both structured and tag-based formats:

```python
from utils.tool_handler import ToolCallParser

# Parse tool calls from an Ollama message
tool_calls = ToolCallParser.parse_tool_calls(message)

# Process each tool call
for tool_name, tool_args in tool_calls:
    # Call the tool
    result = call_tool(tool_name, tool_args)
    # Process the result
    # ...
```

### Tool Result Formatter

The `tool_result.py` module provides a `ToolResultFormatter` class for consistent formatting of tool results:

```python
from utils.tool_result import ToolResultFormatter

# Format a tool result
formatted_result = ToolResultFormatter.format_result(tool_name, result)

# Format an error
error_message = ToolResultFormatter.format_error(tool_name, error)
```

## Plugin Architecture

The plugin architecture enables dynamic registration and discovery of agents and tools.

### Agent Registry

The `registry.py` module provides a singleton `AgentRegistry` class for registering agents and tools:

```python
from core.registry import AgentRegistry

# Get the registry
registry = AgentRegistry()

# Register an agent
registry.register_agent("SQLAgent", sql_agent)

# Register a tool
registry.register_tool(
    name="query_data",
    tool_function=sql_agent.query_data,
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

# Get all tools
tools = registry.get_all_tools()
```

### Agent Interface

The `agent_interface.py` module defines an abstract base class that all agents must implement:

```python
from core.agent_interface import Agent

class MyAgent(Agent):
    def register_tools(self) -> None:
        # Register agent's tools with the registry
        pass
    
    def initialize(self) -> None:
        # Initialize the agent
        pass
    
    def process_request(self, request: Dict[str, Any]) -> Dict[str, Any]:
        # Process a request directed to this agent
        pass
```

### Server Factory

The `server_factory.py` module provides a factory for creating and configuring MCP servers with registered agents:

```python
from core.server_factory import MCPServerFactory

# Create a server with specified agents
mcp = MCPServerFactory.create_server(
    name="My MCP Server",
    agent_modules=["agents.sql_agent.SQLAgent", "agents.time_agent.TimeAgent"]
)

# Register an additional agent with an existing server
MCPServerFactory.register_additional_agent(
    mcp=mcp,
    agent_module="agents.my_agent.MyAgent"
)
```

## Modularization

The modularization components provide a proper package structure and configuration management.

### Configuration

The `config.py` module provides a singleton `Config` class for centralized configuration management:

```python
from core.config import Config

# Get the configuration
config = Config()

# Get a configuration value
model_name = config.get("ollama.model", "llama3.2:1b")
db_path = config.get("database.path", "./database.db")
```

### Database Access

The `db.py` module provides a secure database access layer with connection pooling:

```python
from utils.db import Database

# Create a database instance
db = Database(db_path="./database.db")

# Execute a query
results = db.execute_query(
    query="SELECT * FROM users WHERE age > :min_age",
    params={"min_age": 18}
)

# Execute an update
affected_rows = db.execute_update(
    query="UPDATE users SET active = :active WHERE id = :id",
    params={"active": True, "id": 123}
)

# Get tables and schema
tables = db.get_tables()
schema = db.get_schema()
```

## Time Functionality Agent

The time functionality agent provides tools for time-related operations.

### Time Agent

The `time_agent.py` module implements the `TimeAgent` class with various time-related tools:

```python
from agents.time_agent import TimeAgent

# Create a time agent
time_agent = TimeAgent()

# Initialize and register tools
time_agent.initialize()
time_agent.register_tools()

# Use time tools
current_time = time_agent.get_current_time(timezone="UTC", format="iso")
time_diff = time_agent.calculate_time_difference(
    start_time="2023-01-01T00:00:00Z",
    end_time="2023-01-02T12:30:45Z",
    unit="hours"
)
```

### Available Time Tools

The time agent provides the following tools:

1. `get_current_time`: Get the current time in a specified timezone and format
2. `calculate_time_difference`: Calculate the difference between two timestamps
3. `format_timestamp`: Format a timestamp in a specified format
4. `get_time_in_timezone`: Get the current time in a specific timezone

## Error Handling

The error handling components provide a robust error handling system with custom exceptions, retry mechanisms, and graceful degradation patterns.

### Custom Exceptions

The `exceptions.py` module defines a hierarchy of custom exceptions:

```python
from utils.exceptions import DatabaseError, ToolExecutionError

# Raise a database error
raise DatabaseError("Failed to connect to database")

# Raise a tool execution error
raise ToolExecutionError(tool_name="query_data", message="Invalid SQL query")
```

### Retry Mechanisms

The `retry.py` module provides decorators for implementing retry logic with exponential backoff:

```python
from utils.retry import retry, CircuitBreaker

# Retry a function with exponential backoff
@retry(exceptions=[ConnectionError], max_tries=3, delay=1.0, backoff=2.0)
def fetch_data():
    # Function that might fail temporarily
    pass

# Apply circuit breaker pattern
@CircuitBreaker(failure_threshold=5, recovery_timeout=30.0)
def call_external_service():
    # Function that might fail for extended periods
    pass
```

### Graceful Degradation

The `degradation.py` module provides utilities for implementing graceful degradation patterns:

```python
from utils.degradation import with_fallback, FeatureToggle

# Provide a fallback value when a function fails
@with_fallback(fallback_value=[], exceptions=[ConnectionError])
def get_items():
    # Function that might fail
    pass

# Use feature toggles
FeatureToggle.set_feature("advanced_search", enabled=True)

@FeatureToggle.when_enabled("advanced_search")
def perform_advanced_search():
    # Function that should only run when the feature is enabled
    pass
```

## Security Enhancements

The security components provide utilities for implementing security best practices.

### SQL Security

The `security.py` module provides utilities for preventing SQL injection:

```python
from utils.security import SQLSecurity

# Check if a query is potentially unsafe
is_safe = SQLSecurity.is_safe_query(query)

# Parameterize a query
parameterized_query, param_values = SQLSecurity.parameterize_query(
    query="SELECT * FROM users WHERE age > :min_age",
    params={"min_age": 18}
)

# Safely execute a query
results = SQLSecurity.safe_execute(conn, query, params)
```

### Input Validation

The `security.py` module also provides a decorator for validating function input:

```python
from utils.security import validate_input

# Validate function input against a schema
@validate_input({
    "required": ["username", "password"],
    "properties": {
        "username": {
            "type": "string",
            "pattern": "^[a-zA-Z0-9_]{3,16}$"
        },
        "password": {
            "type": "string",
            "minLength": 8
        }
    }
})
def create_user(username, password):
    # Function with validated input
    pass
```

### Sanitization

The `security.py` module provides functions for sanitizing HTML and filenames:

```python
from utils.security import sanitize_html, sanitize_filename

# Sanitize HTML to prevent XSS attacks
safe_html = sanitize_html(user_input)

# Sanitize a filename to prevent path traversal
safe_filename = sanitize_filename(user_input)
```

## Testing and Deployment

### Running the Application

To run the application, use the `main.py` script with the appropriate mode:

```bash
# Run in server mode
python main.py --server-mode

# Run in client mode
python main.py --client-mode

# Run in web interface mode
python main.py --web-mode
```

### Adding New Agents

To add a new agent to the application:

1. Create a new agent class that implements the `Agent` interface
2. Register the agent with the registry
3. Update the configuration to enable the agent

Example:

```python
from core.agent_interface import Agent
from core.registry import AgentRegistry

class MyAgent(Agent):
    def __init__(self):
        self.registry = AgentRegistry()
    
    def register_tools(self) -> None:
        self.registry.register_tool(
            name="my_tool",
            tool_function=self.my_tool,
            description="My custom tool",
            schema={
                "type": "object",
                "properties": {
                    "param": {
                        "type": "string",
                        "description": "A parameter"
                    }
                }
            }
        )
    
    def initialize(self) -> None:
        # Initialize the agent
        pass
    
    def process_request(self, request: Dict[str, Any]) -> Dict[str, Any]:
        # Process a request
        pass
    
    def my_tool(self, param: str = None) -> str:
        # Implement the tool
        return f"Tool result: {param}"
```

### Configuration

The application can be configured using environment variables or a configuration file:

```bash
# Set environment variables
export OLLAMA_MODEL_NAME=llama3.2:1b
export DATABASE_PATH=./database.db
export SERVER_NAME="My MCP Server"
export ENABLED_AGENTS=SQLAgent,TimeAgent
```

Or create a `config.json` file:

```json
{
  "ollama": {
    "model": "llama3.2:1b",
    "api_url": "http://localhost:11434"
  },
  "database": {
    "path": "./database.db"
  },
  "server": {
    "name": "My MCP Server",
    "agents": ["SQLAgent", "TimeAgent"]
  },
  "web": {
    "port": 7860,
    "share": false
  }
}
```

## Conclusion

This implementation guide provides a comprehensive overview of the improvements made to the MCP Server/Client application. By following this guide, you can understand and extend the application with new features and agents.

The modular architecture, plugin system, and robust error handling make the application more maintainable, extensible, and reliable. The security enhancements ensure that the application is protected against common vulnerabilities.
