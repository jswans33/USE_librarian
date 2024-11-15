"""Core file system scanning module."""
from datetime import datetime
from pathlib import Path
from typing import Dict, Generator, List, Optional, Set
from rich.progress import Progress, SpinnerColumn, TimeElapsedColumn
from rich.tree import Tree
from rich.console import Console
from rich import print as rprint

from .models import (
    FileInfo, DirectoryInfo, ScanResult,
    ScanOptions, ScanError, AccessError, InvalidPathError
)
from ..utils import ensure_path, format_timestamp, get_relative_path

class FileScanner:
    """Handles directory traversal and file analysis."""
    
    def __init__(self, root_path: str | Path, options: Optional[ScanOptions] = None):
        """Initialize scanner with root directory and options.
        
        Args:
            root_path: Directory path to scan
            options: Scan configuration options
        
        Raises:
            InvalidPathError: If path doesn't exist or isn't a directory
        """
        self.root_path = ensure_path(root_path)
        self.options = options or ScanOptions()
        self.console = Console()
        
        if not self.root_path.is_dir():
            raise InvalidPathError(f"Path is not a directory: {root_path}")
    
    def _should_process_path(self, path: Path) -> bool:
        """Check if a path should be processed based on options."""
        # Check if path is hidden
        if not self.options.include_hidden and path.name.startswith('.'):
            return False
            
        # Check ignore patterns
        if self.options.ignore_patterns:
            for pattern in self.options.ignore_patterns:
                if path.match(pattern):
                    return False
        
        return True
    
    def _scan_files(self) -> Generator[Path, None, None]:
        """Generate all files in directory tree."""
        try:
            for file_path in self.root_path.rglob("*"):
                try:
                    if (file_path.is_file() and 
                        (self.options.follow_links or not file_path.is_symlink()) and
                        self._should_process_path(file_path)):
                        yield file_path
                except PermissionError:
                    rprint(f"[yellow]Warning: Permission denied: {file_path}[/]")
                except Exception as e:
                    rprint(f"[yellow]Warning: Error processing {file_path}: {str(e)}[/]")
        except KeyboardInterrupt:
            return
    
    def scan(self) -> ScanResult:
        """Perform directory scan."""
        extension_stats: Dict[str, Dict[str, int]] = {}
        files: List[FileInfo] = []
        directories: List[DirectoryInfo] = []
        total_size = 0
        
        try:
            with Progress(
                SpinnerColumn(),
                *Progress.get_default_columns(),
                TimeElapsedColumn(),
                console=self.console
            ) as progress:
                # Count files
                count_task = progress.add_task(
                    "[yellow]Counting files...", total=None
                )
                
                file_paths = list(self._scan_files())
                total_files = len(file_paths)
                progress.remove_task(count_task)
                
                # Process files
                process_task = progress.add_task(
                    "[green]Analyzing files...", total=total_files
                )
                
                # Track processed directories
                processed_dirs = set()
                
                for file_path in file_paths:
                    # Update progress
                    progress.update(process_task, advance=1)
                    
                    try:
                        # Get file stats
                        stats = file_path.stat()
                        
                        # Create FileInfo
                        file_info = FileInfo(
                            name=file_path.name,
                            path=file_path,
                            relative_path=get_relative_path(file_path, self.root_path),
                            extension=file_path.suffix.lower() if file_path.suffix else None,
                            size_bytes=stats.st_size,
                            created_date=datetime.fromtimestamp(stats.st_ctime),
                            modified_date=datetime.fromtimestamp(stats.st_mtime),
                            is_hidden=file_path.name.startswith('.')
                        )
                        files.append(file_info)
                        
                        # Update extension stats
                        ext = file_info.extension or "(no extension)"
                        if ext not in extension_stats:
                            extension_stats[ext] = {"count": 0, "size": 0}
                        extension_stats[ext]["count"] += 1
                        extension_stats[ext]["size"] += stats.st_size
                        
                        total_size += stats.st_size
                        
                        # Process directories
                        dir_path = file_path.parent
                        current_path = self.root_path
                        for part in get_relative_path(dir_path, self.root_path).parts:
                            current_path = current_path / part
                            if current_path not in processed_dirs:
                                processed_dirs.add(current_path)
                                rel_path = get_relative_path(current_path, self.root_path)
                                
                                dir_info = DirectoryInfo(
                                    path=current_path,
                                    relative_path=rel_path,
                                    depth=len(rel_path.parts),
                                    parent_path=current_path.parent if current_path != self.root_path else None
                                )
                                directories.append(dir_info)
                                
                    except PermissionError:
                        rprint(f"[yellow]Warning: Permission denied: {file_path}[/]")
                    except Exception as e:
                        rprint(f"[yellow]Warning: Error processing {file_path}: {str(e)}[/]")
                
            return ScanResult(
                root_path=self.root_path,
                total_files=total_files,
                total_size=total_size,
                files=files,
                directories=directories,
                extension_stats=extension_stats
            )
            
        except KeyboardInterrupt:
            rprint("\n[yellow]Scan interrupted. Returning partial results...[/]")
            return ScanResult(
                root_path=self.root_path,
                total_files=len(files),
                total_size=total_size,
                files=files,
                directories=directories,
                extension_stats=extension_stats
            )
