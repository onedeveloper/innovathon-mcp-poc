"""
Plugin manager for the MCP Server/Client application.

This module provides a manager for agent plugins, including
discovery, loading, initialization, and registration.
"""
from typing import Dict, List, Tuple, Optional, Any
import logging
import os
from .plugin_registry import PluginRegistry
from .agent_plugin import AgentPlugin

# Set up logging
logger = logging.getLogger(__name__)

class PluginManager:
    """
    Manager for agent plugins.
    
    This class manages the lifecycle of agent plugins, including
    discovery, loading, initialization, and registration.
    """
    
    def __init__(self, registry: PluginRegistry):
        """
        Initialize the plugin manager.
        
        Args:
            registry: The plugin registry to use
        """
        self.registry = registry
        self.plugins = {}
    
    def discover_and_load_plugins(self, plugin_dir: str = "./agents") -> List[AgentPlugin]:
        """
        Discover and load available plugins.
        
        Args:
            plugin_dir: The directory to search for plugins
            
        Returns:
            A list of loaded plugin instances
        """
        loaded_plugins = []
        
        try:
            # Discover available plugins
            plugin_modules = self.registry.discover_plugins(plugin_dir)
            logger.info(f"Discovered {len(plugin_modules)} plugin modules")
            
            # Load each plugin
            for module_path in plugin_modules:
                plugin = self.registry.load_plugin(module_path)
                if plugin:
                    loaded_plugins.append(plugin)
                    self.plugins[plugin.name] = plugin
            
            logger.info(f"Loaded {len(loaded_plugins)} plugins")
            return loaded_plugins
            
        except Exception as e:
            logger.error(f"Error discovering and loading plugins: {e}")
            return loaded_plugins
    
    def initialize_plugins(self, plugins: List[AgentPlugin]) -> bool:
        """
        Initialize the specified plugins.
        
        Args:
            plugins: The list of plugins to initialize
            
        Returns:
            True if all plugins were initialized successfully, False otherwise
        """
        success = True
        
        try:
            # Resolve dependencies
            ordered_plugins = self.registry.resolve_dependencies(plugins)
            logger.info(f"Initializing {len(ordered_plugins)} plugins in dependency order")
            
            # Initialize each plugin in order
            for plugin in ordered_plugins:
                try:
                    logger.info(f"Initializing plugin: {plugin.name}")
                    plugin.initialize()
                    logger.info(f"Successfully initialized plugin: {plugin.name}")
                except Exception as e:
                    logger.error(f"Error initializing plugin {plugin.name}: {e}")
                    success = False
            
            return success
            
        except Exception as e:
            logger.error(f"Error initializing plugins: {e}")
            return False
    
    def register_plugin_tools(self, plugins: List[AgentPlugin]) -> bool:
        """
        Register tools for the specified plugins.
        
        Args:
            plugins: The list of plugins to register tools for
            
        Returns:
            True if all tools were registered successfully, False otherwise
        """
        success = True
        
        try:
            # Register tools for each plugin
            for plugin in plugins:
                try:
                    logger.info(f"Registering tools for plugin: {plugin.name}")
                    plugin.register_tools()
                    logger.info(f"Successfully registered tools for plugin: {plugin.name}")
                except Exception as e:
                    logger.error(f"Error registering tools for plugin {plugin.name}: {e}")
                    success = False
            
            return success
            
        except Exception as e:
            logger.error(f"Error registering plugin tools: {e}")
            return False
    
    def load_and_initialize_all(self, plugin_dir: str = "./agents") -> bool:
        """
        Discover, load, initialize, and register all available plugins.
        
        Args:
            plugin_dir: The directory to search for plugins
            
        Returns:
            True if all operations were successful, False otherwise
        """
        try:
            # Discover and load plugins
            plugins = self.discover_and_load_plugins(plugin_dir)
            if not plugins:
                logger.warning("No plugins were loaded")
                return False
            
            # Initialize plugins
            if not self.initialize_plugins(plugins):
                logger.warning("Some plugins failed to initialize")
                return False
            
            # Register plugin tools
            if not self.register_plugin_tools(plugins):
                logger.warning("Some plugin tools failed to register")
                return False
            
            # Register plugins with the registry
            for plugin in plugins:
                self.registry.register_plugin(plugin)
            
            logger.info(f"Successfully loaded and initialized {len(plugins)} plugins")
            return True
            
        except Exception as e:
            logger.error(f"Error loading and initializing plugins: {e}")
            return False
    
    def get_plugin(self, name: str) -> Optional[AgentPlugin]:
        """
        Get a plugin by name.
        
        Args:
            name: The name of the plugin to get
            
        Returns:
            The plugin instance or None if not found
        """
        return self.plugins.get(name)
    
    def get_all_plugins(self) -> Dict[str, AgentPlugin]:
        """
        Get all loaded plugins.
        
        Returns:
            A dictionary of plugin name to plugin instance
        """
        return self.plugins
