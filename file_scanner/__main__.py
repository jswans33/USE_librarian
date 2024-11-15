"""Main entry point for running file_scanner as a module."""
import sys
from PySide6.QtWidgets import QApplication

from .ui.cli import main as cli_main
from .ui.gui import MainWindow

def main():
    """Entry point with interface selection."""
    # Check for --cli flag
    if len(sys.argv) > 1 and sys.argv[1] == '--cli':
        cli_main()
        return

    # Default to GUI
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())

if __name__ == '__main__':
    main()
