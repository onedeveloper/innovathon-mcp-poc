import os
import time
import sqlite3
from typing import List, Dict, Any # Removed unused imports

import gradio as gr
import ollama # Added ollama
from dotenv import load_dotenv
from rich.console import Console
from rich.markdown import Markdown

# Load environment variables
load_dotenv()

# Create a console for rich text formatting (kept for potential future use)
console = Console()

# Helper function to get schema
def get_db_schema(db_path="database.db"):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
    tables = cursor.fetchall()
    schema_str = "Database Schema:\n"
    for table_name in tables:
        table_name = table_name[0]
        schema_str += f"\nTable: {table_name}\nColumns:\n"
        cursor.execute(f"PRAGMA table_info({table_name});")
        columns = cursor.fetchall()
        for col in columns:
            # cid, name, type, notnull, dflt_value, pk
            schema_str += f"- {col[1]} ({col[2]}){' PRIMARY KEY' if col[5] else ''}{' NOT NULL' if col[3] else ''}\n"
    conn.close()
    return schema_str

# Helper function to format results
def format_results_as_markdown(cursor, rows):
    if not cursor.description: # Handle cases like INSERT/UPDATE/DELETE
        return ""
    headers = [description[0] for description in cursor.description]
    markdown_table = "| " + " | ".join(headers) + " |\n"
    markdown_table += "| " + " | ".join(["---"] * len(headers)) + " |\n"
    for row in rows:
        markdown_table += "| " + " | ".join(map(str, row)) + " |\n"
    return markdown_table

# Global chat processor instance
chat_processor = None

# Check if database exists, if not create a sample one
def initialize_database():
    if not os.path.exists("database.db"):
        conn = sqlite3.connect("database.db")
        cursor = conn.cursor()
        
        # Create sample tables
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY,
            name TEXT NOT NULL,
            email TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        ''')
        
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS products (
            id INTEGER PRIMARY KEY,
            name TEXT NOT NULL,
            price REAL NOT NULL,
            stock INTEGER DEFAULT 0
        )
        ''')
        
        # Insert sample data
        cursor.executemany('''
        INSERT INTO users (name, email) VALUES (?, ?)
        ''', [
            ('John Doe', 'john@example.com'),
            ('Jane Smith', 'jane@example.com'),
            ('Bob Johnson', 'bob@example.com'),
        ])
        
        cursor.executemany('''
        INSERT INTO products (name, price, stock) VALUES (?, ?, ?)
        ''', [
            ('Laptop', 999.99, 10),
            ('Smartphone', 699.99, 20),
            ('Headphones', 149.99, 30),
            ('Monitor', 299.99, 15),
        ])
        
        conn.commit()
        conn.close()
        print("Created sample database with users and products tables")

