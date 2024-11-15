"""Panel for scan controls and options."""
from pathlib import Path
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QLineEdit, QFileDialog,
    QStyle, QSizePolicy
)
from PySide6.QtCore import Signal, Qt

class ScanPanel(QWidget):
    """Panel containing scan controls."""
    
    scan_requested = Signal(str)  # Emits directory path
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self._init_ui()
    
    def _init_ui(self):
        """Initialize the user interface."""
        layout = QHBoxLayout(self)
        layout.setContentsMargins(4, 4, 4, 4)
        layout.setSpacing(4)
        
        # Path input with placeholder and tooltip
        self.path_input = QLineEdit()
        self.path_input.setPlaceholderText("Select directory to scan...")
        self.path_input.setToolTip("Enter or browse for a directory to scan")
        self.path_input.setSizePolicy(
            QSizePolicy.Expanding,  # Horizontal stretch
            QSizePolicy.Fixed       # Fixed vertical size
        )
        self.path_input.setMinimumWidth(400)  # Minimum width
        layout.addWidget(self.path_input)
        
        # Browse button with icon
        browse_button = QPushButton()
        browse_button.setIcon(self.style().standardIcon(QStyle.SP_DirIcon))
        browse_button.setToolTip("Browse for directory")
        browse_button.setFixedWidth(40)  # Make it square-ish
        browse_button.clicked.connect(self._browse_directory)
        layout.addWidget(browse_button)
        
        # Scan button with icon
        self.scan_button = QPushButton("Scan")
        self.scan_button.setIcon(self.style().standardIcon(QStyle.SP_BrowserReload))
        self.scan_button.setToolTip("Start scanning the selected directory")
        self.scan_button.setFixedWidth(80)  # Fixed width for consistency
        self.scan_button.clicked.connect(self._request_scan)
        layout.addWidget(self.scan_button)
        
        # Enable scan on Enter key in path input
        self.path_input.returnPressed.connect(self._request_scan)
    
    def _browse_directory(self):
        """Open directory selection dialog."""
        directory = QFileDialog.getExistingDirectory(
            self,
            "Select Directory to Scan",
            str(Path.home()),
            QFileDialog.ShowDirsOnly | QFileDialog.DontResolveSymlinks
        )
        if directory:
            self.path_input.setText(directory)
            self.path_input.setToolTip(directory)  # Show full path on hover
    
    def _request_scan(self):
        """Emit scan request with selected path."""
        path = self.path_input.text()
        if path:
            self.scan_requested.emit(path)
    
    def set_scanning(self, is_scanning: bool):
        """Update UI state during scanning."""
        self.scan_button.setEnabled(not is_scanning)
        self.path_input.setEnabled(not is_scanning)
        if is_scanning:
            self.scan_button.setText("Scanning...")
            self.scan_button.setIcon(self.style().standardIcon(QStyle.SP_BrowserStop))
        else:
            self.scan_button.setText("Scan")
            self.scan_button.setIcon(self.style().standardIcon(QStyle.SP_BrowserReload))
