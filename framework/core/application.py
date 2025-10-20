"""Application Module

Provides the main application container and lifecycle management.
"""

import sys
import signal
import logging
from typing import Dict, List, Optional, Any, Callable
from abc import ABC, abstractmethod
from .registry import Registry


class ApplicationState:
    """Application state enum"""
    INITIALIZING = "initializing"
    RUNNING = "running"
    STOPPING = "stopping"
    STOPPED = "stopped"
    ERROR = "error"


class ApplicationError(Exception):
    """Base exception for application errors"""
    pass


class Application:
    """Main Application Container
    
    Manages application lifecycle, configuration, and component coordination.
    Provides dependency injection through the Registry.
    
    Example:
        app = Application(name="MyApp")
        app.register_service("database", DatabaseService())
        app.register_component(APIComponent())
        app.run()
    """
    
    def __init__(self, name: str, config: Optional[Dict[str, Any]] = None):
        """Initialize the application.
        
        Args:
            name: Application name
            config: Optional configuration dictionary
        """
        self.name = name
        self.config = config or {}
        self.registry = Registry()
        self.components: List[Any] = []
        self.state = ApplicationState.INITIALIZING
        self.logger = self._setup_logging()
        self._shutdown_handlers: List[Callable] = []
        self._startup_handlers: List[Callable] = []
        
    def _setup_logging(self) -> logging.Logger:
        """Configure application logging."""
        logger = logging.getLogger(self.name)
        handler = logging.StreamHandler(sys.stdout)
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        handler.setFormatter(formatter)
        logger.addHandler(handler)
        logger.setLevel(self.config.get('log_level', logging.INFO))
        return logger
    
    def register_service(self, name: str, service: Any, singleton: bool = True) -> None:
        """Register a service in the application registry.
        
        Args:
            name: Service identifier
            service: Service instance or factory
            singleton: Whether to treat as singleton
        """
        self.registry.register(name, service, singleton=singleton)
        self.logger.info(f"Registered service: {name}")
    
    def register_component(self, component: Any) -> None:
        """Register a component with the application.
        
        Args:
            component: Component instance
        """
        self.components.append(component)
        self.logger.info(f"Registered component: {component.__class__.__name__}")
    
    def get_service(self, name: str) -> Any:
        """Retrieve a registered service.
        
        Args:
            name: Service identifier
            
        Returns:
            Service instance
        """
        return self.registry.resolve(name)
    
    def on_startup(self, handler: Callable) -> None:
        """Register a startup handler.
        
        Args:
            handler: Callable to execute on startup
        """
        self._startup_handlers.append(handler)
    
    def on_shutdown(self, handler: Callable) -> None:
        """Register a shutdown handler.
        
        Args:
            handler: Callable to execute on shutdown
        """
        self._shutdown_handlers.append(handler)
    
    def initialize(self) -> None:
        """Initialize application and all components."""
        self.logger.info(f"Initializing application: {self.name}")
        
        try:
            # Execute startup handlers
            for handler in self._startup_handlers:
                handler(self)
            
            # Initialize all components
            for component in self.components:
                if hasattr(component, 'initialize'):
                    component.initialize(self)
                    self.logger.debug(f"Initialized component: {component.__class__.__name__}")
            
            self.state = ApplicationState.RUNNING
            self.logger.info("Application initialized successfully")
            
        except Exception as e:
            self.state = ApplicationState.ERROR
            self.logger.error(f"Failed to initialize application: {e}")
            raise ApplicationError(f"Initialization failed: {e}") from e
    
    def run(self) -> None:
        """Run the application."""
        self.initialize()
        
        # Setup signal handlers
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)
        
        self.logger.info(f"Application {self.name} is running")
        
        # Start all components
        for component in self.components:
            if hasattr(component, 'start'):
                component.start()
    
    def _signal_handler(self, signum, frame):
        """Handle system signals for graceful shutdown."""
        self.logger.info(f"Received signal {signum}, initiating shutdown")
        self.shutdown()
    
    def shutdown(self) -> None:
        """Shutdown the application gracefully."""
        if self.state == ApplicationState.STOPPING:
            return
        
        self.logger.info("Shutting down application")
        self.state = ApplicationState.STOPPING
        
        try:
            # Stop all components in reverse order
            for component in reversed(self.components):
                if hasattr(component, 'stop'):
                    try:
                        component.stop()
                        self.logger.debug(f"Stopped component: {component.__class__.__name__}")
                    except Exception as e:
                        self.logger.error(f"Error stopping component: {e}")
            
            # Execute shutdown handlers
            for handler in self._shutdown_handlers:
                try:
                    handler(self)
                except Exception as e:
                    self.logger.error(f"Error in shutdown handler: {e}")
            
            self.state = ApplicationState.STOPPED
            self.logger.info("Application shutdown complete")
            
        except Exception as e:
            self.logger.error(f"Error during shutdown: {e}")
            self.state = ApplicationState.ERROR
            raise
    
    def __enter__(self):
        """Context manager entry."""
        self.initialize()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.shutdown()
        return False
