"""File scanner package for directory analysis and cataloging."""
from .core import (
    FileInfo, DirectoryInfo, ScanResult, ScanOptions,
    FileScanner, ScanError, AccessError, InvalidPathError
)
from .database import StatsManager, CatalogManager

__version__ = "1.0.0"

__all__ = [
    # Core functionality
    'FileScanner',
    'ScanOptions',
    
    # Database managers
    'StatsManager',
    'CatalogManager',
    
    # Data models
    'FileInfo',
    'DirectoryInfo',
    'ScanResult',
    
    # Exceptions
    'ScanError',
    'AccessError',
    'InvalidPathError'
]
