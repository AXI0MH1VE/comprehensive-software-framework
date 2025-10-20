"""Core Framework Components

This module contains the fundamental building blocks of the framework:
- Application: Main application container
- Component: Base component interface
- Service: Service layer abstraction
- Registry: Dependency injection container
"""

from .application import Application
from .component import Component, ComponentLifecycle
from .service import Service, ServiceProvider
from .registry import Registry, Container

__all__ = [
    "Application",
    "Component",
    "ComponentLifecycle",
    "Service",
    "ServiceProvider",
    "Registry",
    "Container",
]
