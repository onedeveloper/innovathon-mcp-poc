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
