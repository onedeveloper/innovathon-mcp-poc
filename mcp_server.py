# server.py
import sqlite3

from loguru import logger
from mcp.server.fastmcp import FastMCP

# Create an MCP server
mcp = FastMCP("Demo")


@mcp.tool()
def query_data(sql: str) -> str:
    """Execute SQL queries safely"""
    logger.info(f"Executing SQL query: {sql}")
    conn = sqlite3.connect("./database.db")
    try:
        result = conn.execute(sql).fetchall()
        conn.commit()
        return "\n".join(str(row) for row in result)
    except Exception as e:
        return f"Error: {str(e)}"
    finally:
        conn.close()


@mcp.tool()
def list_tables() -> str:
    """Lists all non-system tables in the database."""
    logger.info("Listing database tables")
    conn = sqlite3.connect("./database.db")
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%';")
        tables = cursor.fetchall()
        if not tables:
            return "No tables found in the database."
        # Format the list of tables
        table_list = "\n".join([f"- {table[0]}" for table in tables])
        return f"Tables in the database:\n{table_list}"
    except Exception as e:
        return f"Error listing tables: {str(e)}"
    finally:
        conn.close()


@mcp.tool()
def get_database_schema() -> str:
    """Retrieves the CREATE TABLE statements for all tables in the database."""
    logger.info("Retrieving database schema")
    conn = sqlite3.connect("./database.db")
    try:
        cursor = conn.cursor()
        # Query sqlite_master for table creation SQL
        cursor.execute("SELECT sql FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%';")
        schema_rows = cursor.fetchall()
        # Format the schema string
        schema_str = "\n\n".join([row[0] for row in schema_rows if row[0]])
        if not schema_str:
            return "No tables found in the database."
        return f"Database Schema:\n```sql\n{schema_str}\n```"
    except Exception as e:
        return f"Error retrieving schema: {str(e)}"
    finally:
        conn.close()


@mcp.prompt()
def example_prompt(code: str) -> str:
    return f"Please review this code:\n\n{code}"


if __name__ == "__main__":
    print("Starting server...")
    # Initialize and run the server
    mcp.run(transport="stdio")