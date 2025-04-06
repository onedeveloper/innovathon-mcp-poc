"""
Enhanced registry for agent plugins.

This module extends the AgentRegistry to support plugin discovery
and dependency management.
"""
from typing import Dict, List, Tuple, Optional, Any
import logging
import importlib
import os
import inspect
from .registry import AgentRegistry
from .agent_plugin import AgentPlugin

# Set up logging
logger = logging.getLogger(__name__)

class PluginRegistry(AgentRegistry):
    """
    Enhanced registry for agent plugins.
    
    This class extends the AgentRegistry to support plugin discovery
    and dependency management.
    """
    
    def __init__(self):
        """Initialize the plugin registry."""
        super().__init__()
        self.plugin_modules = {}
    
    def discover_plugins(self, plugin_dir: str = "./agents") -> List[str]:
        """
        Discover available plugins in the specified directory.
        
        Args:
            plugin_dir: The directory to search for plugins
            
        Returns:
            A list of discovered plugin module paths
        """
        discovered_plugins = []
        
        try:
            # Ensure the plugin directory exists
            if not os.path.isdir(plugin_dir):
                logger.warning(f"Plugin directory {plugin_dir} does not exist")
                return discovered_plugins
            
            # Get all subdirectories in the plugin directory
            for item in os.listdir(plugin_dir):
                item_path = os.path.join(plugin_dir, item)
                
                # Skip non-directories and special directories
                if not os.path.isdir(item_path) or item.startswith('__'):
                    continue
                
                # Check if the directory contains a plugin.py file
                plugin_file = os.path.join(item_path, "plugin.py")
                if os.path.isfile(plugin_file):
                    # Convert directory path to module path
                    module_path = f"agents.{item}.plugin"
                    discovered_plugins.append(module_path)
                    logger.info(f"Discovered plugin module: {module_path}")
            
            return discovered_plugins
            
        except Exception as e:
            logger.error(f"Error discovering plugins: {e}")
            return discovered_plugins
    
    def load_plugin(self, plugin_module_path: str) -> Optional[AgentPlugin]:
        """
        Load a plugin from the specified module path.
        
        Args:
            plugin_module_path: The module path of the plugin to load
            
        Returns:
            The loaded plugin instance or None if loading failed
        """
        try:
            # Import the plugin module
            logger.info(f"Loading plugin module: {plugin_module_path}")
            module = importlib.import_module(plugin_module_path)
            
            # Find the AgentPlugin subclass in the module
            for name, obj in inspect.getmembers(module):
                if (inspect.isclass(obj) and 
                    issubclass(obj, AgentPlugin) and 
                    obj != AgentPlugin):
                    
                    # Create an instance of the plugin
                    plugin = obj()
                    logger.info(f"Loaded plugin: {plugin.name} (version {plugin.version})")
                    
                    # Store the module path for future reference
                    self.plugin_modules[plugin.name] = plugin_module_path
                    
                    return plugin
            
            logger.warning(f"No AgentPlugin subclass found in module: {plugin_module_path}")
            return None
            
        except Exception as e:
            logger.error(f"Error loading plugin {plugin_module_path}: {e}")
            return None
    
    def register_plugin(self, plugin: AgentPlugin) -> bool:
        """
        Register a plugin with the registry.
        
        Args:
            plugin: The plugin instance to register
            
        Returns:
            True if registration was successful, False otherwise
        """
        try:
            # Validate the plugin
            if not plugin.validate():
                logger.error(f"Plugin validation failed: {plugin.name}")
                return False
            
            # Register the plugin as an agent
            self.register_agent(plugin.name, plugin)
            logger.info(f"Registered plugin: {plugin.name}")
            
            return True
            
        except Exception as e:
            logger.error(f"Error registering plugin {plugin.name}: {e}")
            return False
    
    def resolve_dependencies(self, plugins: List[AgentPlugin]) -> List[AgentPlugin]:
        """
        Resolve dependencies between plugins and order them for initialization.
        
        Args:
            plugins: The list of plugins to resolve dependencies for
            
        Returns:
            An ordered list of plugins with dependencies resolved
        """
        # Create a dependency graph
        graph = {}
        for plugin in plugins:
            graph[plugin.name] = plugin.dependencies
        
        # Perform topological sort
        ordered_names = self._topological_sort(graph)
        
        # Map back to plugin instances
        plugin_map = {plugin.name: plugin for plugin in plugins}
        ordered_plugins = [plugin_map[name] for name in ordered_names if name in plugin_map]
        
        return ordered_plugins
    
    def _topological_sort(self, graph: Dict[str, List[str]]) -> List[str]:
        """
        Perform a topological sort on the dependency graph.
        
        Args:
            graph: The dependency graph
            
        Returns:
            A topologically sorted list of plugin names
        """
        # Initialize variables
        visited = set()
        temp_visited = set()
        result = []
        
        def visit(node):
            if node in temp_visited:
                # Circular dependency detected
                logger.warning(f"Circular dependency detected involving {node}")
                return
            
            if node not in visited:
                temp_visited.add(node)
                
                # Visit dependencies
                for dependency in graph.get(node, []):
                    visit(dependency)
                
                temp_visited.remove(node)
                visited.add(node)
                result.append(node)
        
        # Visit all nodes
        for node in graph:
            if node not in visited:
                visit(node)
        
        # Reverse the result to get the correct order
        return result[::-1]
