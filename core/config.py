"""
Configuration module for the MCP Server/Client application.

This module provides centralized configuration management for the application.
"""
import os
from typing import Dict, Any, Optional
import json
import logging
from dotenv import load_dotenv

# Set up logging
logger = logging.getLogger(__name__)

class Config:
    """
    Singleton configuration manager.
    
    This class provides centralized configuration management for the application,
    loading settings from environment variables and configuration files.
    """
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(Config, cls).__new__(cls)
            cls._instance._load_config()
            logger.info("Created new Config instance")
        return cls._instance
    
    def _load_config(self):
        """Load configuration from environment variables and config file."""
        # Load environment variables
        load_dotenv()
        logger.info("Loaded environment variables from .env file")
        
        # Default configuration
        self.config = {
            "ollama": {
                "model": os.getenv("OLLAMA_MODEL_NAME", "llama3.2:1b"),
                "api_url": os.getenv("OLLAMA_API_URL", "http://localhost:11434"),
            },
            "database": {
                "path": os.getenv("DATABASE_PATH", "./database.db"),
            },
            "server": {
                "name": os.getenv("SERVER_NAME", "MCP Demo"),
                "agents": os.getenv("ENABLED_AGENTS", "SQLAgent,TimeAgent").split(","),
            },
            "web": {
                "port": int(os.getenv("WEB_PORT", "7860")),
                "share": os.getenv("SHARE_APP", "false").lower() == "true",
            }
        }
        
        # Load from config file if it exists
        config_file = os.getenv("CONFIG_FILE", "config.json")
        if os.path.exists(config_file):
            try:
                with open(config_file, 'r') as f:
                    file_config = json.load(f)
                    # Update config with file values
                    self._update_dict(self.config, file_config)
                logger.info(f"Loaded configuration from {config_file}")
            except Exception as e:
                logger.error(f"Error loading config file: {e}")
    
    def _update_dict(self, target: Dict, source: Dict) -> None:
        """
        Recursively update a dictionary.
        
        Args:
            target: The target dictionary to update
            source: The source dictionary with new values
        """
        for key, value in source.items():
            if key in target and isinstance(target[key], dict) and isinstance(value, dict):
                self._update_dict(target[key], value)
            else:
                target[key] = value
    
    def get(self, key: str, default: Any = None) -> Any:
        """
        Get a configuration value by key.
        
        Args:
            key: The configuration key (dot-separated for nested values)
            default: The default value to return if the key is not found
            
        Returns:
            The configuration value or the default if not found
        """
        keys = key.split('.')
        value = self.config
        for k in keys:
            if isinstance(value, dict) and k in value:
                value = value[k]
            else:
                logger.warning(f"Configuration key not found: {key}, using default: {default}")
                return default
        logger.debug(f"Retrieved configuration value for {key}: {value}")
        return value
