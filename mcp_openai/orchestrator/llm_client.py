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
