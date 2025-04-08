# MCP Agentic System - Implementation Approach

This document outlines the detailed implementation approach for each component of the MCP Agentic System.

## 1. SQLiteAgent Implementation

### File Structure
```
sqlite_agent/
├── server.py       # Main server file with MCP tools
├── db_utils.py     # Database utility functions
├── requirements.txt
└── .env            # Configuration
```

### Dependencies
```
mcp[cli]
fastapi
uvicorn
pydantic
```

### Implementation Steps

#### server.py
```python
from mcp.server.fastmcp import FastMCP
from pydantic import BaseModel
from typing import List, Dict, Any, Optional
import sqlite3
import os
from db_utils import get_db_connection, is_safe_query

# Initialize MCP server
mcp = FastMCP("SQLiteAgent")

# Get database path from environment variable
DB_PATH = os.getenv("SQLITE_DB_PATH", "database.db")

class TableSchema(BaseModel):
    column_name: str
    data_type: str
    is_nullable: bool
    is_primary_key: bool

class QueryResult(BaseModel):
    rows: List[Dict[str, Any]]
    row_count: int

@mcp.tool(description="List all tables in the connected SQLite database")
def list_tables() -> List[str]:
    """Returns a list of all table names in the database."""
    conn = get_db_connection(DB_PATH)
    cursor = conn.cursor()
    
    # Query for all table names
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
    tables = [row[0] for row in cursor.fetchall()]
    
    conn.close()
    return tables

@mcp.tool(description="Get schema information for a specific table")
def describe_table(table_name: str) -> List[TableSchema]:
    """Returns schema information for the specified table."""
    conn = get_db_connection(DB_PATH)
    cursor = conn.cursor()
    
    # Get table info
    cursor.execute(f"PRAGMA table_info({table_name});")
    columns = cursor.fetchall()
    
    result = []
    for col in columns:
        result.append(TableSchema(
            column_name=col[1],
            data_type=col[2],
            is_nullable=not col[3],
            is_primary_key=bool(col[5])
        ))
    
    conn.close()
    return result

@mcp.tool(description="Execute a read-only SQL query and return results")
def query_db(query: str) -> QueryResult:
    """Executes a read-only SQL query and returns the results."""
    # Validate query is safe (SELECT only)
    if not is_safe_query(query):
        raise ValueError("Only SELECT queries are allowed for security reasons")
    
    conn = get_db_connection(DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute(query)
    columns = [desc[0] for desc in cursor.description]
    rows = cursor.fetchall()
    
    # Convert to list of dictionaries
    result_rows = []
    for row in rows:
        result_rows.append({columns[i]: row[i] for i in range(len(columns))})
    
    conn.close()
    return QueryResult(rows=result_rows, row_count=len(result_rows))

# Run with: uvicorn server:mcp.app --port 8001
```

#### db_utils.py
```python
import sqlite3
import re

def get_db_connection(db_path):
    """Create a database connection to the SQLite database."""
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    return conn

def is_safe_query(query):
    """Check if a query is safe (SELECT only)."""
    # Remove comments and normalize whitespace
    clean_query = re.sub(r'--.*$', '', query, flags=re.MULTILINE)
    clean_query = re.sub(r'/\*.*?\*/', '', clean_query, flags=re.DOTALL)
    clean_query = clean_query.strip()
    
    # Check if query starts with SELECT
    return clean_query.upper().startswith('SELECT')
```

## 2. TimeAgent Implementation

### File Structure
```
time_agent/
├── server.py       # Main server file with MCP tools
├── requirements.txt
└── .env            # Configuration
```

### Dependencies
```
mcp[cli]
fastapi
uvicorn
pydantic
```

### Implementation Steps

