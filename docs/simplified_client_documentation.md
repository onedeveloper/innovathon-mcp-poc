# Simplified MCP Chat Client - Usage Documentation

## Overview

The Simplified MCP Chat Client is a command-line interface for interacting with your local MCP Server implementation and its agents. It provides a chat-like interface that allows you to send messages and receive responses, with support for both LLM-powered interactions using Ollama and direct tool calls.

This client is designed to work directly with your local implementation without requiring the external `mcp-server` package, making it compatible with Python 3.12 and earlier versions.

## Installation

### Prerequisites

Before using the Simplified MCP Chat Client, ensure you have the following dependencies installed:

```bash
# Install core dependencies
uv add jsonschema pytz

# Install optional dependencies for enhanced experience
uv add rich ollama
```

Note: The `rich` library provides enhanced console output with syntax highlighting and markdown rendering, but the client will work without it. The `ollama` library is only needed if you want to use LLM-powered interactions.

### Ollama Setup (Optional)

For LLM-powered interactions, you need to install and run Ollama:

1. Install Ollama from [https://ollama.com/](https://ollama.com/)
2. Start the Ollama server
3. Pull a model (e.g., `ollama pull llama3.2:1b`)

## Running the Chat Client

### Basic Usage

To start the chat client with default settings:

```bash
python simple_mcp_chat_client.py
```

This will start the client in direct tool calls mode, where you need to manually specify tool calls.

### LLM Mode

To start the chat client with LLM-powered interactions:

```bash
python simple_mcp_chat_client.py --model llama3.2:1b
```

Replace `llama3.2:1b` with any model available in your Ollama installation.

### Advanced Options

The chat client supports several command-line options:

```bash
python simple_mcp_chat_client.py --server-script ./mcp_server.py --model llama3.2:1b
```

- `--server-script`: Path to the MCP Server script (default: `./mcp_server.py`)
- `--model`: The model to use for LLM-powered interactions (default: environment variable `OLLAMA_MODEL_NAME` or `llama3.2:1b`)

## Interaction Modes

### LLM Mode

In LLM mode, you can interact with the chat client using natural language. The LLM will interpret your messages and call the appropriate tools when needed.

Example:

```
You: What time is it?
Assistant: I'll check the current time for you.

Calling tool: get_current_time
{
  "format": "human"
}

Tool result:
Wednesday, April 06, 2025 18:30:45 UTC

