"""Statistics database management module."""
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from datetime import datetime
from rich.console import Console
from rich.table import Table
from rich import print as rprint
import sqlite3

from .base import DatabaseManager
from ..core.models import ScanResult
from ..utils import format_timestamp, format_size
from ..utils.formatting import create_scan_summary

class StatsManager(DatabaseManager):
    """Manages file statistics database operations."""
    
    def __init__(self, db_path: str = "file_stats.db"):
        """Initialize statistics database."""
        self.console = Console()
        super().__init__(db_path)
    
    def _create_tables(self) -> None:
        """Create statistics tables if they don't exist."""
        queries = [
            # Scan results table
            """
            CREATE TABLE IF NOT EXISTS scan_results (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                scan_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                root_path TEXT NOT NULL,
                total_files INTEGER NOT NULL,
                total_size_bytes INTEGER NOT NULL
            )
            """,
            # File types table
            """
            CREATE TABLE IF NOT EXISTS file_types (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                scan_id INTEGER NOT NULL,
                extension TEXT NOT NULL,
                count INTEGER NOT NULL,
                total_size_bytes INTEGER NOT NULL,
                FOREIGN KEY (scan_id) REFERENCES scan_results (id)
            )
            """
        ]
        
        for query in queries:
            self.execute_update(query)
    
    def _update_schema(self) -> None:
        """Update database schema with any missing columns."""
        # Add status column to scan_results if it doesn't exist
        scan_results_columns = self._get_table_columns("scan_results")
        
        if "status" not in scan_results_columns:
            self._add_column(
                "scan_results",
                "status",
                "TEXT DEFAULT 'completed'"
            )
        
        if "total_size_bytes" not in scan_results_columns:
            self._add_column(
                "scan_results",
                "total_size_bytes",
                "INTEGER DEFAULT 0"
            )
    
    def save_scan_results(self, scan_result: ScanResult) -> int:
        """Save scan results, overwriting previous scan of same path."""
        # First mark any existing scans of this path as archived
        try:
            self.execute_update(
                "UPDATE scan_results SET status = 'archived' WHERE root_path = ?",
                (str(scan_result.root_path),)
            )
        except sqlite3.OperationalError:
            # If status column doesn't exist, that's okay
            pass
        
        # Insert new scan record
        scan_id = self.execute_insert(
            """
            INSERT INTO scan_results (
                root_path, total_files, total_size_bytes, status
            ) VALUES (?, ?, ?, 'completed')
            """,
            (str(scan_result.root_path), scan_result.total_files, scan_result.total_size)
        )
        
        # Insert extension statistics
        ext_queries = []
        for ext, stats in scan_result.extension_stats.items():
            ext_queries.append((
                """
                INSERT INTO file_types (
                    scan_id, extension, count, total_size_bytes
                ) VALUES (?, ?, ?, ?)
                """,
                (scan_id, ext, stats['count'], stats['size'])
            ))
        
        if ext_queries:
            self.execute_transaction(ext_queries)
        
        return scan_id
    
    def list_scans(self) -> None:
        """Display all scans in the database with their summary."""
        try:
            query = """
                SELECT 
                    sr.id,
                    sr.scan_date,
                    sr.root_path,
                    sr.total_files,
                    sr.total_size_bytes,
                    sr.status,
                    COUNT(DISTINCT ft.extension) as unique_extensions,
                    SUM(ft.total_size_bytes) as total_size
                FROM scan_results sr
                LEFT JOIN file_types ft ON sr.id = ft.scan_id
                GROUP BY sr.id
                ORDER BY sr.scan_date DESC
            """
            
            results = self.execute_query(query)
        except sqlite3.OperationalError:
            # Fallback query without status
            query = """
                SELECT 
                    sr.id,
                    sr.scan_date,
                    sr.root_path,
                    sr.total_files,
                    sr.total_size_bytes,
                    COUNT(DISTINCT ft.extension) as unique_extensions,
                    SUM(ft.total_size_bytes) as total_size
                FROM scan_results sr
                LEFT JOIN file_types ft ON sr.id = ft.scan_id
                GROUP BY sr.id
                ORDER BY sr.scan_date DESC
            """
            
            results = self.execute_query(query)
        
        if not results:
            rprint("[yellow]No scans found in database.[/]")
            return
        
        # Create and populate the table
        table = Table(show_header=True, header_style="bold magenta")
        table.add_column("ID", style="cyan", justify="right")
        table.add_column("Date", style="blue")
        table.add_column("Directory", style="green")
        table.add_column("Files", justify="right", style="yellow")
        table.add_column("Types", justify="right", style="red")
        table.add_column("Total Size", justify="right", style="magenta")
        if 'status' in results[0]:
            table.add_column("Status", style="cyan")
        
        for row in results:
            row_data = [
                str(row['id']),
                format_timestamp(datetime.fromisoformat(row['scan_date'])),
                row['root_path'],
                f"{row['total_files']:,}",
                str(row['unique_extensions'] or 0),
                format_size(row['total_size_bytes'])
            ]
            
            if 'status' in row:
                row_data.append(row['status'])
            
            table.add_row(*row_data)
        
        self.console.print("\n[bold]Scan History:[/]")
        self.console.print(table)
    
    def get_scan_details(self, scan_id: int) -> None:
        """Display detailed analysis of a specific scan."""
        try:
            # Get scan metadata
            scan_query = """
                SELECT scan_date, root_path, total_files, total_size_bytes, status
                FROM scan_results
                WHERE id = ?
            """
            
            scan_results = self.execute_query(scan_query, (scan_id,))
        except sqlite3.OperationalError:
            # Fallback query without status
            scan_query = """
                SELECT scan_date, root_path, total_files, total_size_bytes
                FROM scan_results
                WHERE id = ?
            """
            
            scan_results = self.execute_query(scan_query, (scan_id,))
        
        if not scan_results:
            rprint(f"[red]No scan found with ID {scan_id}[/]")
            return
        
        scan = scan_results[0]
        
        # Get extension statistics
        ext_query = """
            SELECT 
                extension,
                count,
                total_size_bytes,
                (count * 100.0 / ?) as percentage
            FROM file_types
            WHERE scan_id = ?
            ORDER BY count DESC
        """
        
        ext_results = self.execute_query(
            ext_query, 
            (scan['total_files'], scan_id)
        )
        
        # Display results
        rprint(f"\n[bold]Scan Analysis for:[/] [blue]{scan['root_path']}[/]")
        rprint(f"[bold]Date:[/] {format_timestamp(datetime.fromisoformat(scan['scan_date']))}")
        if 'status' in scan:
            rprint(f"[bold]Status:[/] {scan['status']}")
        rprint(f"[bold]Total Files:[/] [green]{scan['total_files']:,}[/]")
        rprint(f"[bold]Total Size:[/] [green]{format_size(scan['total_size_bytes'])}[/]")
        
        if ext_results:
            # Create extension breakdown table
            table = Table(show_header=True, header_style="bold magenta")
            table.add_column("Extension", style="cyan")
            table.add_column("Count", justify="right", style="green")
            table.add_column("Size", justify="right", style="yellow")
            table.add_column("Percentage", justify="right", style="red")
            
            for row in ext_results:
                table.add_row(
                    row['extension'],
                    f"{row['count']:,}",
                    format_size(row['total_size_bytes']),
                    f"{row['percentage']:.1f}%"
                )
            
            self.console.print("\n[bold]File Type Distribution:[/]")
            self.console.print(table)
