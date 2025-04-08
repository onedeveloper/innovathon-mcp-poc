# MCP Agentic System - Environment Setup

This document provides instructions for setting up the environment and running the MCP Agentic System.

## Prerequisites

- Python 3.10+
- pip (Python package installer)
- SQLite3

## Environment Setup

1. Clone the repository or extract the project files to your local machine.

2. Create a `.env` file in each component directory with the following content:

```
# SQLiteAgent .env (sqlite_agent/.env)
SQLITE_DB_PATH=database.db

# TimeAgent .env (time_agent/.env)
# No specific environment variables needed

# Orchestrator .env (orchestrator/.env)
SQLITE_AGENT_URL=http://localhost:8001
TIME_AGENT_URL=http://localhost:8002
LLM_PROVIDER=openai
OPENAI_API_KEY=your_openai_key
LLM_MODEL=gpt-4

# CLI .env (cli/.env)
ORCHESTRATOR_URL=http://localhost:8000
```

Note: Replace `your_openai_key` with an actual OpenAI API key.

3. Install dependencies for each component:

```bash
# SQLiteAgent
cd sqlite_agent
pip install -r requirements.txt

# TimeAgent
cd ../time_agent
pip install -r requirements.txt

# Orchestrator
cd ../orchestrator
pip install -r requirements.txt

# CLI
cd ../cli
pip install -r requirements.txt
```

## Running the System

1. Start the SQLiteAgent:

```bash
cd sqlite_agent
uvicorn server:mcp.app --host 0.0.0.0 --port 8001
```

2. Start the TimeAgent:

```bash
cd time_agent
uvicorn server:mcp.app --host 0.0.0.0 --port 8002
```

3. Start the Orchestrator:

```bash
cd orchestrator
uvicorn orchestrator:app --host 0.0.0.0 --port 8000
```

4. Run the CLI client:

```bash
cd cli
python cli.py
```

## Testing

1. Create a test database:

```bash
python test_db_setup.py
```

2. Run individual component tests:

```bash
python test_sqlite_agent.py
python test_time_agent.py
python test_orchestrator.py
```

3. Run integration tests:

```bash
python test_integration.py
```

## Example Queries

Once the CLI client is running, you can try the following example queries:

- "What tables are in the database?"
- "What is the schema of the users table?"
- "How many users are older than 25?"
- "What day is it today?"
- "How many days until January 1, 2026?"
- "How many days between January 1, 2025 and July 4, 2025?"

## Troubleshooting

- If you encounter connection errors, ensure all services are running on the correct ports.
- If you see authentication errors with the LLM API, check your API key in the `.env` file.
- If the SQLiteAgent cannot find the database, check the `SQLITE_DB_PATH` environment variable.
