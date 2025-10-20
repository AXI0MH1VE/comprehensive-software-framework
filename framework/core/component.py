"""Component Module

Provides base component interface and lifecycle management.
"""

from abc import ABC, abstractmethod
from typing import Any, Optional
import logging


class ComponentLifecycle:
    """Component lifecycle states"""
    CREATED = "created"
    INITIALIZING = "initializing"
    INITIALIZED = "initialized"
    STARTING = "starting"
    STARTED = "started"
    STOPPING = "stopping"
    STOPPED = "stopped"
    ERROR = "error"


class ComponentError(Exception):
    """Base exception for component errors"""
    pass


class Component(ABC):
    """Base Component Interface
    
    All framework components should inherit from this base class.
    Provides standard lifecycle management and dependency injection.
    
    Example:
        class MyComponent(Component):
            def initialize(self, app):
                self.db = app.get_service('database')
                self.logger.info('Component initialized')
            
            def start(self):
                self.logger.info('Component started')
            
            def stop(self):
                self.logger.info('Component stopped')
    """
    
    def __init__(self, name: Optional[str] = None):
        """Initialize component.
        
        Args:
            name: Optional component name
        """
        self.name = name or self.__class__.__name__
        self.state = ComponentLifecycle.CREATED
        self.logger = logging.getLogger(self.name)
        self.app: Optional[Any] = None
    
    def initialize(self, app: Any) -> None:
        """Initialize component with application context.
        
        Args:
            app: Application instance
        """
        self.state = ComponentLifecycle.INITIALIZING
        self.app = app
        try:
            self._on_initialize()
            self.state = ComponentLifecycle.INITIALIZED
            self.logger.info(f"{self.name} initialized")
        except Exception as e:
            self.state = ComponentLifecycle.ERROR
            self.logger.error(f"Failed to initialize {self.name}: {e}")
            raise ComponentError(f"Initialization failed: {e}") from e
    
    def start(self) -> None:
        """Start component operation."""
        if self.state != ComponentLifecycle.INITIALIZED:
            raise ComponentError(f"Cannot start component in state: {self.state}")
        
        self.state = ComponentLifecycle.STARTING
        try:
            self._on_start()
            self.state = ComponentLifecycle.STARTED
            self.logger.info(f"{self.name} started")
        except Exception as e:
            self.state = ComponentLifecycle.ERROR
            self.logger.error(f"Failed to start {self.name}: {e}")
            raise ComponentError(f"Start failed: {e}") from e
    
    def stop(self) -> None:
        """Stop component operation."""
        if self.state not in [ComponentLifecycle.STARTED, ComponentLifecycle.ERROR]:
            return
        
        self.state = ComponentLifecycle.STOPPING
        try:
            self._on_stop()
            self.state = ComponentLifecycle.STOPPED
            self.logger.info(f"{self.name} stopped")
        except Exception as e:
            self.state = ComponentLifecycle.ERROR
            self.logger.error(f"Failed to stop {self.name}: {e}")
            raise ComponentError(f"Stop failed: {e}") from e
    
    def _on_initialize(self) -> None:
        """Hook called during initialization. Override in subclasses."""
        pass
    
    def _on_start(self) -> None:
        """Hook called during start. Override in subclasses."""
        pass
    
    def _on_stop(self) -> None:
        """Hook called during stop. Override in subclasses."""
        pass
    
    def get_service(self, name: str) -> Any:
        """Get service from application registry.
        
        Args:
            name: Service name
            
        Returns:
            Service instance
        """
        if not self.app:
            raise ComponentError("Component not initialized with application")
        return self.app.get_service(name)
    
    def __repr__(self) -> str:
        return f"<{self.__class__.__name__} name={self.name} state={self.state}>"


class StatefulComponent(Component):
    """Component with internal state management.
    
    Extends base Component with state persistence capabilities.
    """
    
    def __init__(self, name: Optional[str] = None):
        super().__init__(name)
        self._state_data: dict = {}
    
    def get_state(self, key: str, default: Any = None) -> Any:
        """Get state value.
        
        Args:
            key: State key
            default: Default value if key not found
            
        Returns:
            State value
        """
        return self._state_data.get(key, default)
    
    def set_state(self, key: str, value: Any) -> None:
        """Set state value.
        
        Args:
            key: State key
            value: State value
        """
        self._state_data[key] = value
    
    def clear_state(self) -> None:
        """Clear all state data."""
        self._state_data.clear()
    
    def _on_stop(self) -> None:
        """Clear state on stop."""
        self.clear_state()
        super()._on_stop()
