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
