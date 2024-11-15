"""Test script for database filtering with logging."""
from PySide6.QtWidgets import QApplication
import sys
from pathlib import Path

from file_scanner.services import DatabaseService, LoggerService
from file_scanner.core.scanner import FileScanner
from file_scanner.ui.panels.database_panel import DatabasePanel

def main():
    """Run filter test."""
    try:
        # Initialize Qt
        app = QApplication(sys.argv)
        
        # Create services
        db_service = DatabaseService()
        logger = LoggerService()
        
        # Create panel
        panel = DatabasePanel(db_service, logger)
        panel.show()
        
        # Log test start
        logger.log_action("Filter test started")
        
        # Scan current directory
        scanner = FileScanner(".")
        result = scanner.scan()
        
        # Update database
        db_service.process_scan_result(result)
        
        # Test filters
        test_filters = [
            ("Name", ".py"),      # Python files
            ("Size", "KB"),       # Kilobyte files
            ("Extension", "txt"), # Text files
            ("Name", "xyz123")    # Should find no matches
        ]
        
        print("\nTesting filters...")
        for column, text in test_filters:
            print(f"\nApplying filter: {column}='{text}'")
            panel.table_view.set_filter(column, text)
            
            # Process events to allow filter to apply
            app.processEvents()
        
        print("\nCheck app.log for filter results")
        
        # Start Qt event loop
        return app.exec()
        
    except Exception as e:
        print(f"\n✗ Error: {str(e)}")
        import traceback
        traceback.print_exc()
        return 1

if __name__ == '__main__':
    sys.exit(main())
