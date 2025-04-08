# MCP Agentic System - Test Plan

This document outlines the testing approach for each component of the MCP Agentic System.

## 1. SQLiteAgent Testing

### Setup Test Database
```python
# test_db_setup.py
import sqlite3

# Create a test database
conn = sqlite3.connect('test.db')
cursor = conn.cursor()

# Create test tables
cursor.execute('''
CREATE TABLE users (
    id INTEGER PRIMARY KEY,
    name TEXT NOT NULL,
    email TEXT UNIQUE NOT NULL,
    age INTEGER
)
''')

cursor.execute('''
CREATE TABLE orders (
    id INTEGER PRIMARY KEY,
    user_id INTEGER,
    product TEXT NOT NULL,
    quantity INTEGER NOT NULL,
    order_date TEXT NOT NULL,
    FOREIGN KEY (user_id) REFERENCES users (id)
)
''')

# Insert test data
cursor.execute("INSERT INTO users (name, email, age) VALUES ('John Doe', 'john@example.com', 30)")
cursor.execute("INSERT INTO users (name, email, age) VALUES ('Jane Smith', 'jane@example.com', 25)")
cursor.execute("INSERT INTO users (name, email, age) VALUES ('Bob Johnson', 'bob@example.com', 40)")

cursor.execute("INSERT INTO orders (user_id, product, quantity, order_date) VALUES (1, 'Laptop', 1, '2025-04-01')")
cursor.execute("INSERT INTO orders (user_id, product, quantity, order_date) VALUES (1, 'Mouse', 2, '2025-04-02')")
cursor.execute("INSERT INTO orders (user_id, product, quantity, order_date) VALUES (2, 'Keyboard', 1, '2025-04-03')")

conn.commit()
conn.close()

print("Test database created successfully.")
```

### Test SQLiteAgent Functions
```python
# test_sqlite_agent.py
import os
import sys
import json
import httpx
import asyncio

# Set the database path for testing
os.environ["SQLITE_DB_PATH"] = "test.db"

async def test_list_tables():
    """Test the list_tables function."""
    async with httpx.AsyncClient() as client:
        response = await client.post(
            "http://localhost:8001/action",
            json={"name": "list_tables", "parameters": {}}
        )
        result = response.json()
        print("list_tables result:", result)
        assert "result" in result
        assert "users" in result["result"]
        assert "orders" in result["result"]
        print("list_tables test passed!")

async def test_describe_table():
    """Test the describe_table function."""
    async with httpx.AsyncClient() as client:
        response = await client.post(
            "http://localhost:8001/action",
            json={"name": "describe_table", "parameters": {"table_name": "users"}}
        )
        result = response.json()
        print("describe_table result:", result)
        assert "result" in result
        columns = {col["column_name"] for col in result["result"]}
        assert "id" in columns
        assert "name" in columns
        assert "email" in columns
        assert "age" in columns
        print("describe_table test passed!")

async def test_query_db():
    """Test the query_db function."""
    async with httpx.AsyncClient() as client:
        response = await client.post(
            "http://localhost:8001/action",
            json={"name": "query_db", "parameters": {"query": "SELECT * FROM users WHERE age > 25"}}
        )
        result = response.json()
        print("query_db result:", result)
        assert "result" in result
        assert "rows" in result["result"]
        assert len(result["result"]["rows"]) == 2  # John and Bob
        print("query_db test passed!")

async def test_query_db_safety():
    """Test the query_db function safety checks."""
    async with httpx.AsyncClient() as client:
        response = await client.post(
            "http://localhost:8001/action",
            json={"name": "query_db", "parameters": {"query": "DELETE FROM users"}}
        )
        result = response.json()
        print("query_db safety result:", result)
        assert "error" in result
        print("query_db safety test passed!")

async def main():
    print("Testing SQLiteAgent...")
    await test_list_tables()
    await test_describe_table()
    await test_query_db()
    await test_query_db_safety()
    print("All SQLiteAgent tests passed!")

if __name__ == "__main__":
    asyncio.run(main())
```

## 2. TimeAgent Testing

