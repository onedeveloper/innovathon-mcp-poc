from mcp.server.fastmcp import FastMCP
from pydantic import BaseModel
from typing import List, Dict, Any, Optional
import sqlite3
import os
from db_utils import get_db_connection, is_safe_query

# Initialize MCP server
mcp = FastMCP("SQLiteAgent")

# Get database path from environment variable
DB_PATH = os.getenv("SQLITE_DB_PATH", "database.db")

class TableSchema(BaseModel):
    column_name: str
    data_type: str
    is_nullable: bool
    is_primary_key: bool

class QueryResult(BaseModel):
    rows: List[Dict[str, Any]]
    row_count: int

@mcp.tool(description="List all tables in the connected SQLite database")
def list_tables() -> List[str]:
    """Returns a list of all table names in the database."""
    conn = get_db_connection(DB_PATH)
    cursor = conn.cursor()
    
    # Query for all table names
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
    tables = [row[0] for row in cursor.fetchall()]
    
    conn.close()
    return tables

@mcp.tool(description="Get schema information for a specific table")
def describe_table(table_name: str) -> List[TableSchema]:
    """Returns schema information for the specified table."""
    conn = get_db_connection(DB_PATH)
    cursor = conn.cursor()
    
    # Get table info
    cursor.execute(f"PRAGMA table_info({table_name});")
    columns = cursor.fetchall()
    
    result = []
    for col in columns:
        result.append(TableSchema(
            column_name=col[1],
            data_type=col[2],
            is_nullable=not col[3],
            is_primary_key=bool(col[5])
        ))
    
    conn.close()
    return result

@mcp.tool(description="Execute a read-only SQL query and return results")
def query_db(query: str) -> QueryResult:
    """Executes a read-only SQL query and returns the results."""
    # Validate query is safe (SELECT only)
    if not is_safe_query(query):
        raise ValueError("Only SELECT queries are allowed for security reasons")
    
    conn = get_db_connection(DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute(query)
    columns = [desc[0] for desc in cursor.description]
    rows = cursor.fetchall()
    
    # Convert to list of dictionaries
    result_rows = []
    for row in rows:
        result_rows.append({columns[i]: row[i] for i in range(len(columns))})
    
    conn.close()
    return QueryResult(rows=result_rows, row_count=len(result_rows))

# Run with: uvicorn server:mcp.app --port 8001
