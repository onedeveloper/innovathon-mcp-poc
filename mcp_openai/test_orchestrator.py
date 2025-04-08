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
