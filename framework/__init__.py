"""Comprehensive Software Framework

A robust, production-ready software framework with complete implementation,
clear architecture, and robust design patterns.
"""

__version__ = "1.0.0"
__author__ = "Framework Development Team"
__license__ = "MIT"

from .core import (
    Application,
    Component,
    Service,
    Registry,
)

from .data import (
    Model,
    Repository,
    QueryBuilder,
    Transaction,
)

from .utils import (
    Logger,
    Config,
    Validator,
    Cache,
)

__all__ = [
    "Application",
    "Component",
    "Service",
    "Registry",
    "Model",
    "Repository",
    "QueryBuilder",
    "Transaction",
    "Logger",
    "Config",
    "Validator",
    "Cache",
]
