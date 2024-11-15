"""Base database management module."""
from abc import ABC, abstractmethod
import sqlite3
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Set
from datetime import datetime
from rich import print as rprint

from ..utils import ensure_path

class DatabaseManager(ABC):
    """Abstract base class for database operations."""
    
    def __init__(self, db_path: str):
        """Initialize database connection.
        
        Args:
            db_path: Path to SQLite database file
        """
        self.db_path = ensure_path(db_path) if Path(db_path).exists() else Path(db_path)
        self._create_tables()
        self._update_schema()
    
    def _get_connection(self) -> sqlite3.Connection:
        """Get a database connection with row factory."""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn
    
    @abstractmethod
    def _create_tables(self) -> None:
        """Create necessary database tables if they don't exist."""
        pass
    
    def _get_table_columns(self, table_name: str) -> Set[str]:
        """Get set of column names for a table."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(f"PRAGMA table_info({table_name})")
            return {row['name'] for row in cursor.fetchall()}
    
    def _add_column(self, table_name: str, column_name: str, column_type: str) -> None:
        """Add a new column to an existing table."""
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(f"ALTER TABLE {table_name} ADD COLUMN {column_name} {column_type}")
                conn.commit()
                rprint(f"[yellow]Added column {column_name} to {table_name}[/]")
        except sqlite3.OperationalError as e:
            if "duplicate column name" not in str(e).lower():
                raise
    
    def _update_schema(self) -> None:
        """Update database schema with any missing columns."""
        pass
    
    def execute_query(self, query: str, params: Optional[Tuple] = None) -> List[Dict[str, Any]]:
        """Execute a SELECT query and return results as dictionaries."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(query, params or ())
            return [dict(row) for row in cursor.fetchall()]
    
    def execute_insert(self, query: str, params: Optional[Tuple] = None) -> int:
        """Execute an INSERT query and return the last insert ID."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(query, params or ())
            conn.commit()
            return cursor.lastrowid or 0
    
    def execute_update(self, query: str, params: Optional[Tuple] = None) -> int:
        """Execute an UPDATE/DELETE query and return affected rows."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(query, params or ())
            conn.commit()
            return cursor.rowcount
    
    def execute_transaction(self, queries: List[Tuple[str, Optional[Tuple]]], return_last_id: bool = False) -> Optional[int]:
        """Execute multiple queries in a transaction."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            last_id = None
            try:
                for query, params in queries:
                    cursor.execute(query, params or ())
                    if return_last_id:
                        last_id = cursor.lastrowid
                conn.commit()
                return last_id if return_last_id else None
            except Exception:
                conn.rollback()
                raise
    
    def table_exists(self, table_name: str) -> bool:
        """Check if a table exists in the database."""
        query = """
            SELECT name FROM sqlite_master 
            WHERE type='table' AND name=?
        """
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(query, (table_name,))
            return cursor.fetchone() is not None
    
    def backup_database(self, backup_path: str) -> None:
        """Create a backup of the database."""
        with self._get_connection() as conn:
            backup_conn = sqlite3.connect(backup_path)
            conn.backup(backup_conn)
            backup_conn.close()
    
    def vacuum(self) -> None:
        """Optimize database by removing unused space."""
        with self._get_connection() as conn:
            conn.execute("VACUUM")
