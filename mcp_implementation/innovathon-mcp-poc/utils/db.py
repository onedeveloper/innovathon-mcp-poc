"""
Database utilities for the MCP Server/Client application.

This module provides a secure database connection pool and utilities
for safely executing database operations.
"""
import sqlite3
import threading
import logging
from contextlib import contextmanager
from typing import List, Dict, Any, Tuple, Optional
from ..utils.security import SQLSecurity
from ..utils.retry import retry
from ..utils.exceptions import DatabaseError

# Set up logging
logger = logging.getLogger(__name__)

class DatabasePool:
    """
    Thread-safe connection pool for SQLite database.
    
    This class provides a pool of database connections that can be
    reused across multiple requests, improving performance.
    """
    _instance = None
    _lock = threading.Lock()
    
    def __new__(cls, db_path: str = "./database.db", pool_size: int = 5):
        with cls._lock:
            if cls._instance is None:
                cls._instance = super(DatabasePool, cls).__new__(cls)
                cls._instance.db_path = db_path
                cls._instance.pool_size = pool_size
                cls._instance._connections = []
                cls._instance._in_use = set()
                logger.info(f"Created new DatabasePool instance for {db_path}")
        return cls._instance
    
    @contextmanager
    def get_connection(self):
        """
        Get a connection from the pool.
        
        Returns:
            A database connection that will be returned to the pool when done
        """
        conn = self._get_connection()
        try:
            yield conn
        finally:
            self._release_connection(conn)
    
    def _get_connection(self) -> sqlite3.Connection:
        """
        Get a connection from the pool or create a new one.
        
        Returns:
            A database connection
        """
        with self._lock:
            # Check for available connections
            for conn in self._connections:
                if conn not in self._in_use:
                    self._in_use.add(conn)
                    return conn
            
            # Create a new connection if pool is not full
            if len(self._connections) < self.pool_size:
                try:
                    conn = sqlite3.connect(self.db_path)
                    # Enable foreign keys
                    conn.execute("PRAGMA foreign_keys = ON")
                    self._connections.append(conn)
                    self._in_use.add(conn)
                    logger.debug(f"Created new database connection, pool size: {len(self._connections)}")
                    return conn
                except sqlite3.Error as e:
                    logger.error(f"Error creating database connection: {e}")
                    raise DatabaseError(f"Failed to connect to database: {e}")
            
            # Wait for a connection to become available
            # In a real implementation, we would use a condition variable
            # For simplicity, we'll just create a new connection
            try:
                conn = sqlite3.connect(self.db_path)
                # Enable foreign keys
                conn.execute("PRAGMA foreign_keys = ON")
                logger.warning("Connection pool full, creating temporary connection")
                return conn
            except sqlite3.Error as e:
                logger.error(f"Error creating temporary database connection: {e}")
                raise DatabaseError(f"Failed to connect to database: {e}")
    
    def _release_connection(self, conn: sqlite3.Connection) -> None:
        """
        Release a connection back to the pool.
        
        Args:
            conn: The connection to release
        """
        with self._lock:
            if conn in self._in_use:
                self._in_use.remove(conn)
                logger.debug(f"Released connection back to pool, available: {len(self._connections) - len(self._in_use)}")

class Database:
    """
    Secure database access layer.
    
    This class provides methods for safely executing database operations
    with proper error handling and security measures.
    """
    
    def __init__(self, db_path: str = "./database.db"):
        """
        Initialize the database access layer.
        
        Args:
            db_path: Path to the SQLite database file
        """
        self.pool = DatabasePool(db_path)
        logger.info(f"Initialized Database with path: {db_path}")
    
    @retry(exceptions=[sqlite3.Error, DatabaseError], max_tries=3, delay=0.5)
    def execute_query(self, query: str, params: Dict[str, Any] = None) -> List[Tuple]:
        """
        Execute a query with parameters and return the results.
        
        Args:
            query: The SQL query with named parameters
            params: Dictionary of parameter names to values
            
        Returns:
            Query results as a list of tuples
            
        Raises:
            DatabaseError: If the query execution fails
        """
        if params is None:
            params = {}
        
        logger.debug(f"Executing query: {query} with params: {params}")
        
        with self.pool.get_connection() as conn:
            try:
                # Use SQLSecurity to safely execute the query
                result = SQLSecurity.safe_execute(conn, query, params)
                conn.commit()
                logger.debug(f"Query executed successfully, returned {len(result)} rows")
                return result
            except (sqlite3.Error, ValueError) as e:
                conn.rollback()
                logger.error(f"Error executing query: {e}")
                raise DatabaseError(f"Query execution failed: {e}")
    
    @retry(exceptions=[sqlite3.Error, DatabaseError], max_tries=3, delay=0.5)
    def execute_update(self, query: str, params: Dict[str, Any] = None) -> int:
        """
        Execute an update query and return the number of affected rows.
        
        Args:
            query: The SQL query with named parameters
            params: Dictionary of parameter names to values
            
        Returns:
            Number of affected rows
            
        Raises:
            DatabaseError: If the update execution fails
        """
        if params is None:
            params = {}
        
        logger.debug(f"Executing update: {query} with params: {params}")
        
        with self.pool.get_connection() as conn:
            try:
                # Use SQLSecurity to safely execute the query
                parameterized_query, param_values = SQLSecurity.parameterize_query(query, params)
                
                # Check if the query is potentially unsafe
                if not SQLSecurity.is_safe_query(query):
                    raise ValueError("Potentially unsafe SQL query rejected")
                
                cursor = conn.cursor()
                cursor.execute(parameterized_query, param_values)
                conn.commit()
                
                affected_rows = cursor.rowcount
                logger.debug(f"Update executed successfully, affected {affected_rows} rows")
                return affected_rows
            except (sqlite3.Error, ValueError) as e:
                conn.rollback()
                logger.error(f"Error executing update: {e}")
                raise DatabaseError(f"Update execution failed: {e}")
    
    def get_tables(self) -> List[str]:
        """
        Get a list of all tables in the database.
        
        Returns:
            List of table names
            
        Raises:
            DatabaseError: If the operation fails
        """
        logger.debug("Getting list of tables")
        
        with self.pool.get_connection() as conn:
            try:
                cursor = conn.cursor()
                cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%';")
                tables = [row[0] for row in cursor.fetchall()]
                logger.debug(f"Found {len(tables)} tables")
                return tables
            except sqlite3.Error as e:
                logger.error(f"Error getting tables: {e}")
                raise DatabaseError(f"Failed to get tables: {e}")
    
    def get_schema(self) -> Dict[str, str]:
        """
        Get the schema for all tables in the database.
        
        Returns:
            Dictionary mapping table names to their CREATE statements
            
        Raises:
            DatabaseError: If the operation fails
        """
        logger.debug("Getting database schema")
        
        with self.pool.get_connection() as conn:
            try:
                cursor = conn.cursor()
                cursor.execute("SELECT name, sql FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%';")
                schema = {row[0]: row[1] for row in cursor.fetchall()}
                logger.debug(f"Retrieved schema for {len(schema)} tables")
                return schema
            except sqlite3.Error as e:
                logger.error(f"Error getting schema: {e}")
                raise DatabaseError(f"Failed to get schema: {e}")
