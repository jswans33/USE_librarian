"""Core domain models and interfaces."""
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
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
        """Get human-readable file size."""
        if self.size_bytes < 1024:
            return f"{self.size_bytes} B"
        elif self.size_bytes < 1024*1024:
            return f"{self.size_bytes/1024:.1f} KB"
        elif self.size_bytes < 1024*1024*1024:
            return f"{self.size_bytes/(1024*1024):.1f} MB"
        else:
            return f"{self.size_bytes/(1024*1024*1024):.2f} GB"

@dataclass
class DirectoryInfo:
    """Information about a directory in the system."""
    path: Path
    relative_path: Path
    depth: int
    parent_path: Optional[Path]

    @property
    def name(self) -> str:
        """Get directory name."""
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
        """Get human-readable total size."""
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
    ignore_patterns: List[str] = field(default_factory=list)
    include_hidden: bool = True

    def __post_init__(self):
        """Ensure ignore_patterns is a list."""
        if self.ignore_patterns is None:
            self.ignore_patterns = []

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
