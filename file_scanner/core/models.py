"""Core domain models and interfaces."""
from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

@dataclass
class FileInfo:
    """Information about a single file in the system."""
    name: str
    path: Path
    relative_path: Path
    extension: Optional[str]
    size_bytes: int
    created_date: datetime
    modified_date: datetime
    is_hidden: bool

    @property
    def formatted_size(self) -> str:
        """Get human-readable file size.
        
        Returns:
            Formatted size string (e.g., "1.5 MB")
        """
        if self.size_bytes < 1024:
            return f"{self.size_bytes} B"
        elif self.size_bytes < 1024*1024:
            return f"{self.size_bytes/1024:.1f} KB"
        elif self.size_bytes < 1024*1024*1024:
            return f"{self.size_bytes/(1024*1024):.1f} MB"
        else:
            return f"{self.size_bytes/(1024*1024*1024):.1f} GB"

@dataclass
class DirectoryInfo:
    """Information about a directory in the system."""
    path: Path
    relative_path: Path
    depth: int
    parent_path: Optional[Path]

    @property
    def name(self) -> str:
        """Get directory name.
        
        Returns:
            Name of the directory
        """
        return self.path.name

@dataclass
class ScanResult:
    """Results of a directory scan operation."""
    root_path: Path
    total_files: int
    total_size: int
    files: List[FileInfo]
    directories: List[DirectoryInfo]
    extension_stats: Dict[str, Dict[str, int]]

    @property
    def formatted_total_size(self) -> str:
        """Get human-readable total size.
        
        Returns:
            Formatted size string
        """
        if self.total_size < 1024:
            return f"{self.total_size} B"
        elif self.total_size < 1024*1024:
            return f"{self.total_size/1024:.1f} KB"
        elif self.total_size < 1024*1024*1024:
            return f"{self.total_size/(1024*1024):.1f} MB"
        else:
            return f"{self.total_size/(1024*1024*1024):.2f} GB"

@dataclass
class ScanOptions:
    """Configuration options for directory scanning."""
    max_depth: Optional[int] = None
    follow_links: bool = False
    ignore_patterns: List[str] = None
    include_hidden: bool = True

class IFileScanner(ABC):
    """Interface for file scanning operations."""
    
    @abstractmethod
    def scan(self) -> ScanResult:
        """Perform directory scan.
        
        Returns:
            ScanResult containing scan information
        """
        pass
    
    @abstractmethod
    def display_tree(self, max_depth: Optional[int] = None) -> None:
        """Display directory tree structure.
        
        Args:
            max_depth: Maximum depth to display
        """
        pass

class IStatsManager(ABC):
    """Interface for file statistics operations."""
    
    @abstractmethod
    def save_scan_results(self, scan_result: ScanResult) -> int:
        """Save scan results to database.
        
        Args:
            scan_result: Results of directory scan
            
        Returns:
            ID of saved scan record
        """
        pass
    
    @abstractmethod
    def list_scans(self) -> None:
        """Display all scans in database."""
        pass
    
    @abstractmethod
    def get_scan_details(self, scan_id: int) -> None:
        """Display detailed analysis of a scan.
        
        Args:
            scan_id: ID of scan to analyze
        """
        pass

class ICatalogManager(ABC):
    """Interface for file catalog operations."""
    
    @abstractmethod
    def create_catalog(self, scan_result: ScanResult) -> int:
        """Create new catalog from scan results.
        
        Args:
            scan_result: Results of directory scan
            
        Returns:
            ID of new catalog
        """
        pass
    
    @abstractmethod
    def get_file_info(self, catalog_id: int, path_pattern: Optional[str] = None) -> None:
        """Display detailed file information.
        
        Args:
            catalog_id: ID of catalog to analyze
            path_pattern: Optional path pattern to filter files
        """
        pass
    
    @abstractmethod
    def get_directory_tree(self, catalog_id: int) -> None:
        """Display directory structure.
        
        Args:
            catalog_id: ID of catalog to show
        """
        pass

# Domain Exceptions
class ScanError(Exception):
    """Base class for scan-related errors."""
    pass

class AccessError(ScanError):
    """Raised when access to a file or directory is denied."""
    pass

class InvalidPathError(ScanError):
    """Raised when a path is invalid or doesn't exist."""
    pass
