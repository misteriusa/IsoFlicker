import os
import sys
import importlib.util
import inspect
from typing import Dict, List, Any, Callable, Optional
from abc import ABC, abstractmethod


class Plugin(ABC):
    """Base class for all plugins"""
    
    def __init__(self, name: str, version: str, description: str):
        self.name = name
        self.version = version
        self.description = description
    
    @abstractmethod
    def initialize(self, app_context: Any) -> bool:
        """Initialize the plugin with application context
        
        Args:
            app_context: Application context object
            
        Returns:
            bool: True if initialization was successful, False otherwise
        """
        pass
    
    @abstractmethod
    def cleanup(self):
        """Clean up plugin resources"""
        pass


class PluginManager:
    """Manages loading, initializing, and running plugins"""
    
    def __init__(self, plugins_directory: str = "plugins"):
        self.plugins_directory = plugins_directory
        self.plugins: Dict[str, Plugin] = {}
        self.plugin_modules: Dict[str, Any] = {}
        self.app_context: Any = None
    
    def set_app_context(self, app_context: Any):
        """Set the application context for plugins
        
        Args:
            app_context: Application context object
        """
        self.app_context = app_context
    
    def discover_plugins(self) -> List[str]:
        """Discover available plugins in the plugins directory
        
        Returns:
            List[str]: List of plugin module names
        """
        plugin_modules = []
        
        if not os.path.exists(self.plugins_directory):
            return plugin_modules
            
        # Add plugins directory to Python path
        if self.plugins_directory not in sys.path:
            sys.path.append(self.plugins_directory)
        
        # Look for Python files in the plugins directory
        for filename in os.listdir(self.plugins_directory):
            if filename.endswith(".py") and filename != "__init__.py":
                module_name = filename[:-3]  # Remove .py extension
                plugin_modules.append(module_name)
        
        return plugin_modules
    
    def load_plugin(self, module_name: str) -> Optional[Plugin]:
        """Load a plugin from a module
        
        Args:
            module_name: Name of the plugin module to load
            
        Returns:
            Plugin: Loaded plugin instance, or None if loading failed
        """
        try:
            # Construct the full path to the module
            module_path = os.path.join(self.plugins_directory, f"{module_name}.py")
            
            # Load the module
            spec = importlib.util.spec_from_file_location(module_name, module_path)
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            
            # Store the module
            self.plugin_modules[module_name] = module
            
            # Find plugin classes in the module
            plugin_classes = []
            for name, obj in inspect.getmembers(module):
                if (inspect.isclass(obj) and 
                    issubclass(obj, Plugin) and 
                    obj != Plugin):
                    plugin_classes.append(obj)
            
            if not plugin_classes:
                print(f"No Plugin subclass found in {module_name}")
                return None
            
            # Create an instance of the first plugin class found
            plugin_class = plugin_classes[0]
            try:
                plugin_instance = plugin_class()
            except Exception as e:
                print(f"Failed to instantiate plugin class {plugin_class}: {e}")
                return None
            
            # Store the plugin
            self.plugins[module_name] = plugin_instance
            
            return plugin_instance
            
        except Exception as e:
            print(f"Failed to load plugin {module_name}: {e}")
            return None
    
    def load_all_plugins(self) -> Dict[str, Plugin]:
        """Load all available plugins
        
        Returns:
            Dict[str, Plugin]: Dictionary of loaded plugins
        """
        plugin_modules = self.discover_plugins()
        loaded_plugins = {}
        
        for module_name in plugin_modules:
            plugin = self.load_plugin(module_name)
            if plugin:
                loaded_plugins[module_name] = plugin
                
        return loaded_plugins
    
    def initialize_plugin(self, plugin_name: str) -> bool:
        """Initialize a specific plugin
        
        Args:
            plugin_name: Name of the plugin to initialize
            
        Returns:
            bool: True if initialization was successful, False otherwise
        """
        if plugin_name not in self.plugins:
            print(f"Plugin {plugin_name} not found")
            return False
            
        try:
            plugin = self.plugins[plugin_name]
            return plugin.initialize(self.app_context)
        except Exception as e:
            print(f"Failed to initialize plugin {plugin_name}: {e}")
            return False
    
    def initialize_all_plugins(self) -> Dict[str, bool]:
        """Initialize all loaded plugins
        
        Returns:
            Dict[str, bool]: Dictionary mapping plugin names to initialization success
        """
        results = {}
        
        for plugin_name in self.plugins:
            results[plugin_name] = self.initialize_plugin(plugin_name)
            
        return results
    
    def cleanup_plugin(self, plugin_name: str):
        """Clean up a specific plugin
        
        Args:
            plugin_name: Name of the plugin to clean up
        """
        if plugin_name in self.plugins:
            try:
                plugin = self.plugins[plugin_name]
                plugin.cleanup()
            except Exception as e:
                print(f"Error cleaning up plugin {plugin_name}: {e}")
    
    def cleanup_all_plugins(self):
        """Clean up all plugins"""
        for plugin_name in list(self.plugins.keys()):
            self.cleanup_plugin(plugin_name)
    
    def get_plugin(self, plugin_name: str) -> Optional[Plugin]:
        """Get a specific plugin by name
        
        Args:
            plugin_name: Name of the plugin to retrieve
            
        Returns:
            Plugin: Plugin instance, or None if not found
        """
        return self.plugins.get(plugin_name)
    
    def list_plugins(self) -> List[str]:
        """List all loaded plugins
        
        Returns:
            List[str]: List of plugin names
        """
        return list(self.plugins.keys())


