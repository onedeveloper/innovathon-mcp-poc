# MCP Agentic System - README

## Overview

The MCP Agentic System is a Proof of Concept (PoC) system that demonstrates how a user chat client can interact with a central Orchestrator, which employs a Large Language Model (LLM) to decide whether to return an answer outright or invoke external tools via the Model Context Protocol (MCP).

The system consists of four main components:

1. **SQLiteAgent**: A FastAPI-based MCP agent that provides database operations against a SQLite database.
2. **TimeAgent**: A FastAPI-based MCP agent that provides date and time calculation utilities.
3. **Orchestrator**: A central coordinator that decides when to use tools vs. direct answers, powered by PydanticAI.
4. **CLI Client**: A simple text interface for user interactions.

## System Architecture

The system follows a modular architecture where specialized agents expose their functionality as tools via the MCP protocol. The Orchestrator dynamically discovers these tools, presents them to an LLM, and dispatches calls to the appropriate agent when needed.

### Data Flow

1. User enters a query in the CLI
2. CLI sends the query to the Orchestrator
3. Orchestrator fetches tool schemas from MCP Agents
4. Orchestrator sends prompt to LLM
5. If LLM returns a tool call, Orchestrator dispatches it to the appropriate agent
6. Orchestrator returns the final response to the CLI
7. CLI displays the response to the user

## Components

### SQLiteAgent

The SQLiteAgent provides database operations against a SQLite database. It exposes the following functions:

- `list_tables()`: Returns a list of all tables in the connected database
- `describe_table(table_name)`: Returns schema information for a specific table
- `query_db(query)`: Executes read-only SQL queries and returns results

### TimeAgent

The TimeAgent provides date and time calculation utilities. It exposes the following functions:

- `get_current_day()`: Returns the current weekday
- `get_current_date()`: Returns the current date in YYYY-MM-DD format
- `days_until(target_date)`: Calculates days until a future date
- `days_since(past_date)`: Calculates days since a past date
- `days_between(date1, date2)`: Calculates the difference in days between two dates

### Orchestrator

The Orchestrator is the central coordinator that decides when to use tools vs. direct answers. It:

1. Dynamically fetches tool schemas from MCP Agents
2. Constructs LLM prompts with user query and available tools
3. Parses LLM responses to determine if a tool call is needed
4. Dispatches tool calls to appropriate MCP Agents when necessary
5. Returns final responses to the CLI client

### CLI Client

The CLI Client is a simple text interface for user interactions. It:

1. Presents a command loop for user input
2. Sends user queries to the Orchestrator
3. Displays responses from the Orchestrator

## Installation and Setup

See [Setup Instructions](docs/setup_instructions.md) for detailed installation and setup instructions.

## Usage

Once the system is running, you can interact with it through the CLI client. Here are some example queries:

- "What tables are in the database?"
- "What is the schema of the users table?"
- "How many users are older than 25?"
- "What day is it today?"
- "How many days until January 1, 2026?"
- "How many days between January 1, 2025 and July 4, 2025?"

## Testing

The system includes comprehensive test scripts for each component and integration testing. See [Test Plan](docs/test_plan.md) for detailed testing information.

## Documentation

- [System Architecture](docs/system_architecture.md): Detailed architecture of the system
- [Implementation Approach](docs/implementation_approach.md): Detailed implementation approach for each component
- [Implementation Plan](docs/implementation_plan.md): Phased implementation plan with timelines and priorities
- [Setup Instructions](docs/setup_instructions.md): Installation and setup instructions
- [Test Plan](docs/test_plan.md): Comprehensive testing approach

## Future Extensions

Future extensions to the system could include:

- Security/authentication/TLS
- Multi-tool chain workflows
- Persistent conversation history
- GUI/Web chat frontends
- Richer agent metadata
- Advanced observability/logging

## License

This project is licensed under the MIT License - see the LICENSE file for details.
