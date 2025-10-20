"""Service Module

Provides service layer abstraction and provider pattern.
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, Optional, Callable
import logging


class ServiceError(Exception):
    """Base exception for service errors"""
    pass


class Service(ABC):
    """Base Service Interface
    
    Services provide reusable business logic and external integrations.
    All services should inherit from this base class.
    
    Example:
        class DatabaseService(Service):
            def _on_initialize(self):
                self.connection = create_connection()
            
            def query(self, sql):
                return self.connection.execute(sql)
            
            def _on_cleanup(self):
                self.connection.close()
    """
    
    def __init__(self, name: Optional[str] = None):
        """Initialize service.
        
        Args:
            name: Optional service name
        """
        self.name = name or self.__class__.__name__
        self.logger = logging.getLogger(self.name)
        self._initialized = False
    
    def initialize(self, config: Optional[Dict[str, Any]] = None) -> None:
        """Initialize the service.
        
        Args:
            config: Optional configuration dictionary
        """
        if self._initialized:
            self.logger.warning(f"{self.name} already initialized")
            return
        
        try:
            self._on_initialize(config or {})
            self._initialized = True
            self.logger.info(f"{self.name} initialized")
        except Exception as e:
            self.logger.error(f"Failed to initialize {self.name}: {e}")
            raise ServiceError(f"Initialization failed: {e}") from e
    
    def cleanup(self) -> None:
        """Cleanup service resources."""
        if not self._initialized:
            return
        
        try:
            self._on_cleanup()
            self._initialized = False
            self.logger.info(f"{self.name} cleaned up")
        except Exception as e:
            self.logger.error(f"Failed to cleanup {self.name}: {e}")
            raise ServiceError(f"Cleanup failed: {e}") from e
    
    def _on_initialize(self, config: Dict[str, Any]) -> None:
        """Hook called during initialization. Override in subclasses.
        
        Args:
            config: Configuration dictionary
        """
        pass
    
    def _on_cleanup(self) -> None:
        """Hook called during cleanup. Override in subclasses."""
        pass
    
    @property
    def is_initialized(self) -> bool:
        """Check if service is initialized."""
        return self._initialized
    
    def __repr__(self) -> str:
        return f"<{self.__class__.__name__} name={self.name} initialized={self._initialized}>"


class ServiceProvider:
    """Service Provider Pattern Implementation
    
    Manages service lifecycle and provides dependency resolution.
    
    Example:
        provider = ServiceProvider()
        provider.register('cache', CacheService)
        provider.register('api', APIService, config={'timeout': 30})
        
        cache = provider.get('cache')
    """
    
    def __init__(self):
        """Initialize service provider."""
        self._services: Dict[str, Any] = {}
        self._factories: Dict[str, Callable] = {}
        self._configs: Dict[str, Dict] = {}
        self._singletons: Dict[str, Any] = {}
        self.logger = logging.getLogger("ServiceProvider")
    
    def register(self, 
                 name: str, 
                 factory: Callable, 
                 config: Optional[Dict[str, Any]] = None,
                 singleton: bool = True) -> None:
        """Register a service.
        
        Args:
            name: Service identifier
            factory: Service factory (class or callable)
            config: Optional configuration
            singleton: Whether to use singleton pattern
        """
        self._factories[name] = factory
        self._configs[name] = config or {}
        
        if not singleton and name in self._singletons:
            del self._singletons[name]
        
        self.logger.info(f"Registered service: {name}")
    
    def get(self, name: str) -> Any:
        """Get a service instance.
        
        Args:
            name: Service identifier
            
        Returns:
            Service instance
        """
        # Return singleton if exists
        if name in self._singletons:
            return self._singletons[name]
        
        # Get or create instance
        if name not in self._factories:
            raise ServiceError(f"Service not registered: {name}")
        
        factory = self._factories[name]
        config = self._configs.get(name, {})
        
        try:
            # Create instance
            if isinstance(factory, type):
                instance = factory()
            else:
                instance = factory()
            
            # Initialize if it's a Service
            if isinstance(instance, Service):
                instance.initialize(config)
            
            # Store as singleton
            self._singletons[name] = instance
            
            self.logger.debug(f"Created service instance: {name}")
            return instance
            
        except Exception as e:
            self.logger.error(f"Failed to create service {name}: {e}")
            raise ServiceError(f"Failed to create service: {e}") from e
    
    def has(self, name: str) -> bool:
        """Check if service is registered.
        
        Args:
            name: Service identifier
            
        Returns:
            True if service is registered
        """
        return name in self._factories
    
    def cleanup_all(self) -> None:
        """Cleanup all initialized services."""
        for name, instance in self._singletons.items():
            try:
                if isinstance(instance, Service):
                    instance.cleanup()
                self.logger.debug(f"Cleaned up service: {name}")
            except Exception as e:
                self.logger.error(f"Error cleaning up service {name}: {e}")
        
        self._singletons.clear()
        self.logger.info("All services cleaned up")
    
    def __del__(self):
        """Cleanup on deletion."""
        self.cleanup_all()