# Example plugin interface for extending functionality
class VideoProcessorPlugin(Plugin):
    """Base class for video processor plugins"""
    
    def __init__(self):
        super().__init__(
            "VideoProcessorPlugin",
            "1.0.0",
            "Base class for video processor plugins"
        )
    
    @abstractmethod
    def process_frame(self, frame: Any, time: float, config: Dict[str, Any]) -> Any:
        """Process a video frame
        
        Args:
            frame: Video frame to process
            time: Current time in seconds
            config: Configuration dictionary
            
        Returns:
            Processed frame
        """
        pass


class AudioProcessorPlugin(Plugin):
    """Base class for audio processor plugins"""
    
    def __init__(self):
        super().__init__(
            "AudioProcessorPlugin",
            "1.0.0",
            "Base class for audio processor plugins"
        )
    
    @abstractmethod
    def process_audio(self, audio_data: Any, config: Dict[str, Any]) -> Any:
        """Process audio data
        
        Args:
            audio_data: Audio data to process
            config: Configuration dictionary
            
        Returns:
            Processed audio data
        """
        pass


class UIExtensionPlugin(Plugin):
    """Base class for UI extension plugins"""
    
    def __init__(self):
        super().__init__(
            "UIExtensionPlugin",
            "1.0.0",
            "Base class for UI extension plugins"
        )
    
    @abstractmethod
    def extend_ui(self, main_window: Any) -> bool:
        """Extend the user interface
        
        Args:
            main_window: Main application window
            
        Returns:
            bool: True if extension was successful, False otherwise
        """
        pass


def main():
    """Example usage of the plugin manager"""
    # Create plugin manager
    plugin_manager = PluginManager("plugins")
    
    # Set application context (in a real app, this would be the main application object)
    plugin_manager.set_app_context({"app_name": "IsoFlicker Pro", "version": "2.0"})
    
    # Load all plugins
    loaded_plugins = plugin_manager.load_all_plugins()
    print(f"Loaded {len(loaded_plugins)} plugins:")
    for name in loaded_plugins:
        print(f"  - {name}")
    
    # Initialize all plugins
    init_results = plugin_manager.initialize_all_plugins()
    print("\nPlugin initialization results:")
    for name, success in init_results.items():
        status = "SUCCESS" if success else "FAILED"
        print(f"  - {name}: {status}")
    
    # List plugins
    plugin_list = plugin_manager.list_plugins()
    print(f"\nActive plugins: {plugin_list}")
    
    # Clean up
    plugin_manager.cleanup_all_plugins()


if __name__ == "__main__":
    main()