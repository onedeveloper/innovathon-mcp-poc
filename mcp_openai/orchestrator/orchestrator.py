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
