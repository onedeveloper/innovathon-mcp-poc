# AI SQL Assistant

A natural language interface for interacting with SQLite databases, powered by Ollama.

## Overview

This application allows users to interact with SQLite databases using natural language. Instead of writing SQL queries manually, users can ask questions or give instructions in plain English, and the AI will generate and execute the appropriate SQL queries, returning formatted results.

## Features

- **Natural Language Queries**: Ask questions about your data in plain English
- **SQL Query Generation**: Automatically generates SQL queries based on user input
- **Query Execution**: Executes the generated queries against a connected SQLite database
- **Result Formatting**: Displays query results in a readable format
- **Error Handling**: Provides clear explanations when queries fail
- **Example Queries**: Includes sample queries to help users get started

## Architecture

The application consists of three main components:

1. **Web Interface** (`app.py`): A Gradio web interface that allows users to interact with the AI
2. **MCP Server** (`mcp_server.py`): A server that handles SQL query execution
3. **MCP Client** (`mcp_client.py`): A client that facilitates communication between the web interface and the MCP server

## Prerequisites

- Python 3.11+
- [uv](https://github.com/astral-sh/uv) (Python package installer and resolver)
- [Ollama](https://ollama.com/) installed and running locally.
## Installation

1. Clone this repository:
   ```
   git clone https://github.com/onedeveloper/innovathon-mcp-poc.git
   cd ai-sql-assistant
   ```

2. Install dependencies using uv:
   ```bash
   uv sync
   ```

3. **(Optional)** Create a `.env` file in the project root to specify the Ollama model:
   ```
   OLLAMA_MODEL_NAME=your_ollama_model_name # e.g., llama3.2:1b
   ```
   If not set, the application defaults to `llama3.2:1b`.

4. Ensure the Ollama model you intend to use is available locally. You can pull it using:
   ```bash
   ollama pull <model_name> # e.g., ollama pull llama3.2:1b
   ```

## Usage

1. Start the application:
   ```
   python app.py
   ```

2. Open your web browser and navigate to:
   ```
   http://127.0.0.1:7860
   ```

3. Type in a natural language query and press Enter or click Submit.

## Sample Queries

Here are some example queries you can try:

- "List all tables in the database"
- "Show me all users"
- "Count how many products cost more than $300"
- "What's the total value of all products in stock?"
- "Insert a new product called 'Tablet' with price $499.99 and stock 5"
- "Update the price of Laptop to $1099.99"

## Sample Database

The application creates a sample SQLite database with the following tables:

### Users Table
- `id`: INTEGER (Primary Key)
- `name`: TEXT
- `email`: TEXT
- `created_at`: TIMESTAMP

### Products Table
- `id`: INTEGER (Primary Key)
- `name`: TEXT
- `price`: REAL
- `stock`: INTEGER

## Technical Details

### MCP (Model Context Protocol)

The application uses MCP to manage communication between the AI model and the SQLite database tools. MCP allows the model to call functions (tools) provided by the `mcp_server.py` (like `query_data`, `get_database_schema`, `list_tables`) and receive results, enabling it to interact with the database.

### Ollama

The application uses a local Ollama model (defaulting to `llama3.2:1b`, configurable via the `OLLAMA_MODEL_NAME` environment variable) to:
1. Understand natural language queries.
2. Decide which MCP tool to call (`query_data`, `get_database_schema`, or `list_tables`).
3. Format the results from the tools for the user.

### SQLite

The application uses SQLite for database operations. SQLite is:
- Lightweight
- Serverless
- Self-contained
- Zero-configuration

## Customization

### Connecting to Your Own Database

To use your own SQLite database instead of the sample one:

1. Replace the database initialization in `app.py` with your own database file path
2. Update the sample table documentation in the UI to match your schema

### Modifying the System Prompt

The system prompt that guides the AI model's behavior can be modified in the `ChatProcessor` class in `app.py`.

## Limitations

- Currently only supports SQLite databases
- Complex queries might require refinement
- Limited error recovery for malformed queries

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

This project is licensed under the MIT License - see the LICENSE file for details.
