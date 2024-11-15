"""Test script for scanning and database updates."""
from PySide6.QtWidgets import QApplication
import sys
from pathlib import Path

from file_scanner.services import DatabaseService
from file_scanner.core.scanner import FileScanner
from file_scanner.ui.panels.database_panel import DatabasePanel

def main():
    """Run scan test."""
    try:
        # Initialize Qt
        app = QApplication(sys.argv)
        
        # Create services
        db_service = DatabaseService()
        
        # Create panel
        panel = DatabasePanel(db_service)
        panel.show()
        
        # Scan current directory
        scanner = FileScanner(".")
        result = scanner.scan()
        
        # Update database
        db_service.process_scan_result(result)
        
        print(f"\nScanned {result.total_files} files")
        print(f"Total size: {result.formatted_total_size}")
        
        # Start Qt event loop
        return app.exec()
        
    except Exception as e:
        print(f"\n✗ Error: {str(e)}")
        import traceback
        traceback.print_exc()
        return 1

if __name__ == '__main__':
    sys.exit(main())
