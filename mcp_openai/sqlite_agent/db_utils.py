import sqlite3
import re

def get_db_connection(db_path):
    """Create a database connection to the SQLite database."""
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    return conn

def is_safe_query(query):
    """Check if a query is safe (SELECT only)."""
    # Remove comments and normalize whitespace
    clean_query = re.sub(r'--.*$', '', query, flags=re.MULTILINE)
    clean_query = re.sub(r'/\*.*?\*/', '', clean_query, flags=re.DOTALL)
    clean_query = clean_query.strip()
    
    # Check if query starts with SELECT
    return clean_query.upper().startswith('SELECT')
