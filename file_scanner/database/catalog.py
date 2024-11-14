"""File catalog database management module."""
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from datetime import datetime
from rich.console import Console
from rich.table import Table
from rich.tree import Tree
from rich import print as rprint
import sqlite3

from .base import DatabaseManager
from ..core.models import ScanResult
from ..utils import format_timestamp, format_size
from ..utils.formatting import create_file_table, create_directory_tree

class CatalogManager(DatabaseManager):
    """Manages detailed file catalog database operations."""
    
    def __init__(self, db_path: str = "file_catalog.db"):
        """Initialize catalog database.
        
        Args:
            db_path: Path to SQLite database file
        """
        self.console = Console()
        super().__init__(db_path)
    
    def _create_tables(self) -> None:
        """Create catalog tables if they don't exist."""
        queries = [
            # Catalogs table
            """
            CREATE TABLE IF NOT EXISTS catalogs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                scan_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                root_path TEXT NOT NULL,
                total_files INTEGER NOT NULL,
                total_size_bytes INTEGER NOT NULL
            )
            """,
            # Files table
            """
            CREATE TABLE IF NOT EXISTS files (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                catalog_id INTEGER NOT NULL,
                file_name TEXT NOT NULL,
                directory_path TEXT NOT NULL,
                relative_path TEXT NOT NULL,
                extension TEXT,
                size_bytes INTEGER NOT NULL,
                created_date TIMESTAMP,
                modified_date TIMESTAMP NOT NULL,
                is_hidden BOOLEAN NOT NULL,
                FOREIGN KEY (catalog_id) REFERENCES catalogs (id)
            )
            """,
            # Directories table
            """
            CREATE TABLE IF NOT EXISTS directories (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                catalog_id INTEGER NOT NULL,
                directory_path TEXT NOT NULL,
                relative_path TEXT NOT NULL,
                depth INTEGER NOT NULL,
                parent_path TEXT,
                FOREIGN KEY (catalog_id) REFERENCES catalogs (id)
            )
            """
        ]
        
        for query in queries:
            self.execute_update(query)
    
    def _update_schema(self) -> None:
        """Update database schema with any missing columns."""
        # Add status column to catalogs if it doesn't exist
        catalogs_columns = self._get_table_columns("catalogs")
        
        if "status" not in catalogs_columns:
            self._add_column(
                "catalogs",
                "status",
                "TEXT DEFAULT 'active'"
            )
        
        if "total_size_bytes" not in catalogs_columns:
            self._add_column(
                "catalogs",
                "total_size_bytes",
                "INTEGER DEFAULT 0"
            )
        
        # Add any missing columns to files table
        files_columns = self._get_table_columns("files")
        
        if "created_date" not in files_columns:
            self._add_column(
                "files",
                "created_date",
                "TIMESTAMP"
            )
        
        if "is_hidden" not in files_columns:
            self._add_column(
                "files",
                "is_hidden",
                "BOOLEAN DEFAULT 0"
            )
    
    def create_catalog(self, scan_result: ScanResult) -> int:
        """Create a new catalog from scan results.
        
        Args:
            scan_result: Results of directory scan
            
        Returns:
            ID of the new catalog
        """
        # Insert catalog entry
        catalog_id = self.execute_insert(
            """
            INSERT INTO catalogs (
                root_path, total_files, total_size_bytes, status
            ) VALUES (?, ?, ?, 'active')
            """,
            (str(scan_result.root_path), scan_result.total_files, scan_result.total_size)
        )
        
        # Process directories
        dir_queries = []
        for dir_info in scan_result.directories:
            dir_queries.append((
                """
                INSERT INTO directories (
                    catalog_id, directory_path, relative_path,
                    depth, parent_path
                ) VALUES (?, ?, ?, ?, ?)
                """,
                (
                    catalog_id,
                    str(dir_info.path),
                    str(dir_info.relative_path),
                    dir_info.depth,
                    str(dir_info.parent_path) if dir_info.parent_path else None
                )
            ))
        
        if dir_queries:
            self.execute_transaction(dir_queries)
        
        # Process files
        file_queries = []
        for file_info in scan_result.files:
            file_queries.append((
                """
                INSERT INTO files (
                    catalog_id, file_name, directory_path, relative_path,
                    extension, size_bytes, created_date, modified_date,
                    is_hidden
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    catalog_id,
                    file_info.name,
                    str(file_info.path.parent),
                    str(file_info.relative_path),
                    file_info.extension,
                    file_info.size_bytes,
                    file_info.created_date,
                    file_info.modified_date,
                    file_info.is_hidden
                )
            ))
        
        if file_queries:
            # Process in batches to handle large file sets
            batch_size = 1000
            for i in range(0, len(file_queries), batch_size):
                batch = file_queries[i:i + batch_size]
                self.execute_transaction(batch)
        
        return catalog_id
    
    def get_file_info(self, catalog_id: int, path_pattern: Optional[str] = None) -> None:
        """Display detailed file information for a catalog.
        
        Args:
            catalog_id: ID of the catalog to analyze
            path_pattern: Optional pattern to filter files
        """
        try:
            # Get catalog info
            catalog_query = """
                SELECT scan_date, root_path, total_files, total_size_bytes, status
                FROM catalogs WHERE id = ?
            """
            
            catalog_results = self.execute_query(catalog_query, (catalog_id,))
        except sqlite3.OperationalError:
            # Fallback query without status
            catalog_query = """
                SELECT scan_date, root_path, total_files, total_size_bytes
                FROM catalogs WHERE id = ?
            """
            
            catalog_results = self.execute_query(catalog_query, (catalog_id,))
        
        if not catalog_results:
            rprint(f"[red]No catalog found with ID {catalog_id}[/]")
            return
        
        catalog = catalog_results[0]
        
        # Build file query
        file_query = """
            SELECT file_name, relative_path, extension, 
                   size_bytes, created_date, modified_date, is_hidden
            FROM files 
            WHERE catalog_id = ?
        """
        params = [catalog_id]
        
        if path_pattern:
            file_query += " AND relative_path LIKE ?"
            params.append(f"%{path_pattern}%")
        
        file_query += " ORDER BY relative_path"
        
        files = self.execute_query(file_query, tuple(params))
        
        # Display results
        rprint(f"\n[bold]Catalog Analysis for:[/] [blue]{catalog['root_path']}[/]")
        rprint(f"[bold]Date:[/] {format_timestamp(datetime.fromisoformat(catalog['scan_date']))}")
        if 'status' in catalog:
            rprint(f"[bold]Status:[/] {catalog['status']}")
        rprint(f"[bold]Total Files:[/] [green]{catalog['total_files']:,}[/]")
        rprint(f"[bold]Total Size:[/] [green]{format_size(catalog['total_size_bytes'])}[/]")
        
        if files:
            # Create files table
            table = create_file_table(files, self.console)
            self.console.print("\n[bold]Files:[/]")
            self.console.print(table)
    
    def get_directory_tree(self, catalog_id: int) -> None:
        """Display directory structure for a catalog.
        
        Args:
            catalog_id: ID of the catalog to show
        """
        # Get catalog info
        catalog_query = """
            SELECT root_path FROM catalogs WHERE id = ?
        """
        
        catalog_results = self.execute_query(catalog_query, (catalog_id,))
        if not catalog_results:
            rprint(f"[red]No catalog found with ID {catalog_id}[/]")
            return
        
        root_path = catalog_results[0]['root_path']
        
        # Get directories
        dir_query = """
            SELECT relative_path, depth
            FROM directories
            WHERE catalog_id = ?
            ORDER BY depth, relative_path
        """
        
        directories = self.execute_query(dir_query, (catalog_id,))
        
        # Create tree
        tree = create_directory_tree(Path(root_path), directories, self.console)
        self.console.print("\n[bold]Directory Structure:[/]")
        self.console.print(tree)
