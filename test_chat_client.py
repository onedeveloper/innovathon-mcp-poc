"""
Test script for the CLI chat client with the MCP server.

This script demonstrates how to run and test the CLI chat client with the MCP server.
"""
import subprocess
import time
import os
import sys
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s | %(levelname)-8s | %(name)s:%(funcName)s:%(lineno)d - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)

def check_dependencies():
    """Check if all required dependencies are installed."""
    try:
        import rich
        import mcp
        import jsonschema
        logger.info("Core dependencies are installed")
        
        try:
            import ollama
            logger.info("Ollama is installed - LLM mode will be available")
        except ImportError:
            logger.warning("Ollama is not installed - only direct tool calls will be available")
            logger.warning("To install Ollama: uv add ollama")
        
        try:
            import pytz
            logger.info("pytz is installed - timezone functionality will be available")
        except ImportError:
            logger.warning("pytz is not installed - timezone functionality may be limited")
            logger.warning("To install pytz: uv add pytz")
        
        return True
    except ImportError as e:
        logger.error(f"Missing dependency: {e}")
        logger.error("Please install all required dependencies: uv add -r requirements.txt")
        return False

def check_ollama_server():
    """Check if Ollama server is running."""
    try:
        import ollama
        client = ollama.Client()
        models = client.list()
        logger.info(f"Ollama server is running with {len(models.get('models', []))} models available")
        return True
    except Exception as e:
        logger.warning(f"Ollama server check failed: {e}")
        logger.warning("If you want to use LLM mode, please start the Ollama server")
        logger.warning("For direct tool calls only, you can ignore this warning")
        return False

def main():
    """Main entry point for the test script."""
    logger.info("Starting CLI chat client test")
    
    # Check dependencies
    if not check_dependencies():
        return
    
    # Check Ollama server (optional)
    check_ollama_server()
    
    # Print instructions
    print("\n" + "="*80)
    print("CLI CHAT CLIENT TEST INSTRUCTIONS")
    print("="*80)
    print("\nThis script will help you test the CLI chat client with the MCP server.")
    print("\nThere are two ways to run the chat client:")
    
    print("\n1. Using Ollama (LLM mode):")
    print("   - Requires Ollama to be installed and running")
    print("   - Provides natural language interaction with the MCP server")
    print("   - Command: python mcp_chat_client.py --model llama3.2:1b")
    print("   - You can replace llama3.2:1b with any model available in your Ollama installation")
    
    print("\n2. Using direct tool calls (no LLM):")
    print("   - Does not require Ollama")
    print("   - Requires manual tool call syntax")
    print("   - Command: python mcp_chat_client.py")
    print("   - Tool call format: tool:tool_name{arg1:value1,arg2:value2}")
    print("   - Example: tool:get_current_time{format:human}")
    print("   - Example: tool:query_data{sql:SELECT sqlite_version();}")
    
    print("\nThe chat client will display available tools when it starts.")
    print("To exit the chat client, type 'exit', 'quit', or 'bye'.")
    
    print("\n" + "="*80)
    print("RUNNING THE CHAT CLIENT")
    print("="*80)
    
    # Ask user which mode to run
    while True:
        mode = input("\nWhich mode would you like to test? (1 for LLM mode, 2 for direct tool calls, q to quit): ")
        
        if mode.lower() in ['q', 'quit', 'exit']:
            print("Exiting test script...")
            return
        
        if mode == '1':
            # Check if Ollama is available
            try:
                import ollama
                # Ask for model name
                model = input("Enter Ollama model name (default: llama3.2:1b): ") or "llama3.2:1b"
                print(f"\nStarting chat client in LLM mode with model {model}...")
                print("Press Ctrl+C to stop the client\n")
                
                # Run the chat client
                subprocess.run([sys.executable, "mcp_chat_client.py", "--model", model])
                break
            except ImportError:
                print("Ollama is not installed. Please install it with: uv add ollama")
                continue
        
        elif mode == '2':
            print("\nStarting chat client in direct tool calls mode...")
            print("Press Ctrl+C to stop the client\n")
            
            # Run the chat client
            subprocess.run([sys.executable, "mcp_chat_client.py"])
            break
        
        else:
            print("Invalid choice. Please enter 1, 2, or q.")

if __name__ == "__main__":
    main()