#### server.py
```python
from mcp.server.fastmcp import FastMCP
from datetime import datetime, timedelta
import calendar

# Initialize MCP server
mcp = FastMCP("TimeAgent")

@mcp.tool(description="Get the current weekday")
def get_current_day() -> str:
    """Returns the current weekday name."""
    return calendar.day_name[datetime.now().weekday()]

@mcp.tool(description="Get the current date in YYYY-MM-DD format")
def get_current_date() -> str:
    """Returns the current date in YYYY-MM-DD format."""
    return datetime.now().strftime("%Y-%m-%d")

@mcp.tool(description="Calculate days until a future date")
def days_until(target_date: str) -> int:
    """
    Calculate the number of days until a future date.
    
    Args:
        target_date: Future date in YYYY-MM-DD format
        
    Returns:
        Number of days until the target date
    """
    current_date = datetime.now().date()
    future_date = datetime.strptime(target_date, "%Y-%m-%d").date()
    
    if future_date < current_date:
        raise ValueError("Target date must be in the future")
        
    delta = future_date - current_date
    return delta.days

@mcp.tool(description="Calculate days since a past date")
def days_since(past_date: str) -> int:
    """
    Calculate the number of days since a past date.
    
    Args:
        past_date: Past date in YYYY-MM-DD format
        
    Returns:
        Number of days since the past date
    """
    current_date = datetime.now().date()
    past_date_obj = datetime.strptime(past_date, "%Y-%m-%d").date()
    
    if past_date_obj > current_date:
        raise ValueError("Past date must be in the past")
        
    delta = current_date - past_date_obj
    return delta.days

@mcp.tool(description="Calculate days between two dates")
def days_between(date1: str, date2: str) -> int:
    """
    Calculate the number of days between two dates.
    
    Args:
        date1: First date in YYYY-MM-DD format
        date2: Second date in YYYY-MM-DD format
        
    Returns:
        Absolute number of days between the two dates
    """
    date1_obj = datetime.strptime(date1, "%Y-%m-%d").date()
    date2_obj = datetime.strptime(date2, "%Y-%m-%d").date()
    
    delta = abs((date2_obj - date1_obj).days)
    return delta

# Run with: uvicorn server:mcp.app --port 8002
```

## 3. Orchestrator Implementation

### File Structure
```
orchestrator/
├── orchestrator.py  # Main orchestrator implementation
├── llm_client.py    # LLM API client
├── mcp_client.py    # MCP client for agent communication
├── requirements.txt
└── .env             # Configuration
```

### Dependencies
```
fastapi
uvicorn
pydantic
pydantic-ai
httpx
python-dotenv
```

### Implementation Steps

#### orchestrator.py
```python
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List, Dict, Any, Optional, Union
import os
import json
import asyncio
from dotenv import load_dotenv

from llm_client import LLMClient
from mcp_client import MCPClient

# Load environment variables
load_dotenv()

# Initialize FastAPI app
app = FastAPI(title="MCP Orchestrator")

# Initialize clients
llm_client = LLMClient()
sqlite_agent = MCPClient(os.getenv("SQLITE_AGENT_URL", "http://localhost:8001"))
time_agent = MCPClient(os.getenv("TIME_AGENT_URL", "http://localhost:8002"))

# Define request/response models
class ChatRequest(BaseModel):
    query: str

class ChatResponse(BaseModel):
    response: str
    status: str = "success"
    error: Optional[str] = None

@app.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    try:
        # Fetch context from all MCP agents asynchronously
        contexts = await asyncio.gather(
            sqlite_agent.get_context(),
            time_agent.get_context()
        )
        
        # Combine tool schemas from all agents
        tools = []
        for context in contexts:
            if context and "tools" in context:
                tools.extend(context["tools"])
        
        # Prepare prompt with tools and user query
        prompt = f"""You are an expert assistant with tool access. Use one of these functions if appropriate, or answer directly:

Functions:
{json.dumps(tools, indent=2)}

User question:
{request.query}

Your response:
"""
        
        # Call LLM
        llm_response = await llm_client.generate(prompt, tools)
        
        # Check if LLM wants to call a tool
        if llm_response.get("type") == "tool_call":
            tool_name = llm_response["tool_call"]["name"]
            tool_params = llm_response["tool_call"]["parameters"]
            
            # Determine which agent has this tool
            agent_with_tool = None
            for i, context in enumerate(contexts):
                if any(tool["name"] == tool_name for tool in context.get("tools", [])):
                    agent_with_tool = [sqlite_agent, time_agent][i]
                    break
            
            if not agent_with_tool:
                return ChatResponse(
                    response=f"I tried to use a tool '{tool_name}' but couldn't find it.",
                    status="error",
                    error=f"Tool '{tool_name}' not found in any agent"
                )
            
            # Call the tool
            tool_result = await agent_with_tool.call_action(tool_name, tool_params)
            
            # Format the result for the user
            return ChatResponse(
                response=f"I used the {tool_name} tool to find: {json.dumps(tool_result, indent=2)}"
            )
        else:
            # Return direct LLM response
            return ChatResponse(response=llm_response["content"])
            
    except Exception as e:
        return ChatResponse(
            response=f"Sorry, I encountered an error: {str(e)}",
            status="error",
            error=str(e)
        )

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
```