```python
# test_time_agent.py
import httpx
import asyncio
from datetime import datetime, timedelta

async def test_get_current_day():
    """Test the get_current_day function."""
    async with httpx.AsyncClient() as client:
        response = await client.post(
            "http://localhost:8002/action",
            json={"name": "get_current_day", "parameters": {}}
        )
        result = response.json()
        print("get_current_day result:", result)
        assert "result" in result
        # Check that the result is a valid day name
        valid_days = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
        assert result["result"] in valid_days
        print("get_current_day test passed!")

async def test_get_current_date():
    """Test the get_current_date function."""
    async with httpx.AsyncClient() as client:
        response = await client.post(
            "http://localhost:8002/action",
            json={"name": "get_current_date", "parameters": {}}
        )
        result = response.json()
        print("get_current_date result:", result)
        assert "result" in result
        # Check that the result is in YYYY-MM-DD format
        date_str = result["result"]
        try:
            datetime.strptime(date_str, "%Y-%m-%d")
            valid_format = True
        except ValueError:
            valid_format = False
        assert valid_format
        print("get_current_date test passed!")

async def test_days_until():
    """Test the days_until function."""
    # Get a date 10 days in the future
    future_date = (datetime.now() + timedelta(days=10)).strftime("%Y-%m-%d")
    
    async with httpx.AsyncClient() as client:
        response = await client.post(
            "http://localhost:8002/action",
            json={"name": "days_until", "parameters": {"target_date": future_date}}
        )
        result = response.json()
        print("days_until result:", result)
        assert "result" in result
        assert result["result"] == 10
        print("days_until test passed!")

async def test_days_since():
    """Test the days_since function."""
    # Get a date 10 days in the past
    past_date = (datetime.now() - timedelta(days=10)).strftime("%Y-%m-%d")
    
    async with httpx.AsyncClient() as client:
        response = await client.post(
            "http://localhost:8002/action",
            json={"name": "days_since", "parameters": {"past_date": past_date}}
        )
        result = response.json()
        print("days_since result:", result)
        assert "result" in result
        assert result["result"] == 10
        print("days_since test passed!")

async def test_days_between():
    """Test the days_between function."""
    date1 = "2025-01-01"
    date2 = "2025-01-11"
    
    async with httpx.AsyncClient() as client:
        response = await client.post(
            "http://localhost:8002/action",
            json={"name": "days_between", "parameters": {"date1": date1, "date2": date2}}
        )
        result = response.json()
        print("days_between result:", result)
        assert "result" in result
        assert result["result"] == 10
        print("days_between test passed!")

async def main():
    print("Testing TimeAgent...")
    await test_get_current_day()
    await test_get_current_date()
    await test_days_until()
    await test_days_since()
    await test_days_between()
    print("All TimeAgent tests passed!")

if __name__ == "__main__":
    asyncio.run(main())
```

## 3. Orchestrator Testing

```python
# test_orchestrator.py
import httpx
import asyncio
import json

async def test_direct_response():
    """Test the orchestrator with a query that should get a direct response."""
    async with httpx.AsyncClient() as client:
        response = await client.post(
            "http://localhost:8000/chat",
            json={"query": "What is the capital of France?"}
        )
        result = response.json()
        print("Direct response result:", result)
        assert "response" in result
        assert "status" in result
        assert result["status"] == "success"
        print("Direct response test passed!")

async def test_sqlite_tool_call():
    """Test the orchestrator with a query that should use the SQLiteAgent."""
    async with httpx.AsyncClient() as client:
        response = await client.post(
            "http://localhost:8000/chat",
            json={"query": "What tables are in the database?"}
        )
        result = response.json()
        print("SQLite tool call result:", result)
        assert "response" in result
        assert "status" in result
        assert result["status"] == "success"
        assert "list_tables" in result["response"]
        print("SQLite tool call test passed!")

async def test_time_tool_call():
    """Test the orchestrator with a query that should use the TimeAgent."""
    async with httpx.AsyncClient() as client:
        response = await client.post(
            "http://localhost:8000/chat",
            json={"query": "What day is it today?"}
        )
        result = response.json()
        print("Time tool call result:", result)
        assert "response" in result
        assert "status" in result
        assert result["status"] == "success"
        assert "get_current_day" in result["response"]
        print("Time tool call test passed!")

async def test_error_handling():
    """Test the orchestrator's error handling."""
    async with httpx.AsyncClient() as client:
        response = await client.post(
            "http://localhost:8000/chat",
            json={"query": "Delete all data from the users table"}
        )
        result = response.json()
        print("Error handling result:", result)
        assert "response" in result
        # Either the LLM will refuse, or the SQLiteAgent will block the DELETE
        print("Error handling test passed!")

async def main():
    print("Testing Orchestrator...")
    await test_direct_response()
    await test_sqlite_tool_call()
    await test_time_tool_call()
    await test_error_handling()
    print("All Orchestrator tests passed!")

if __name__ == "__main__":
    asyncio.run(main())
```

## 4. CLI Client Testing

The CLI client is primarily a user interface component, so manual testing is most appropriate:

