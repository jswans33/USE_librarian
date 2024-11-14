"""Formatting utilities for output display."""
from datetime import datetime
from pathlib import Path
from typing import Dict, List
from rich.console import Console
from rich.table import Table
from rich.tree import Tree

from ..core.models import FileInfo, DirectoryInfo, ScanResult
from . import format_size, format_timestamp

def create_file_table(files: List[FileInfo], console: Console) -> Table:
    """Create a formatted table of files.
    
    Args:
        files: List of file information
        console: Rich console for output
        
    Returns:
        Formatted table
    """
    table = Table(show_header=True, header_style="bold magenta")
    table.add_column("File Name", style="cyan")
    table.add_column("Path", style="blue")
    table.add_column("Type", style="yellow")
    table.add_column("Size", justify="right", style="green")
    table.add_column("Modified", style="magenta")
    
    for file in files:
        table.add_row(
            f"{'.' if file.is_hidden else ''}{file.name}",
            str(file.relative_path),
            file.extension or "(none)",
            format_size(file.size_bytes),
            format_timestamp(file.modified_date)
        )
    
    return table

def create_directory_tree(
    root_path: Path,
    directories: List[DirectoryInfo],
    console: Console
) -> Tree:
    """Create a formatted directory tree.
    
    Args:
        root_path: Base directory path
        directories: List of directory information
        console: Rich console for output
        
    Returns:
        Formatted tree
    """
    tree = Tree(f"[bold yellow]{root_path}[/]")
    path_to_tree = {Path(): tree}
    
    # Sort directories by depth and path
    sorted_dirs = sorted(
        directories,
        key=lambda d: (d.depth, str(d.relative_path))
    )
    
    for dir_info in sorted_dirs:
        parent_path = dir_info.relative_path.parent
        
        if parent_path in path_to_tree:
            branch = path_to_tree[parent_path].add(
                f"[bold blue]{dir_info.name}/[/]"
            )
            path_to_tree[dir_info.relative_path] = branch
    
    return tree

def create_scan_summary(scan_result: ScanResult, console: Console) -> Table:
    """Create a formatted summary table of scan results.
    
    Args:
        scan_result: Results of directory scan
        console: Rich console for output
        
    Returns:
        Formatted table
    """
    table = Table(show_header=True, header_style="bold magenta")
    table.add_column("Extension", style="cyan")
    table.add_column("Count", justify="right", style="green")
    table.add_column("Size", justify="right", style="yellow")
    table.add_column("Percentage", justify="right", style="red")
    
    # Sort extensions by count
    sorted_exts = sorted(
        scan_result.extension_stats.items(),
        key=lambda x: x[1]['count'],
        reverse=True
    )
    
    for ext, stats in sorted_exts:
        percentage = (stats['count'] / scan_result.total_files) * 100
        table.add_row(
            ext,
            f"{stats['count']:,}",
            format_size(stats['size']),
            f"{percentage:.1f}%"
        )
    
    return table

def create_scan_header(scan_result: ScanResult) -> List[str]:
    """Create formatted header lines for scan results.
    
    Args:
        scan_result: Results of directory scan
        
    Returns:
        List of formatted header lines
    """
    return [
        f"[bold]Scan Results for:[/] [blue]{scan_result.root_path}[/]",
        f"[bold]Total Files:[/] [green]{scan_result.total_files:,}[/]",
        f"[bold]Total Size:[/] [green]{format_size(scan_result.total_size)}[/]",
        f"[bold]File Types:[/] [yellow]{len(scan_result.extension_stats)}[/]"
    ]