#### llm_client.py
```python
import os
import json
from typing import List, Dict, Any, Optional
import httpx
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class LLMClient:
    def __init__(self):
        self.provider = os.getenv("LLM_PROVIDER", "openai").lower()
        self.openai_api_key = os.getenv("OPENAI_API_KEY", "")
        self.anthropic_api_key = os.getenv("ANTHROPIC_API_KEY", "")
        self.model = os.getenv("LLM_MODEL", "gpt-4")
        
        if self.provider == "openai" and not self.openai_api_key:
            raise ValueError("OPENAI_API_KEY environment variable is required")
        elif self.provider == "anthropic" and not self.anthropic_api_key:
            raise ValueError("ANTHROPIC_API_KEY environment variable is required")
    
    async def generate(self, prompt: str, tools: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Generate a response from the LLM."""
        if self.provider == "openai":
            return await self._call_openai(prompt, tools)
        elif self.provider == "anthropic":
            return await self._call_anthropic(prompt, tools)
        else:
            raise ValueError(f"Unsupported LLM provider: {self.provider}")
    
    async def _call_openai(self, prompt: str, tools: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Call the OpenAI API."""
        async with httpx.AsyncClient() as client:
            # Convert MCP tool format to OpenAI function format
            functions = []
            for tool in tools:
                functions.append({
                    "name": tool["name"],
                    "description": tool.get("description", ""),
                    "parameters": tool.get("parameters", {})
                })
            
            response = await client.post(
                "https://api.openai.com/v1/chat/completions",
                headers={
                    "Authorization": f"Bearer {self.openai_api_key}",
                    "Content-Type": "application/json"
                },
                json={
                    "model": self.model,
                    "messages": [{"role": "user", "content": prompt}],
                    "functions": functions,
                    "function_call": "auto"
                },
                timeout=30.0
            )
            
            response.raise_for_status()
            result = response.json()
            
            message = result["choices"][0]["message"]
            
            # Check if there's a function call
            if "function_call" in message:
                function_call = message["function_call"]
                return {
                    "type": "tool_call",
                    "tool_call": {
                        "name": function_call["name"],
                        "parameters": json.loads(function_call["arguments"])
                    }
                }
            else:
                return {
                    "type": "text",
                    "content": message["content"]
                }
    
    async def _call_anthropic(self, prompt: str, tools: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Call the Anthropic API."""
        async with httpx.AsyncClient() as client:
            # Convert MCP tool format to Anthropic tool format
            anthropic_tools = []
            for tool in tools:
                anthropic_tools.append({
                    "name": tool["name"],
                    "description": tool.get("description", ""),
                    "input_schema": tool.get("parameters", {})
                })
            
            response = await client.post(
                "https://api.anthropic.com/v1/messages",
                headers={
                    "x-api-key": self.anthropic_api_key,
                    "anthropic-version": "2023-06-01",
                    "Content-Type": "application/json"
                },
                json={
                    "model": self.model,
                    "messages": [{"role": "user", "content": prompt}],
                    "tools": anthropic_tools
                },
                timeout=30.0
            )
            
            response.raise_for_status()
            result = response.json()
            
            message = result["content"][0]
            
            # Check if there's a tool call
            if message["type"] == "tool_use":
                return {
                    "type": "tool_call",
                    "tool_call": {
                        "name": message["name"],
                        "parameters": message["input"]
                    }
                }
            else:
                return {
                    "type": "text",
                    "content": message["text"]
                }
```

#### mcp_client.py
```python
from typing import Dict, Any, Optional
import httpx

class MCPClient:
    def __init__(self, base_url: str):
        self.base_url = base_url.rstrip("/")
    
    async def get_context(self) -> Dict[str, Any]:
        """Get the context (tool schemas) from an MCP agent."""
        async with httpx.AsyncClient() as client:
            try:
                response = await client.get(f"{self.base_url}/context", timeout=5.0)
                response.raise_for_status()
                return response.json()
            except httpx.HTTPError as e:
                print(f"Error fetching context from {self.base_url}: {str(e)}")
                return {}
    
    async def call_action(self, name: str, parameters: Dict[str, Any]) -> Any:
        """Call an action on an MCP agent."""
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.base_url}/action",
                json={"name": name, "parameters": parameters},
                timeout=10.0
            )
            response.raise_for_status()
            result = response.json()
            
            if "error" in result and result["error"]:
                raise Exception(f"MCP agent error: {result['error']}")
            
            return result.get("result")
```

## 4. CLI Client Implementation

### File Structure
```
cli/
├── cli.py          # CLI client implementation
├── requirements.txt
└── .env            # Configuration
```

### Dependencies
```
httpx
python-dotenv
```

### Implementation Steps

