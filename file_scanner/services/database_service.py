"""Database service for managing file scan data."""
import sqlite3
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import List, Iterator, Optional, Protocol, Tuple
from pathlib import Path
import os

from ..core.models import FileInfo, ScanResult

@dataclass
class DatabaseEntry:
    """Represents a database entry for a file."""
    name: str
    path: str
    size: str
    created: str
    modified: str
    extension: str

    @classmethod
    def from_file_info(cls, file_info: FileInfo) -> 'DatabaseEntry':
        """Create a database entry from FileInfo."""
        return cls(
            name=file_info.name,
            path=str(file_info.relative_path),
            size=file_info.formatted_size,
            created=file_info.created_date.strftime("%Y-%m-%d %H:%M:%S"),
            modified=file_info.modified_date.strftime("%Y-%m-%d %H:%M:%S"),
            extension=file_info.extension or "(none)"
        )

@dataclass
class ScanInfo:
    """Information about a scan."""
    timestamp: str
    root_path: str
    total_files: int
    total_size: str

class DatabaseObserver(Protocol):
    """Protocol for database observers."""
    def on_entries_added(self, entries: List[DatabaseEntry]): ...
    def on_database_cleared(self): ...
    def set_scan_time(self, timestamp: str): ...

class DatabaseService:
    """Service for managing file scan data."""
    
    BATCH_SIZE = 1000
    MAX_SCAN_AGE_DAYS = 30  # Keep scans for 30 days
    
    def __init__(self, logger=None):
        """Initialize database service.
        
        Args:
            logger: Optional logger service
        """
        self._observers: List[DatabaseObserver] = []
        self._entries: List[DatabaseEntry] = []
        self.logger = logger
        self._current_scan: Optional[ScanInfo] = None
        
        # Ensure data directory exists
        self.data_dir = Path("data")
        self.data_dir.mkdir(exist_ok=True)
        
        # Set database path
        self.db_path = self.data_dir / "scan_history.db"
        
        if self.logger:
            self.logger.log_action(f"Database path: {self.db_path}")
        
        self._init_db()
        self._cleanup_old_scans()
    
    def _init_db(self):
        """Initialize SQLite database."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                # Enable foreign keys
                conn.execute("PRAGMA foreign_keys = ON")
                
                # Create tables
                conn.execute("""
                    CREATE TABLE IF NOT EXISTS scans (
                        id INTEGER PRIMARY KEY,
                        scan_date TIMESTAMP,
                        root_path TEXT,
                        total_files INTEGER,
                        total_size TEXT
                    )
                """)
                conn.execute("""
                    CREATE TABLE IF NOT EXISTS files (
                        id INTEGER PRIMARY KEY,
                        scan_id INTEGER,
                        name TEXT,
                        path TEXT,
                        size TEXT,
                        created TEXT,
                        modified TEXT,
                        extension TEXT,
                        FOREIGN KEY (scan_id) REFERENCES scans(id) ON DELETE CASCADE
                    )
                """)
                
                # Create index on scan_date for faster cleanup
                conn.execute("""
                    CREATE INDEX IF NOT EXISTS idx_scan_date 
                    ON scans(scan_date)
                """)
                
                if self.logger:
                    self.logger.log_action("Database initialized")
                
        except Exception as e:
            if self.logger:
                self.logger.log_error(f"Failed to initialize database: {str(e)}")
            raise
    
    def _cleanup_old_scans(self):
        """Remove scans older than MAX_SCAN_AGE_DAYS."""
        try:
            cutoff_date = (
                datetime.now() - timedelta(days=self.MAX_SCAN_AGE_DAYS)
            ).strftime("%Y-%m-%d %H:%M:%S")
            
            with sqlite3.connect(self.db_path) as conn:
                # Get count of old scans
                cursor = conn.execute(
                    "SELECT COUNT(*) FROM scans WHERE scan_date < ?",
                    (cutoff_date,)
                )
                old_scan_count = cursor.fetchone()[0]
                
                if old_scan_count > 0:
                    # Delete old scans (cascade will handle files)
                    conn.execute(
                        "DELETE FROM scans WHERE scan_date < ?",
                        (cutoff_date,)
                    )
                    
                    if self.logger:
                        self.logger.log_action(
                            f"Cleaned up {old_scan_count} scans older than {self.MAX_SCAN_AGE_DAYS} days"
                        )
        
        except Exception as e:
            if self.logger:
                self.logger.log_error(f"Failed to cleanup old scans: {str(e)}")
    
    def has_data(self) -> bool:
        """Check if database has any scan data."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.execute("SELECT COUNT(*) FROM scans")
                count = cursor.fetchone()[0]
                return count > 0
        except Exception:
            return False
    
    def get_last_scan_info(self) -> Optional[ScanInfo]:
        """Get information about the last scan without loading data."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.execute(
                    """
                    SELECT scan_date, root_path, total_files, total_size 
                    FROM scans ORDER BY scan_date DESC LIMIT 1
                    """
                )
                row = cursor.fetchone()
                if row:
                    scan_date, root_path, total_files, total_size = row
                    return ScanInfo(
                        timestamp=scan_date,
                        root_path=root_path,
                        total_files=total_files,
                        total_size=total_size
                    )
        except Exception as e:
            if self.logger:
                self.logger.log_error(f"Failed to get last scan info: {str(e)}")
        return None
    
    def load_last_scan(self) -> Optional[ScanInfo]:
        """Load the most recent scan from database."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                # Get last scan ID
                cursor = conn.execute(
                    """
                    SELECT id, scan_date, root_path, total_files, total_size 
                    FROM scans ORDER BY scan_date DESC LIMIT 1
                    """
                )
                row = cursor.fetchone()
                if row:
                    scan_id, scan_date, root_path, total_files, total_size = row
                    
                    # Create scan info
                    self._current_scan = ScanInfo(
                        timestamp=scan_date,
                        root_path=root_path,
                        total_files=total_files,
                        total_size=total_size
                    )
                    
                    if self.logger:
                        self.logger.log_action(
                            f"Loading scan from {scan_date}\n"
                            f"Path: {root_path}\n"
                            f"Files: {total_files:,}\n"
                            f"Size: {total_size}"
                        )
                    
                    # Notify observers of scan time
                    for observer in self._observers:
                        observer.set_scan_time(scan_date)
                    
                    # Load files from this scan
                    cursor = conn.execute(
                        "SELECT name, path, size, created, modified, extension FROM files WHERE scan_id = ?",
                        (scan_id,)
                    )
                    entries = [
                        DatabaseEntry(*row)
                        for row in cursor.fetchall()
                    ]
                    
                    # Notify observers in batches
                    for i in range(0, len(entries), self.BATCH_SIZE):
                        batch = entries[i:i + self.BATCH_SIZE]
                        self._entries.extend(batch)
                        self._notify_batch_added(batch)
                    
                    return self._current_scan
                else:
                    if self.logger:
                        self.logger.log_action("No previous scans found")
                    
        except Exception as e:
            if self.logger:
                self.logger.log_error(f"Failed to load last scan: {str(e)}")
        return None
    
    def add_observer(self, observer: DatabaseObserver):
        """Add an observer for database updates."""
        self._observers.append(observer)
    
    def remove_observer(self, observer: DatabaseObserver):
        """Remove an observer."""
        self._observers.remove(observer)
    
    def clear(self):
        """Clear all entries."""
        self._entries.clear()
        self._current_scan = None
        for observer in self._observers:
            observer.on_database_cleared()
    
    def process_scan_result(self, result: ScanResult):
        """Process scan result and update database."""
        self.clear()
        
        try:
            # Save scan to database
            scan_date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            
            with sqlite3.connect(self.db_path) as conn:
                # Insert scan record
                cursor = conn.execute(
                    """
                    INSERT INTO scans (scan_date, root_path, total_files, total_size)
                    VALUES (?, ?, ?, ?)
                    """,
                    (
                        scan_date,
                        str(result.root_path),
                        result.total_files,
                        result.formatted_total_size
                    )
                )
                scan_id = cursor.lastrowid
                
                # Update current scan info
                self._current_scan = ScanInfo(
                    timestamp=scan_date,
                    root_path=str(result.root_path),
                    total_files=result.total_files,
                    total_size=result.formatted_total_size
                )
                
                # Notify observers of scan time
                for observer in self._observers:
                    observer.set_scan_time(scan_date)
                
                # Insert files in batches
                batch = []
                for file_info in result.files:
                    entry = DatabaseEntry.from_file_info(file_info)
                    self._entries.append(entry)
                    batch.append(entry)
                    
                    if len(batch) >= self.BATCH_SIZE:
                        # Save batch to database
                        conn.executemany(
                            """
                            INSERT INTO files (scan_id, name, path, size, created, modified, extension)
                            VALUES (?, ?, ?, ?, ?, ?, ?)
                            """,
                            [
                                (scan_id, e.name, e.path, e.size, e.created, e.modified, e.extension)
                                for e in batch
                            ]
                        )
                        # Notify observers
                        self._notify_batch_added(batch)
                        batch = []
                
                # Process remaining entries
                if batch:
                    conn.executemany(
                        """
                        INSERT INTO files (scan_id, name, path, size, created, modified, extension)
                        VALUES (?, ?, ?, ?, ?, ?, ?)
                        """,
                        [
                            (scan_id, e.name, e.path, e.size, e.created, e.modified, e.extension)
                            for e in batch
                        ]
                    )
                    self._notify_batch_added(batch)
        
        except Exception as e:
            if self.logger:
                self.logger.log_error(f"Failed to save scan: {str(e)}")
            raise
    
    def _notify_batch_added(self, entries: List[DatabaseEntry]):
        """Notify observers of new entries."""
        for observer in self._observers:
            observer.on_entries_added(entries)
    
    @property
    def columns(self) -> List[str]:
        """Get database columns."""
        return ["Name", "Path", "Size", "Created", "Modified", "Extension"]
    
    def get_entries(self) -> Iterator[DatabaseEntry]:
        """Get all entries."""
        yield from self._entries
    
    @property
    def current_scan(self) -> Optional[ScanInfo]:
        """Get information about the current scan."""
        return self._current_scan