class ChatProcessor:
    def __init__(self):
        self.messages: list[Dict[str, str]] = [] # Simple list of dicts for history
        self.db_schema = get_db_schema()
        self.system_prompt: str = f"""You are an expert SQLite assistant.
Your task is to translate the user's natural language query into a valid SQLite query based on the provided database schema.
{self.db_schema}
Instructions:
1. Analyze the user's request and the database schema.
2. Generate *only* the SQLite query that fulfills the user's request.
3. Do not add any explanations, comments, or introductory text before or after the SQL query.
4. Ensure the generated query is valid SQLite syntax.
5. If the user asks for information not derivable from the schema (e.g., "What's the weather?"), respond with "I can only answer questions about the database."
6. If the user's request is ambiguous or unclear, ask for clarification by responding with "Could you please clarify your request?".
7. Output *only* the raw SQL query or one of the specific error messages mentioned above."""
        # No backend server start needed

    def _process_query(self, query: str) -> str:
        """Process a query using Ollama, execute SQL, return the response message"""
        # Add user query to history
        self.messages.append({"role": "user", "content": query})

        # Prepare messages for Ollama (include system prompt and history)
        ollama_messages = [
            {"role": "system", "content": self.system_prompt},
            *self.messages # Send the whole history
        ]

        try:
            # Call Ollama
            response = ollama.chat(
                model='gemma3:27b', # Make sure this model is pulled in Ollama
                messages=ollama_messages
            )
            generated_sql = response['message']['content'].strip()

            # Check for refusal messages from the prompt instructions
            if generated_sql == "I can only answer questions about the database." or \
               generated_sql == "Could you please clarify your request?":
                 self.messages.append({"role": "assistant", "content": generated_sql})
                 return generated_sql

            # Assume the response is SQL, try executing it
            conn = sqlite3.connect("database.db")
            cursor = conn.cursor()
            try:
                start_time = time.time()
                cursor.execute(generated_sql)
                execution_time = time.time() - start_time

                # Check if it was a SELECT query or a modification query
                if generated_sql.strip().upper().startswith("SELECT"):
                    rows = cursor.fetchall()
                    if rows:
                        # Format results
                        result_str = format_results_as_markdown(cursor, rows)
                        result_str += f"\n\n_(Query executed in {execution_time:.2f} seconds)_"
                    else:
                        result_str = f"Query executed successfully, but returned no results.\n\n_(Query executed in {execution_time:.2f} seconds)_"
                else:
                    conn.commit() # Commit changes for INSERT, UPDATE, DELETE
                    result_str = f"Query executed successfully. {cursor.rowcount} row(s) affected.\n\n_(Query executed in {execution_time:.2f} seconds)_"

                self.messages.append({"role": "assistant", "content": result_str}) # Add successful result to history
                return result_str

            except sqlite3.Error as e:
                conn.rollback() # Rollback on error
                error_message = f"SQLite Error: `{e}`\n\nAttempted Query:\n```sql\n{generated_sql}\n```"
                self.messages.append({"role": "assistant", "content": error_message}) # Add error to history
                return error_message
            finally:
                conn.close()

        except Exception as e:
            # Catch errors from Ollama call or other issues
            error_message = f"An unexpected error occurred: {e}"
            self.messages.append({"role": "assistant", "content": error_message})
            return error_message

def submit_query(query: str, chat_history: list) -> tuple[list, list]:
    """Submit a query to the chat processor and update the chat history"""
    global chat_processor # Access the global instance
    if not query.strip():
        return chat_history, chat_history

    # Add user message to history immediately for UI update
    chat_history.append((query, None))

    # Process the query directly using the global instance
    response_text = chat_processor._process_query(query) # This updates internal history

    # Update the Gradio chat history with the response
    chat_history[-1] = (query, response_text)

    return chat_history, chat_history

def main():
    # Initialize the database with sample data if needed
    initialize_database()
    
    # Initialize the global chat processor instance
    global chat_processor
    chat_processor = ChatProcessor()
    
    # Create the Gradio interface
    with gr.Blocks(title="AI SQL Assistant", theme=gr.themes.Soft(), css="footer {visibility: hidden}") as demo:
        gr.Markdown("# AI SQL Assistant")
        gr.Markdown("""This application allows you to interact with a SQLite database using natural language. 
        Ask questions about the data or request SQL operations, and the AI will generate and execute the appropriate SQL queries.
        
        **Sample tables in the database:**
        - `users` (id, name, email, created_at)
        - `products` (id, name, price, stock)
        """)
        
        chatbot = gr.Chatbot(
            label="Chat", 
            height=500,
            bubble_full_width=False,
            show_copy_button=True
        )
        
        with gr.Row():
            msg = gr.Textbox(
                label="Ask a question or request a SQL operation",
                placeholder="For example: 'Show me all users' or 'How many products do we have in stock?'",
                scale=9
            )
            submit = gr.Button("Submit", scale=1)
        
        with gr.Accordion("Example Queries", open=False):
            example_queries = [
                "List all tables in the database",
                "Show me all users",
                "Count how many products cost more than $300",
                "What's the total value of all products in stock?",
                "Insert a new product called 'Tablet' with price $499.99 and stock 5",
                "Update the price of Laptop to $1099.99"
            ]
            gr.Examples(
                examples=example_queries,
                inputs=msg
            )
        
        # Set up event handlers
        submit.click(submit_query, [msg, chatbot], [chatbot, chatbot]).then(
            lambda: "", None, [msg]  # Clear the input box after submission
        )
        msg.submit(submit_query, [msg, chatbot], [chatbot, chatbot]).then(
            lambda: "", None, [msg]  # Clear the input box after submission
        )
        
    # Launch the interface
    demo.launch(share=False, server_port=7860)

if __name__ == "__main__":
    main()
