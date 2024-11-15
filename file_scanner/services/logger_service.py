"""Logging service for tracking application events."""
import logging
from datetime import datetime
from pathlib import Path
from typing import Optional

class LoggerService:
    """Service for logging application events."""
    
    def __init__(self, log_file: Optional[str] = None):
        """Initialize logger.
        
        Args:
            log_file: Optional path to log file. If None, logs to 'app.log'
        """
        # Create logger
        self.logger = logging.getLogger('FileScanner')
        self.logger.setLevel(logging.INFO)
        
        # Create formatters
        file_formatter = logging.Formatter(
            '%(asctime)s - %(levelname)s - %(message)s'
        )
        console_formatter = logging.Formatter(
            '%(message)s'
        )
        
        # File handler
        if not log_file:
            log_file = 'app.log'
        
        file_handler = logging.FileHandler(log_file, encoding='utf-8')
        file_handler.setLevel(logging.INFO)
        file_handler.setFormatter(file_formatter)
        self.logger.addHandler(file_handler)
        
        # Console handler
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.INFO)
        console_handler.setFormatter(console_formatter)
        self.logger.addHandler(console_handler)
    
    def log_filter(self, column: str, text: str, matches: int, total: int = None):
        """Log filter operation.
        
        Args:
            column: Column being filtered
            text: Filter text
            matches: Number of matches found
            total: Total number of rows (optional)
        """
        if total:
            percentage = (matches / total) * 100 if total > 0 else 0
            self.logger.info(
                f"Filter: {column}='{text}' | {matches}/{total} matches ({percentage:.1f}%)"
            )
        else:
            self.logger.info(
                f"Filter: {column}='{text}' | {matches} matches"
            )
    
    def log_scan_start(self, path: str):
        """Log scan start.
        
        Args:
            path: Directory being scanned
        """
        self.logger.info(f"Starting scan of: {path}")
    
    def log_scan_complete(self, total_files: int, total_size: str):
        """Log scan completion.
        
        Args:
            total_files: Number of files scanned
            total_size: Total size of files (formatted)
        """
        self.logger.info(
            f"Scan complete: {total_files:,} files, {total_size}"
        )
    
    def log_error(self, error: str):
        """Log error message.
        
        Args:
            error: Error message
        """
        self.logger.error(f"Error: {error}")
    
    def log_action(self, action: str):
        """Log user action.
        
        Args:
            action: Description of action
        """
        self.logger.info(f"Action: {action}")
    
    def log_filter_no_matches(self, column: str, text: str, suggestion: Optional[str] = None):
        """Log when a filter returns no matches.
        
        Args:
            column: Column that was filtered
            text: Filter text that produced no matches
            suggestion: Optional suggestion for user
        """
        msg = f"No matches found for filter: {column}='{text}'"
        if suggestion:
            msg += f"\nSuggestion: {suggestion}"
        self.logger.info(msg)
