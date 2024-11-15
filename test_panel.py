"""Test script for DatabasePanel inheritance."""
from PySide6.QtWidgets import QApplication
import sys

from file_scanner.ui.widgets.panel_widget import PanelWidget
from file_scanner.services.database_service import DatabaseObserver, DatabaseEntry
from typing import List

# Debug metaclasses
print("\nDebugging metaclasses:")
print(f"PanelWidget metaclass: {type(PanelWidget)}")
print(f"DatabaseObserver metaclass: {type(DatabaseObserver)}")

class TestPanel(PanelWidget, DatabaseObserver):
    """Test panel with multiple inheritance."""
    
    def __init__(self):
        # Initialize both parent classes
        PanelWidget.__init__(self, "Test")
        # No need to call DatabaseObserver.__init__ as it's an ABC
    
    def on_entries_added(self, entries: List[DatabaseEntry]):
        print("Entries added")
    
    def on_database_cleared(self):
        print("Database cleared")

def main():
    """Run the test."""
    try:
        app = QApplication(sys.argv)
        panel = TestPanel()
        print("\nTest Results:")
        print("✓ Panel creation successful")
        print("✓ Multiple inheritance working")
        
        # Test observer methods
        panel.on_database_cleared()
        panel.on_entries_added([])
        print("✓ Observer methods working")
        
        return 0
    except Exception as e:
        print(f"\n✗ Error: {str(e)}")
        print(f"✗ Error type: {type(e)}")
        import traceback
        traceback.print_exc()
        return 1

if __name__ == '__main__':
    sys.exit(main())
