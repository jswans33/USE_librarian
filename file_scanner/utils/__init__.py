"""Utility functions and helpers."""
from datetime import datetime
from pathlib import Path
from typing import Union

def ensure_path(path: Union[str, Path]) -> Path:
    """Convert string to Path and ensure it exists.
    
    Args:
        path: Path string or Path object
        
    Returns:
        Resolved Path object
        
    Raises:
        FileNotFoundError: If path doesn't exist
    """
    path_obj = Path(path).resolve()
    if not path_obj.exists():
        raise FileNotFoundError(f"Path does not exist: {path}")
    return path_obj

def format_timestamp(timestamp: Union[float, datetime]) -> str:
    """Format timestamp as human-readable string.
    
    Args:
        timestamp: Unix timestamp or datetime object
        
    Returns:
        Formatted date string
    """
    if isinstance(timestamp, float):
        dt = datetime.fromtimestamp(timestamp)
    else:
        dt = timestamp
    return dt.strftime("%Y-%m-%d %H:%M:%S")

def format_size(size_bytes: int) -> str:
    """Format size in bytes to human readable string.
    
    Args:
        size_bytes: Size in bytes
        
    Returns:
        Formatted size string (e.g., "1.5 MB")
    """
    if size_bytes < 1024:
        return f"{size_bytes} B"
    elif size_bytes < 1024*1024:
        return f"{size_bytes/1024:.1f} KB"
    elif size_bytes < 1024*1024*1024:
        return f"{size_bytes/(1024*1024):.1f} MB"
    else:
        return f"{size_bytes/(1024*1024*1024):.2f} GB"

def get_relative_path(path: Path, base: Path) -> Path:
    """Get relative path that handles paths outside base.
    
    Args:
        path: Path to make relative
        base: Base path to make relative to
        
    Returns:
        Relative path
    """
    try:
        return path.relative_to(base)
    except ValueError:
        # Path is outside base directory
        return path

__all__ = [
    'ensure_path',
    'format_timestamp',
    'format_size',
    'get_relative_path'
]
