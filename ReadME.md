# AI SQL Assistant

A natural language interface for interacting with SQLite databases, powered by Ollama running a local LLM (e.g., Gemma).

## Overview

This application allows users to interact with SQLite databases using natural language. Instead of writing SQL queries manually, users can ask questions or give instructions in plain English. A locally running Large Language Model (LLM) via Ollama generates the appropriate SQL query, which the application then executes, returning formatted results.

## Features

- **Natural Language Queries**: Ask questions about your data in plain English
- **SQL Query Generation**: Automatically generates SQL queries based on user input
- **Query Execution**: Executes the generated queries against a connected SQLite database
- **Result Formatting**: Displays query results in a readable format
- **Error Handling**: Provides clear explanations when queries fail
- **Example Queries**: Includes sample queries to help users get started

## Architecture

The application consists of two main components:

1.  **Web Interface & Backend Logic** (`app.py`): A Gradio web interface that handles user interaction, sends requests to Ollama, receives generated SQL, executes the SQL against the database, and formats the results.
2.  **Local LLM Service (Ollama)**: A separate service running locally (e.g., `ollama serve`) that hosts the language model (e.g., `gemma3:27b`) and provides an API for `app.py` to call.

```mermaid
graph LR
    subgraph User Machine
        subgraph Gradio UI (app.py)
            UI[User Interface] --> Input{User Input (NL Query)}
        end

        subgraph Backend Logic (app.py)
            Input --> CP[ChatProcessor]
            CP -- NL Query + History + Prompt --> OllamaClient[Ollama Client Call]
            OllamaClient -- Generated SQL --> CP
            CP -- Execute SQL --> DB[(database.db)]
            DB -- Results --> CP
            CP -- Formatted Results/Response --> UI
        end

        subgraph Ollama Service
            OllamaClient <--> OllamaAPI[Ollama API (localhost:11434)]
            OllamaAPI -- Runs --> LLM[LLM Model (e.g., gemma3:27b)]
        end
    end

    style DB fill:#f9f,stroke:#333,stroke-width:2px
    style OllamaService fill:#ccf,stroke:#333,stroke-width:1px
```

## Prerequisites

- Python 3.11+ (as specified in `pyproject.toml`)
- [Ollama](https://ollama.com/) installed and running.
- An Ollama-compatible model downloaded, e.g., `ollama pull gemma3:27b`

## Installation

1. Clone this repository:
   ```
   git clone https://github.com/yourusername/ai-sql-assistant.git
   cd ai-sql-assistant
   ```

2. Install dependencies using `uv` (recommended) or `pip`:
   ```bash
   # Using uv (preferred)
   uv sync

   # Or using pip
   pip install .
   ```
   *(Note: A `.env` file is no longer required for API keys)*

## Usage

1. Ensure the Ollama service is running in a separate terminal:
   ```bash
   ollama serve
   ```
   *(Wait for it to indicate it's listening)*

2. Start the application in another terminal:
   ```bash
   python app.py
   ```

2. Open your web browser and navigate to:
   ```
   http://localhost:7860
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

### Ollama & Local LLM

The application uses [Ollama](https://ollama.com/) to interact with a locally running Large Language Model (LLM), such as `gemma3:27b`. The LLM is responsible for:
1. Understanding natural language queries based on the provided database schema.
2. Generating the corresponding SQLite query.

The `app.py` script then takes this generated SQL and executes it directly.

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

The system prompt that guides the local LLM's behavior (instructing it how to generate SQL based on the schema) can be modified in the `ChatProcessor` class in `app.py`. The database schema is automatically fetched and included in this prompt.

## Limitations

- Currently only supports SQLite databases
- Complex queries might require refinement
- Limited error recovery for malformed queries

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

This project is licensed under the MIT License - see the LICENSE file for details.
