# MCP Agentic System - System Architecture

## Overview

This document outlines the detailed architecture for the MCP Agentic System, which consists of:

1. Two FastAPI-based MCP agents (SQLiteAgent and TimeAgent)
2. A central Orchestrator Agent (powered by PydanticAI)
3. A simple CLI client

The system enables natural language interactions with specialized tools through a unified interface, leveraging Large Language Models (LLMs) for decision-making on when to use tools versus providing direct answers.

## Component Architecture

### 1. MCP Agents

#### SQLiteAgent
- **Purpose**: Provides database operations against a SQLite database
- **Technology**: python-sdk (mcp.server.fastmcp.FastMCP)
- **Exposed Functions**:
  - `list_tables()`: Returns a list of all tables in the connected database
  - `describe_table(table_name: str)`: Returns schema information for a specific table
  - `query_db(query: str)`: Executes read-only SQL queries and returns results
- **Implementation Details**:
  - Uses Python's sqlite3 library for database operations
  - Implements safety checks to prevent unsafe queries (only allows SELECT statements)
  - Exposes functions as tools via the @mcp.tool decorator
  - Runs on port 8001

#### TimeAgent
- **Purpose**: Provides date and time calculation utilities
- **Technology**: python-sdk (mcp.server.fastmcp.FastMCP)
- **Exposed Functions**:
  - `get_current_day()`: Returns the current weekday
  - `get_current_date()`: Returns the current date in YYYY-MM-DD format
  - `days_until(target_date: str)`: Calculates days until a future date
  - `days_since(past_date: str)`: Calculates days since a past date
  - `days_between(date1: str, date2: str)`: Calculates the difference in days between two dates
- **Implementation Details**:
  - Uses Python's datetime library for date calculations
  - Exposes functions as tools via the @mcp.tool decorator
  - Runs on port 8002

### 2. Orchestrator Agent

- **Purpose**: Central coordinator that decides when to use tools vs. direct answers
- **Technology**: PydanticAI + FastAPI
- **Key Functions**:
  - Dynamically fetches tool schemas from MCP Agents
  - Constructs LLM prompts with user query and available tools
  - Parses LLM responses to determine if a tool call is needed
  - Dispatches tool calls to appropriate MCP Agents when necessary
  - Returns final responses to the CLI client
- **Implementation Details**:
  - Uses PydanticAI to wrap LLM interactions
  - Implements async HTTP requests via httpx
  - Maintains a stateless design between calls
  - Exposes a `/chat` endpoint for client interactions
  - Runs on port 8000

### 3. CLI Client

- **Purpose**: Provides a simple text interface for user interactions
- **Technology**: Python + requests/httpx
- **Key Functions**:
  - Presents a command loop for user input
  - Sends user queries to the Orchestrator
  - Displays responses from the Orchestrator
- **Implementation Details**:
  - Uses Python's built-in input() function for user interaction
  - Communicates with the Orchestrator via HTTP POST requests
  - Formats and displays responses in a user-friendly manner

## Data Flow

1. **User Query Flow**:
   - User enters a query in the CLI
   - CLI sends a POST request to `http://<ORCHESTRATOR>/chat` with JSON payload: `{"query": "<user question>"}`
   - Orchestrator processes the query and returns a JSON response: `{"response": "...", "status": "success/error", "error": "...optional..."}`
   - CLI displays the response to the user

2. **Orchestrator Processing Flow**:
   - Orchestrator receives query from CLI
   - Asynchronously queries both MCP Agents' `/context` endpoints to get tool schemas
   - Constructs a prompt containing the user query and available tool schemas
   - Sends the prompt to the LLM (OpenAI or Anthropic)
   - Parses the LLM response:
     - If direct answer: returns it to the CLI
     - If tool call: dispatches an `/action` call to the relevant MCP Agent
   - If tool was called, formats the tool result and returns it to the CLI

3. **MCP Agent Processing Flow**:
   - Agent receives `/context` request from Orchestrator and returns function schemas
   - Agent receives `/action` request from Orchestrator when a tool is called
   - Agent executes the requested function with provided parameters
   - Agent returns the function result to the Orchestrator

## API Interfaces

### CLI to Orchestrator
- **Endpoint**: POST `/chat`
- **Request Format**:
  ```json
  {
    "query": "string"
  }
  ```
- **Response Format**:
  ```json
  {
    "response": "string",
    "status": "success|error",
    "error": "string (optional)"
  }
  ```

### Orchestrator to MCP Agents
- **Context Endpoint**: GET `/context`
- **Response Format**:
  ```json
  {
    "name": "string",
    "description": "string",
    "tools": [
      {
        "name": "string",
        "description": "string",
        "parameters": {
          "type": "object",
          "properties": {...},
          "required": [...]
        },
        "returns": {...}
      },
      ...
    ]
  }
  ```

- **Action Endpoint**: POST `/action`
- **Request Format**:
  ```json
  {
    "name": "string",
    "parameters": {...}
  }
  ```
- **Response Format**:
  ```json
  {
    "result": "any",
    "error": "string (optional)"
  }
  ```

## Deployment Architecture

```
┌─────────────┐         ┌─────────────────┐         ┌───────────────┐
│             │  HTTP   │                 │  HTTP   │               │
│  CLI Client │ ───────►│   Orchestrator  │ ───────►│  SQLiteAgent  │
│             │         │                 │         │               │
└─────────────┘         └─────────────────┘         └───────────────┘
                                │
                                │ HTTP
                                ▼
                         ┌───────────────┐         ┌───────────────┐
                         │               │  HTTP   │               │
                         │   TimeAgent   │ ◄─────► │    LLM API    │
                         │               │         │               │
                         └───────────────┘         └───────────────┘
```

- **SQLiteAgent**: Runs on port 8001
- **TimeAgent**: Runs on port 8002
- **Orchestrator**: Runs on port 8000
- **CLI**: Direct user interaction, no port needed

## Configuration

The system will use environment variables for configuration:

```
# MCP Agent URLs
SQLITE_AGENT_URL=http://localhost:8001
TIME_AGENT_URL=http://localhost:8002

# LLM Configuration
LLM_PROVIDER=openai  # or anthropic
OPENAI_API_KEY=your_openai_key
ANTHROPIC_API_KEY=your_anthropic_key
LLM_MODEL=gpt-4  # or claude-3-opus-20240229

# SQLite Configuration
SQLITE_DB_PATH=/path/to/database.db
```

## Error Handling

- **CLI**: Displays error messages from the Orchestrator
- **Orchestrator**: 
  - Handles LLM API errors
  - Handles MCP Agent communication errors
  - Returns appropriate error messages to the CLI
- **MCP Agents**:
  - Handle function execution errors
  - Return error messages to the Orchestrator

## Future Extensions

As noted in the specifications, future extensions could include:
- Security/authentication/TLS
- Multi-tool chain workflows
- Persistent conversation history
- GUI/Web chat frontends
- Richer agent metadata
- Advanced observability/logging
