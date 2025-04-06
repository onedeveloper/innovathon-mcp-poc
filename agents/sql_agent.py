"""
SQL Agent implementation for the MCP Server/Client application.

This module provides an agent that handles SQL operations on a SQLite database.
"""
import sqlite3
from typing import Dict, Any, Optional
import logging
from ..core.agent_interface import Agent
from ..core.registry import AgentRegistry

# Set up logging
logger = logging.getLogger(__name__)

class SQLAgent(Agent):
    """
    Agent for handling SQL operations on a SQLite database.
    
    This agent provides tools for querying, listing tables, and retrieving
    schema information from a SQLite database.
    """
    
    def __init__(self, db_path: str = "./database.db"):
        """
        Initialize the SQL agent.
        
        Args:
            db_path: Path to the SQLite database file
        """
        self.registry = AgentRegistry()
        self.db_path = db_path
        logger.info(f"Initialized SQLAgent with database: {db_path}")
        
    def register_tools(self) -> None:
        """Register SQL-related tools with the registry."""
        logger.info("Registering SQL tools with registry")
        
        # Register query_data tool
        self.registry.register_tool(
            name="query_data",
            tool_function=self.query_data,
            description="Execute SQL queries safely",
            schema={
                "type": "object",
                "required": ["sql"],
                "properties": {
                    "sql": {
                        "type": "string",
                        "description": "SQL query to execute"
                    }
                }
            }
        )
        
        # Register list_tables tool
        self.registry.register_tool(
            name="list_tables",
            tool_function=self.list_tables,
            description="Lists all non-system tables in the database.",
            schema={
                "type": "object",
                "properties": {}
            }
        )
        
        # Register get_database_schema tool
        self.registry.register_tool(
            name="get_database_schema",
            tool_function=self.get_database_schema,
            description="Retrieves the CREATE TABLE statements for all tables in the database.",
            schema={
                "type": "object",
                "properties": {}
            }
        )
    
    def initialize(self) -> None:
        """Initialize the SQL agent by checking if the database exists."""
        logger.info("Initializing SQLAgent")
        # Check if database exists
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%';")
            tables = cursor.fetchall()
            conn.close()
            
            if tables:
                logger.info(f"Database initialized with {len(tables)} tables")
            else:
                logger.warning("Database exists but contains no tables")
        except sqlite3.Error as e:
            logger.error(f"Error initializing database: {e}")
    
    def process_request(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process a SQL-related request.
        
        Args:
            request: The request to process
            
        Returns:
            The response to the request
        """
        # This is a placeholder for future direct agent-to-agent communication
        # Currently not used as tools are called directly
        return {"status": "error", "message": "Direct request processing not implemented"}
    
    def query_data(self, sql: str) -> str:
        """
        Execute SQL queries safely.
        
        Args:
            sql: The SQL query to execute
            
        Returns:
            The query results as a string
        """
        logger.info(f"Executing SQL query: {sql}")
        conn = sqlite3.connect(self.db_path)
        try:
            result = conn.execute(sql).fetchall()
            conn.commit()
            logger.info(f"Query executed successfully, returned {len(result)} rows")
            return "\n".join(str(row) for row in result)
        except Exception as e:
            logger.error(f"Error executing SQL query: {e}")
            return f"Error: {str(e)}"
        finally:
            conn.close()
    
    def list_tables(self) -> str:
        """
        List all non-system tables in the database.
        
        Returns:
            A formatted string listing all tables
        """
        logger.info("Listing database tables")
        conn = sqlite3.connect(self.db_path)
        try:
            cursor = conn.cursor()
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%';")
            tables = cursor.fetchall()
            if not tables:
                logger.info("No tables found in database")
                return "No tables found in the database."
            
            # Format the list of tables
            table_list = "\n".join([f"- {table[0]}" for table in tables])
            logger.info(f"Found {len(tables)} tables in database")
            return f"Tables in the database:\n{table_list}"
        except Exception as e:
            logger.error(f"Error listing tables: {e}")
            return f"Error listing tables: {str(e)}"
        finally:
            conn.close()
    
    def get_database_schema(self) -> str:
        """
        Retrieve the CREATE TABLE statements for all tables in the database.
        
        Returns:
            A formatted string containing the schema
        """
        logger.info("Retrieving database schema")
        conn = sqlite3.connect(self.db_path)
        try:
            cursor = conn.cursor()
            # Query sqlite_master for table creation SQL
            cursor.execute("SELECT sql FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%';")
            schema_rows = cursor.fetchall()
            # Format the schema string
            schema_str = "\n\n".join([row[0] for row in schema_rows if row[0]])
            if not schema_str:
                logger.info("No tables found in database")
                return "No tables found in the database."
            
            logger.info(f"Retrieved schema for {len(schema_rows)} tables")
            return f"Database Schema:\n```sql\n{schema_str}\n```"
        except Exception as e:
            logger.error(f"Error retrieving schema: {e}")
            return f"Error retrieving schema: {str(e)}"
        finally:
            conn.close()