#### cli.py
```python
import os
import sys
import json
import asyncio
import httpx
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Get orchestrator URL from environment
ORCHESTRATOR_URL = os.getenv("ORCHESTRATOR_URL", "http://localhost:8000")

async def send_query(query: str) -> dict:
    """Send a query to the orchestrator and return the response."""
    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(
                f"{ORCHESTRATOR_URL}/chat",
                json={"query": query},
                timeout=30.0
            )
            response.raise_for_status()
            return response.json()
        except httpx.HTTPError as e:
            print(f"Error communicating with orchestrator: {str(e)}")
            return {"status": "error", "error": str(e), "response": "Failed to communicate with the orchestrator."}

async def main():
    print("MCP Agentic System CLI")
    print("Type 'exit' or 'quit' to exit")
    print("=" * 50)
    
    while True:
        # Get user input
        query = input("\nYou: ").strip()
        
        # Check for exit command
        if query.lower() in ["exit", "quit"]:
            print("Goodbye!")
            break
        
        # Skip empty queries
        if not query:
            continue
        
        print("Thinking...")
        
        # Send query to orchestrator
        response = await send_query(query)
        
        # Display response
        if response["status"] == "success":
            print(f"\nAssistant: {response['response']}")
        else:
            print(f"\nError: {response.get('error', 'Unknown error')}")
            print(f"Assistant: {response['response']}")

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nGoodbye!")
        sys.exit(0)
```

## 5. Project Setup and Configuration

### Directory Structure
```
mcp_project/
├── sqlite_agent/
│   ├── server.py
│   ├── db_utils.py
│   └── requirements.txt
├── time_agent/
│   ├── server.py
│   └── requirements.txt
├── orchestrator/
│   ├── orchestrator.py
│   ├── llm_client.py
│   ├── mcp_client.py
│   └── requirements.txt
├── cli/
│   ├── cli.py
│   └── requirements.txt
├── .env.example
├── setup.sh
└── README.md
```

### .env.example
```
# MCP Agent URLs
SQLITE_AGENT_URL=http://localhost:8001
TIME_AGENT_URL=http://localhost:8002
ORCHESTRATOR_URL=http://localhost:8000

# LLM Configuration
LLM_PROVIDER=openai  # or anthropic
OPENAI_API_KEY=your_openai_key
ANTHROPIC_API_KEY=your_anthropic_key
LLM_MODEL=gpt-4  # or claude-3-opus-20240229

# SQLite Configuration
SQLITE_DB_PATH=/path/to/database.db
```

### setup.sh
```bash
#!/bin/bash

# Create virtual environments for each component
echo "Creating virtual environments..."
python3 -m venv sqlite_agent/venv
python3 -m venv time_agent/venv
python3 -m venv orchestrator/venv
python3 -m venv cli/venv

# Install dependencies for SQLiteAgent
echo "Installing SQLiteAgent dependencies..."
sqlite_agent/venv/bin/pip install -r sqlite_agent/requirements.txt

# Install dependencies for TimeAgent
echo "Installing TimeAgent dependencies..."
time_agent/venv/bin/pip install -r time_agent/requirements.txt

# Install dependencies for Orchestrator
echo "Installing Orchestrator dependencies..."
orchestrator/venv/bin/pip install -r orchestrator/requirements.txt

# Install dependencies for CLI
echo "Installing CLI dependencies..."
cli/venv/bin/pip install -r cli/requirements.txt

# Create .env files from example
echo "Creating .env files..."
cp .env.example sqlite_agent/.env
cp .env.example time_agent/.env
cp .env.example orchestrator/.env
cp .env.example cli/.env

echo "Setup complete! Please update the .env files with your configuration."
```

## 6. Running the System

### Start SQLiteAgent
```bash
cd sqlite_agent
source venv/bin/activate
uvicorn server:mcp.app --host 0.0.0.0 --port 8001
```

### Start TimeAgent
```bash
cd time_agent
source venv/bin/activate
uvicorn server:mcp.app --host 0.0.0.0 --port 8002
```

### Start Orchestrator
```bash
cd orchestrator
source venv/bin/activate
uvicorn orchestrator:app --host 0.0.0.0 --port 8000
```

### Run CLI Client
```bash
cd cli
source venv/bin/activate
python cli.py
```

## 7. Testing Strategy

1. **Unit Testing**:
   - Test each MCP Agent function individually
   - Test LLM client with mock responses
   - Test MCP client with mock responses

2. **Integration Testing**:
   - Test Orchestrator with mock MCP Agents
   - Test CLI with mock Orchestrator

3. **End-to-End Testing**:
   - Test complete system flow with sample queries
   - Validate SQLiteAgent with a test database
   - Validate TimeAgent with various date calculations

4. **Example Test Queries**:
   - "What tables are in the database?"
   - "What is the schema of the users table?"
   - "How many days until Christmas?"
   - "What day of the week is it today?"
   - "How many days between January 1, 2025 and July 4, 2025?"
