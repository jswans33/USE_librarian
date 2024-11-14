"""File scanner package for directory analysis and cataloging.

This package provides tools for:
- Fast directory scanning and analysis
- Detailed file cataloging
- File type statistics
- Directory structure visualization

Example usage:
    from file_scanner.core import FileScanner, ScanOptions
    from file_scanner.database import StatsManager, CatalogManager
    
    # Configure scan options
    options = ScanOptions(
        max_depth=3,
        include_hidden=False
    )
    
    # Create scanner and perform scan
    scanner = FileScanner("path/to/scan", options)
    result = scanner.scan()
    
    # Save results
    stats_db = StatsManager()
    catalog_db = CatalogManager()
    
    scan_id = stats_db.save_scan_results(result)
    catalog_id = catalog_db.create_catalog(result)
"""

from .core import (
    FileInfo,
    DirectoryInfo,
    ScanResult,
    ScanOptions,
    FileScanner,
    ScanError,
    AccessError,
    InvalidPathError
)
from .database import StatsManager, CatalogManager

__version__ = "1.0.0"
__author__ = "Your Name"
__license__ = "MIT"

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
    'InvalidPathError',
]
