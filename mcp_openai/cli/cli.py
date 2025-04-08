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
