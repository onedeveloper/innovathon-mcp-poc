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