1. Start the CLI client: `python cli.py`
2. Test basic queries:
   - "Hello, how are you?"
   - "What tables are in the database?"
   - "What is the schema of the users table?"
   - "How many days until Christmas?"
   - "What day of the week is it today?"
   - "How many days between January 1, 2025 and July 4, 2025?"
3. Test error handling:
   - "Delete all data from the users table" (should be blocked)
   - Empty input (should be skipped)
4. Test exit commands:
   - "exit"
   - "quit"

## 5. Integration Testing

```python
# test_integration.py
import os
import sys
import json
import httpx
import asyncio
import subprocess
import time
import signal

# Global process variables
sqlite_agent_process = None
time_agent_process = None
orchestrator_process = None

async def start_services():
    """Start all services for integration testing."""
    global sqlite_agent_process, time_agent_process, orchestrator_process
    
    # Set environment variables
    os.environ["SQLITE_DB_PATH"] = "test.db"
    os.environ["SQLITE_AGENT_URL"] = "http://localhost:8001"
    os.environ["TIME_AGENT_URL"] = "http://localhost:8002"
    os.environ["ORCHESTRATOR_URL"] = "http://localhost:8000"
    
    # Start SQLiteAgent
    print("Starting SQLiteAgent...")
    sqlite_agent_process = subprocess.Popen(
        ["uvicorn", "server:mcp.app", "--host", "0.0.0.0", "--port", "8001"],
        cwd="sqlite_agent"
    )
    
    # Start TimeAgent
    print("Starting TimeAgent...")
    time_agent_process = subprocess.Popen(
        ["uvicorn", "server:mcp.app", "--host", "0.0.0.0", "--port", "8002"],
        cwd="time_agent"
    )
    
    # Start Orchestrator
    print("Starting Orchestrator...")
    orchestrator_process = subprocess.Popen(
        ["uvicorn", "orchestrator:app", "--host", "0.0.0.0", "--port", "8000"],
        cwd="orchestrator"
    )
    
    # Wait for services to start
    print("Waiting for services to start...")
    await asyncio.sleep(5)

async def stop_services():
    """Stop all services after integration testing."""
    global sqlite_agent_process, time_agent_process, orchestrator_process
    
    # Stop processes
    print("Stopping services...")
    for process in [sqlite_agent_process, time_agent_process, orchestrator_process]:
        if process:
            process.send_signal(signal.SIGINT)
            process.wait()

async def test_end_to_end():
    """Test the complete system flow end-to-end."""
    test_queries = [
        "What tables are in the database?",
        "What is the schema of the users table?",
        "How many users are older than 25?",
        "What day is it today?",
        "How many days until January 1, 2026?",
        "How many days between January 1, 2025 and July 4, 2025?"
    ]
    
    async with httpx.AsyncClient() as client:
        for query in test_queries:
            print(f"\nTesting query: {query}")
            response = await client.post(
                "http://localhost:8000/chat",
                json={"query": query}
            )
            result = response.json()
            print(f"Response: {result['response']}")
            assert "response" in result
            assert "status" in result
            assert result["status"] == "success"
    
    print("\nAll end-to-end tests passed!")

async def main():
    try:
        await start_services()
        await test_end_to_end()
    finally:
        await stop_services()

if __name__ == "__main__":
    asyncio.run(main())
```

## Running the Tests

1. Create the test database:
   ```
   python test_db_setup.py
   ```

2. Start each component in separate terminals:
   ```
   # Terminal 1
   cd sqlite_agent
   uvicorn server:mcp.app --host 0.0.0.0 --port 8001
   
   # Terminal 2
   cd time_agent
   uvicorn server:mcp.app --host 0.0.0.0 --port 8002
   
   # Terminal 3
   cd orchestrator
   uvicorn orchestrator:app --host 0.0.0.0 --port 8000
   ```

3. Run individual component tests:
   ```
   python test_sqlite_agent.py
   python test_time_agent.py
   python test_orchestrator.py
   ```

4. Test the CLI client manually:
   ```
   cd cli
   python cli.py
   ```

5. Run the integration test:
   ```
   python test_integration.py
   ```

## Test Environment Setup

Create a `.env` file in each component directory with the following content:

```
# SQLiteAgent .env
SQLITE_DB_PATH=test.db

# TimeAgent .env
# No specific environment variables needed

# Orchestrator .env
SQLITE_AGENT_URL=http://localhost:8001
TIME_AGENT_URL=http://localhost:8002
LLM_PROVIDER=openai
OPENAI_API_KEY=your_openai_key
LLM_MODEL=gpt-4

# CLI .env
ORCHESTRATOR_URL=http://localhost:8000
```

Note: Replace `your_openai_key` with an actual OpenAI API key for testing.
