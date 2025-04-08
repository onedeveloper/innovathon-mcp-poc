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
