"""GUI implementation using PySide6."""
from typing import Optional
import signal

from PySide6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout,
    QHBoxLayout, QSplitter, QStatusBar,
    QMessageBox, QApplication
)
from PySide6.QtCore import QThread, Signal, Qt, QTimer
from PySide6.QtGui import QCloseEvent

from ..core.models import ScanOptions, ScanResult
from ..core.scanner import FileScanner
from ..services import DatabaseService
from ..services.logger_service import LoggerService
from .panels import (
    ScanPanel, ResultsPanel,
    ConfigPanel, DatabasePanel
)
from .progress import ProgressHandler
from .theme import COMBINED_STYLE

class ScanWorker(QThread):
    """Worker thread for file scanning operations."""
    
    scan_completed = Signal(object)  # Emits ScanResult
    scan_error = Signal(str)  # Emits error message
    
    def __init__(self, path: str, options: Optional[ScanOptions] = None):
        super().__init__()
        self.path = path
        self.options = options or ScanOptions()
        self.progress_handler = ProgressHandler()
    
    def run(self):
        """Execute the scan operation."""
        try:
            # Create scanner with progress handler
            scanner = FileScanner(
                self.path, 
                self.options,
                progress_updater=self.progress_handler
            )
            
            # Execute scan
            result = scanner.scan()
            self.scan_completed.emit(result)
            
        except Exception as e:
            self.scan_error.emit(str(e))

class MainWindow(QMainWindow):
    """Main application window."""
    
    def __init__(self):
        super().__init__()
        self.setWindowTitle("File Scanner")
        self.setMinimumSize(1200, 800)
        
        # Apply theme
        QApplication.instance().setStyleSheet(COMBINED_STYLE)
        
        # Initialize services
        self.logger = LoggerService()
        self.database_service = DatabaseService(self.logger)
        
        # Initialize UI
        self._init_ui()
        
        # Initialize state
        self.current_scan: Optional[ScanWorker] = None
        self.current_options = ScanOptions()
        
        # Setup signal handlers
        signal.signal(signal.SIGINT, self._handle_sigint)
        
        # Setup status bar update timer
        self._setup_status_timer()
        
        # Log application start
        self.logger.log_action("Application started")
        
        # Show initial status
        if self.database_service.has_data():
            scan_info = self.database_service.get_last_scan_info()
            if scan_info:
                self.status_bar.showMessage(
                    f"Previous scan available: {scan_info.total_files:,} files from {scan_info.timestamp}",
                    5000
                )
            else:
                self.status_bar.showMessage("Ready", 5000)
        else:
            self.status_bar.showMessage("Ready - No previous scans found", 5000)
    
    def _init_ui(self):
        """Initialize the user interface."""
        # Create central widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(8, 8, 8, 8)
        main_layout.setSpacing(8)
        
        # Create scan controls at top
        self.scan_panel = ScanPanel()
        self.scan_panel.setMaximumHeight(60)  # Slightly taller for better visibility
        main_layout.addWidget(self.scan_panel)
        
        # Create main splitter
        main_splitter = QSplitter(Qt.Horizontal)
        main_splitter.setChildrenCollapsible(False)
        main_splitter.setHandleWidth(2)  # Thinner splitter handle
        
        # Left side - Config and Results
        left_splitter = QSplitter(Qt.Vertical)
        left_splitter.setChildrenCollapsible(False)
        left_splitter.setHandleWidth(2)  # Thinner splitter handle
        
        # Config panel
        self.config_panel = ConfigPanel()
        self.config_panel.setMaximumHeight(300)  # Limit height
        left_splitter.addWidget(self.config_panel)
        
        # Results panel
        self.results_panel = ResultsPanel()
        left_splitter.addWidget(self.results_panel)
        
        # Set size ratio (40% config, 60% results)
        left_splitter.setSizes([120, 180])
        
        main_splitter.addWidget(left_splitter)
        
        # Right side - Database view
        self.database_panel = DatabasePanel(self.database_service, self.logger)
        main_splitter.addWidget(self.database_panel)
        
        # Set initial splitter sizes (30% left, 70% right)
        main_splitter.setSizes([300, 700])
        
        # Add splitter to main layout
        main_layout.addWidget(main_splitter)
        
        # Create status bar
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        
        # Connect signals
        self.scan_panel.scan_requested.connect(self._start_scan)
        self.config_panel.config_changed.connect(self._update_options)
    
    def _setup_status_timer(self):
        """Setup timer for status bar updates."""
        self.status_timer = QTimer(self)
        self.status_timer.timeout.connect(self._update_status)
        self.status_timer.start(1000)  # Update every second
    
    def _update_status(self):
        """Update status bar with current state."""
        if self.current_scan and self.current_scan.isRunning():
            memory = self.current_scan.thread().stackSize() / (1024 * 1024)  # MB
            self.status_bar.showMessage(f"Scanning... (Memory: {memory:.1f} MB)")
    
    def _update_options(self, options: ScanOptions):
        """Update current scan options."""
        self.current_options = options
        self.status_bar.showMessage("Scan options updated", 3000)
        self.logger.log_action("Scan options updated")
    
    def _start_scan(self, path: str):
        """Start the scanning process."""
        # Update UI state
        self.scan_panel.set_scanning(True)
        self.status_bar.showMessage("Starting scan...")
        
        # Log scan start
        self.logger.log_scan_start(path)
        
        # Clear previous results
        self.database_service.clear()
        
        # Start scan in worker thread with current options
        self.current_scan = ScanWorker(path, self.current_options)
        
        # Connect signals
        self.current_scan.scan_completed.connect(self._handle_scan_completed)
        self.current_scan.scan_error.connect(self._handle_scan_error)
        self.current_scan.progress_handler.progress_updated.connect(
            self.results_panel.update_progress
        )
        
        # Start scanning
        self.current_scan.start()
    
    def _handle_scan_completed(self, result: ScanResult):
        """Handle scan completion."""
        # Update UI
        self.scan_panel.set_scanning(False)
        self.results_panel.show_results(result)
        
        # Update database through service
        self.database_service.process_scan_result(result)
        
        # Log completion
        self.logger.log_scan_complete(
            result.total_files,
            result.formatted_total_size
        )
        
        self.status_bar.showMessage(
            f"Scan completed - {result.total_files:,} files, {result.formatted_total_size}",
            5000
        )
        
        # Cleanup
        self.current_scan = None
    
    def _handle_scan_error(self, error_msg: str):
        """Handle scan errors."""
        # Update UI
        self.scan_panel.set_scanning(False)
        self.results_panel.show_error(error_msg)
        self.status_bar.showMessage(f"Error: {error_msg}", 5000)
        
        # Log error
        self.logger.log_error(error_msg)
        
        # Show error dialog
        QMessageBox.critical(
            self,
            "Scan Error",
            f"An error occurred during scanning:\n\n{error_msg}"
        )
        
        # Cleanup
        self.current_scan = None
    
    def _handle_sigint(self, signum, frame):
        """Handle interrupt signal."""
        self.close()
    
    def closeEvent(self, event: QCloseEvent):
        """Handle window close event."""
        if self.current_scan and self.current_scan.isRunning():
            reply = QMessageBox.question(
                self,
                "Confirm Exit",
                "A scan is currently in progress. Are you sure you want to exit?",
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.No
            )
            
            if reply == QMessageBox.Yes:
                # Stop the scan
                self.current_scan.terminate()
                self.current_scan.wait()
                event.accept()
            else:
                event.ignore()
        else:
            self.logger.log_action("Application closed")
            event.accept()
