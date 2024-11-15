"""Database service for managing file scan data."""
import sqlite3
from dataclasses import dataclass, asdict
from datetime import datetime, timedelta
from typing import List, Iterator, Optional, Protocol, Tuple, Set
from pathlib import Path
import json
import os

from ..core.models import FileInfo, ScanResult
from ..core.metadata import MetadataService, FileMetadata, FileTag, FilePattern
from ..core.directory_parser import DirectoryGroup

@dataclass
class DatabaseEntry:
    """Represents a database entry for a file."""
    name: str
    path: str
    size: str
    created: str
    modified: str
    extension: str
    tags: Set[str] = None  # Tag names
    category: Optional[str] = None
    subcategory: Optional[str] = None
    patterns: Set[str] = None  # Pattern descriptions
    parsed_info: Optional[str] = None  # Formatted parsed name info
    directory_info: Optional[str] = None  # Formatted directory group info

    @classmethod
    def from_file_info(cls, file_info: FileInfo, metadata: Optional[FileMetadata] = None) -> 'DatabaseEntry':
        """Create a database entry from FileInfo."""
        entry = cls(
            name=file_info.name,
            path=str(file_info.relative_path),
            size=file_info.formatted_size,
            created=file_info.created_date.strftime("%Y-%m-%d %H:%M:%S"),
            modified=file_info.modified_date.strftime("%Y-%m-%d %H:%M:%S"),
            extension=file_info.extension or "(none)"
        )
        
        if metadata:
            entry.tags = {tag.name for tag in metadata.tags}
            entry.category = metadata.category
            entry.subcategory = metadata.subcategory
            entry.patterns = {pattern.description for pattern in metadata.patterns}
            if metadata.parsed_name:
                from ..core.file_parser import FileNameParser
                entry.parsed_info = FileNameParser().format_parsed_name(metadata.parsed_name)
            if metadata.directory_group:
                from ..core.directory_parser import DirectoryAnalyzer
                analyzer = DirectoryAnalyzer()
                entry.directory_info = analyzer.format_group_info(metadata.directory_group)
        
        return entry

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
    CURRENT_VERSION = 4  # Increment when schema changes
    
    def __init__(self, logger=None):
        """Initialize database service."""
        self._observers: List[DatabaseObserver] = []
        self._entries: List[DatabaseEntry] = []
        self.logger = logger
        self._current_scan: Optional[ScanInfo] = None
        self.metadata_service = MetadataService()
        
        # Ensure data directory exists
        self.data_dir = Path("data")
        self.data_dir.mkdir(exist_ok=True)
        
        # Set database path
        self.db_path = self.data_dir / "scan_history.db"
        
        if self.logger:
            self.logger.log_action(f"Database path: {self.db_path}")
        
        self.init_db()
        self.cleanup_old_scans()
    
    def add_observer(self, observer: DatabaseObserver) -> None:
        """Add an observer for database updates."""
        if observer not in self._observers:
            self._observers.append(observer)
            # Update new observer with current scan info
            if self._current_scan:
                observer.set_scan_time(self._current_scan.timestamp)
    
    def remove_observer(self, observer: DatabaseObserver) -> None:
        """Remove an observer."""
        if observer in self._observers:
            self._observers.remove(observer)
    
    def clear(self) -> None:
        """Clear all entries."""
        self._entries.clear()
        self._current_scan = None
        for observer in self._observers:
            observer.on_database_cleared()
    
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
                        """
                        SELECT name, path, size, created, modified, extension,
                               tags, category, subcategory, patterns, parsed_info,
                               directory_info
                        FROM files WHERE scan_id = ?
                        """,
                        (scan_id,)
                    )
                    entries = []
                    for row in cursor:
                        entry = DatabaseEntry(
                            name=row[0],
                            path=row[1],
                            size=row[2],
                            created=row[3],
                            modified=row[4],
                            extension=row[5],
                            tags=set(json.loads(row[6])) if row[6] else set(),
                            category=row[7],
                            subcategory=row[8],
                            patterns=set(json.loads(row[9])) if row[9] else set(),
                            parsed_info=row[10],
                            directory_info=row[11]
                        )
                        entries.append(entry)
                    
                    # Notify observers in batches
                    for i in range(0, len(entries), self.BATCH_SIZE):
                        batch = entries[i:i + self.BATCH_SIZE]
                        self._entries.extend(batch)
                        self.notify_batch_added(batch)
                    
                    return self._current_scan
                else:
                    if self.logger:
                        self.logger.log_action("No previous scans found")
                    
        except Exception as e:
            if self.logger:
                self.logger.log_error(f"Failed to load last scan: {str(e)}")
        return None
    
    def init_db(self) -> None:
        """Initialize SQLite database."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                # Enable foreign keys
                conn.execute("PRAGMA foreign_keys = ON")
                
                # Create version table if it doesn't exist
                conn.execute("""
                    CREATE TABLE IF NOT EXISTS version (
                        id INTEGER PRIMARY KEY CHECK (id = 1),
                        version INTEGER NOT NULL
                    )
                """)
                
                # Get current version
                cursor = conn.execute("SELECT version FROM version WHERE id = 1")
                row = cursor.fetchone()
                current_version = row[0] if row else 0
                
                # Perform migrations if needed
                if current_version < self.CURRENT_VERSION:
                    self._migrate_database(conn, current_version)
                
                if self.logger:
                    self.logger.log_action("Database initialized")
                
        except Exception as e:
            if self.logger:
                self.logger.log_error(f"Failed to initialize database: {str(e)}")
            raise
    
    def _migrate_database(self, conn: sqlite3.Connection, from_version: int) -> None:
        """Migrate database schema to current version."""
        try:
            if from_version == 0:
                # Initial schema
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
                from_version = 1
            
            if from_version == 1:
                # Add metadata columns
                conn.execute("ALTER TABLE files ADD COLUMN tags TEXT")
                conn.execute("ALTER TABLE files ADD COLUMN category TEXT")
                conn.execute("ALTER TABLE files ADD COLUMN patterns TEXT")
                
                # Create indexes
                conn.execute("""
                    CREATE INDEX IF NOT EXISTS idx_scan_date 
                    ON scans(scan_date)
                """)
                conn.execute("""
                    CREATE INDEX IF NOT EXISTS idx_tags
                    ON files(tags)
                """)
                from_version = 2
            
            if from_version == 2:
                # Add new metadata columns
                conn.execute("ALTER TABLE files ADD COLUMN subcategory TEXT")
                conn.execute("ALTER TABLE files ADD COLUMN parsed_info TEXT")
                
                # Create index on category
                conn.execute("""
                    CREATE INDEX IF NOT EXISTS idx_category
                    ON files(category, subcategory)
                """)
                from_version = 3
            
            if from_version == 3:
                # Add directory info column
                conn.execute("ALTER TABLE files ADD COLUMN directory_info TEXT")
                from_version = 4
            
            # Update version
            conn.execute("DELETE FROM version")
            conn.execute(
                "INSERT INTO version (id, version) VALUES (1, ?)",
                (self.CURRENT_VERSION,)
            )
            
            if self.logger:
                self.logger.log_action(f"Database migrated to version {self.CURRENT_VERSION}")
        
        except Exception as e:
            if self.logger:
                self.logger.log_error(f"Failed to migrate database: {str(e)}")
            raise
    
    def cleanup_old_scans(self) -> None:
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
    
    def notify_batch_added(self, entries: List[DatabaseEntry]) -> None:
        """Notify observers of new entries."""
        for observer in self._observers:
            observer.on_entries_added(entries)
    
    def process_scan_result(self, result: ScanResult) -> None:
        """Process scan result and update database."""
        self.clear()
        
        try:
            # Save scan to database
            scan_date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            
            # Analyze directory structure first
            root_path = Path(result.root_path)
            directory_group = self.metadata_service.analyze_directory(root_path)
            
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
                    # Analyze file metadata
                    metadata = self.metadata_service.analyze_file(
                        Path(result.root_path) / file_info.relative_path
                    )
                    
                    # Create entry
                    entry = DatabaseEntry.from_file_info(file_info, metadata)
                    self._entries.append(entry)
                    batch.append((entry, metadata))
                    
                    if len(batch) >= self.BATCH_SIZE:
                        # Save batch to database
                        self._save_batch(conn, scan_id, batch)
                        # Notify observers
                        self.notify_batch_added([e for e, _ in batch])
                        batch = []
                
                # Process remaining entries
                if batch:
                    self._save_batch(conn, scan_id, batch)
                    self.notify_batch_added([e for e, _ in batch])
        
        except Exception as e:
            if self.logger:
                self.logger.log_error(f"Failed to save scan: {str(e)}")
            raise
    
    def _save_batch(self, conn: sqlite3.Connection, scan_id: int, 
                   batch: List[Tuple[DatabaseEntry, FileMetadata]]) -> None:
        """Save a batch of entries to database."""
        conn.executemany(
            """
            INSERT INTO files (
                scan_id, name, path, size, created, modified, extension,
                tags, category, subcategory, patterns, parsed_info, directory_info
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            [
                (
                    scan_id,
                    entry.name,
                    entry.path,
                    entry.size,
                    entry.created,
                    entry.modified,
                    entry.extension,
                    json.dumps(list(entry.tags)) if entry.tags else None,
                    entry.category,
                    entry.subcategory,
                    json.dumps(list(entry.patterns)) if entry.patterns else None,
                    entry.parsed_info,
                    entry.directory_info
                )
                for entry, _ in batch
            ]
        )
    
    @property
    def columns(self) -> List[str]:
        """Get database columns."""
        return [
            "Name", "Path", "Size", "Created", "Modified", 
            "Extension", "Category", "Subcategory", "Tags", 
            "Patterns", "Parsed Info", "Directory Info"
        ]
    
    def get_entries(self) -> Iterator[DatabaseEntry]:
        """Get all entries."""
        yield from self._entries
    
    @property
    def current_scan(self) -> Optional[ScanInfo]:
        """Get information about the current scan."""
        return self._current_scan
    
    def get_all_tags(self) -> Set[str]:
        """Get all unique tags in the database."""
        return self.metadata_service.get_all_tags()
    
    def get_all_patterns(self) -> List[FilePattern]:
        """Get all detected patterns."""
        return self.metadata_service.get_all_patterns()
    
    def get_files_by_tag(self, tag: str) -> List[DatabaseEntry]:
        """Get all files with a specific tag."""
        return [
            entry for entry in self._entries
            if entry.tags and tag in entry.tags
        ]
    
    def get_files_by_pattern(self, pattern: str) -> List[DatabaseEntry]:
        """Get all files with a specific pattern."""
        return [
            entry for entry in self._entries
            if entry.patterns and pattern in entry.patterns
        ]
    
    def get_files_by_category(self, category: str) -> List[DatabaseEntry]:
        """Get all files in a specific category."""
        return [
            entry for entry in self._entries
            if entry.category == category
        ]
