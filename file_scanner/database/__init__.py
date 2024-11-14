"""Database management package."""
from .base import DatabaseManager
from .stats import StatsManager
from .catalog import CatalogManager

__all__ = [
    'DatabaseManager',  # Base class for database operations
    'StatsManager',     # Handles file statistics
    'CatalogManager'    # Handles detailed file catalogs
]
